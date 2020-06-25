import numpy as np
import clans.config as cfg


#@profile
def create_sequences_array(sequences_list):
    # Insert the sequences to a NumPy structured array with the following fields: seq_title, sequence, x_coordinate, y_coordinate, z_cordinate
    dt = np.dtype([('seq_title', 'U100'), ('sequence', 'U1000'), ('x_coor', 'float32'), ('y_coor', 'float32'), ('z_coor', 'float32')])
    cfg.sequences_array = np.array(sequences_list, dtype=dt)
    #print("create_sequences_array: Sequences_array=\n" + str(cfg.sequences_array))


#@profile
def update_positions(xyz_coor):
    cfg.sequences_array['x_coor'] = xyz_coor[0]
    cfg.sequences_array['y_coor'] = xyz_coor[1]
    cfg.sequences_array['z_coor'] = xyz_coor[2]



