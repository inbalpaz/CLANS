import numpy as np
import numba
from vispy.color import ColorArray
import clans.config as cfg
import random


#@profile
def create_sequences_array(sequences_list):
    # Resize the sequences array according to the input number of sequences
    np.resize(cfg.sequences_array, cfg.run_params['total_sequences_num'])

    # Insert the sequences to a NumPy structured array with the following fields:
    # seq_title, sequence, x_coordinate, y_coordinate, z_cordinate, in_group(initialized with -1)
    cfg.sequences_array = np.array(sequences_list, dtype=cfg.seq_dt)

    #print("create_sequences_array: Sequences_array=\n" + str(cfg.sequences_array))


def init_seuences_in_groups():
    cfg.sequences_in_groups['manual'] = np.full(cfg.run_params['total_sequences_num'], -1)


def add_seq_length_param():

    cfg.sequences_array['seq_length'] = np.char.str_len(cfg.sequences_array['sequence'])

    min_seq_length = np.amin(cfg.sequences_array['seq_length'])
    max_seq_length = np.amax(cfg.sequences_array['seq_length'])

    if min_seq_length != max_seq_length:
        cfg.sequences_array['norm_seq_length'] = (cfg.sequences_array['seq_length'] - min_seq_length) / \
                                                 (max_seq_length - min_seq_length)

    else:
        if min_seq_length == 0:
            cfg.sequences_array['norm_seq_length'] = np.zeros(cfg.run_params['total_sequences_num'])
        else:
            cfg.sequences_array['norm_seq_length'] = np.full(cfg.run_params['total_sequences_num'], 0.5)


def add_numeric_params(params_dict):

    added_params = []

    for param_name in params_dict:

        # Sort the sequence indices in case they were originally provided by sequence_ID, not necessarily ordered
        sorted_keys = sorted(params_dict[param_name].keys())
        values_list = []

        for key in sorted_keys:
            values_list.append(params_dict[param_name][key])

        # If parameter already exists: add a serial number to it
        if param_name in cfg.sequences_numeric_params:
            param_name = param_name + "_1"

        cfg.sequences_numeric_params[param_name] = dict()

        cfg.sequences_numeric_params[param_name]['raw'] = np.array(values_list, dtype=float)
        normalize_numeric_param(param_name)

        cfg.sequences_numeric_params[param_name]['min_color'] = cfg.min_param_color
        cfg.sequences_numeric_params[param_name]['max_color'] = cfg.max_param_color

        added_params.append(param_name)

    return added_params


# Add numeric parameters that were saved in a full CLANS file (including colors)
def add_saved_numeric_params(params_dict):

    for param_name in params_dict:
        cfg.sequences_numeric_params[param_name] = dict()

        cfg.sequences_numeric_params[param_name]['raw'] = np.array(params_dict[param_name]['values'], dtype=float)
        normalize_numeric_param(param_name)

        min_color_arr = params_dict[param_name]['min_color'].split(';')
        max_color_arr = params_dict[param_name]['max_color'].split(';')

        for i in range(4):
            min_color_arr[i] = int(min_color_arr[i]) / 255
            max_color_arr[i] = int(max_color_arr[i]) / 255
        cfg.sequences_numeric_params[param_name]['min_color'] = ColorArray(min_color_arr)
        cfg.sequences_numeric_params[param_name]['max_color'] = ColorArray(max_color_arr)


def normalize_numeric_param(param_name):

    min_val = np.amin(cfg.sequences_numeric_params[param_name]['raw'])
    max_val = np.amax(cfg.sequences_numeric_params[param_name]['raw'])

    if min_val != max_val:
        cfg.sequences_numeric_params[param_name]['norm'] = (cfg.sequences_numeric_params[param_name]['raw'] - min_val) / \
                                                 (max_val - min_val)

    else:
        if min_val == 0:
            cfg.sequences_numeric_params[param_name]['norm'] = np.zeros(cfg.run_params['total_sequences_num'])
        else:
            cfg.sequences_numeric_params[param_name]['norm'] = np.full(cfg.run_params['total_sequences_num'], 0.5)


# Mode: full / subset
def update_positions(xyz_coor, mode):

    # Full data mode -> update 'normal' coordinates
    if mode == "full":
        cfg.sequences_array['x_coor'] = xyz_coor[0]
        cfg.sequences_array['y_coor'] = xyz_coor[1]

        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            cfg.sequences_array['z_coor'] = xyz_coor[2]

    # Subset mode -> update the subset coordinates after clustering the subset only
    else:
        cfg.sequences_array['x_coor_subset'] = xyz_coor[0]
        cfg.sequences_array['y_coor_subset'] = xyz_coor[1]

        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            cfg.sequences_array['z_coor_subset'] = xyz_coor[2]


# Subset_dict is a dictionary holding the indices of the sequences in the subset
def update_positions_subset(xyz_coor, subset_dict):
    i = 0
    for seq_index in sorted(subset_dict):
        cfg.sequences_array['x_coor_subset'][seq_index] = xyz_coor[i][0]
        cfg.sequences_array['y_coor_subset'][seq_index] = xyz_coor[i][1]
        cfg.sequences_array['z_coor_subset'][seq_index] = xyz_coor[i][2]
        i += 1


# Returns a random coordinate between -1 and 1
def generate_rand_pos():
    rand = random.random() * 2 - 1
    return rand


@numba.njit(parallel=True)
def init_positions(seq_num):
    coor_array = np.zeros((seq_num, 3))

    for i in range(seq_num):
        for j in range(3):
            coor_array[i][j] = random.random() * 2 - 1
    return coor_array[:, 0], coor_array[:, 1], coor_array[:, 2]


def rollback_subset_positions():
    for i in range(cfg.run_params['total_sequences_num']):
        cfg.sequences_array['x_coor_subset'][i] = cfg.sequences_array['x_coor'][i]
        cfg.sequences_array['y_coor_subset'][i] = cfg.sequences_array['y_coor'][i]
        cfg.sequences_array['z_coor_subset'][i] = cfg.sequences_array['z_coor'][i]



