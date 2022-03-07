import random
import clans.config as cfg


def create_artificial_metadata_file_with_seq_name(file_name):

    dir_path = "/Users/ipaz/ownCloud/Documents/CLANS-Python/input_files/meta_data/"
    file_path = dir_path + file_name + "_metadata.txt"

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

    dir_path = "/Users/ipaz/ownCloud/Documents/CLANS-Python/input_files/meta_data/"
    file_path = dir_path + file_name + "_metadata.txt"

    output = open(file_path, "w")

    output.write("Sequence_ID\tParam_1\tParam2\n")

    for seq_index in range(cfg.run_params['total_sequences_num']):
        param1 = generate_rand_int(1000)
        param2 = generate_rand_float()
        line = str(seq_index) + "\t" + str(param1) + "\t" + str(param2) + "\n"
        output.write(line)

    output.close()


def generate_rand_int(n):
    rand = random.randrange(n)
    return rand


def generate_rand_float():
    rand = random.random()
    return rand

