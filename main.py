import time
import os
import clans.config as cfg
import clans.io.parser as parser
import clans.io.file_handler as fh
import clans.similarity_search.blast as blast
import clans.layouts.layout_handler as lh

# Parse the command-line arguments
parser.parse_arguments()
cfg.run_params['working_dir'] = os.getcwd()

# Read the input file (fasta/clans) and fill the relevant main data-structures: the structured array of sequences
# and in the case of a clans file, also the 2D matrix of similarity values of pairs
before = time.time()
fh.read_input_file(cfg.run_params['input_file'], cfg.run_params['input_format'])
after = time.time()
duration = (after - before)
if cfg.run_params['is_problem']:
    print(cfg.run_params['error'])
    exit()
else:
    print("Reading the input file took "+str(duration)+" seconds")

## Perform BLAST search and fill the HSP's E-values in the similarity matrix
if cfg.run_params['run_blast']:
    before = time.time()
    blast.find_HSPs()
    after = time.time()
    duration = (after - before)
    if cfg.run_params['is_problem']:
        print(cfg.run_params['error'])
        exit()
    else:
        print("Performing the BLAST search took " + str(duration) + " seconds")

## Run the Fruchterman-Reingold layout calculation for the defined number of rounds
if cfg.run_params['num_of_rounds'] > 0:
    before = time.time()
    lh.calculate_layout("FR")
    after = time.time()
    duration = (after - before)
    print("The calculation of " + str(cfg.run_params['rounds_done']) + " rounds took "+str(duration)+" seconds")

## Write the output file
before = time.time()
fh.write_file(cfg.run_params['output_file'], cfg.output_format)
after = time.time()
duration = (after - before)
print("Writing the output file took "+str(duration)+" seconds")
