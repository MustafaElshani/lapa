import pytest
import pysam
import pyBigWig
import pandas as pd
import numpy as np
from lapa.count import TailTesCounter, \
    count_tes_bam_samples, agg_tes_samples
from conftest import quantseq_gm12_bam, short_bam, chr17_chrom_sizes


def load_reads(seq, cigar, flag, pos):
    bam = pysam.AlignmentFile(quantseq_gm12_bam)
    read = {
        'name': 'NS500169:839:HMNMLAFX2:1:11309:11029:9457',
        'flag': flag,
        'ref_name': 'chr17',
        'ref_pos': pos,
        'map_quality': '255',
        'cigar': cigar,
        'next_ref_name': '*',
        'next_ref_pos': '0',
        'length': '0',
        'seq': seq,
        'qual': '5' * len(seq),
        'tags': []
    }
    return pysam.AlignedSegment.from_dict(read, bam.header)


def test_detect_polyA():
    seq = 'CGCAATATGACGTTTCCATTTACTTTGGATTATATGTCATTATAAATATTAACAAATAAGACTTAAAAAGGACACCTTCGGGTAGGTCAGACCAAAATACAAAACTTGTCTGTGGGACTGCAGTTTGGA'
    cigar = '127M2S'
    flag = '16'
    pos = '143694'
    read = load_reads(seq, cigar, flag, pos)

    polyA_site, tail_len, percent_A = TailTesCounter.detect_polyA_tail(read)

    assert polyA_site is None
    assert tail_len == 0
    assert percent_A == 0

    seq = 'GCGCAGCAGGGGTGGTCGCCATGGAGACGCGTGGCCCTGGCCTGGCGGTCCGCGCTGAGAGTCGCCGATTAGTCGGCATCGGGCCTCGGGCGCCCCCGGGGCGGGTTGGGTTGCAGCCCAGCGGGCGGCTGGACCGCCGCGGTGGGGCGGGGACAATGGGGTACAAGGACAACGACGGCGAGGAGGAGGAGCGGGAGGGCGGCGCCGCGGGCCCGCGGGGGTCTAGACTGCCCCCCATCACAGGCGGCGCCTCCGAGCTGGCCAAACGGAAGGTGAAGAAGAAAAAAAGGAAGAAGAAGACCAAGGGGTCTGGCAAGGGGGACGGGATCTTGCTCTGGGGAAAGCCAGCTGCAGTGTTGTGTGGGCTGCCTGAGGAAAGGTGCCCTCCGGAAAGAAATGATGTCTCCGCCCAACAGCATGGTGGACCTGAGTCCTGCTACCAGCCACATGAGTGTGCTTGGAAGCAGGTGGAGCCCAGTTGAGCCTTGAGGTGCCTCCCTCTGTGAGAGACCCCAAGCCGGAGACATCCGGCCAAGAGGCACCCAGATTCCTGCCCCACAGAAACTGATACAATAACGTTGTTTAAAGCCACTACATTTGGAGGTAATCTTGTTACACAGCAATAACTGACTAATACAGTCGGCCTCTTCCATCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    cigar = '324M10025N331M100S'
    flag = '0'
    pos = '410323'
    read = load_reads(seq, cigar, flag, pos)

    polyA_site, tail_len, percent_A = TailTesCounter.detect_polyA_tail(read)

    assert polyA_site == 421002
    assert tail_len == 100
    assert percent_A == 1

    seq = 'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTATGACGTTTCCATTTACTTTGGATTATATGTCATTATAAATATTAACAAATAAGACTTAAAAAGGACACCTTCGGGTAGGTCAGACCAAAATACAAAACTTGTCTGTGGGACTGCAGTTTGAGGACAGTGTCTGCAGCCGTCACATGGCAGCAAAACGGGGTTAAGCAGTGCACGAGAGTCTGCGTCGACGACAGCCAGAGTCCATGCATCGGGAGGTTCACTCGGTTTGCGAAGGAACAACGGGCTCGGCATGCACGGGCTCGGCGGCGGCGGACGGGCCGGGGCGCAGTTCCCCGCGCTCGCCACTAGAGGTCAGGAGGTGACCGCTTCGGGGCTGGAAGACGGGCCCGTCGGGGATTGGCGCAGGCGGCGGGCGGGGCGGCGGGCGGGGCGGCGCTGGAGGCAGCGCCTGGTTACTGACACCTGGAATGACTTTTTTTTTTTGGCATCAGATTTCCTGTCTTTGTGGGGATGATGGACCCGAGTAAAGATGCCCATTCGGGGTCAAAGGCAGAGCCGCTTCTGCAGCTTCTCAAAGCGTTGTTTGTTTGTTTTTTTTTCTGAGACGGAGTCTTGCTCTGTCGCCCAGGCTGGAGTGCAGTGCCGCGATCTTGGCTCACTGCAGCCTTCACCTCCCGGGTTCAAGCGATTCTCGTGCCTCAGCCTCCCTGAGTAGCTGGGACTACAGGCGTGCGCCACCACACCCGGCTAATTTTTGTATTTTTAGTAGAGATGGGGTTTCGCCCTGTTGGCCAGGCGGGTTTCGAACTCCTGACCTCAGGTGATCCGCCAGCCTCGGCCTCCCAAAGTGCTGCAATTACAGGCGTGAGCCATCGTGCCTCAAAACGCTTTAACAGAAAGACAATCTGCACGGGATCTAAAAGGGTGCTGAGATCCTAGGGAAGGAAGGATCCAAACTTCCTGGGGAGTTCCTGCCCGAGTGCCTGTGCTGCCCCTGGGCTGGCTGGCCAGTAAGCCCGCCTCCCAGCCTGACTGTCCCCATCTTTCGGTCCCAGCCCCATTTGCACAGCCTGGGCAGTAGAGGGCCCTGGACTGGGGGGCTGGAGTTCTGGGTTCTTGTCCCAGCTGTGCCCCTTCAGGCCCCTTTCACCCACTGGGCCTCACATTCCCCATGTGCCTAATAAGGAAGTCATGGTAGGTGGGGGGTACAGCCTCTTCTCGCTTTGCCATTCACTTCTGTGTCTTCAGAGAGGCTGTCAAATCTCCTCTCTGAATGAGACCCCCAAAAAAGCAAAGCTAAGAAGATACCCAGAGCTTAACTAGACACCAGGCCTTTTAGAAATAGACCACCTCTTACCTTAGGCCCCCAGAGGGTGCCCATTCTGTGTGGAGAAAAGAGGAGCCCTTGCCTCAGCCCCCAGAGGCTAGGGTGGGGTGGCTGAGTTTTGGGGCCAGGTTAGACACCTCTGGGGAAGCCTGAAGTAGCACGGATGGTTTCAAAGCCAGCGGATGAGGTGGCAGGACAGTGACAAGACCCCAGGTCTCCATCATGCACCTGAGCTTACTGAGCCTTCACCTGGTGTCTCTGCTGAGTCTCCGACAGACCAAGAGGGAAGGGACTGGGGTACCGACCCCCAGAGAGAGAAAGCGGCAGTCAGAGGACCTGGGTTTGAGTCCTGGTTCACCCCTTCCTGGCTGTGTGGCCTTGGCAAACTACTCAGACTCTGGGAACCTGTTTCACCTGCAAGATGGGGATGAGAATCAAACCCACCTTGCAGGGCTGTGAACATGCGTTCAGACCAGTGCATGCAAAAACCTTCACACAAAAACCCTTCCTAAAGGCAGGGAGACAAGTCTCCAGGAGCAGCAGGTGGCCAGGGACTGTGTGGGGGCTGGGGTCCTGTTTTCCCCGCAACCTGGGAAAGGCCTGATGGGCACTTGGTAGGATTCAAATCATAACCCTGGACCTCAGGTGGTGGTGTGTGCTTTGTGTCTGCAGTGGAAGGTCCCACCGTCGTGCCTGTGAGTCCCTCTATCGTGTTGAAGGGGTGGGCAGCAGGCGGGGGAGCCCAGGCTGGCAGCTAGCAGGACCTCTCTGGTGTGAGCTCAGCACGCCAATTCCCCTGAAGCGTGGTGTCCAGCACTCTGGGCTGGGGGCTGTGGATCCTGGTTCCAGCTGTGTGGGGCCTGGAAGGCCCTGGGCAGGTCACCTGACCTCTCTGGGCCTGTTTCCATCACACACTGATGGGCTGAGCACACTGGGACTCTGGCTGTGCAACTCCTTGGCTCTGCATTTGTTCACCCAGCGTTCCTGAGGGGCCCTTGGTAGGCAGAGAAAGTTTGTGGGCTTCAGGCATGGGCCCCAAGATTCAGATACTCTCAAGCCTCCTGGGGAGTCTCACTCAGGGGAGCAGACAGGCCCACCAGCCAGGGTGATTCTTGCTCAGCTCCTGGAGGGTGGAGCTGGCCCCACAGGCCTCCCCAAAGACAAGGCCCTGGACGGCCACTGATTACTCCCAAAAGGGACATCTGTGGCGGTAGTGGGGACCAAGATGCCACGAGCAAGCACCCGGAGGCCCCCAGTGTGAGCCATGGAGTGGAGGGGAGGGGAAAGGGCAGAGTCAGGACGTGTAGGAATGCTTGCTTTTTTTCCAAGCACAAGGGACCCTTTTCTCCACTGCAGCTGACCTGATGCTTATGCCAGGAAGGAGGAGGGGCGGGCTCCGTCCTTGAGGTCCCTCAGGAGTAGAAAGAGATCAGAGTGGGAGACTTGGGTCTGAGGTCTGAACTTGAGCCTACACCAGTTTCTCCATGGTGTTTCCATCACGTCCCCCACCTCCTGCCTCGAGCCTCACACCTTCCTAACAAACCCTCCCCTGGAGAGGAGACCCTGGGTCCACAGCACCCGGCCCCATTGGCTTTCTCTCTCCAGGCGTTTTAGACCACTCCCACTGCCTGGACTGCTTTTAGAAGCCCTCACTCACCCTCCAAGGCCTTACGGAAGCACCGCCTCCTCCAGGAAGCCGTCCCTGACCTCCCGGCAGAGTCAGCAGAGCCCACGGTACTTGCAGACTGGCCAAGCTGGTCTTGGTATTTCTCACCCCAGTTGGAATGGTTTGTTCCCAGCTTCCTGACTAGATGGGAACTCCCTGAGGGCAGGCCCTGTGTCTCATTCACCCCAGGGCTTGTGGAATCATTGAGTGAAGCATGTGCCAATTTACCCATCATCAGGAGCCTCCGGGAACTCTGGCAGACTTTCGGCCGGCAGGCCCGCTTCTTCCATCTGTCCAGCAGCGAAGGAGATGAGGGATGCAGTTAGGCTTTCTTGGGCTGGAGCAGCCAGTCTTCAAGGTCCCATCCTCCACC'
    cigar = '104S257M5D11M2I97M12D186M1I1030M1D357M2I57M1D31M1D474M1I108M1D253M1D272M1D190M'
    flag = '16'
    pos = '143699'
    read = load_reads(seq, cigar, flag, pos)

    polyA_site, tail_len, percent_A = TailTesCounter.detect_polyA_tail(read)

    assert polyA_site == 143698
    assert tail_len == 104
    assert percent_A == 1

    seq = 'CAAATAGGAGCAGTATGATTTTTTCTTTTATTTTTAATTGACAAATAATAATTATATAAACAATGTAATTTCTAACAACAAAGGAATGCTAAAAAATATACAAAAAAAAAAAAAAAAAAAAGAGCGGAGGCGCCCCCGGGTGCACGCCGG'
    cigar = '1S119M30S'
    flag = '0'
    pos = '716075'
    read = load_reads(seq, cigar, flag, pos)

    polyA_site, tail_len, percent_A = TailTesCounter.detect_polyA_tail(read)

    assert polyA_site == 716193
    assert tail_len == 1
    assert percent_A == 1

    seq = 'GGGCCGGGCGGGCCGCCGGGGGCGCTGCCGCCCTTTTTTTTTTTTTTTTTTAAGAGCAGAGTGAACTCTTTATTGATTATACAAATTACCACTATTTATTTTAAACCCAAAGTGACTTCAAAGTTGTTTTTTGGTTTTTAAAGGGGCTAC'
    flag = '16'
    cigar = '50S100M'
    pos = '515042'
    read = load_reads(seq, cigar, flag, pos)

    polyA_site, tail_len, percent_A = TailTesCounter.detect_polyA_tail(read)

    assert polyA_site == 515041
    assert tail_len == 17
    assert percent_A == 1


