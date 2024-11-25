import os
import sys
import shutil
import re
import numpy as np
from Bio import SeqIO
import subprocess
import multiprocessing
import clans.config as cfg
import clans.clans.data.sequence_pairs as sp


def find_HSPs():
    # Create the blast-output directory under the working directory
    blast_out_path = cfg.run_params['working_dir'] + '/blast_output/'

    # If the blast output dir already exists - delete its content
    if os.path.exists(blast_out_path):
        print("\nDirectory " + blast_out_path + " already exists - deleting its content")
        shutil.rmtree(blast_out_path)
    # Create a new blast output dir
    try:
        os.makedirs(blast_out_path)
    except OSError:
        print("\nmkdir " + blast_out_path + " has failed")
        exit()

    blastDB_path = blast_out_path + "blastDB/"
    if not os.path.isdir(blastDB_path):
        os.mkdir(blastDB_path)

    fasta_batches_path = blast_out_path + "fasta_batches/"
    if not os.path.isdir(fasta_batches_path):
        os.mkdir(fasta_batches_path)

    out_batches_path = blast_out_path + "out_batches/"
    if not os.path.isdir(out_batches_path):
        os.mkdir(out_batches_path)

    # Set the output files names and paths
    fasta_file_name = os.path.split(cfg.run_params['input_file'])[1]  # save the file name without the full path
    name_parts = os.path.splitext(fasta_file_name)
    fasta_2line = blast_out_path + name_parts[0] + '_orig' + name_parts[1]
    fasta_indexed = blast_out_path + name_parts[0] + '_indexed' + name_parts[1]
    blast_db_file_path = blastDB_path + name_parts[0] + "_blastDB"

    # Create two FASTA files under the 'blast_output' directory:
    #  one as the original (with one-line sequence) and the other with indices as titles
    prepare_fasta(cfg.run_params['input_file'], fasta_2line, fasta_indexed, fasta_batches_path, name_parts[0])

    # Verify that the files were indeed created
    if not os.path.isfile(fasta_2line) or os.path.getsize(fasta_2line) == 0:
        cfg.run_params['is_problem'] = True
        cfg.run_params['error'] = "Error: creating the two-lines FASTA file " + fasta_2line + " - cannot run BLAST."
        return
    if not os.path.isfile(fasta_indexed) or os.path.getsize(fasta_indexed) == 0:
        cfg.run_params['is_problem'] = True
        cfg.run_params['error'] = "Error creating the indexed file " + fasta_indexed + " - cannot make BLAST DB."
        return

    # Create a BLAST database from the input FASTA file
    rc_db = make_blast_DB(fasta_indexed, blast_db_file_path)

    # makeblastdb has failed
    if rc_db:
        cfg.run_params['is_problem'] = True
        cfg.run_params['error'] = "Cannot create BLAST database."
        return

    # Run the all-vs-all BLAST search in batches using by multiprocessing to speed up the calculation
    rc_blast = manage_blast_execution(fasta_batches_path, blast_db_file_path, out_batches_path)

    # The blast search stage has failed
    if rc_blast:
        cfg.run_params['is_problem'] = True
        cfg.run_params['error'] = "The BLAST search stage has failed."
        return

    # Read the list of HSPs (BLAST output) and save the lower value for each pair of sequences in the global arrays
    # similarity_values_list and similarity_values_mtx
    hsp_error = read_blast_HSPs(out_batches_path)
    if hsp_error != "":
        cfg.run_params['is_problem'] = True
        cfg.run_params['error'] = hsp_error
        return

    fill_values()


def prepare_fasta(orig_file_path, two_line_file, indexed_file, fasta_batches_path, file_prefix):
    # Write the two full fasta files (one with original headers and the indexed one with indexes as headers)
    with open(two_line_file, 'w') as two_line_out:
        with open(indexed_file, 'w') as indexed_out:
            n = 0
            for record in SeqIO.parse(orig_file_path, "fasta"):
                # Change format in the first pass
                SeqIO.write(record, two_line_out, "fasta-2line")

                # Index them in the second
                record.id = str(n)
                record.description = ""
                SeqIO.write(record, indexed_out, "fasta-2line")
                n += 1

    # Set the sequences batch size according to the overall number of sequences
    if cfg.run_params['total_sequences_num'] <= 100000:
        cfg.blast_batch_size = 500
    else:
        cfg.blast_batch_size = 1000

    # Create fasta files with batch_size number of sequences to be later run by blast in parallel
    file_counter = 0
    for seq_in_file_index in range(0, cfg.run_params['total_sequences_num'], cfg.blast_batch_size):

        file_counter += 1
        file_name = fasta_batches_path + file_prefix + str(file_counter) + ".fasta"

        # Open a file that should contain the batch_size fasta sequences
        with open(file_name, 'w') as fasta_batch:

            # A loop over the sequences that should be written to the current file
            for seq_index in range(seq_in_file_index, seq_in_file_index + cfg.blast_batch_size):
                if seq_index < cfg.run_params['total_sequences_num']:
                    fasta_batch.write(">" + str(seq_index) + "\n")
                    fasta_batch.write(cfg.sequences_array['sequence'][seq_index] + "\n")

        fasta_batch.close()


# Creates a BLAST database from the input fasta file
def make_blast_DB(infile, outfile):
    command = "makeblastdb -in " + infile + " -dbtype prot -parse_seqids -out " + outfile

    print("\nExecuting the following BLAST command:")
    print(command)

    try:
        subprocess.run(["makeblastdb", "-in", infile, "-dbtype", "prot", "-parse_seqids", "-out", outfile], check=True)

    except subprocess.CalledProcessError as err:
        print("\nThe following command has failed:")
        print(command)
        print(err)
        return 1

    except Exception as err:
        print("\nThe following command has failed:")
        print(command)
        print(err)
        return 1

    print("...Done!\n")
    return 0


