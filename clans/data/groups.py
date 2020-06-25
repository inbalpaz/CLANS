import clans.config as cfg
import numpy as np


def create_groups_array(groups_list):
    # Insert the groups to a NumPy structured array with the following fields: 'name', 'shape_type', 'size', 'hide', 'color', 'seqIDs'
    dt = np.dtype([('name', 'U100'), ('shape_type', 'uint8'), ('size', 'uint8'), ('hide', 'bool'), ('color', 'U15'),
                   ('seqIDs', 'U1000')])
    cfg.groups_array = np.array(groups_list, dtype=dt)
    #print("groups_array=\n" + str(cfg.groups_array))


def add_group(self):
    pass


def delete_group(self):
    pass


def edit_group(self, group_name):
    pass
