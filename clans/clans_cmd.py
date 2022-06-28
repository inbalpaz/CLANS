# The main script for running clans via the command-line (no graphics) #
########################################################################
import time
import os
import clans.config as cfg
import clans.clans.io.file_handler as fh
import clans.clans.similarity_search.blast as blast
import clans.clans.layouts.layout_handler as lh


def run_cmd():
    # Read the input file (fasta/clans/delimited) and fill the relevant main data-structures
    try:
        print("Reading the input file")
        before = time.time()
        fh.read_input_file(cfg.run_params['input_file'], cfg.run_params['input_format'])
        after = time.time()
        duration = (after - before)
        if cfg.run_params['is_problem']:
            print(cfg.run_params['error'])
            exit()
        else:
            if cfg.run_params['is_debug_mode']:
                print("Reading the input file took "+str(duration)+" seconds")

    except Exception as err:
        print("An error has occurred while reading the input file")
        if cfg.run_params['is_debug_mode']:
            print("Error in run_clans_cmd.py:")
            print(err)
            exit()

    # Perform BLAST search and fill the HSP's E-values in the similarity matrix
    try:
        if cfg.run_params['run_blast']:
            print("Running blast")
            before = time.time()
            blast.find_HSPs()
            after = time.time()
            duration = (after - before)
            if cfg.run_params['is_problem']:
                print(cfg.run_params['error'])
                exit()
            else:
                if cfg.run_params['is_debug_mode']:
                    print("Performing the BLAST search took " + str(duration) + " seconds")

    except Exception as err:
        print("An error has occurred while running the BLAST search")
        if cfg.run_params['is_debug_mode']:
            print("Error in run_clans_cmd.py:")
            print(err)
            exit()

    # Run the Fruchterman-Reingold layout calculation for the defined number of rounds
    try:
        if cfg.run_params['num_of_rounds'] > 0:
            print("Running clustering of " + str(cfg.run_params['num_of_rounds']) + " rounds")
            before = time.time()
            lh.calculate_layout("FR")
            after = time.time()
            duration = (after - before)
            if cfg.run_params['is_debug_mode'] and cfg.run_params['rounds_done'] % 100 != 0:
                print("The calculation of " + str(cfg.run_params['rounds_done']) + " rounds took " + str(duration) +
                      " seconds")

    except Exception as err:
        print("An error has occurred while running the Fruchterman-Reingold layout calculation")
        if cfg.run_params['is_debug_mode']:
            print("Error in run_clans_cmd.py:")
            print(err)
            exit()

    ## Write the output file
    try:
        if cfg.run_params['output_file'] is not None:
            before = time.time()
            fh.write_file(cfg.run_params['output_file'], cfg.run_params['output_format'], 0)
            print("File " + cfg.run_params['output_file'] + " was successfully saved")
            after = time.time()
            duration = (after - before)
            if cfg.run_params['is_debug_mode']:
                print("Writing the output file took "+str(duration)+" seconds")

    except Exception as err:
        print("An error has occurred while saving the output file")
        if cfg.run_params['is_debug_mode']:
            print("Error in run_clans_cmd.py:")
            print(err)
            exit()
