from __future__ import annotations

import os

from v03_pipeline.lib.model import (
    AccessControl,
    DataRoot,
    DatasetType,
    Env,
    PipelineVersion,
    ReferenceDatasetCollection,
    ReferenceGenome,
)


def _v03_pipeline_prefix(
    env: Env,
    root: DataRoot,
    reference_genome: ReferenceGenome,
    dataset_type: DatasetType,
) -> str:
    if env == Env.LOCAL or env == Env.TEST:
        root = DataRoot.LOCAL_DATASETS
    if env == Env.DEV:
        root = DataRoot.SEQR_SCRATCH_TEMP
    return os.path.join(
        root.value,
        reference_genome.value,
        PipelineVersion.V03.value,
        dataset_type.value,
    )


def _v03_reference_data_prefix(
    env: Env,
    root: DataRoot,
    reference_genome: ReferenceGenome,
) -> str:
    if env == Env.LOCAL or env == Env.TEST:
        root = DataRoot.LOCAL_REFERENCE_DATA
    if env == Env.DEV:
        root = DataRoot.SEQR_SCRATCH_TEMP
    return os.path.join(
        root.value,
        reference_genome.value,
        PipelineVersion.V03.value,
    )


def family_table_path(
    env: Env,
    reference_genome: ReferenceGenome,
    dataset_type: DatasetType,
    family_guid: str,
) -> str:
    return os.path.join(
        _v03_pipeline_prefix(
            env,
            DataRoot.SEQR_LOADING_TEMP,
            reference_genome,
            dataset_type,
        ),
        'families',
        family_guid,
        'samples.ht',
    )


def project_table_path(
    env: Env,
    reference_genome: ReferenceGenome,
    dataset_type: DatasetType,
    project_guid: str,
) -> str:
    return os.path.join(
        _v03_pipeline_prefix(
            env,
            DataRoot.SEQR_DATASETS,
            reference_genome,
            dataset_type,
        ),
        'projects',
        project_guid,
        'samples.ht',
    )


def reference_dataset_collection_path(
    env: Env,
    reference_genome: ReferenceGenome,
    reference_dataset_collection: ReferenceDatasetCollection,
) -> str | None:
    if (
        env == Env.LOCAL
        and reference_dataset_collection.access_control == AccessControl.PRIVATE
    ):
        return None
    root = (
        DataRoot.SEQR_REFERENCE_DATA_PRIVATE
        if reference_dataset_collection.access_control == AccessControl.PRIVATE
        else DataRoot.SEQR_REFERENCE_DATA
    )
    return os.path.join(
        _v03_reference_data_prefix(
            env,
            root,
            reference_genome,
        ),
        f'{reference_dataset_collection.value}.ht',
    )


def variant_annotations_table_path(
    env: Env,
    reference_genome: ReferenceGenome,
    dataset_type: DatasetType,
) -> str:
    return os.path.join(
        _v03_pipeline_prefix(
            env,
            DataRoot.SEQR_DATASETS,
            reference_genome,
            dataset_type,
        ),
        'annotations.ht',
    )


def variant_lookup_table_path(
    env: Env,
    reference_genome: ReferenceGenome,
    dataset_type: DatasetType,
) -> str:
    return os.path.join(
        _v03_pipeline_prefix(
            env,
            DataRoot.SEQR_DATASETS,
            reference_genome,
            dataset_type,
        ),
        'lookup.ht',
    )
