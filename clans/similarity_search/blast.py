import os
import re
import numpy as np
from Bio import SeqIO
from Bio.Blast.Applications import NcbimakeblastdbCommandline
from Bio.Blast.Applications import NcbiblastpCommandline
import clans.config as cfg
import clans.data.sequence_pairs as sp


def find_HSPs():

    # Create the blast-output directory under the working directory
    blast_out_path = cfg.run_params['working_dir'] + '/blast_output/'
    if not os.path.isdir(blast_out_path):
        os.mkdir(blast_out_path)

    # Set the output files names and paths
    fasta_file_name = os.path.split(cfg.run_params['input_file'])[1]  # save the file name without the full path
    name_parts = os.path.splitext(fasta_file_name)
    fasta_2line = blast_out_path + name_parts[0] + '_orig' + name_parts[1]
    fasta_indexed = blast_out_path + name_parts[0] + '_indexed' + name_parts[1]
    out_blast = blast_out_path + name_parts[0] + '.blast'

    # Create two FASTA files under the 'blast_output' directory:
    #  one as the original (with one-line sequence) and the other with indices as titles
    prepare_fasta(cfg.run_params['input_file'], fasta_2line, fasta_indexed)

    # Create a BLAST database from the input FASTA file
    make_blast_DB(fasta_indexed)

    # Run the all-vs-all BLAST search
    run_blast(fasta_indexed, out_blast)

    # Read the list of HSPs (BLAST output) and save the lower value for each pair of sequences in the global arrays
    # similarity_values_list and similarity_values_mtx
    read_blast_HSPs(out_blast)
    #print("similarity matrix:\n" + str(cfg.similarity_values_mtx))

    # Calculate and save the attraction values
    sp.calculate_attraction_values()
    sp.define_connected_sequences('hsp')


def prepare_fasta(orig_file_path, two_line_file, indexed_file):

    with open(two_line_file, 'w') as two_line_out:
        with open(indexed_file, 'w') as indexed_out:

            n = 0
            for record in SeqIO.parse(orig_file_path, "fasta"):
                # Change format in the first pass
                record.seq = record.seq.ungap("-")
                SeqIO.write(record, two_line_out, "fasta-2line")

                # Index them in the second
                record.id = str(n)
                record.description = ""
                SeqIO.write(record, indexed_out, "fasta-2line")
                n += 1


## Creates a BLAST database from the input fasta file
def make_blast_DB(infile):
    command = NcbimakeblastdbCommandline(dbtype="prot", input_file=infile)
    stdout, stderr = command()


def run_blast(query, out_blast):
    # Set the parameters for the BLAST run
    db = query
    evalue = cfg.run_params['evalue_cutoff'] # user-defined parameter
    matrix = cfg.run_params['scoring_matrix'] # user-defined parameter
    outfmt = "\"6 qacc sacc evalue\""
    max_hsps = 1
    max_target_seqs = cfg.run_params['total_sequences_num']
    threads_num = os.cpu_count()

    # Set the gap_open and gap_extend parameters according to the scoring matrix
    gapopen = 11
    gapext = 1
    if matrix == "BLOSUM80" or matrix == "PAM70":
        gapopen = 10
    elif matrix == "PAM30":
        gapopen = 9
    elif matrix == "BLOSUM45":
        gapopen = 15
        gapext = 2

    print('Running all-against-all blastp for {} sequences...'.format(max_target_seqs))
    command = NcbiblastpCommandline(query=query, db=db, evalue=evalue, outfmt=outfmt, out=out_blast,
                                    num_threads=threads_num, max_target_seqs=max_target_seqs, seg="no", gapopen=gapopen
                                    , gapextend=gapext)
    stdout, stderr = command()


def read_blast_HSPs(blast_out):
    cfg.similarity_values_mtx = np.ones([cfg.run_params['total_sequences_num'], cfg.run_params['total_sequences_num']])

    with open(blast_out) as infile:
        for line in infile:
            m = re.search("^(\d+)\s+(\d+)\s+(\S+)", line.strip())
            if m:
                index1 = int(m.group(1))
                index2 = int(m.group(2))
                evalue = float(m.group(3))

                if index1 < index2:
                    cfg.similarity_values_mtx[index1][index2] = evalue

                elif index1 > index2:
                    # The E-value of the reciprocal pair is better - update the matrix
                    if evalue < cfg.similarity_values_mtx[index2][index1]:
                        cfg.similarity_values_mtx[index1][index2] = evalue
                        cfg.similarity_values_mtx[index2][index1] = evalue
                    else:
                        cfg.similarity_values_mtx[index1][index2] = cfg.similarity_values_mtx[index2][index1]

        # Save the HSP line (in CLANS format) with the original E-value in the non-redundant pairs-list
        for i in range(cfg.run_params['total_sequences_num']-1):
            for j in range(i+1, cfg.run_params['total_sequences_num']):
                if i < j:
                    if cfg.similarity_values_mtx[i][j] <= cfg.run_params['evalue_cutoff']:
                        hsp_line = str(i) + ' ' + str(j) + ':' + str(cfg.similarity_values_mtx[i][j]) + '\n'
                        cfg.similarity_values_list.append(hsp_line)
                        if cfg.similarity_values_mtx[i][j] == 0.0:
                            cfg.similarity_values_mtx[i][j] = 10 ** -180









