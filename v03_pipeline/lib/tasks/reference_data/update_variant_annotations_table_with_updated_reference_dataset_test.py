import shutil
from unittest import mock

import hail as hl
import luigi.worker

from v03_pipeline.lib.annotations.enums import (
    BIOTYPES,
    CLINVAR_PATHOGENICITIES,
    CONSEQUENCE_TERMS,
    LOF_FILTERS,
    MITOTIP_PATHOGENICITIES,
)
from v03_pipeline.lib.model import (
    DatasetType,
    ReferenceDatasetCollection,
    ReferenceGenome,
    SampleType,
)
from v03_pipeline.lib.paths import valid_reference_dataset_collection_path
from v03_pipeline.lib.reference_data.clinvar import CLINVAR_ASSERTIONS
from v03_pipeline.lib.tasks.files import GCSorLocalFolderTarget
from v03_pipeline.lib.tasks.reference_data.update_variant_annotations_table_with_updated_reference_dataset import (
    UpdateVariantAnnotationsTableWithUpdatedReferenceDataset,
)
from v03_pipeline.lib.test.mock_complete_task import MockCompleteTask
from v03_pipeline.lib.test.mocked_dataroot_testcase import MockedDatarootTestCase

TEST_COMBINED_1 = 'v03_pipeline/var/test/reference_data/test_combined_1.ht'
TEST_HGMD_1 = 'v03_pipeline/var/test/reference_data/test_hgmd_1.ht'
TEST_INTERVAL_1 = 'v03_pipeline/var/test/reference_data/test_interval_1.ht'
TEST_COMBINED_MITO_1 = 'v03_pipeline/var/test/reference_data/test_combined_mito_1.ht'
TEST_INTERVAL_MITO_1 = 'v03_pipeline/var/test/reference_data/test_interval_mito_1.ht'
TEST_COMBINED_37 = 'v03_pipeline/var/test/reference_data/test_combined_37.ht'
TEST_HGMD_37 = 'v03_pipeline/var/test/reference_data/test_hgmd_37.ht'


