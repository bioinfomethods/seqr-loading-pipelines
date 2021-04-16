import unittest
import mock
import os
import sys
import tempfile
import time

import hail as hl

from sv_pipeline.genome.load_data import sub_setting_mt, annotate_fields, main, WGS_SAMPLE_TYPE

GENE_ID_MAPPING = {
    'OR4F5': 'ENSG00000284662.1_2',
    'ATAD3A': 'ENSG00000284663',
    'CDK11B': 'ENSG00000284664',
}

VCF_DATA = [
'##fileformat=VCFv4.2',
'##FORMAT=<ID=CN,Number=1,Type=Integer,Description="Predicted copy state">',
'##FORMAT=<ID=CNQ,Number=1,Type=Integer,Description="Read-depth genotype quality">',
'##FORMAT=<ID=EV,Number=1,Type=String,Description="Classes of evidence supporting final genotype">',
'##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">',
'##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
'##FORMAT=<ID=PE_GQ,Number=1,Type=Integer,Description="Paired-end genotype quality">',
'##FORMAT=<ID=PE_GT,Number=1,Type=Integer,Description="Paired-end genotype">',
'##FORMAT=<ID=RD_CN,Number=1,Type=Integer,Description="Predicted copy state">',
'##FORMAT=<ID=RD_GQ,Number=1,Type=Integer,Description="Read-depth genotype quality">',
'##FORMAT=<ID=SR_GQ,Number=1,Type=Integer,Description="Split read genotype quality">',
'##FORMAT=<ID=SR_GT,Number=1,Type=Integer,Description="Split-read genotype">',
'##INFO=<ID=ALGORITHMS,Number=.,Type=String,Description="Source algorithms">',
'##INFO=<ID=CHR2,Number=1,Type=String,Description="Chromosome for END coordinate">',
'##INFO=<ID=CPX_INTERVALS,Number=.,Type=String,Description="Genomic intervals constituting complex variant.">',
'##INFO=<ID=CPX_TYPE,Number=1,Type=String,Description="Class of complex variant.">',
'##INFO=<ID=END,Number=1,Type=Integer,Description="End position of the structural variant">',
'##INFO=<ID=END2,Number=1,Type=Integer,Description="Position of breakpoint on CHR2">',
'##INFO=<ID=EVIDENCE,Number=.,Type=String,Description="Classes of random forest support.">',
'##INFO=<ID=SOURCE,Number=1,Type=String,Description="Source of inserted sequence.">',
'##INFO=<ID=STRANDS,Number=1,Type=String,Description="Breakpoint strandedness [++,+-,-+,--]">',
'##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="SV length">',
'##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Type of structural variant">',
'##INFO=<ID=UNRESOLVED_TYPE,Number=1,Type=String,Description="Class of unresolved variant.">',
'##INFO=<ID=PROTEIN_CODING__LOF,Number=.,Type=String,Description="Gene(s) on which the SV is predicted to have a loss-of-function effect.">',
'##INFO=<ID=LINCRNA__LOF,Number=.,Type=String,Description="Gene(s) on which the SV is predicted to have a loss-of-function effect.">',
'##INFO=<ID=PROTEIN_CODING__DUP_LOF,Number=.,Type=String,Description="Gene(s) on which the SV is predicted to have a loss-of-function effect via intragenic exonic duplication.">',
'##INFO=<ID=LINCRNA__DUP_LOF,Number=.,Type=String,Description="Gene(s) on which the SV is predicted to have a loss-of-function effect via intragenic exonic duplication.">',
'##INFO=<ID=PROTEIN_CODING__COPY_GAIN,Number=.,Type=String,Description="Gene(s) on which the SV is predicted to have a copy-gain effect.">',
'##INFO=<ID=LINCRNA__COPY_GAIN,Number=.,Type=String,Description="Gene(s) on which the SV is predicted to have a copy-gain effect.">',
'##INFO=<ID=PROTEIN_CODING__DUP_PARTIAL,Number=.,Type=String,Description="Gene(s) which are partially overlapped by an SV\'s duplication, such that an unaltered copy is preserved.">',
'##INFO=<ID=LINCRNA__DUP_PARTIAL,Number=.,Type=String,Description="Gene(s) which are partially overlapped by an SV\'s duplication, such that an unaltered copy is preserved.">',
'##INFO=<ID=PROTEIN_CODING__MSV_EXON_OVR,Number=.,Type=String,Description="Gene(s) on which the multiallelic SV would be predicted to have a LOF, DUP_LOF, COPY_GAIN, or DUP_PARTIAL annotation if the SV were biallelic.">',
'##INFO=<ID=LINCRNA__MSV_EXON_OVR,Number=.,Type=String,Description="Gene(s) on which the multiallelic SV would be predicted to have a LOF, DUP_LOF, COPY_GAIN, or DUP_PARTIAL annotation if the SV were biallelic.">',
'##INFO=<ID=PROTEIN_CODING__INTRONIC,Number=.,Type=String,Description="Gene(s) where the SV was found to lie entirely within an intron.">',
'##INFO=<ID=LINCRNA__INTRONIC,Number=.,Type=String,Description="Gene(s) where the SV was found to lie entirely within an intron.">',
'##INFO=<ID=PROTEIN_CODING__INV_SPAN,Number=.,Type=String,Description="Gene(s) which are entirely spanned by an SV\'s inversion.">',
'##INFO=<ID=LINCRNA__INV_SPAN,Number=.,Type=String,Description="Gene(s) which are entirely spanned by an SV\'s inversion.">',
'##INFO=<ID=PROTEIN_CODING__UTR,Number=.,Type=String,Description="Gene(s) for which the SV is predicted to disrupt a UTR.">',
'##INFO=<ID=LINCRNA__UTR,Number=.,Type=String,Description="Gene(s) for which the SV is predicted to disrupt a UTR.">',
'##INFO=<ID=NONCODING_SPAN,Number=.,Type=String,Description="Classes of noncoding elements spanned by SV.">',
'##INFO=<ID=NONCODING_BREAKPOINT,Number=.,Type=String,Description="Classes of noncoding elements disrupted by SV breakpoint.">',
'##INFO=<ID=PROTEIN_CODING__NEAREST_TSS,Number=.,Type=String,Description="Nearest transcription start site to intragenic variants.">',
'##INFO=<ID=PROTEIN_CODING__INTERGENIC,Number=0,Type=Flag,Description="SV does not overlap coding sequence.">',
'##INFO=<ID=PROTEIN_CODING__PROMOTER,Number=.,Type=String,Description="Genes whose promoter sequence (1 kb) was disrupted by SV.">',
'##INFO=<ID=AN,Number=1,Type=Integer,Description="Total number of alleles genotyped (for biallelic sites) or individuals with copy-state estimates (for multiallelic sites).">',
'##INFO=<ID=AC,Number=A,Type=Integer,Description="Number of non-reference alleles observed (for biallelic sites) or individuals at each copy state (for multiallelic sites).">',
'##INFO=<ID=AF,Number=A,Type=Float,Description="Allele frequency (for biallelic sites) or copy-state frequency (for multiallelic sites).">',
'##INFO=<ID=N_BI_GENOS,Number=1,Type=Integer,Description="Total number of individuals with complete genotypes (biallelic sites only).">',
'##INFO=<ID=N_HOMREF,Number=1,Type=Integer,Description="Number of individuals with homozygous reference genotypes (biallelic sites only).">',
'##INFO=<ID=N_HET,Number=1,Type=Integer,Description="Number of individuals with heterozygous genotypes (biallelic sites only).">',
'##INFO=<ID=N_HOMALT,Number=1,Type=Integer,Description="Number of individuals with homozygous alternate genotypes (biallelic sites only).">',
'##INFO=<ID=FREQ_HOMREF,Number=1,Type=Float,Description="Homozygous reference genotype frequency (biallelic sites only).">',
'##INFO=<ID=FREQ_HET,Number=1,Type=Float,Description="Heterozygous genotype frequency (biallelic sites only).">',
'##INFO=<ID=FREQ_HOMALT,Number=1,Type=Float,Description="Homozygous alternate genotype frequency (biallelic sites only).">',
'##INFO=<ID=MALE_AN,Number=1,Type=Integer,Description="Total number of MALE alleles genotyped (for biallelic sites) or MALE individuals with copy-state estimates (for multiallelic sites).">',
'##INFO=<ID=MALE_AC,Number=A,Type=Integer,Description="Number of non-reference MALE alleles observed (for biallelic sites) or MALE individuals at each copy state (for multiallelic sites).">',
'##INFO=<ID=MALE_AF,Number=A,Type=Float,Description="MALE allele frequency (for biallelic sites) or MALE copy-state frequency (for multiallelic sites).">',
'##INFO=<ID=MALE_N_BI_GENOS,Number=1,Type=Integer,Description="Total number of MALE individuals with complete genotypes (biallelic sites only).">',
'##INFO=<ID=MALE_N_HOMREF,Number=1,Type=Integer,Description="Number of MALE individuals with homozygous reference genotypes (biallelic sites only).">',
'##INFO=<ID=MALE_N_HET,Number=1,Type=Integer,Description="Number of MALE individuals with heterozygous genotypes (biallelic sites only).">',
'##INFO=<ID=MALE_N_HOMALT,Number=1,Type=Integer,Description="Number of MALE individuals with homozygous alternate genotypes (biallelic sites only).">',
'##INFO=<ID=MALE_FREQ_HOMREF,Number=1,Type=Float,Description="MALE homozygous reference genotype frequency (biallelic sites only).">',
'##INFO=<ID=MALE_FREQ_HET,Number=1,Type=Float,Description="MALE heterozygous genotype frequency (biallelic sites only).">',
'##INFO=<ID=MALE_FREQ_HOMALT,Number=1,Type=Float,Description="MALE homozygous alternate genotype frequency (biallelic sites only).">',
'##INFO=<ID=FEMALE_AN,Number=1,Type=Integer,Description="Total number of FEMALE alleles genotyped (for biallelic sites) or FEMALE individuals with copy-state estimates (for multiallelic sites).">',
'##INFO=<ID=FEMALE_AC,Number=A,Type=Integer,Description="Number of non-reference FEMALE alleles observed (for biallelic sites) or FEMALE individuals at each copy state (for multiallelic sites).">',
'##INFO=<ID=FEMALE_AF,Number=A,Type=Float,Description="FEMALE allele frequency (for biallelic sites) or FEMALE copy-state frequency (for multiallelic sites).">',
'##INFO=<ID=FEMALE_N_BI_GENOS,Number=1,Type=Integer,Description="Total number of FEMALE individuals with complete genotypes (biallelic sites only).">',
'##INFO=<ID=FEMALE_N_HOMREF,Number=1,Type=Integer,Description="Number of FEMALE individuals with homozygous reference genotypes (biallelic sites only).">',
'##INFO=<ID=FEMALE_N_HET,Number=1,Type=Integer,Description="Number of FEMALE individuals with heterozygous genotypes (biallelic sites only).">',
'##INFO=<ID=FEMALE_N_HOMALT,Number=1,Type=Integer,Description="Number of FEMALE individuals with homozygous alternate genotypes (biallelic sites only).">',
'##INFO=<ID=FEMALE_FREQ_HOMREF,Number=1,Type=Float,Description="FEMALE homozygous reference genotype frequency (biallelic sites only).">',
'##INFO=<ID=FEMALE_FREQ_HET,Number=1,Type=Float,Description="FEMALE heterozygous genotype frequency (biallelic sites only).">',
'##INFO=<ID=FEMALE_FREQ_HOMALT,Number=1,Type=Float,Description="FEMALE homozygous alternate genotype frequency (biallelic sites only).">',
'##INFO=<ID=gnomAD_V2_SVID,Number=1,Type=String,Description="Allele frequency (for biallelic sites) or copy-state frequency (for multiallelic sites) of an overlapping event in gnomad.">',
'##INFO=<ID=gnomAD_V2_AF,Number=1,Type=Float,Description="Allele frequency (for biallelic sites) or copy-state frequency (for multiallelic sites) of an overlapping event in gnomad.">',
'#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	SAMPLE-1	SAMPLE-2	SAMPLE-3	SAMPLE-4	SAMPLE-5',
'chr1	10000	DUP_chr1_1	N	<DUP>	999	LOW_CALL_RATE	END=17000;SVTYPE=DUP;CHR2=chr1;SVLEN=7000;ALGORITHMS=depth;EVIDENCE=RD;PROTEIN_CODING__NEAREST_TSS=OR4F5;PROTEIN_CODING__INTERGENIC;NONCODING_SPAN=DNase;NONCODING_BREAKPOINT=DNase;AN=1428;AC=370;AF=0.259104;N_BI_GENOS=714;N_HOMREF=415;N_HET=228;N_HOMALT=71;FREQ_HOMREF=0.581232;FREQ_HET=0.319328;FREQ_HOMALT=0.0994398;MALE_AN=772;MALE_AC=214;MALE_AF=0.277202;MALE_N_BI_GENOS=386;MALE_N_HOMREF=216;MALE_N_HET=126;MALE_N_HOMALT=44;MALE_FREQ_HOMREF=0.559586;MALE_FREQ_HET=0.326425;MALE_FREQ_HOMALT=0.11399;FEMALE_AN=656;FEMALE_AC=156;FEMALE_AF=0.237805;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=199;FEMALE_N_HET=102;FEMALE_N_HOMALT=27;FEMALE_FREQ_HOMREF=0.606707;FEMALE_FREQ_HET=0.310976;FEMALE_FREQ_HOMALT=0.0823171	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/1:999:3:999:.:.:.:.:RD	0/1:52:3:52:.:.:.:.:RD	0/1:19:3:19:.:.:.:.:RD	0/0:1:2:1:.:.:.:.:RD	0/0:31:2:31:.:.:.:.:RD',
'chr1	10000	DUP_chr1_2	N	<DUP>	999	LOW_CALL_RATE;UNRESOLVED	END=53500;SVTYPE=DUP;CHR2=chr1;SVLEN=43500;ALGORITHMS=depth;EVIDENCE=BAF,RD;PROTEIN_CODING__NEAREST_TSS=OR4F5;PROTEIN_CODING__INTERGENIC;LINCRNA__COPY_GAIN=FAM138A,MIR1302-2HG;NONCODING_SPAN=DNase;NONCODING_BREAKPOINT=DNase;AN=1428;AC=70;AF=0.04902;N_BI_GENOS=714;N_HOMREF=649;N_HET=60;N_HOMALT=5;FREQ_HOMREF=0.908964;FREQ_HET=0.0840336;FREQ_HOMALT=0.0070028;MALE_AN=772;MALE_AC=46;MALE_AF=0.059585;MALE_N_BI_GENOS=386;MALE_N_HOMREF=344;MALE_N_HET=38;MALE_N_HOMALT=4;MALE_FREQ_HOMREF=0.891192;MALE_FREQ_HET=0.0984456;MALE_FREQ_HOMALT=0.0103627;FEMALE_AN=656;FEMALE_AC=24;FEMALE_AF=0.036585;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=305;FEMALE_N_HET=22;FEMALE_N_HOMALT=1;FEMALE_FREQ_HOMREF=0.929878;FEMALE_FREQ_HET=0.0670732;FEMALE_FREQ_HOMALT=0.00304878	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/0:1:2:1:.:.:.:.:RD	0/1:119:3:119:.:.:.:.:RD	0/1:119:3:119:.:.:.:.:RD	0/0:999:2:999:.:.:.:.:RD	0/0:133:2:133:.:.:.:.:RD',
'chr1	10602	BND_chr1_1	N	<BND>	461	UNRESOLVED;UNSTABLE_AF_PCRMINUS	END=10602;SVTYPE=BND;CHR2=chr12;STRANDS=+-;SVLEN=-1;ALGORITHMS=manta;EVIDENCE=SR;UNRESOLVED_TYPE=SINGLE_ENDER_+-;END2=10546;AN=1428;AC=88;AF=0.061625;N_BI_GENOS=714;N_HOMREF=626;N_HET=88;N_HOMALT=0;FREQ_HOMREF=0.876751;FREQ_HET=0.123249;FREQ_HOMALT=0;MALE_AN=772;MALE_AC=51;MALE_AF=0.066062;MALE_N_BI_GENOS=386;MALE_N_HOMREF=335;MALE_N_HET=51;MALE_N_HOMALT=0;MALE_FREQ_HOMREF=0.867876;MALE_FREQ_HET=0.132124;MALE_FREQ_HOMALT=0;FEMALE_AN=656;FEMALE_AC=37;FEMALE_AF=0.056402;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=291;FEMALE_N_HET=37;FEMALE_N_HOMALT=0;FEMALE_FREQ_HOMREF=0.887195;FEMALE_FREQ_HET=0.112805;FEMALE_FREQ_HOMALT=0;gnomAD_V2_SVID=gnomAD-SV_v2.1_BND_1_1;gnomAD_V2_AF=0.00678599998354912	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/0:999:.:.:0:23:0:999:PE,SR	0/0:999:.:.:0:23:0:999:PE,SR	0/0:999:.:.:0:1:0:999:PE,SR	0/0:999:.:.:0:3:0:999:PE,SR	0/0:999:.:.:0:23:0:999:PE,SR',
'chr1	41950	DUP_chr1_3	N	<DUP>	999	LOW_CALL_RATE	END=52000;SVTYPE=DUP;CHR2=chr1;SVLEN=10050;ALGORITHMS=depth;EVIDENCE=BAF,RD;PROTEIN_CODING__NEAREST_TSS=OR4F5;PROTEIN_CODING__INTERGENIC;AN=1428;AC=28;AF=0.019608;N_BI_GENOS=714;N_HOMREF=687;N_HET=26;N_HOMALT=1;FREQ_HOMREF=0.962185;FREQ_HET=0.0364146;FREQ_HOMALT=0.00140056;MALE_AN=772;MALE_AC=15;MALE_AF=0.01943;MALE_N_BI_GENOS=386;MALE_N_HOMREF=371;MALE_N_HET=15;MALE_N_HOMALT=0;MALE_FREQ_HOMREF=0.96114;MALE_FREQ_HET=0.0388601;MALE_FREQ_HOMALT=0;FEMALE_AN=656;FEMALE_AC=13;FEMALE_AF=0.019817;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=316;FEMALE_N_HET=11;FEMALE_N_HOMALT=1;FEMALE_FREQ_HOMREF=0.963415;FEMALE_FREQ_HET=0.0335366;FEMALE_FREQ_HOMALT=0.00304878;gnomAD_V2_SVID=gnomAD-SV_v2.1_DUP_1_1;gnomAD_V2_AF=0.068962998688221	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/0:31:2:31:.:.:.:.:RD	0/0:58:2:58:.:.:.:.:RD	0/0:1:2:1:.:.:.:.:RD	0/0:112:2:112:.:.:.:.:RD	0/0:999:2:999:.:.:.:.:RD',
'chr1	44000	DUP_chr1_4	N	<DUP>	999	UNSTABLE_AF_PCRMINUS;LOW_CALL_RATE	END=66000;SVTYPE=DUP;CHR2=chr1;SVLEN=22000;ALGORITHMS=depth;EVIDENCE=RD;PROTEIN_CODING__DUP_PARTIAL=OR4F5;NONCODING_SPAN=DNase;AN=1428;AC=96;AF=0.067227;N_BI_GENOS=714;N_HOMREF=641;N_HET=50;N_HOMALT=23;FREQ_HOMREF=0.897759;FREQ_HET=0.070028;FREQ_HOMALT=0.0322129;MALE_AN=772;MALE_AC=54;MALE_AF=0.069948;MALE_N_BI_GENOS=386;MALE_N_HOMREF=345;MALE_N_HET=28;MALE_N_HOMALT=13;MALE_FREQ_HOMREF=0.893782;MALE_FREQ_HET=0.0725389;MALE_FREQ_HOMALT=0.0336788;FEMALE_AN=656;FEMALE_AC=42;FEMALE_AF=0.064024;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=296;FEMALE_N_HET=22;FEMALE_N_HOMALT=10;FEMALE_FREQ_HOMREF=0.902439;FEMALE_FREQ_HET=0.0670732;FEMALE_FREQ_HOMALT=0.0304878	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/0:125:1:125:.:.:.:.:RD	0/0:72:2:72:.:.:.:.:RD	0/0:130:2:130:.:.:.:.:RD	0/0:1:2:1:.:.:.:.:RD	0/0:1:2:1:.:.:.:.:RD',
'chr1	44250	DUP_chr1_5	N	<DUP>	999	LOW_CALL_RATE	END=116000;SVTYPE=DUP;CHR2=chr1;SVLEN=71750;ALGORITHMS=depth;EVIDENCE=BAF,RD;PROTEIN_CODING__COPY_GAIN=OR4F5;LINCRNA__COPY_GAIN=AL627309.3;LINCRNA__DUP_PARTIAL=AL627309.1;NONCODING_SPAN=DNase;AN=1428;AC=82;AF=0.057423;N_BI_GENOS=714;N_HOMREF=646;N_HET=54;N_HOMALT=14;FREQ_HOMREF=0.904762;FREQ_HET=0.0756303;FREQ_HOMALT=0.0196078;MALE_AN=772;MALE_AC=43;MALE_AF=0.055699;MALE_N_BI_GENOS=386;MALE_N_HOMREF=351;MALE_N_HET=27;MALE_N_HOMALT=8;MALE_FREQ_HOMREF=0.909326;MALE_FREQ_HET=0.0699482;MALE_FREQ_HOMALT=0.0207254;FEMALE_AN=656;FEMALE_AC=39;FEMALE_AF=0.059451;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=295;FEMALE_N_HET=27;FEMALE_N_HOMALT=6;FEMALE_FREQ_HOMREF=0.89939;FEMALE_FREQ_HET=0.0823171;FEMALE_FREQ_HOMALT=0.0182927	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/0:1:1:1:.:.:.:.:RD	0/0:36:2:36:.:.:.:.:RD	0/0:94:2:94:.:.:.:.:RD	0/0:130:1:130:.:.:.:.:RD	0/0:999:1:999:.:.:.:.:RD',
'chr1	51400	DEL_chr1_1	N	<DEL>	999	UNSTABLE_AF_PCRMINUS	END=64000;SVTYPE=DEL;CHR2=chr1;SVLEN=12600;ALGORITHMS=depth;EVIDENCE=RD;PROTEIN_CODING__NEAREST_TSS=OR4F5;PROTEIN_CODING__INTERGENIC;NONCODING_SPAN=DNase;AN=1428;AC=306;AF=0.214286;N_BI_GENOS=714;N_HOMREF=443;N_HET=236;N_HOMALT=35;FREQ_HOMREF=0.620448;FREQ_HET=0.330532;FREQ_HOMALT=0.0490196;MALE_AN=772;MALE_AC=156;MALE_AF=0.202073;MALE_N_BI_GENOS=386;MALE_N_HOMREF=246;MALE_N_HET=124;MALE_N_HOMALT=16;MALE_FREQ_HOMREF=0.637306;MALE_FREQ_HET=0.321244;MALE_FREQ_HOMALT=0.0414508;FEMALE_AN=656;FEMALE_AC=150;FEMALE_AF=0.228659;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=197;FEMALE_N_HET=112;FEMALE_N_HOMALT=19;FEMALE_FREQ_HOMREF=0.60061;FEMALE_FREQ_HET=0.341463;FEMALE_FREQ_HOMALT=0.0579268	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/1:125:1:125:.:.:.:.:RD	0/0:72:2:72:.:.:.:.:RD	0/0:112:2:112:.:.:.:.:RD	0/0:1:2:1:.:.:.:.:RD	0/0:8:2:8:.:.:.:.:RD',
'chr1	52600	CNV_chr1_1	N	<CNV>	999	FAIL_minGQ	END=58000;SVTYPE=CNV;CHR2=chr1;SVLEN=5400;ALGORITHMS=depth;EVIDENCE=RD;PROTEIN_CODING__NEAREST_TSS=OR4F5;PROTEIN_CODING__INTERGENIC;NONCODING_SPAN=DNase;AN=0;AC=0;AF=0;MALE_AN=0;MALE_AC=0;MALE_AF=0;FEMALE_AN=0;FEMALE_AC=0;FEMALE_AF=0	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV:CN:CNQ	.:.:1:125:.:.:.:.:RD:1:125	.:.:2:130:.:.:.:.:RD:2:130	.:.:2:23:.:.:.:.:RD:2:23	.:.:2:1:.:.:.:.:RD:2:1	.:.:2:1:.:.:.:.:RD:2:1',
'chr1	66234	BND_chr1_2	N	<BND>	807	UNRESOLVED	END=66234;SVTYPE=BND;CHR2=chr19;STRANDS=-+;SVLEN=-1;ALGORITHMS=manta;EVIDENCE=PE;UNRESOLVED_TYPE=SINGLE_ENDER_-+;END2=108051;AN=1428;AC=236;AF=0.165266;N_BI_GENOS=714;N_HOMREF=514;N_HET=164;N_HOMALT=36;FREQ_HOMREF=0.719888;FREQ_HET=0.229692;FREQ_HOMALT=0.0504202;MALE_AN=772;MALE_AC=131;MALE_AF=0.169689;MALE_N_BI_GENOS=386;MALE_N_HOMREF=275;MALE_N_HET=91;MALE_N_HOMALT=20;MALE_FREQ_HOMREF=0.712435;MALE_FREQ_HET=0.235751;MALE_FREQ_HOMALT=0.0518135;FEMALE_AN=656;FEMALE_AC=105;FEMALE_AF=0.160061;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=239;FEMALE_N_HET=73;FEMALE_N_HOMALT=16;FEMALE_FREQ_HOMREF=0.728659;FEMALE_FREQ_HET=0.222561;FEMALE_FREQ_HOMALT=0.0487805	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/0:999:.:.:0:23:0:999:PE,SR	0/0:999:.:.:0:999:0:999:PE,SR	0/0:999:.:.:0:999:0:999:PE,SR	0/0:999:.:.:0:999:0:999:PE,SR	0/0:999:.:.:0:999:0:999:PE,SR',
'chr1	1495464	CPX_chr1_1	N	<CPX>	999	PASS	END=1495554;SVTYPE=CPX;CHR2=chr1;SVLEN=184;ALGORITHMS=manta;EVIDENCE=PE;CPX_TYPE=dDUP;SOURCE=DUP_chr1:1533874-1534058;CPX_INTERVALS=DUP_chr1:1533874-1534058;PROTEIN_CODING__DUP_PARTIAL=ATAD3A;AN=1428;AC=7;AF=0.004902;N_BI_GENOS=714;N_HOMREF=707;N_HET=7;N_HOMALT=0;FREQ_HOMREF=0.990196;FREQ_HET=0.00980392;FREQ_HOMALT=0;MALE_AN=772;MALE_AC=4;MALE_AF=0.005181;MALE_N_BI_GENOS=386;MALE_N_HOMREF=382;MALE_N_HET=4;MALE_N_HOMALT=0;MALE_FREQ_HOMREF=0.989637;MALE_FREQ_HET=0.0103627;MALE_FREQ_HOMALT=0;FEMALE_AN=656;FEMALE_AC=3;FEMALE_AF=0.004573;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=325;FEMALE_N_HET=3;FEMALE_N_HOMALT=0;FEMALE_FREQ_HOMREF=0.990854;FEMALE_FREQ_HET=0.00914634;FEMALE_FREQ_HOMALT=0	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/0:999:.:.:0:999:0:999:PE,SR	0/0:999:.:.:0:999:0:999:PE,SR	0/0:999:.:.:0:999:0:999:PE,SR	0/0:999:.:.:0:999:0:999:PE,SR	0/1:782:.:.:1:782:1:1:PE,SR',
'chr1	1643228	INS_chr1_10	N	<INS:ME:SVA>	250	PASS	END=1643309;SVTYPE=INS;CHR2=chr1;SVLEN=169;ALGORITHMS=melt;EVIDENCE=SR;PROTEIN_CODING__INTRONIC=CDK11B;AN=1428;AC=11;AF=0.007703;N_BI_GENOS=714;N_HOMREF=703;N_HET=11;N_HOMALT=0;FREQ_HOMREF=0.984594;FREQ_HET=0.0154062;FREQ_HOMALT=0;MALE_AN=772;MALE_AC=5;MALE_AF=0.006477;MALE_N_BI_GENOS=386;MALE_N_HOMREF=381;MALE_N_HET=5;MALE_N_HOMALT=0;MALE_FREQ_HOMREF=0.987047;MALE_FREQ_HET=0.0129534;MALE_FREQ_HOMALT=0;FEMALE_AN=656;FEMALE_AC=6;FEMALE_AF=0.009146;FEMALE_N_BI_GENOS=328;FEMALE_N_HOMREF=322;FEMALE_N_HET=6;FEMALE_N_HOMALT=0;FEMALE_FREQ_HOMREF=0.981707;FEMALE_FREQ_HET=0.0182927;FEMALE_FREQ_HOMALT=0;gnomAD_V2_SVID=gnomAD-SV_v2.1_INS_1_47;gnomAD_V2_AF=0.00130899995565414	GT:GQ:RD_CN:RD_GQ:PE_GT:PE_GQ:SR_GT:SR_GQ:EV	0/0:999:.:.:0:999:0:999:PE,SR	0/0:999:.:.:0:999:0:999:PE,SR	0/0:999:.:.:0:999:0:24:PE,SR	0/0:999:.:.:0:999:0:999:PE,SR	0/1:1:.:.:0:999:1:1:SR',
]

