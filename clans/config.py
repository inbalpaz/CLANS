import numpy as np

## Running parameters
run_params = {  # a dict to hold all the running parameters (given by the user / defaults) - filled by parser.py
    'is_problem': 0,
    'error': None,
    'total_sequences_num': 1
}

## Data-related variables

# a NumPy 1D structured array with the following fields:
# 'seq_title', 'sequence', 'x_coordinate', 'y_coordinate', 'z_coordinate', 'in_group'
# ('in_group' = group index. In case there is no group assignment, 'in_group' = -1)
seq_dt = np.dtype([('seq_title', 'U100'), ('sequence', 'U1000'), ('x_coor', 'float32'), ('y_coor', 'float32'),
                   ('z_coor', 'float32'), ('in_group', 'int16')])
sequences_array = np.empty(run_params['total_sequences_num'], dtype=seq_dt)

# a list of dictionaries holding the following info for each group:
# 'name', 'shape_type', 'size', 'hide', 'color', 'numbers', 'color_array', 'seqIDs'
# 'seqIDs' is a dictionary holding the indices of the sequences belonging to each group
groups_list = []

similarity_values_list = []  # a list of the non-redundant significant HSPs ('seq1_index', 'seq2_index', 'Evalue')
similarity_values_mtx = []  # a 2D matrix filled with Evalues for all pairs (redundant). The diagonal and non-significant pairs = 1
attraction_values_list = []  # a list of the non-redundant attraction values ('seq1_index', 'seq2_index', 'attraction value')
attraction_values_mtx = []  # a 2D matrix filled with attraction values for all pairs (redundant). The diagonal and non-significant pairs = 0
connected_sequences_mtx = []  # a boolean matrix (redundant). 1 for connected sequences (according to current Pvalue cutoff)
connected_sequences_list = []  # a 2D matrix listing the pairs of connected sequences according to the current P-value (non-redundant).
att_values_for_connected_list = [] # a 2D matrix listing the attraction values of connected sequences according to the current P-value (non-redundant).

## Defaults
# i/o related parameters
type_of_values = 'hsp'
input_format = 'clans'
output_format = 'clans'

# Blast-related default parameters
BLAST_Evalue_cutoff = 1.0
BLAST_scoring_matrix = 'BLOSUM62'

# Clustering parameters defaults
similarity_cutoff = 1e-4
num_of_dimensions = 3

# Layout-related default parameters
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