@pytest.fixture
def tes_counter_short():
    return TailTesCounter(short_bam)


def test_TailTesCounter_iter_tailed_reads(tes_counter_short):
    tailed = sum(1 for i in tes_counter_short.iter_tailed_reads())
    assert tailed > 3900


def test_TailTesCounter_tail_len_dist(tes_counter_short):
    tail_len = tes_counter_short.tail_len_dist()
    assert tail_len.shape[0] > 20


def test_TailTesCounter_save_tailed_reads(tes_counter_short, tmp_path):
    tailed_bam = str(tmp_path / 'tailed.bam')
    tes_counter_short.save_tailed_reads(tailed_bam)

    tailed_bam = pysam.AlignmentFile(tailed_bam, 'rb')
    tailed = sum(1 for i in tailed_bam)
    assert tailed > 3900


def test_TailTesCounter_count(tes_counter_short):
    tes = tes_counter_short.count()
    assert len(tes) > 1000


def test_TailTesCounter_to_df(tes_counter_short):
    df = tes_counter_short.to_df()
    assert df.shape[0] > 1000


def test_count_tes_samples(tmp_path):
    output_dir = tmp_path / 'multi_sample'
    output_dir.mkdir()

    df = pd.DataFrame({
        'sample': ['short_rep1', 'short_rep2', 'short', 'short'],
        'path': [short_bam, short_bam, short_bam, short_bam]
    })
    df_count = count_tes_bam_samples(df, 'tail')
    df_all, tes = agg_tes_samples(df_count, chr17_chrom_sizes, output_dir)

    pd.testing.assert_frame_equal(
        tes['short_rep1'],
        tes['short_rep2']
    )
    _df = tes['short_rep1'].copy()
    _df['count'] *= 4
    pd.testing.assert_frame_equal(df_all, _df)

    _df = tes['short_rep1'].copy()
    _df['count'] *= 2
    pd.testing.assert_frame_equal(tes['short'], _df)

    assert {i.name for i in output_dir.iterdir()} == {
        'all_tes_counts_pos.bw',
        'all_tes_counts_neg.bw',
        'short_tes_counts_pos.bw',
        'short_tes_counts_neg.bw',
        'short_rep1_tes_counts_pos.bw',
        'short_rep1_tes_counts_neg.bw',
        'short_rep2_tes_counts_pos.bw',
        'short_rep2_tes_counts_neg.bw'
    }

    bw_pos = pyBigWig.open(str(output_dir / 'all_tes_counts_pos.bw'))
    bw_neg = pyBigWig.open(str(output_dir / 'all_tes_counts_neg.bw'))
    count = np.nansum(
        bw_pos.values('chr17',
                      int(df_all['End'].min() - 1),
                      int(df_all['End'].max()))
    ) + np.nansum(
        bw_neg.values('chr17',
                      int(df_all['End'].min() - 1),
                      int(df_all['End'].max()))
    )
    assert df_all['count'].sum() == count

    bw_pos = pyBigWig.open(str(output_dir / 'short_tes_counts_pos.bw'))
    bw_neg = pyBigWig.open(str(output_dir / 'short_tes_counts_neg.bw'))
    count = np.nansum(
        bw_pos.values('chr17',
                      int(df_all['End'].min() - 1),
                      int(df_all['End'].max()))
    ) + np.nansum(
        bw_neg.values('chr17',
                      int(df_all['End'].min() - 1),
                      int(df_all['End'].max()))
    )
    assert df_all['count'].sum() / 2 == count

    output_dir = tmp_path / 'single_sample'
    output_dir.mkdir()

    df = pd.DataFrame({
        'sample': ['short', 'short'],
        'path': [short_bam, short_bam]
    })

    df_count = count_tes_bam_samples(df, 'tail')
    df_all, tes = agg_tes_samples(df_count, chr17_chrom_sizes, output_dir)
    assert {i.name for i in output_dir.iterdir()} == {
        'all_tes_counts_pos.bw', 'all_tes_counts_neg.bw'}
