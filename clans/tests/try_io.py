import random
import clans.config as cfg


def create_artificial_metadata_file_with_seq_name(file_name):

    dir_path = "clans/input_example/metadata/numerical_features/"
    file_path = dir_path + file_name + "_numeric_params_by_seq_name.txt"

    output = open(file_path, "w")

    output.write("Sequence_ID\tParam_1\tParam2\n")

    for seq_index in range(cfg.run_params['total_sequences_num']):
        param1 = generate_rand_int(1000)
        param2 = generate_rand_float()
        seq_id = cfg.sequences_array['seq_ID'][seq_index]
        line = seq_id + "\t" + str(param1) + "\t" + str(param2) + "\n"
        output.write(line)

    output.close()


def create_artificial_metadata_file_with_seq_index(file_name):

    dir_path = "clans/input_example/metadata/numerical_features/"
    file_path = dir_path + file_name + "_numeric_params_by_seq_index.txt"

    output = open(file_path, "w")

    output.write("Sequence_ID\tParam_3\tParam4\n")

    for seq_index in range(cfg.run_params['total_sequences_num']):
        param1 = generate_rand_int(1000)
        param2 = generate_rand_float()
        line = str(seq_index) + "\t" + str(param1) + "\t" + str(param2) + "\n"
        output.write(line)

    output.close()


def create_artificial_metadata_groups_file_with_seq_name(file_name):

    dir_path = "clans/input_example/metadata/groups/"
    file_path = dir_path + file_name + "groups_by_seq_name.txt"

    output = open(file_path, "w")

    output.write("Sequence_ID\tCategory_1\n")

    groups = ['group1', 'group2', 'group3', 'group4', 'group5', 'group6', 'group7']
    for seq_index in range(cfg.run_params['total_sequences_num']):

        group_index = generate_rand_int(7)
        seq_id = cfg.sequences_array['seq_ID'][seq_index]
        line = seq_id + "\t" + groups[group_index] + "\n"
        output.write(line)

    output.close()


def create_artificial_metadata_groups_file_with_seq_index(file_name):

    dir_path = "clans/input_example/metadata/groups/"
    file_path = dir_path + file_name + "groups_by_seq_index.txt"

    output = open(file_path, "w")

    output.write("Sequence_ID\tCategory_2\n")

    groups = ['group1', 'group2', 'group3', 'group4', 'group5', 'group6', 'group7', 'group8']
    for seq_index in range(cfg.run_params['total_sequences_num']):

        group_index = generate_rand_int(8)
        line = str(seq_index) + "\t" + groups[group_index] + "\n"
        output.write(line)

    output.close()


def generate_rand_int(n):
    rand = random.randrange(n)
    return rand


def generate_rand_float():
    rand = random.random()
    return rand