@mock.patch(
    'v03_pipeline.lib.tasks.base.base_variant_annotations_table.UpdatedReferenceDatasetCollectionTask',
)
@mock.patch(
    'v03_pipeline.lib.tasks.base.base_variant_annotations_table.BaseVariantAnnotationsTableTask.initialize_table',
)
class UpdateVATWithUpdatedRDC(MockedDatarootTestCase):
    def setUp(self) -> None:
        super().setUp()
        shutil.copytree(
            TEST_COMBINED_1,
            valid_reference_dataset_collection_path(
                ReferenceGenome.GRCh38,
                DatasetType.SNV_INDEL,
                ReferenceDatasetCollection.COMBINED,
            ),
        )
        shutil.copytree(
            TEST_HGMD_1,
            valid_reference_dataset_collection_path(
                ReferenceGenome.GRCh38,
                DatasetType.SNV_INDEL,
                ReferenceDatasetCollection.HGMD,
            ),
        )
        shutil.copytree(
            TEST_INTERVAL_1,
            valid_reference_dataset_collection_path(
                ReferenceGenome.GRCh38,
                DatasetType.SNV_INDEL,
                ReferenceDatasetCollection.INTERVAL,
            ),
        )
        shutil.copytree(
            TEST_COMBINED_MITO_1,
            valid_reference_dataset_collection_path(
                ReferenceGenome.GRCh38,
                DatasetType.MITO,
                ReferenceDatasetCollection.COMBINED,
            ),
        )
        shutil.copytree(
            TEST_INTERVAL_MITO_1,
            valid_reference_dataset_collection_path(
                ReferenceGenome.GRCh38,
                DatasetType.MITO,
                ReferenceDatasetCollection.INTERVAL,
            ),
        )
        shutil.copytree(
            TEST_COMBINED_37,
            valid_reference_dataset_collection_path(
                ReferenceGenome.GRCh37,
                DatasetType.SNV_INDEL,
                ReferenceDatasetCollection.COMBINED,
            ),
        )
        shutil.copytree(
            TEST_HGMD_37,
            valid_reference_dataset_collection_path(
                ReferenceGenome.GRCh37,
                DatasetType.SNV_INDEL,
                ReferenceDatasetCollection.HGMD,
            ),
        )

    def test_update_vat_with_updated_rdc_snv_indel_38(
        self,
        mock_initialize_table,
        mock_update_rdc_task,
    ):
        mock_update_rdc_task.return_value = MockCompleteTask()
        mock_initialize_table.return_value = hl.Table.parallelize(
            [
                hl.Struct(
                    locus=hl.Locus(
                        contig='chr1',
                        position=871269,
                        reference_genome='GRCh38',
                    ),
                    alleles=['A', 'C'],
                ),
            ],
            hl.tstruct(
                locus=hl.tlocus('GRCh38'),
                alleles=hl.tarray(hl.tstr),
            ),
            key=['locus', 'alleles'],
            globals=hl.Struct(
                paths=hl.Struct(),
                versions=hl.Struct(),
                enums=hl.Struct(),
                updates=hl.empty_set(hl.tstruct(callset=hl.tstr, project_guid=hl.tstr)),
            ),
        )
        task = UpdateVariantAnnotationsTableWithUpdatedReferenceDataset(
            reference_genome=ReferenceGenome.GRCh38,
            dataset_type=DatasetType.SNV_INDEL,
            sample_type=SampleType.WGS,
        )
        worker = luigi.worker.Worker()
        worker.add(task)
        worker.run()
        self.assertTrue(GCSorLocalFolderTarget(task.output().path).exists())
        self.assertTrue(task.complete())

        ht = hl.read_table(task.output().path)
        self.assertCountEqual(
            ht.collect(),
            [
                hl.Struct(
                    locus=hl.Locus(
                        contig='chr1',
                        position=871269,
                        reference_genome='GRCh38',
                    ),
                    alleles=['A', 'C'],
                    cadd=hl.Struct(PHRED=2),
                    clinvar=None,
                    dbnsfp=hl.Struct(
                        REVEL_score=0.0430000014603138,
                        SIFT_pred_id=None,
                        Polyphen2_HVAR_pred_id=None,
                        MutationTaster_pred_id=0,
                    ),
                    eigen=hl.Struct(Eigen_phred=1.5880000591278076),
                    exac=hl.Struct(
                        AF_POPMAX=0.0004100881633348763,
                        AF=0.0004633000062312931,
                        AC_Adj=51,
                        AC_Het=51,
                        AC_Hom=0,
                        AC_Hemi=None,
                        AN_Adj=108288,
                    ),
                    gnomad_exomes=hl.Struct(
                        AF=0.00012876000255346298,
                        AN=240758,
                        AC=31,
                        Hom=0,
                        AF_POPMAX_OR_GLOBAL=0.0001119549197028391,
                        FAF_AF=9.315000352216884e-05,
                        Hemi=0,
                    ),
                    gnomad_genomes=None,
                    mpc=None,
                    primate_ai=None,
                    splice_ai=hl.Struct(
                        delta_score=0.029999999329447746,
                        splice_consequence_id=3,
                    ),
                    topmed=None,
                    gnomad_non_coding_constraint=hl.Struct(z_score=0.75),
                    screen=hl.Struct(region_type_ids=[1]),
                    hgmd=hl.Struct(accession='abcdefg', class_id=3),
                ),
            ],
        )
        self.assertCountEqual(
            ht.globals.collect(),
            [
                hl.Struct(
                    paths=hl.Struct(
                        cadd='gs://seqr-reference-data/GRCh37/CADD/CADD_snvs_and_indels.v1.6.ht',
                        clinvar='ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/clinvar.vcf.gz',
                        dbnsfp='gs://seqr-reference-data/GRCh37/dbNSFP/v2.9.3/dbNSFP2.9.3_variant.ht',
                        eigen='gs://seqr-reference-data/GRCh37/eigen/EIGEN_coding_noncoding.grch37.ht',
                        exac='gs://seqr-reference-data/GRCh37/gnomad/ExAC.r1.sites.vep.ht',
                        gnomad_exomes='gs://gcp-public-data--gnomad/release/2.1.1/ht/exomes/gnomad.exomes.r2.1.1.sites.ht',
                        gnomad_genomes='gs://gcp-public-data--gnomad/release/2.1.1/ht/genomes/gnomad.genomes.r2.1.1.sites.ht',
                        mpc='gs://seqr-reference-data/GRCh37/MPC/fordist_constraint_official_mpc_values.ht',
                        primate_ai='gs://seqr-reference-data/GRCh37/primate_ai/PrimateAI_scores_v0.2.ht',
                        splice_ai='gs://seqr-reference-data/GRCh37/spliceai/spliceai_scores.ht',
                        topmed='gs://seqr-reference-data/GRCh37/TopMed/bravo-dbsnp-all.removed_chr_prefix.liftunder_GRCh37.ht',
                        gnomad_non_coding_constraint='gs://seqr-reference-data/GRCh38/gnomad_nc_constraint/gnomad_non-coding_constraint_z_scores.ht',
                        screen='gs://seqr-reference-data/GRCh38/ccREs/GRCh38-ccREs.ht',
                        hgmd='gs://seqr-reference-data-private/GRCh38/HGMD/HGMD_Pro_2023.1_hg38.vcf.gz',
                    ),
                    versions=hl.Struct(
                        cadd='v1.6',
                        clinvar='2023-11-26',
                        dbnsfp='2.9.3',
                        eigen=None,
                        exac=None,
                        gnomad_exomes='r2.1.1',
                        gnomad_genomes='r2.1.1',
                        mpc=None,
                        primate_ai='v0.2',
                        splice_ai=None,
                        topmed=None,
                        gnomad_non_coding_constraint=None,
                        screen=None,
                        hgmd=None,
                    ),
                    enums=hl.Struct(
                        cadd=hl.Struct(),
                        clinvar=hl.Struct(
                            pathogenicity=CLINVAR_PATHOGENICITIES,
                            assertion=CLINVAR_ASSERTIONS,
                        ),
                        dbnsfp=hl.Struct(
                            SIFT_pred=['D', 'T'],
                            Polyphen2_HVAR_pred=['D', 'P', 'B'],
                            MutationTaster_pred=['D', 'A', 'N', 'P'],
                        ),
                        eigen=hl.Struct(),
                        exac=hl.Struct(),
                        gnomad_exomes=hl.Struct(),
                        gnomad_genomes=hl.Struct(),
                        mpc=hl.Struct(),
                        primate_ai=hl.Struct(),
                        splice_ai=hl.Struct(
                            splice_consequence=[
                                'Acceptor gain',
                                'Acceptor loss',
                                'Donor gain',
                                'Donor loss',
                                'No consequence',
                            ],
                        ),
                        topmed=hl.Struct(),
                        gnomad_non_coding_constraint=hl.Struct(),
                        screen=hl.Struct(
                            region_type=[
                                'CTCF-bound',
                                'CTCF-only',
                                'DNase-H3K4me3',
                                'PLS',
                                'dELS',
                                'pELS',
                                'DNase-only',
                                'low-DNase',
                            ],
                        ),
                        hgmd=hl.Struct(
                            **{'class': ['DFP', 'DM', 'DM?', 'DP', 'FP', 'R']},
                        ),
                        sorted_transcript_consequences=hl.Struct(
                            biotype=BIOTYPES,
                            consequence_term=CONSEQUENCE_TERMS,
                            lof_filter=LOF_FILTERS,
                        ),
                    ),
                    updates=set(),
                ),
            ],
        )

    def test_update_vat_with_updated_rdc_mito_38(
        self,
        mock_initialize_table,
        mock_update_rdc_task,
    ):
        mock_update_rdc_task.return_value = MockCompleteTask()
        mock_initialize_table.return_value = hl.Table.parallelize(
            [
                hl.Struct(
                    locus=hl.Locus(
                        contig='chrM',
                        position=1,
                        reference_genome='GRCh38',
                    ),
                    alleles=['A', 'C'],
                ),
            ],
            hl.tstruct(
                locus=hl.tlocus('GRCh38'),
                alleles=hl.tarray(hl.tstr),
            ),
            key=['locus', 'alleles'],
            globals=hl.Struct(
                paths=hl.Struct(),
                versions=hl.Struct(),
                enums=hl.Struct(),
                updates=hl.empty_set(hl.tstruct(callset=hl.tstr, project_guid=hl.tstr)),
            ),
        )
        task = UpdateVariantAnnotationsTableWithUpdatedReferenceDataset(
            reference_genome=ReferenceGenome.GRCh38,
            dataset_type=DatasetType.MITO,
            sample_type=SampleType.WGS,
        )
        worker = luigi.worker.Worker()
        worker.add(task)
        worker.run()
        self.assertTrue(GCSorLocalFolderTarget(task.output().path).exists())
        self.assertTrue(task.complete())

        ht = hl.read_table(task.output().path)
        self.assertCountEqual(
            ht.globals.collect(),
            [
                hl.Struct(
                    paths=hl.Struct(
                        gnomad_mito='gs://gcp-public-data--gnomad/release/3.1/ht/genomes/gnomad.genomes.v3.1.sites.chrM.ht',
                        helix_mito='gs://seqr-reference-data/GRCh38/mitochondrial/Helix/HelixMTdb_20200327.ht',
                        hmtvar='gs://seqr-reference-data/GRCh38/mitochondrial/HmtVar/HmtVar%20Jan.%2010%202022.ht',
                        mitomap='gs://seqr-reference-data/GRCh38/mitochondrial/MITOMAP/mitomap-confirmed-mutations-2022-02-04.ht',
                        mitimpact='gs://seqr-reference-data/GRCh38/mitochondrial/MitImpact/MitImpact_db_3.0.7.ht',
                        clinvar_mito='ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz',
                        dbnsfp_mito='gs://seqr-reference-data/GRCh38/dbNSFP/v4.2/dbNSFP4.2a_variant.ht',
                        high_constraint_region_mito='gs://seqr-reference-data/GRCh38/mitochondrial/Helix high constraint intervals Feb-15-2022.tsv',
                    ),
                    versions=hl.Struct(
                        gnomad_mito='v3.1',
                        helix_mito='20200327',
                        hmtvar='Jan. 10 2022',
                        mitomap='Feb. 04 2022',
                        mitimpact='3.0.7',
                        clinvar_mito='2023-07-22',
                        dbnsfp_mito='4.2',
                        high_constraint_region_mito='Feb-15-2022',
                    ),
                    enums=hl.Struct(
                        gnomad_mito=hl.Struct(),
                        helix_mito=hl.Struct(),
                        hmtvar=hl.Struct(),
                        mitomap=hl.Struct(),
                        mitimpact=hl.Struct(),
                        clinvar_mito=hl.Struct(
                            pathogenicity=CLINVAR_PATHOGENICITIES,
                            assertion=CLINVAR_ASSERTIONS,
                        ),
                        dbnsfp_mito=hl.Struct(
                            SIFT_pred=['D', 'T'],
                            Polyphen2_HVAR_pred=['D', 'P', 'B'],
                            MutationTaster_pred=['D', 'A', 'N', 'P'],
                            fathmm_MKL_coding_pred=['D', 'N'],
                        ),
                        high_constraint_region_mito=hl.Struct(),
                        sorted_transcript_consequences=hl.Struct(
                            biotype=BIOTYPES,
                            consequence_term=CONSEQUENCE_TERMS,
                            lof_filter=LOF_FILTERS,
                        ),
                        mitotip=hl.Struct(
                            trna_prediction=MITOTIP_PATHOGENICITIES,
                        ),
                    ),
                    updates=set(),
                ),
            ],
        )
        self.assertCountEqual(
            ht.collect(),
            [
                hl.Struct(
                    locus=hl.Locus(
                        contig='chrM',
                        position=1,
                        reference_genome='GRCh38',
                    ),
                    alleles=['A', 'C'],
                    clinvar_mito=None,
                    dbnsfp_mito=hl.Struct(
                        REVEL_score=None,
                        VEST4_score=None,
                        MutPred_score=None,
                        SIFT_pred_id=None,
                        Polyphen2_HVAR_pred_id=None,
                        MutationTaster_pred_id=None,
                        fathmm_MKL_coding_pred_id=None,
                    ),
                    gnomad_mito=None,
                    helix_mito=hl.Struct(
                        AC=1,
                        AF=5.102483555674553e-06,
                        AC_het=0,
                        AF_het=0.0,
                        AN=195982,
                        max_hl=None,
                    ),
                    hmtvar=hl.Struct(score=0.6700000166893005),
                    mitomap=None,
                    mitimpact=hl.Struct(score=0.5199999809265137),
                    high_constraint_region_mito=True,
                ),
            ],
        )

    def test_update_vat_with_updated_rdc_snv_indel_37(
        self,
        mock_initialize_table,
        mock_update_rdc_task,
    ):
        mock_update_rdc_task.return_value = MockCompleteTask()
        mock_initialize_table.return_value = hl.Table.parallelize(
            [
                hl.Struct(
                    locus=hl.Locus(
                        contig=1,
                        position=871269,
                        reference_genome='GRCh37',
                    ),
                    alleles=['A', 'C'],
                ),
            ],
            hl.tstruct(
                locus=hl.tlocus('GRCh37'),
                alleles=hl.tarray(hl.tstr),
            ),
            key=['locus', 'alleles'],
            globals=hl.Struct(
                paths=hl.Struct(),
                versions=hl.Struct(),
                enums=hl.Struct(),
                updates=hl.empty_set(hl.tstruct(callset=hl.tstr, project_guid=hl.tstr)),
            ),
        )
        task = UpdateVariantAnnotationsTableWithUpdatedReferenceDataset(
            reference_genome=ReferenceGenome.GRCh37,
            dataset_type=DatasetType.SNV_INDEL,
            sample_type=SampleType.WGS,
        )
        worker = luigi.worker.Worker()
        worker.add(task)
        worker.run()
        self.assertTrue(GCSorLocalFolderTarget(task.output().path).exists())
        self.assertTrue(task.complete())

        ht = hl.read_table(task.output().path)
        self.assertCountEqual(
            ht.globals.collect(),
            [
                hl.Struct(
                    paths=hl.Struct(
                        cadd='gs://seqr-reference-data/GRCh37/CADD/CADD_snvs_and_indels.v1.6.ht',
                        clinvar='ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh37/clinvar.vcf.gz',
                        dbnsfp='gs://seqr-reference-data/GRCh37/dbNSFP/v2.9.3/dbNSFP2.9.3_variant.ht',
                        eigen='gs://seqr-reference-data/GRCh37/eigen/EIGEN_coding_noncoding.grch37.ht',
                        exac='gs://seqr-reference-data/GRCh37/gnomad/ExAC.r1.sites.vep.ht',
                        gnomad_exomes='gs://gcp-public-data--gnomad/release/2.1.1/ht/exomes/gnomad.exomes.r2.1.1.sites.ht',
                        gnomad_genomes='gs://gcp-public-data--gnomad/release/2.1.1/ht/genomes/gnomad.genomes.r2.1.1.sites.ht',
                        mpc='gs://seqr-reference-data/GRCh37/MPC/fordist_constraint_official_mpc_values.ht',
                        primate_ai='gs://seqr-reference-data/GRCh37/primate_ai/PrimateAI_scores_v0.2.ht',
                        splice_ai='gs://seqr-reference-data/GRCh37/spliceai/spliceai_scores.ht',
                        topmed='gs://seqr-reference-data/GRCh37/TopMed/bravo-dbsnp-all.removed_chr_prefix.liftunder_GRCh37.ht',
                        hgmd='gs://seqr-reference-data-private/GRCh37/HGMD/HGMD_Pro_2023.1_hg19.vcf.gz',
                    ),
                    versions=hl.Struct(
                        cadd='v1.6',
                        clinvar='2023-11-26',
                        dbnsfp='2.9.3',
                        eigen=None,
                        exac=None,
                        gnomad_exomes='r2.1.1',
                        gnomad_genomes='r2.1.1',
                        mpc=None,
                        primate_ai='v0.2',
                        splice_ai=None,
                        topmed=None,
                        hgmd=None,
                    ),
                    enums=hl.Struct(
                        cadd=hl.Struct(),
                        clinvar=hl.Struct(
                            pathogenicity=CLINVAR_PATHOGENICITIES,
                            assertion=CLINVAR_ASSERTIONS,
                        ),
                        dbnsfp=hl.Struct(
                            SIFT_pred=['D', 'T'],
                            Polyphen2_HVAR_pred=['D', 'P', 'B'],
                            MutationTaster_pred=['D', 'A', 'N', 'P'],
                        ),
                        eigen=hl.Struct(),
                        exac=hl.Struct(),
                        gnomad_exomes=hl.Struct(),
                        gnomad_genomes=hl.Struct(),
                        mpc=hl.Struct(),
                        primate_ai=hl.Struct(),
                        splice_ai=hl.Struct(
                            splice_consequence=[
                                'Acceptor gain',
                                'Acceptor loss',
                                'Donor gain',
                                'Donor loss',
                                'No consequence',
                            ],
                        ),
                        topmed=hl.Struct(),
                        hgmd=hl.Struct(
                            **{'class': ['DM', 'DM?', 'DP', 'DFP', 'FP', 'R']},
                        ),
                        sorted_transcript_consequences=hl.Struct(
                            biotype=BIOTYPES,
                            consequence_term=CONSEQUENCE_TERMS,
                            lof_filter=LOF_FILTERS,
                        ),
                    ),
                    updates=set(),
                ),
            ],
        )
        self.assertCountEqual(
            ht.collect(),
            [
                hl.Struct(
                    locus=hl.Locus(
                        contig=1,
                        position=871269,
                        reference_genome='GRCh37',
                    ),
                    alleles=['A', 'C'],
                    cadd=hl.Struct(PHRED=9.699999809265137),
                    clinvar=None,
                    dbnsfp=hl.Struct(
                        REVEL_score=0.0430000014603138,
                        SIFT_pred_id=None,
                        Polyphen2_HVAR_pred_id=None,
                        MutationTaster_pred_id=0,
                    ),
                    eigen=hl.Struct(Eigen_phred=1.5880000591278076),
                    exac=hl.Struct(
                        AF_POPMAX=0.0004100881633348763,
                        AF=0.0004633000062312931,
                        AC_Adj=51,
                        AC_Het=51,
                        AC_Hom=0,
                        AC_Hemi=None,
                        AN_Adj=108288,
                    ),
                    gnomad_exomes=hl.Struct(
                        AF=0.00012876000255346298,
                        AN=240758,
                        AC=31,
                        Hom=0,
                        AF_POPMAX_OR_GLOBAL=0.0001119549197028391,
                        FAF_AF=9.315000352216884e-05,
                        Hemi=0,
                    ),
                    gnomad_genomes=None,
                    mpc=None,
                    primate_ai=None,
                    splice_ai=hl.Struct(
                        delta_score=0.029999999329447746,
                        splice_consequence_id=3,
                    ),
                    topmed=None,
                    hgmd=None,
                ),
            ],
        )
