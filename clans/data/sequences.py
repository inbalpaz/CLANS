import numpy as np
import numba
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


def add_in_group_column(in_group_array):
    # Fill the 'in_group' field for each sequence - to which group it belongs (group index)
    # In case there is no group assignment - fill -1
    cfg.sequences_array['in_group'] = in_group_array
    #print("add_in_group_column: Sequences_array=\n" + str(cfg.sequences_array))


#@profile
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



