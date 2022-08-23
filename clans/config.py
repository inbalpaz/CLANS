import numpy as np
from vispy.color import ColorArray
import clans

## Defaults
version = "2.0.4"

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

# Sizes
nodes_size_large = 10
nodes_size_medium = 8
nodes_size_small = 6
nodes_size_tiny = 4
text_size = 10
text_size_small = 8

max_groups_num = 300

inactive_color = "#A0A0A0"
title_color = "maroon"
hide_color = [1.0, 1.0, 1.0, 0.0]

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
    'no_gui': False,
    'total_sequences_num': 1,
    'input_format': input_format,
    'input_file': None,
    'output_file': None,
    'output_format': output_format,
    'type_of_values': type_of_values,
    'similarity_cutoff': similarity_cutoff,
    'is_debug_mode': False,
    'is_taxonomy_available': False,
    'finished_taxonomy_search': False,
    'found_taxa_num': 0,
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
    'gravity': layouts['FR']['params']['gravity'],
    'nodes_size': 8,
    'nodes_color': [0.0, 0.0, 0.0, 1.0],
    'nodes_outline_color': [0.0, 0.0, 0.0, 1.0],
    'nodes_outline_width': 0.5,
    'is_uniform_edges_color': False,
    'edges_color': [0.0, 0.0, 0.0, 1.0],
    'edges_color_scale': [[0.8, 0.8, 0.8, 1.0],
                          [0.6, 0.6, 0.6, 1.0],
                          [0.4, 0.4, 0.4, 1.0],
                          [0.2, 0.2, 0.2, 1.0],
                          [0.0, 0.0, 0.0, 1.0]],
    'is_uniform_edges_width': True,
    'edges_width': 1.0,
    'edges_width_scale': [1.0, 1.0, 1.0, 1.0, 1.0],
    'text_size': 10,
    'is_bold': True,
    'is_italic': False
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

# A list of grouping categories, holding all the information about the groups and their settings.
# Each category index is a dictionary holding the following information for each grouping-category:
# name, groups, sequences, nodes_size, nodes_outline_width, text_size, is_bold, is_italic
# - 'name': category name
# - 'sequences': a list of sequences, holding the group_ID to which the sequence belongs in a specific category
# (in case it belongs to no group, it gets -1)
# - 'groups': a dictionary, containing the following levels of information about each group:
# First level: Group_ID
# Second level (holding the following info for each group):
# - 'name', 'size', 'name_size', 'seqIDs', 'order', 'color', 'color_array', 'outline_color', 'is_bold', 'is_italic'
# - 'seqIDs' is a dictionary holding the indices of the sequences belonging to each group
# - 'order' (starting from -1) determines which group is displayed in front of the other (-1 = the most front)
# - 'color' is the old clans format: 225;32;100;255
# - 'color_array' is an array of size 4 to be used by Vispy
# - 'outline_color': array of size 4 for the group node's outline color
groups_by_categories = list()
groups_by_categories.append({
    'name': 'Manual definition',
    'groups': dict(),
    'sequences': list(),
    'nodes_size': run_params['nodes_size'],
    'text_size': run_params['text_size'],
    'nodes_outline_color': run_params['nodes_outline_color'],
    'nodes_outline_width': run_params['nodes_outline_width'],
    'is_bold': True,
    'is_italic': False
})

similarity_values_list = []  # a list of the non-redundant significant HSPs ('seq1_index', 'seq2_index', 'Evalue')
similarity_values_mtx = []  # a 2D matrix filled with Evalues for all pairs (redundant). The diagonal and non-significant pairs = 1
attraction_values_mtx = []  # a 2D matrix filled with attraction values for all pairs (redundant). The diagonal and non-significant pairs = 0
connected_sequences_mtx = []  # a boolean matrix (redundant). 1 for connected sequences (according to current Pvalue cutoff)
connected_sequences_mtx_subset = []
connected_sequences_list = []  # a 2D matrix listing the pairs of connected sequences according to the current P-value (non-redundant).
att_values_for_connected_list = []  # a 2D matrix listing the attraction values of connected sequences according to the current P-value (non-redundant).
connected_sequences_list_subset = []  # a 2D matrix listing the pairs of connected sequences according to the current P-value (non-redundant).
att_values_for_connected_list_subset = []  # a 2D matrix listing the attraction values of connected sequences according to the current P-value (non-redundant).
singeltons_list = []  # Boolean 1D array: contain 1 if sequence is a singelton (under a certain threshold)
singeltons_list_subset = []

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

taxonomy_names_file = str(clans.__path__[0]) + "/clans/taxonomy/names.dmp"
taxonomy_lineage_file = str(clans.__path__[0]) + "/clans/taxonomy/rankedlineage.dmp"

manual_path = str(clans.__path__[0]) + "/manual/Manual.pdf"

icons_dir = str(clans.__path__[0]) + "/clans/GUI/icons/"

input_example_dir = str(clans.__path__[0]) + "/input_example/"





