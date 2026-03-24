#!/usr/bin/env python3
"""
Imperative CLI to run the loading pipeline directly, without the API/worker queue.

Usage:
    python -m v03_pipeline.bin.run_loading_pipeline \
        --callset-path /path/to/vcf.gz \
        --project-guids R0015_acg_001 \
        --reference-genome GRCh38 \
        --dataset-type SNV_INDEL \
        --sample-type WGS \
        --skip-check-sex-and-relatedness \
        --skip-expect-tdr-metrics \
        --run-id my_test_run_001
"""

import argparse
import sys
import uuid

import luigi
import luigi.execution_summary

from v03_pipeline.lib.tasks.write_clickhouse_load_success_file import (
    WriteClickhouseLoadSuccessFileTask,
)


def main():
    parser = argparse.ArgumentParser(
        description='Run the seqr loading pipeline directly.',
    )
    parser.add_argument('--callset-path', required=True)
    parser.add_argument('--project-guids', nargs='+', required=True)
    parser.add_argument('--reference-genome', default='GRCh38')
    parser.add_argument('--dataset-type', default='SNV_INDEL')
    parser.add_argument('--sample-type', default='WGS')
    parser.add_argument('--run-id', default=None)
    parser.add_argument('--attempt-id', type=int, default=1)
    parser.add_argument(
        '--skip-check-sex-and-relatedness',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--skip-expect-tdr-metrics',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--validations-to-skip',
        nargs='*',
        default=[],
    )

    args = parser.parse_args()

    run_id = args.run_id or f'manual_{uuid.uuid4().hex[:8]}'

    task = WriteClickhouseLoadSuccessFileTask(
        callset_path=args.callset_path,
        project_guids=args.project_guids,
        reference_genome=args.reference_genome,
        dataset_type=args.dataset_type,
        sample_type=args.sample_type,
        run_id=run_id,
        attempt_id=args.attempt_id,
        skip_check_sex_and_relatedness=args.skip_check_sex_and_relatedness,
        skip_expect_tdr_metrics=args.skip_expect_tdr_metrics,
        validations_to_skip=args.validations_to_skip,
    )

    result = luigi.build(
        [task],
        detailed_summary=True,
        local_scheduler=True,
    )

    print(f'\n{"=" * 60}')
    print(f'Run ID: {run_id}')
    print(f'Status: {result.status.value[1]}')
    print(f'{"=" * 60}')

    if result.status not in {
        luigi.execution_summary.LuigiStatusCode.SUCCESS,
        luigi.execution_summary.LuigiStatusCode.SUCCESS_WITH_RETRY,
    }:
        print('\nPipeline FAILED.', file=sys.stderr)
        sys.exit(1)

    print('\nPipeline completed successfully.')


if __name__ == '__main__':
    main()
