import clans.config as cfg


def add_group_with_sequences(group_by, points_dict, parameters_dict):

    # Assign a unique ID to the group
    if len(cfg.groups_dict[group_by]) == 0:
        group_ID = 1
    else:
        group_ID = max(cfg.groups_dict[group_by].keys()) + 1
    cfg.groups_dict[group_by][group_ID] = parameters_dict

    # Add the member-sequences indices to the group and remove them from their previous group (if any)
    for seq_index in points_dict:

        # The sequence was a member of another group - delete it from the old group
        if cfg.sequences_in_groups[group_by][seq_index] != -1:
            old_group_ID = cfg.sequences_in_groups[group_by][seq_index]
            if seq_index in cfg.groups_dict[group_by][old_group_ID]['seqIDs']:
                del cfg.groups_dict[group_by][old_group_ID]['seqIDs'][seq_index]

        # Add the new group index to the sequence
        cfg.sequences_in_groups[group_by][seq_index] = group_ID

    cfg.groups_dict[group_by][group_ID]['seqIDs'] = points_dict

    return group_ID


def delete_group(group_by, group_ID):

    # create a list of group_IDs, sorted according to the order
    group_IDs_list = sorted(cfg.groups_dict[group_by].keys(), key=lambda k: cfg.groups_dict[group_by][k]['order'])

    current_order = int(cfg.groups_dict[group_by][group_ID]['order'])

    # Assign new order to all the groups with order higher than the deleted group
    for i in range(current_order+1, len(group_IDs_list)):
        group_index = group_IDs_list[i]
        cfg.groups_dict[group_by][group_index]['order'] -= 1

    # Delete the requested group from the main groups dictionary
    if group_ID in cfg.groups_dict[group_by]:
        del cfg.groups_dict[group_by][group_ID]


def edit_group(group_by, group_ID, points_dict, parameters_dict):
    cfg.groups_dict[group_by][group_ID] = parameters_dict
    cfg.groups_dict[group_by][group_ID]['seqIDs'] = points_dict


def add_to_group(group_by, points_dict, group_ID):

    # A loop over the sequences
    for seq_index in points_dict:

        # Add the sequence index to the group
        cfg.groups_dict[group_by][group_ID]['seqIDs'][seq_index] = 1

        # Add the group index to the sequence
        cfg.sequences_in_groups[group_by][seq_index] = group_ID


def remove_from_group(group_by, points_dict):

    groups_with_deleted_members = {}

    # A loop over the sequences
    for seq_index in points_dict:

        # Find the group index that this sequence belongs to
        group_ID = cfg.sequences_in_groups[group_by][seq_index]

        if group_ID != -1 and seq_index in cfg.groups_dict[group_by][group_ID]['seqIDs']:

            # Remove the sequence index from the group
            del cfg.groups_dict[group_by][group_ID]['seqIDs'][seq_index]

            # Remove the group index from the sequence
            cfg.sequences_in_groups[group_by][seq_index] = -1

            # Add the groupID to a dict of groups, that at least one member was deleted from
            # (to be later checked if they are empty)
            if group_ID not in groups_with_deleted_members:
                groups_with_deleted_members[group_ID] = 1

    return groups_with_deleted_members.copy()
