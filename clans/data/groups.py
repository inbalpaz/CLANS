import clans.config as cfg
import numpy as np


def add_group():
    pass


def delete_group():
    pass


def edit_group():
    pass


def add_to_group(points_dict, group_index):

    # A loop over the sequences
    for seq_index in points_dict:

        # Add the sequence index to the group
        cfg.groups_list[group_index]['seqIDs'][seq_index] = 1

        # Add the group index to the sequence
        cfg.sequences_array[seq_index]['in_group'] = group_index


def remove_from_group(points_dict):

    # A loop over the sequences
    for seq_index in points_dict:

        # Find the group index that this sequence belongs to
        group_index = cfg.sequences_array[seq_index]['in_group']

        if group_index != -1 and seq_index in cfg.groups_list[group_index]['seqIDs']:

            # Remove the sequence index from the group
            del cfg.groups_list[group_index]['seqIDs'][seq_index]

            # Remove the group index from the sequence
            cfg.sequences_array[seq_index]['in_group'] = -1
