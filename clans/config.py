# Data-related variables
sequences_array = []  # a NumPy 1D structured array: 'seq_title', 'sequence', 'x_coordinate', 'y_coordinate', 'z_coordinate'
groups_list = []  # a list of dictionaries holding the following info for ech group: 'name', 'shape_type', 'size', 'hide', 'color', 'seqIDs'
similarity_values_list = []  # a list of the non-redundant significant HSPs ('seq1_index', 'seq2_index', 'Evalue')
similarity_values_mtx = []  # a 2D matrix filled with Evalues for all pairs (redundant). The diagonal and non-significant pairs = 1
attraction_values_list = []  # a list of the non-redundant attraction values ('seq1_index', 'seq2_index', 'attraction value')
attraction_values_mtx = []  # a 2D matrix filled with attraction values for all pairs (redundant). The diagonal and non-significant pairs = 0
connected_sequences = []  # a boolean matrix. 1 for connected sequences (according to current Pvalue cutoff)

## Defaults
# i/o related parameters
type_of_values = 'hsp'
input_format = 'clans'
output_format = 'clans'

# Clustering parameters
BLAST_Evalue_cutoff = 1.0
similarity_cutoff = 1e-4
num_of_dimensions = 3

# Layout-related parameters
layouts = {'FR':
               {'name': 'Fruchterman-Reingold', 'is_default': 1, 'params':
                    {'cooling': 1.0,
                     'current_temp': 1.0,
                     'maxmove': 0.1,
                     'att_val': 10.0,
                     'rep_val': 10.0,
                     'att_exp': 1,
                     'rep_exp': 1,
                     'dampening': 0.2,
                     'gravity': 1.0}}}

## Running parameters
run_params = {  # a dict to hold all the running parameters (given by the user / defaults) - filled by parser.py
    'is_problem': 0,
    'error': None
}