NULL_STR_ARRAY = hl.null(hl.dtype('array<str>'))
NULL_INTERVALS = hl.null(hl.dtype('array<struct{type: str, chrom: str, start: int32, end: int32}>'))
VARIANT0 = hl.struct(variantId='CPX_chr1_1', contig='1', sc=7, sf=0.004902, sn=1428, svType='CPX', start=1495464,
                     end=1495554, sv_callset_Hemi=7, sv_callset_Hom=0, gnomad_svs_ID=hl.null('str'),
                     gnomad_svs_AF=hl.null('float'),
                     pos=1495464, xpos=1001495464,
                     xstart=1001495464, xstop=1001495464,
                     sortedTranscriptConsequences=[hl.struct(gene_symbol='ATAD3A', gene_id='ENSG00000284663',
                                                             predicted_consequence='DUP_PARTIAL')],
                     transcriptConsequenceTerms=['CPX'], svTypeDetail='dDUP',
                     cpxIntervals=[hl.struct(type='DUP', chrom='1', start=1533874, end=1534058)],
                     geneIds=['ATAD3A'], filters=NULL_STR_ARRAY,
                     samples_num_alt_0=['SAMPLE-1', 'SAMPLE-3'],
                     samples_num_alt_1=['SAMPLE-5'],
                     samples_num_alt_2=NULL_STR_ARRAY,
                     genotypes=[
                         hl.struct(sample_id='SAMPLE-1', gq=999, num_alt=0, cn=hl.null('int')),
                         hl.struct(sample_id='SAMPLE-3', gq=999, num_alt=0, cn=hl.null('int')),
                         hl.struct(sample_id='SAMPLE-5', gq=782, num_alt=1, cn=hl.null('int')),
                                ])
