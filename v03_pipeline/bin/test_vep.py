#!/usr/bin/env python3
"""
Test VEP annotation directly, replicating the pipeline's invocation.

Usage:
    python -m v03_pipeline.bin.test_vep /path/to/test.vcf.gz
"""

import sys

import hail as hl

# The pipeline uses these values
VEP_CONFIG = '/var/seqr/vep-reference-data/GRCh38/vep-GRCh38.json'
REFERENCE_GENOME = 'GRCh38'


def main():
    vcf_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/test.vcf'

    hl.init(default_reference=REFERENCE_GENOME)

    # Import VCF the same way the pipeline does (via split_multi_hts)
    mt = hl.import_vcf(
        vcf_path,
        reference_genome=REFERENCE_GENOME,
        force_bgz=True,
        skip_invalid_loci=True,
    )
    mt = hl.split_multi_hts(mt)

    # Get just the variant sites as a Table (pipeline uses callset_ht which is a Table)
    ht = mt.rows().select()

    print(f'Loaded {ht.count()} variants')
    ht.key_by().select('locus', 'alleles').show(5)

    # Run VEP exactly as the pipeline does (see v03_pipeline/lib/vep.py)
    ht = hl.vep(
        ht,
        config=VEP_CONFIG,
        name='vep',
        block_size=1000,
        tolerate_parse_error=True,
        csq=False,
    )

    # Check results
    total = ht.count()
    vep_defined = ht.aggregate(hl.agg.count_where(hl.is_defined(ht.vep)))
    has_transcript_consequences = ht.aggregate(
        hl.agg.count_where(
            hl.is_defined(ht.vep.transcript_consequences)
            & (hl.len(ht.vep.transcript_consequences) > 0),
        ),
    )

    print(f'\n{"=" * 60}')
    print(f'Total variants:                    {total}')
    print(f'VEP defined (non-null):            {vep_defined}')
    print(f'Has transcript consequences:       {has_transcript_consequences}')
    print(f'VEP missing (null):                {total - vep_defined}')
    print(f'{"=" * 60}')

    if vep_defined == 0:
        print('\nERROR: VEP produced NO annotations. VEP is broken/misconfigured.')
        print('Check:')
        print(f'  - VEP config exists: {VEP_CONFIG}')
        print('  - FASTA file exists at path in config')
        print('  - VEP cache/plugins are installed')
        sys.exit(1)

    # Show a sample of VEP output
    print('\nSample VEP output:')
    ht.select(
        most_severe=ht.vep.most_severe_consequence,
        n_transcript_consequences=hl.len(ht.vep.transcript_consequences),
    ).show(5)

    # Show consequence terms for first variant with transcript consequences
    print('\nFirst variant transcript consequence terms:')
    ht_with_tc = ht.filter(
        hl.is_defined(ht.vep.transcript_consequences)
        & (hl.len(ht.vep.transcript_consequences) > 0),
    )
    ht_with_tc.select(
        consequence_terms=ht_with_tc.vep.transcript_consequences.flatmap(
            lambda c: c.consequence_terms,
        ),
    ).show(3)

    print('\nVEP is working correctly.')


if __name__ == '__main__':
    main()