def manage_blast_execution(fasta_batches_path, blast_db_file_path, out_batches_path):
    # Set the parameters for the BLAST run
    evalue = cfg.run_params['evalue_cutoff']  # user-defined parameter
    matrix = cfg.run_params['scoring_matrix']  # user-defined parameter
    outfmt = "6 qacc sacc evalue"
    max_hsps = 1
    max_target_seqs = cfg.run_params['total_sequences_num']
    threads_num = cfg.BLAST_threads_num

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

    # Create a list of the fasta sequences files
    fasta_files_list = []
    for file in os.listdir(fasta_batches_path):
        if re.search(r"^.+\.fasta", file):  # List only fasta files
            fasta_files_list.append(file)
    files_num = len(fasta_files_list)

    # A loop over batches of processes in the size of the available number of threads
    batch_counter = 0
    failed = 0
    for batch_index in range(0, files_num, cfg.run_params['cores_num']):

        batch_processes = []
        batch_counter += 1

        # A loop over the files of a certain multiprocessing batch
        for file_index in range(batch_index, batch_index + cfg.run_params['cores_num']):
            if file_index < files_num:
                fasta_file = fasta_files_list[file_index]
                name_parts = os.path.splitext(fasta_file)
                blast_outfile = name_parts[0] + ".blast"
                fasta_file_path = fasta_batches_path + fasta_file
                blast_file_path = out_batches_path + blast_outfile

                process = multiprocessing.Process(target=run_blastp,
                                                  args=(fasta_file_path, blast_db_file_path, blast_file_path,
                                                        evalue, outfmt, max_hsps, max_target_seqs, threads_num,
                                                        gapopen, gapext))
                # Start the process
                process.start()

                # Add the process to the list for later control
                batch_processes.append(process)

        print("\nRunning " + str(len(batch_processes)) + " processes of blastp in batch number " + str(batch_counter))

        # wait until all the processes in the batch are finished
        fail = 0
        for proc in batch_processes:
            proc.join()
            exit_code = proc.exitcode

            if exit_code != 0:
                fail = 1
                print("\nBatch number " + str(batch_counter) + " failed or finished without any valid hits")
                print("Stopping blast execution")
                break

        if fail:
            break
        else:
            print("\nAll processes in batch number " + str(batch_counter) + " finished successfully")

    if fail:
        return 1
    else:
        return 0


def run_blastp(infile, blast_db_file_path, outfile, evalue, outfmt, max_hsps, max_target_seqs, threads_num, gapopen,
               gapext):
    command = "blastp -query " + infile + " -db " + blast_db_file_path + " -evalue " + str(evalue) + \
              " -out " + outfile + " -outfmt " + outfmt + " -max_target_seqs " + str(max_target_seqs) + \
              " -max_hsps " + str(max_hsps) + " -seg no -gapopen " + str(gapopen) + " -gapextend " + str(gapext) + \
              " -num_threads " + str(threads_num)

    try:
        subprocess.run(["blastp", "-query", infile, "-db", blast_db_file_path, "-evalue", str(evalue),
                        "-out", outfile, "-outfmt", outfmt, "-max_target_seqs", str(max_target_seqs),
                        "-max_hsps", str(max_hsps), "-seg", "no", "-gapopen", str(gapopen), "-gapextend", str(gapext),
                        "-num_threads", str(threads_num)], check=True)

    except subprocess.CalledProcessError as err:
        print("\nThe following command has failed:")
        print(command)
        print(err)
        sys.exit(1)

    except Exception as err:
        print("\nThe following command has failed:")
        print(command)
        print(err)
        sys.exit(1)


def read_blast_HSPs(blast_out_dir):
    error = ""

    # Create a 2D Numpy array for the similarity values and initialize it with 100
    cfg.similarity_values_mtx = np.full([cfg.run_params['total_sequences_num'],
                                         cfg.run_params['total_sequences_num']], 100, dtype=float)
    cfg.attraction_values_mtx = np.zeros([cfg.run_params['total_sequences_num'],
                                          cfg.run_params['total_sequences_num']])

    blast_files_list = []
    for file in os.listdir(blast_out_dir):
        if re.search(r"^.+\.blast", file):  # List only blast files
            blast_files_list.append(file)
    files_num = len(blast_files_list)

    # Verify that there are any output files in the output directory
    if files_num == 0:
        error = "No blast output files."
        return error

    # A loop over the files in the output dir
    for file in blast_files_list:

        file_path = blast_out_dir + file

        with open(file_path) as infile:
            for line in infile:
                m = re.search(r"^(\d+)\s+(\d+)\s+(\S+)", line.strip())
                if m:
                    index1 = int(m.group(1))
                    index2 = int(m.group(2))
                    evalue = float(m.group(3))

                    if index1 < index2:
                        # Assign the Evalue to the pair + reciprocal pair
                        if float(evalue) == 0.0:
                            cfg.similarity_values_mtx[index1][index2] = 10 ** -180
                            cfg.similarity_values_mtx[index2][index1] = 10 ** -180
                        else:
                            cfg.similarity_values_mtx[index1][index2] = evalue
                            cfg.similarity_values_mtx[index2][index1] = evalue

                        pair_tuple = (index1, index2, evalue)
                        cfg.similarity_values_list.append(pair_tuple)

    return error


# Calculate and save the attraction values and apply the similarity cutoff
def fill_values():
    cfg.run_params['type_of_values'] = "hsp"
    sp.calculate_attraction_values()
    sp.define_connected_sequences('hsp')