VARIANT2 = hl.struct(variantId='DUP_chr1_1', contig='1', sc=370, sf=0.259104, sn=1428, svType='DUP', start=10000,
                     end=17000, sv_callset_Hemi=228, sv_callset_Hom=71, gnomad_svs_ID=hl.null('str'),
                     gnomad_svs_AF=hl.null('float'),
                     pos=10000, xpos=1000010000,
                     xstart=1000010000, xstop=1000010000,
                     sortedTranscriptConsequences=[hl.struct(gene_symbol='OR4F5', gene_id='ENSG00000284662.1_2',
                                                             predicted_consequence='NEAREST_TSS')],
                     transcriptConsequenceTerms=['DUP'], svTypeDetail=hl.null('str'), cpxIntervals=NULL_INTERVALS,
                     geneIds=NULL_STR_ARRAY, filters=['LOW_CALL_RATE'],
                     samples_num_alt_0=['SAMPLE-5'],
                     samples_num_alt_1=['SAMPLE-1', 'SAMPLE-3'], samples_num_alt_2=NULL_STR_ARRAY,
                     genotypes=[hl.struct(sample_id='SAMPLE-1', gq=999, num_alt=1, cn=3),
                                hl.struct(sample_id='SAMPLE-3', gq=19, num_alt=1, cn=3),
                                hl.struct(sample_id='SAMPLE-5', gq=31, num_alt=0, cn=2)])
