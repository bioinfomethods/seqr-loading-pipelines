#!/usr/bin/env python3
"""
Standalone script to load Parquet files into ClickHouse.
Run this on the ClickHouse server after the pipeline has generated Parquet files.
"""

import argparse

from v03_pipeline.lib.core import DatasetType, ReferenceGenome
from v03_pipeline.lib.logger import get_logger
from v03_pipeline.lib.misc.clickhouse import load_complete_run

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Load pipeline Parquet outputs into ClickHouse',
    )
    parser.add_argument(
        '--reference-genome',
        required=True,
        choices=['GRCh37', 'GRCh38'],
        help='Reference genome version',
    )
    parser.add_argument(
        '--dataset-type',
        required=True,
        choices=['SNV_INDEL', 'MITO', 'SV', 'GCNV'],
        help='Dataset type',
    )
    parser.add_argument(
        '--run-id',
        required=True,
        help='Run ID (timestamp from the pipeline run)',
    )
    parser.add_argument(
        '--project-guids',
        required=True,
        nargs='+',
        help='Project GUIDs (space-separated)',
    )
    parser.add_argument(
        '--family-guids',
        required=True,
        nargs='+',
        help='Family GUIDs (space-separated)',
    )

    args = parser.parse_args()

    reference_genome = ReferenceGenome(args.reference_genome)
    dataset_type = DatasetType(args.dataset_type)

    logger.info(f'Loading run {args.run_id} into ClickHouse')
    logger.info(f'Reference genome: {reference_genome.value}')
    logger.info(f'Dataset type: {dataset_type.value}')
    logger.info(f'Project GUIDs: {args.project_guids}')
    logger.info(f'Family GUIDs: {args.family_guids}')

    load_complete_run(
        reference_genome=reference_genome,
        dataset_type=dataset_type,
        run_id=args.run_id,
        project_guids=args.project_guids,
        family_guids=args.family_guids,
    )

    logger.info('ClickHouse load completed successfully!')


if __name__ == '__main__':
    main()
