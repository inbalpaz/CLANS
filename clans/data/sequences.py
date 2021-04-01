import numpy as np
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
def update_positions(xyz_coor):
    cfg.sequences_array['x_coor'] = xyz_coor[0]
    cfg.sequences_array['y_coor'] = xyz_coor[1]

    if cfg.run_params['dimensions_num_for_clustering'] == 3:
        cfg.sequences_array['z_coor'] = xyz_coor[2]
    #else:
        #cfg.sequences_array['z_coor'] = 0


# Returns a random coordinate between -1 and 1
def generate_rand_pos():
    rand = random.random() * 2 - 1
    return rand


def init_positions():
    for i in range(cfg.run_params['total_sequences_num']):
        cfg.sequences_array['x_coor'][i] = generate_rand_pos()
        cfg.sequences_array['y_coor'][i] = generate_rand_pos()

        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            cfg.sequences_array['z_coor'][i] = generate_rand_pos()



