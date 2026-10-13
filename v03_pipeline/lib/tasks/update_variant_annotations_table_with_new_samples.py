import hail as hl
import luigi
import luigi.util

from v03_pipeline.lib.annotations.fields import get_fields
from v03_pipeline.lib.logger import get_logger
from v03_pipeline.lib.misc.callsets import get_callset_ht
from v03_pipeline.lib.misc.io import remap_pedigree_hash
from v03_pipeline.lib.paths import (
    new_variants_table_path,
    project_pedigree_path,
    variant_annotations_table_path,
)
from v03_pipeline.lib.tasks.base.base_loading_run_params import (
    BaseLoadingRunParams,
)
from v03_pipeline.lib.tasks.base.base_update import (
    BaseUpdateTask,
)
from v03_pipeline.lib.tasks.files import GCSorLocalTarget
from v03_pipeline.lib.tasks.update_new_variants_with_caids import (
    UpdateNewVariantsWithCAIDsTask,
)
from v03_pipeline.lib.tasks.write_new_variants_table import WriteNewVariantsTableTask

logger = get_logger(__name__)


class StaleNewVariantsError(Exception):
    pass


def union_new_variants(
    ht: hl.Table,
    new_variants_ht: hl.Table,
    run_id: str,
) -> hl.Table:
    """Union a run's new variants into the annotations table without corrupting it.

    new_variants_ht is computed once per run (against the annotations table as it was
    then), assigned contiguous keys from that table's max_key_ + 1, and cached on disk.
    It is only safe to union if the annotations table hasn't changed since:

    * keys start at max_key_ + 1: the normal case, union as-is.
    * every variant is already present under the same key: this run's update was
      already applied (e.g. a re-run of the same run_id), so skip it rather than
      duplicate every row.
    * anything else: the table changed underneath this run (an overlapping or
      interleaved run, or a restored/wiped table). Unioning would give two different
      variants the same key, so fail instead.
    """
    stats = new_variants_ht.aggregate(
        hl.struct(
            n=hl.agg.count(),
            min_key_=hl.agg.min(new_variants_ht.key_),
            max_key_=hl.agg.max(new_variants_ht.key_),
        ),
    )
    if stats.n == 0:
        return ht
    curr_max_key_ = hl.eval(ht.max_key_)
    if stats.min_key_ == curr_max_key_ + 1:
        return ht.union(new_variants_ht, unify=True)
    if stats.max_key_ <= curr_max_key_:
        existing = ht[new_variants_ht.key]
        n_mismatched = new_variants_ht.aggregate(
            hl.agg.count_where(
                hl.is_missing(existing) | (existing.key_ != new_variants_ht.key_),
            ),
        )
        if n_mismatched == 0:
            logger.warning(
                f'All {stats.n} new variants for run {run_id} are already present '
                'in the annotations table with the same keys; the update was '
                'already applied, so skipping the union.',
            )
            return ht
    msg = (
        f'New variants for run {run_id} (keys {stats.min_key_}-{stats.max_key_}) '
        f'were computed against a different version of the annotations table '
        f'(current max_key_ is {curr_max_key_}). Another run has probably updated '
        'the table since; unioning would corrupt it. Re-run with a new run_id.'
    )
    raise StaleNewVariantsError(msg)


@luigi.util.inherits(BaseLoadingRunParams)
class UpdateVariantAnnotationsTableWithNewSamplesTask(
    BaseUpdateTask,
):
    def output(self) -> luigi.Target:
        return GCSorLocalTarget(
            variant_annotations_table_path(
                self.reference_genome,
                self.dataset_type,
            ),
        )

    def requires(self) -> list[luigi.Task]:
        return [
            *super().requires(),
            self.clone(UpdateNewVariantsWithCAIDsTask)
            if self.dataset_type.should_send_to_allele_registry
            else self.clone(WriteNewVariantsTableTask),
        ]

    def complete(self) -> bool:
        return super().complete() and hl.eval(
            hl.bind(
                lambda updates: hl.all(
                    [
                        updates.contains(
                            hl.Struct(
                                callset=self.callset_path,
                                project_guid=project_guid,
                                remap_pedigree_hash=remap_pedigree_hash(
                                    project_pedigree_path(
                                        self.reference_genome,
                                        self.dataset_type,
                                        self.sample_type,
                                        project_guid,
                                    ),
                                ),
                            ),
                        )
                        for project_guid in self.project_guids
                    ],
                ),
                hl.read_table(self.output().path).updates,
            ),
        )

    def initialize_table(self) -> hl.Table:
        key_type = self.dataset_type.table_key_type(self.reference_genome)
        return hl.Table.parallelize(
            [],
            key_type,
            key=key_type.fields,
            globals=hl.Struct(
                versions=hl.Struct(),
                enums=hl.Struct(),
                updates=hl.empty_set(
                    hl.tstruct(
                        callset=hl.tstr,
                        project_guid=hl.tstr,
                        remap_pedigree_hash=hl.tint32,
                    ),
                ),
                migrations=hl.empty_array(hl.tstr),
                max_key_=hl.int64(-1),
            ),
        )

    def update_table(self, ht: hl.Table) -> hl.Table:
        # Gracefully handle case for on-premises uses
        # where key_ field is not present and migration was not run.
        if not hasattr(ht, 'key_'):
            ht = ht.add_index(name='key_')
            ht = ht.annotate_globals(max_key_=(ht.count() - 1))

        new_variants_ht = hl.read_table(
            new_variants_table_path(
                self.reference_genome,
                self.dataset_type,
                self.run_id,
            ),
        )

        # Union with the new variants table and annotate with the lookup table.
        ht = union_new_variants(ht, new_variants_ht, self.run_id)

        if self.dataset_type.variant_frequency_annotation_fns:
            # new_variants_ht consists of variants present in the new callset, fully annotated,
            # but NOT present in the existing annotations table.
            # callset_variants_ht consists of variants present in the new callset, fully annotated,
            # and either present or not present in the existing annotations table.
            callset_ht = get_callset_ht(
                self.reference_genome,
                self.dataset_type,
                self.callset_path,
                self.project_guids,
            )
            callset_variants_ht = ht.semi_join(callset_ht)
            non_callset_variants_ht = ht.anti_join(callset_ht)
            callset_variants_ht = callset_variants_ht.annotate(
                **get_fields(
                    callset_variants_ht,
                    self.dataset_type.variant_frequency_annotation_fns,
                    callset_ht=callset_ht,
                    **self.param_kwargs,
                ),
            )
            ht = non_callset_variants_ht.union(callset_variants_ht, unify=True)

        new_variants_ht_globals = new_variants_ht.index_globals()
        return ht.select_globals(
            versions=new_variants_ht_globals.versions,
            enums=new_variants_ht_globals.enums,
            updates=ht.updates.union(new_variants_ht_globals.updates),
            migrations=ht.migrations,
            max_key_=ht.aggregate(hl.agg.max(ht.key_)),
        )
