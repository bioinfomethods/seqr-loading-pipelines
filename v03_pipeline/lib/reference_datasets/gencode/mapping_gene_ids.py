import gzip
import logging
import os
import requests

logger = logging.getLogger(__name__)

GENCODE_LOCAL_PATH = '/hpc/genomeref/hg38/seqr/gencode.v{gencode_release}.annotation.gtf.gz'
GENCODE_ENSEMBL_TO_REFSEQ_LOCAL_PATH = '/hpc/genomeref/hg38/seqr/gencode.v{gencode_release}.metadata.RefSeq.gz'

GENCODE_GTF_URL = 'http://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_{gencode_release}/gencode.v{gencode_release}.annotation.gtf.gz'
GENCODE_ENSEMBL_TO_REFSEQ_URL = 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_{gencode_release}/gencode.v{gencode_release}.metadata.RefSeq.gz'

# expected GTF file header
GENCODE_FILE_HEADER = [
    'chrom',
    'source',
    'feature_type',
    'start',
    'end',
    'score',
    'strand',
    'phase',
    'info',
]
EXPECTED_ENSEMBLE_TO_REFSEQ_FIELDS = 3


def load_gencode_gene_symbol_to_gene_id(gencode_release: int) -> dict[str, str]:
    file_path = GENCODE_LOCAL_PATH.format(gencode_release=gencode_release)

    if os.path.exists(file_path):
        logger.info(f"Loading GENCODE GTF from local file: {file_path}")
        file_source = gzip.open(file_path, "rt")
    else:
        url = GENCODE_GTF_URL.format(gencode_release=gencode_release)
        logger.info(f"Downloading GENCODE GTF from {url}")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # Ensure request was successful
        file_source = gzip.GzipFile(fileobj=response.raw)

    gene_symbol_to_gene_id = {}
    with file_source as f:
        for line in f:
            if not line or line.startswith('#'):
                continue
            fields = line.strip().split('\t')
            if len(fields) != len(GENCODE_FILE_HEADER):
                raise ValueError(f"Unexpected number of fields: {fields}")
            record = dict(zip(GENCODE_FILE_HEADER, fields, strict=False))
            if record['feature_type'] != 'gene':
                continue
            # Parse info field
            info_fields = {k: v.strip('"') for k, v in 
                           (x.strip().split() for x in record['info'].split(';') if x)}
            gene_symbol_to_gene_id[info_fields['gene_name']] = info_fields['gene_id'].split('.')[0]

    return gene_symbol_to_gene_id


def load_gencode_ensembl_to_refseq_id(gencode_release: int):
    file_path = GENCODE_ENSEMBL_TO_REFSEQ_LOCAL_PATH.format(gencode_release=gencode_release)

    if os.path.exists(file_path):
        logger.info(f"Loading Ensembl-to-RefSeq mapping from local file: {file_path}")
        file_source = gzip.open(file_path, "rt")
    else:
        url = GENCODE_ENSEMBL_TO_REFSEQ_URL.format(gencode_release=gencode_release)
        logger.info(f"Downloading Ensembl-to-RefSeq mapping from {url}")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # Ensure request was successful
        file_source = gzip.GzipFile(fileobj=response.raw)

    ensembl_to_refseq_ids = {}
    with file_source as f:
        for line in f:
            fields = line.strip().split('\t')
            if len(fields) > EXPECTED_ENSEMBLE_TO_REFSEQ_FIELDS:
                raise ValueError("Unexpected number of fields on line in Ensembl-to-RefSeq mapping")
            ensembl_to_refseq_ids[fields[0].split('.')[0]] = fields[1]

    return ensembl_to_refseq_ids
