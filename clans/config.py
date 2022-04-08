import numpy as np
from vispy.color import ColorArray

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

# Colors
min_param_color = ColorArray([1.0, 1.0, 0.0, 1.0])
max_param_color = ColorArray([1.0, 0.0, 0.0, 1.0])
short_color = ColorArray([1.0, 1.0, 0.0, 1.0])
long_color = ColorArray([1.0, 0.0, 0.0, 1.0])

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

## Running parameters
run_params = {  # a dict to hold all the running parameters (given by the user / defaults) - filled by parser.py
    'is_problem': False,
    'error': None,
    'total_sequences_num': 1,
    'input_format': input_format,
    'input_file': None,
    'output_format': output_format,
    'type_of_values': type_of_values,
    'is_debug_mode': False,
    'is_taxonomy_available': False,
    'finished_taxonomy_search': False,
    'dimensions_num_for_clustering': num_of_dimensions,
    'num_of_rounds': 0,
    'rounds_done': 0,
    'cooling': layouts['FR']['params']['cooling'],
    'maxmove': layouts['FR']['params']['maxmove'],
    'att_val': layouts['FR']['params']['att_val'],
    'att_exp': layouts['FR']['params']['att_exp'],
    'rep_val': layouts['FR']['params']['rep_val'],
    'rep_exp': layouts['FR']['params']['rep_exp'],
    'dampening': layouts['FR']['params']['dampening'],
    'gravity': layouts['FR']['params']['gravity']
}

## Data-related variables

# a NumPy 1D structured array with the following fields:
# 'seq_title', 'sequence', 'x_coordinate', 'y_coordinate', 'z_coordinate', 'in_group', 'in_subset'
# 'in_group' = group index. In case there is no group assignment, 'in_group' = -1
# 'in_subset' is a boolean flag, stating whether the index is found in the selected subset or not (False by default)
# the subset coordinates are used to save the subset new coordinates in case it was clustered separately.
# They are initialized with the whole dataset coordinates at the beginning and whenever the view returns to full dataset.
seq_dt = np.dtype([('seq_ID', 'U300'), ('seq_title', 'U300'), ('sequence', 'U3000'), ('seq_length', 'int16'),
                   ('norm_seq_length', 'float32'), ('organism', 'U100'), ('tax_ID', 'U20'),
                   ('x_coor', 'float32'), ('y_coor', 'float32'), ('z_coor', 'float32'), ('in_subset', 'bool'),
                   ('x_coor_subset', 'float32'), ('y_coor_subset', 'float32'), ('z_coor_subset', 'float32')])
sequences_array = np.empty(run_params['total_sequences_num'], dtype=seq_dt)

# A dictionary for connecting each sequence_ID (unique name) ith its index (by order)
sequences_ID_to_index = dict()

# A dictionary of lists containing numeric parameters (for example: 'sequence length') for each sequence
sequences_numeric_params = dict()

# an hierarchic dictionary containing several levels, for holding all the groups information
# Upper level: grouping type (input_file, manual, taxonomy, user-defined)
# Second level: Group_ID
# Inner level (holding the following info for each group):
# - 'name', 'size', 'name_size', 'seqIDs', 'order', 'color', 'color_array', 'is_bold', 'is_italic'
# - 'seqIDs' is a dictionary holding the indices of the sequences belonging to each group
# - 'order' (starting from -1) determines which group is displayed in front of the other (-1 = the most front)
# - 'color' is the old clans format: 225;32;100;255
# - 'color_array' is an array of size 4 to be used by Vispy
# - 'outline_color': array of size 4 for the group node's outline color
groups_dict = dict()
groups_dict['input_file'] = dict()
groups_dict['manual'] = dict()

# A dictionary of lists to hold for each group-type and sequence, the group_ID it belongs to (-1 if belongs to no group)
sequences_in_groups = dict()
sequences_in_groups['input_file'] = []
sequences_in_groups['manual'] = []

similarity_values_list = []  # a list of the non-redundant significant HSPs ('seq1_index', 'seq2_index', 'Evalue')
similarity_values_mtx = []  # a 2D matrix filled with Evalues for all pairs (redundant). The diagonal and non-significant pairs = 1
attraction_values_mtx = []  # a 2D matrix filled with attraction values for all pairs (redundant). The diagonal and non-significant pairs = 0
connected_sequences_mtx = []  # a boolean matrix (redundant). 1 for connected sequences (according to current Pvalue cutoff)
connected_sequences_list = []  # a 2D matrix listing the pairs of connected sequences according to the current P-value (non-redundant).
att_values_for_connected_list = []  # a 2D matrix listing the attraction values of connected sequences according to the current P-value (non-redundant).
connected_sequences_list_subset = []  # a 2D matrix listing the pairs of connected sequences according to the current P-value (non-redundant).
att_values_for_connected_list_subset = []  # a 2D matrix listing the attraction values of connected sequences according to the current P-value (non-redundant).

# Taxonomy-related variables

# a list of dictionaries (the keys are the unique tax_IDs)
# holding the taxonomy hierarchy for each organism: tax_ID, genus, family, order, class, phylum, kingdom, domain
taxonomy_dict = dict()

# A organism_name => tax_ID (organism name as extracted from sequence header)
organisms_dict = dict()

# taxonomic_level => dict of sequence_IDs
seq_by_tax_level_dict = {
    'Family': dict(),
    'Order': dict(),
    'Class': dict(),
    'Phylum': dict(),
    'Kingdom': dict(),
    'Domain': dict()
}

taxonomy_names_file = "clans/taxonomy/names.dmp"
taxonomy_lineage_file = "clans/taxonomy/rankedlineage.dmp"





