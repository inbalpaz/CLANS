import clans.config as cfg
import numpy as np


def add_group_with_sequences(points_dict, parameters_dict):

    # Assign a unique ID to the group
    if len(cfg.groups_dict) == 0:
        group_ID = 1
    else:
        group_ID = max(cfg.groups_dict.keys()) + 1
    cfg.groups_dict[group_ID] = parameters_dict

    # Add the member-sequences indices to the group
    seq_ids_str = ""
    seq_ids_dict = dict()
    for seq_index in points_dict:
        seq_ids_str += str(seq_index) + ";"
        seq_ids_dict[seq_index] = 1

        # Add the group index to the sequence
        cfg.sequences_array[seq_index]['in_group'] = group_ID

    cfg.groups_dict[group_ID]['seqIDs'] = seq_ids_dict
    cfg.groups_dict[group_ID]['numbers'] = seq_ids_str

    return group_ID


def add_empty_group(parameters_dict):
    pass


def delete_group():
    pass


def edit_group():
    pass


def add_to_group(points_dict, group_ID):

    # A loop over the sequences
    for seq_index in points_dict:

        # Add the sequence index to the group
        cfg.groups_dict[group_ID]['seqIDs'][seq_index] = 1

        # Add the group index to the sequence
        cfg.sequences_array[seq_index]['in_group'] = group_ID


def remove_from_group(points_dict):

    # A loop over the sequences
    for seq_index in points_dict:

        # Find the group index that this sequence belongs to
        group_ID = cfg.sequences_array[seq_index]['in_group']

        if group_ID != -1 and seq_index in cfg.groups_dict[group_ID]['seqIDs']:

            # Remove the sequence index from the group
            del cfg.groups_dict[group_ID]['seqIDs'][seq_index]

            # Remove the group index from the sequence
            cfg.sequences_array[seq_index]['in_group'] = -1