VARIANT4 = hl.struct(variantId='INS_chr1_10', contig='1', sc=11, sf=0.007703, sn=1428, svType='INS', start=1643228,
                     end=1643309, sv_callset_Hemi=11, sv_callset_Hom=0, gnomad_svs_ID='gnomAD-SV_v2.1_INS_1_47',
                     gnomad_svs_AF=0.00130899995565414, pos=1643228, xpos=1001643228,
                     xstart=1001643228, xstop=1001643228, sortedTranscriptConsequences=[
        hl.struct(gene_symbol='CDK11B', gene_id='ENSG00000284664', predicted_consequence='INTRONIC')],
                     transcriptConsequenceTerms=['INS'], svTypeDetail='ME:SVA', cpxIntervals=NULL_INTERVALS,
                     geneIds=['CDK11B'], filters=NULL_STR_ARRAY,
                     samples_num_alt_0=['SAMPLE-1', 'SAMPLE-3'],
                     samples_num_alt_1=['SAMPLE-5'],
                     samples_num_alt_2=NULL_STR_ARRAY,
                     genotypes=[hl.struct(sample_id='SAMPLE-1', gq=999, num_alt=0, cn=hl.null('int')),
                                hl.struct(sample_id='SAMPLE-3', gq=999, num_alt=0, cn=hl.null('int')),
                                hl.struct(sample_id='SAMPLE-5', gq=1, num_alt=1, cn=hl.null('int')),])
