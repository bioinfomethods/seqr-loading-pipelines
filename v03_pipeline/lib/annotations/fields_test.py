import os
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

import hail as hl

from v03_pipeline.lib.annotations.fields import get_fields
from v03_pipeline.lib.model import AnnotationType, DatasetType, Env, ReferenceGenome
from v03_pipeline.lib.vep import run_vep

TEST_COMBINED_1 = 'v03_pipeline/var/test/reference_data/test_combined_1.ht'
TEST_HGMD_1 = 'v03_pipeline/var/test/reference_data/test_hgmd_1.ht'
TEST_INTERVAL_1 = 'v03_pipeline/var/test/reference_data/test_interval_1.ht'
LIFTOVER = 'v03_pipeline/var/test/liftover/grch38_to_grch37.over.chain.gz'


@patch('v03_pipeline.lib.paths.DataRoot')
class FieldsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_local_reference_data = tempfile.TemporaryDirectory().name
        shutil.copytree(
            TEST_HGMD_1,
            f'{self._temp_local_reference_data}/v03/GRCh38/reference_datasets/hgmd.ht',
        )
        shutil.copytree(
            TEST_INTERVAL_1,
            f'{self._temp_local_reference_data}/v03/GRCh38/reference_datasets/interval.ht',
        )

    def tearDown(self) -> None:
        if os.path.isdir(self._temp_local_reference_data):
            shutil.rmtree(self._temp_local_reference_data)

    def test_get_rdc_fields(self, mock_dataroot: Mock) -> None:
        mock_dataroot.LOCAL_REFERENCE_DATA.value = self._temp_local_reference_data
        ht = hl.Table.parallelize(
            [],
            hl.tstruct(
                locus=hl.tlocus(ReferenceGenome.GRCh38.value),
                alleles=hl.tarray(hl.tstr),
            ),
            key=('locus', 'alleles'),
        )
        self.assertCountEqual(
            list(
                get_fields(
                    ht,
                    AnnotationType.REFERENCE_DATASET_COLLECTION,
                    env=Env.TEST,
                    dataset_type=DatasetType.SNV,
                    reference_genome=ReferenceGenome.GRCh38,
                ).keys(),
            ),
            ['gnomad_non_coding_constraint', 'screen'],
        )
        self.assertCountEqual(
            list(
                get_fields(
                    ht,
                    AnnotationType.REFERENCE_DATASET_COLLECTION,
                    env=Env.LOCAL,
                    dataset_type=DatasetType.SNV,
                    reference_genome=ReferenceGenome.GRCh38,
                ).keys(),
            ),
            ['gnomad_non_coding_constraint', 'screen'],
        )
        self.assertCountEqual(
            list(
                get_fields(
                    ht,
                    AnnotationType.REFERENCE_DATASET_COLLECTION,
                    env=Env.TEST,
                    dataset_type=DatasetType.MITO,
                    reference_genome=ReferenceGenome.GRCh38,
                ).keys(),
            ),
            [],
        )

    def test_get_formatting_fields(self, mock_dataroot: Mock) -> None:
        mock_dataroot.LOCAL_REFERENCE_DATA.value = self._temp_local_reference_data
        ht = hl.read_table(TEST_COMBINED_1)
        ht = run_vep(
            ht,
            Env.TEST,
            ReferenceGenome.GRCh38,
            DatasetType.SNV,
            None,
        )
        ht = ht.annotate(rsid='abcd')
        self.assertCountEqual(
            list(
                get_fields(
                    ht,
                    AnnotationType.FORMATTING,
                    env=Env.TEST,
                    dataset_type=DatasetType.SNV,
                    reference_genome=ReferenceGenome.GRCh38,
                    liftover_ref_path=LIFTOVER,
                ).keys(),
            ),
            [
                'rg37_locus',
                'rsid',
                'sorted_transcript_consequences',
                'variant_id',
                'xpos',
            ],
        )
        self.assertCountEqual(
            list(
                get_fields(
                    ht,
                    AnnotationType.FORMATTING,
                    env=Env.TEST,
                    dataset_type=DatasetType.SNV,
                    reference_genome=ReferenceGenome.GRCh37,
                    liftover_ref_path=LIFTOVER,
                ).keys(),
            ),
            [
                'rsid',
                'sorted_transcript_consequences',
                'variant_id',
                'xpos',
            ],
        )

    @patch('v03_pipeline.lib.annotations.fields.hl.read_table')
    def test_get_sample_lookup_table_fields(
        self,
        mock_read_table: Mock,
        mock_dataroot: Mock,
    ) -> None:
        mock_dataroot.LOCAL_REFERENCE_DATA.value = self._temp_local_reference_data
        mock_read_table.return_value = hl.Table.parallelize(
            [
                {
                    'locus': hl.Locus('chr1', 1, ReferenceGenome.GRCh38.value),
                    'alleles': ['A', 'C'],
                    'ref_samples': hl.Struct(project_1={'a', 'c'}),
                    'het_samples': hl.Struct(project_1={'b', 'd'}),
                    'hom_samples': hl.Struct(project_1={'e', 'f'}),
                },
            ],
            hl.tstruct(
                locus=hl.tlocus(ReferenceGenome.GRCh38.value),
                alleles=hl.tarray(hl.tstr),
                ref_samples=hl.tstruct(project_1=hl.tset(hl.tstr)),
                het_samples=hl.tstruct(project_1=hl.tset(hl.tstr)),
                hom_samples=hl.tstruct(project_1=hl.tset(hl.tstr)),
            ),
            key=('locus', 'alleles'),
            globals=hl.Struct(
                updates=hl.set([hl.Struct(callset='abc', project_guid='project_1')]),
            ),
        )
        ht = hl.Table.parallelize(
            [],
            hl.tstruct(
                locus=hl.tlocus(ReferenceGenome.GRCh38.value),
                alleles=hl.tarray(hl.tstr),
            ),
            key=('locus', 'alleles'),
        )
        self.assertCountEqual(
            list(
                get_fields(
                    ht,
                    AnnotationType.SAMPLE_LOOKUP_TABLE,
                    env=Env.TEST,
                    dataset_type=DatasetType.SNV,
                    reference_genome=ReferenceGenome.GRCh38,
                ).keys(),
            ),
            ['gt_stats'],
        )