TEST_PASSWORD = 'ExamplePasswd'


class LoadDataTest(unittest.TestCase):
    def setUp(self):
        self.vcf_file = tempfile.mkstemp(suffix='.vcf')[1]
        with open(self.vcf_file, 'w') as f:
            f.writelines('\n'.join(VCF_DATA))
        hl.init()
        self.mt = hl.import_vcf(self.vcf_file, reference_genome='GRCh38')

    def tearDown(self):
        hl.stop()
        os.remove(self.vcf_file)

    @mock.patch('sv_pipeline.genome.load_data.get_sample_subset')
    @mock.patch('sv_pipeline.genome.load_data.logger')
    @mock.patch('sv_pipeline.genome.utils.mapping_gene_ids.gene_id_mapping', hl.literal(GENE_ID_MAPPING))
    def test_sub_and_annotation(self, mock_logger, mock_get_sample):
        # Test subsetting dataset
        mock_get_sample.return_value = {'SAMPLE-1', 'SAMPLE-3', 'SAMPLE-5', 'SAMPLE-6'}
        with self.assertRaises(Exception) as e:
            _ = sub_setting_mt('test_guid', self.mt, sample_type='WGS', skip_sample_subset=False,
                                  ignore_missing_samples=False)
        self.assertEqual(str(e.exception), 'Missing the following 1 samples:\nSAMPLE-6')

        mock_get_sample.return_value = {'SAMPLE-1', 'SAMPLE-3', 'SAMPLE-5'}
        rows = sub_setting_mt('test_guid', self.mt, sample_type='WGS', skip_sample_subset=False, ignore_missing_samples=True)
        calls = [
            mock.call('Missing the following 0 samples:\n'),
            mock.call('Subsetting to 3 samples'),
        ]
        mock_logger.info.assert_has_calls(calls)
        mock_get_sample.assert_called_with('test_guid', 'WGS')
        self.assertEqual(rows.count(), 5)

        # Test annotate required fields
        rows = annotate_fields(rows)
        row_list = rows.take(5)

        self.assertListEqual([row_list[0], row_list[2], row_list[4]], hl.eval([VARIANT0, VARIANT2, VARIANT4]))

    @mock.patch('sv_pipeline.genome.load_data.logger')
    @mock.patch('sv_pipeline.genome.load_data.hl')
    @mock.patch('sv_pipeline.genome.load_data.load_gencode')
    @mock.patch('sv_pipeline.genome.load_data.os')
    @mock.patch('sv_pipeline.genome.load_data.time.time')
    @mock.patch('sv_pipeline.genome.load_data.sub_setting_mt')
    @mock.patch('sv_pipeline.genome.load_data.annotate_fields')
    @mock.patch('sv_pipeline.genome.load_data.ElasticsearchClient')
    def test_main(self, mock_es, mock_annot, mock_subset, mock_time, mock_os, mock_gencode, mock_hl, mock_logger):
        sys.argv[1:] = [self.vcf_file, '--project-guid', 'test_guid']
        mock_os.path.splitext.side_effect = lambda x: os.path.splitext(x)
        mock_os.path.isdir.return_value = True
        mock_hl.read_matrix_table.return_value = self.mt
        mock_time.side_effect = [0, 1, 3, 6]
        subset_rows = self.mt.rows()
        mock_subset.return_value = subset_rows
        rows = self.mt.rows().head(5)
        mock_annot.return_value = rows
        mock_os.environ.get.return_value = TEST_PASSWORD
        mock_es_client = mock_es.return_value
        main()
        mock_gencode.assert_called_with(29, genome_version=WGS_SAMPLE_TYPE, download_path='')
        mt_path = '{}.mt'.format(os.path.splitext(self.vcf_file)[0])
        mock_os.path.isdir.assert_called_with(mt_path)
        mock_hl.read_matrix_table.assert_called_with(mt_path)
        mock_subset.assert_called_with('test_guid', self.mt, WGS_SAMPLE_TYPE, False, False)
        mock_annot.assert_called_with(subset_rows)
        mock_os.environ.get.assert_called_with('PIPELINE_ES_PASSWORD', '')
        mock_es.assert_called_with(host='localhost', port='9200', es_password=TEST_PASSWORD)
        mock_es_client.export_table_to_elasticsearch.assert_called_with(
            rows,
            index_name='test_guid__structural_variants__wgs__grch38__19691231',
            index_type_name='_doc',
            block_size=2000,
            num_shards=6,
            delete_index_before_exporting=True,
            export_globals_to_index_meta=True,
            verbose=True,
        )
        calls = [
            mock.call('Use the existing MatrixTable {}.'.format(mt_path)),
            mock.call('Variant counts: 11'),
            mock.call('Total time for subsetting, annotating, and exporting: 3')
        ]
        mock_logger.info.assert_has_calls(calls)
