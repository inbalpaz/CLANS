import re
import csv
import os
import numpy as np
import clans.config as cfg
import clans.data.sequences as seq
import clans.data.sequence_pairs as sp


class DelimitedFormat:

    def __init__(self):
        self.sequences_list = []
        self.names_indices_dict = {}
        self.file_is_valid = 1
        self.error = ""
        self.type_of_values = "hsp"
        self.file_name = ""

    def read_file(self, file_path):

        self.file_name = os.path.basename(file_path)

        # Verify that the file exists
        if not os.path.isfile(file_path):
            self.file_is_valid = 0
            self.error = "The file \'" + file_path + "\' does not exist"
            return

        # Open and read the delimited text file
        with open(file_path) as infile:
            reader = csv.reader(infile, delimiter='\t')

            seq_index = 0
            for row in reader:

                fields_num = len(row)

                # The file is not valid - must contain at least 3 columns
                if seq_index == 0 and fields_num < 3:
                    self.file_is_valid = 0
                    self.error = "The file " + self.file_name + " is missing information:\n"
                    self.error += "The file must contain at least 3 columns: sequenceID_1, sequenceID_2, " \
                                 "similarity_score/P_value"
                    return

                # Stop if there are empty lines
                if re.search("^\s*$", row[0]):
                    break

                # The file has at least 3 columns
                id1 = row[0]
                id2 = row[1]
                score = row[2]

                # Ignore the first header row (if any)
                if seq_index == 0 and re.search("^\w+$", score):
                    continue

                # The score field is not a valid number
                if not re.search("^\d+\.?\d*[Ee]?[-+]?\d*$", score):
                    self.file_is_valid = 0
                    self.error = "The file " + self.file_name + " has an invalid format:\n"
                    self.error += "The third column must contain a float or exponential number for the " \
                                 "similarity-score or P_value"
                    return

                if fields_num > 3:
                    type_of_values = row[3]
                    if type_of_values == "score" or type_of_values == "att":
                        self.type_of_values = "att"

                # Name 1 is new
                if id1 not in self.names_indices_dict:
                    self.names_indices_dict[id1] = seq_index

                    # Create random x,y,z positions
                    pos_x = seq.generate_rand_pos()
                    pos_y = seq.generate_rand_pos()
                    pos_z = seq.generate_rand_pos()

                    sequence = ""
                    seq_length = 0
                    norm_seq_length = 0.0
                    organism = ""
                    tax_ID = ""

                    seq_tuple = (id1, id1, sequence, seq_length, norm_seq_length, organism, tax_ID, pos_x, pos_y,
                                 pos_z, False, pos_x, pos_y, pos_z)
                    self.sequences_list.append(seq_tuple)
                    cfg.sequences_ID_to_index[id1] = seq_index

                    seq_index += 1

                # Name 2 is new
                if id2 not in self.names_indices_dict:
                    self.names_indices_dict[id2] = seq_index

                    # Create random x,y,z positions
                    pos_x = seq.generate_rand_pos()
                    pos_y = seq.generate_rand_pos()
                    pos_z = seq.generate_rand_pos()

                    sequence = ""
                    seq_length = 0
                    norm_seq_length = 0.0
                    organism = ""
                    tax_ID = ""

                    seq_tuple = (id2, id2, sequence, seq_length, norm_seq_length, organism, tax_ID, pos_x, pos_y,
                                 pos_z, False, pos_x, pos_y, pos_z)
                    self.sequences_list.append(seq_tuple)
                    cfg.sequences_ID_to_index[id2] = seq_index

                    seq_index += 1

                pair_tuple = (self.names_indices_dict[id1], self.names_indices_dict[id2], score)
                cfg.similarity_values_list.append(pair_tuple)

        # Get the total number of sequences
        cfg.run_params['total_sequences_num'] = seq_index
        print("Total number of sequences: " + str(cfg.run_params['total_sequences_num']))

        # Create a 2D Numpy array for the similarity values and initialize it with 1
        cfg.similarity_values_mtx = np.full([cfg.run_params['total_sequences_num'],
                                                 cfg.run_params['total_sequences_num']], 100, dtype=float)
        cfg.attraction_values_mtx = np.zeros([cfg.run_params['total_sequences_num'],
                                                  cfg.run_params['total_sequences_num']])

        # Go over the list of pairs to fill the matrix
        for pair in cfg.similarity_values_list:
            index1 = pair[0]
            index2 = pair[1]
            score = pair[2]

            # Assign the Evalue to the pair + reciprocal pair
            # E-values (HSPs)
            if self.type_of_values == "hsp":
                if float(score) == 0.0:
                    cfg.similarity_values_mtx[index1][index2] = 10 ** -180
                    cfg.similarity_values_mtx[index2][index1] = 10 ** -180
                else:
                    cfg.similarity_values_mtx[index1][index2] = score
                    cfg.similarity_values_mtx[index2][index1] = score
            # Scores 0.0-1.0 (attraction values)
            else:
                if 0.0 <= float(score) <= 1.0:
                    cfg.attraction_values_mtx[index1][index2] = score
                    cfg.attraction_values_mtx[index2][index1] = score
                else:
                    self.file_is_valid = 0
                    self.error = "The file " + self.file_name + " has invalid format:\n"
                    self.error += "Attraction values must be numbers between 0 and 1"
                    break

        if self.file_is_valid == 0:
            print(self.error)

    def fill_values(self):
        # Create the structured NumPy array of sequences
        seq.create_sequences_array(self.sequences_list)
        seq.init_seuences_in_groups()

        # Apply the similarity cutoff
        if self.type_of_values == "hsp":
            cfg.run_params['type_of_values'] = "hsp"
            cfg.run_params['similarity_cutoff'] = cfg.similarity_cutoff
            sp.calculate_attraction_values()
            sp.define_connected_sequences('hsp')

        elif self.type_of_values == 'att':
            cfg.run_params['type_of_values'] = "att"
            # If the user forgot to set the P-value between 0-1 (to match attraction values), set it to 0.1
            if cfg.run_params['similarity_cutoff'] < 0.1:
                cfg.run_params['similarity_cutoff'] = 0.1
            sp.define_connected_sequences('att')

    def write_file(self, file_path):

        output = open(file_path, "w")

        output.write("ID_1\tID_2\tSimilarity_score\tType_of_score\n")

        for i in range(len(cfg.similarity_values_list)):
            index1 = cfg.similarity_values_list[i][0]
            index2 = cfg.similarity_values_list[i][1]
            score = cfg.similarity_values_list[i][2]

            pair_str = cfg.sequences_array[int(index1)]['seq_ID'] + "\t" + cfg.sequences_array[int(index2)]['seq_ID'] \
                       + "\t" + score + "\t" + cfg.run_params['type_of_values'] + "\n"
            output.write(pair_str)

        output.close()

    def read_metadata(self, file_path):

        param_name = ""
        error = ""
        sequences_params_dict = dict()
        params = []

        # Open and read the delimited text file
        with open(file_path) as infile:
            reader = csv.reader(infile, delimiter='\t')

            header = next(reader)
            if header is None:
                error = "The file is invalid.\nPlease upload a tab-delimited file containing at least two columns: " \
                        "sequenceID, parameter_1.\nThe file should contain a header line with the parameter names\n" \
                        "and may contain more than one parameter column."
                return param_name, error

            fields_num = len(header)

            if fields_num < 2:
                error = "The file is not valid."
                return sequences_params_dict, error

            col_num = len(header)
            for i in range(1, col_num):
                param_name = header[i]

                # Verify that there is indeed a header
                if re.search("^\d+\.?\d?$", param_name):
                    error = "It seems that the file contains no header line.\n" \
                            "Please upload a tab-delimited file containing at least two columns: " \
                            "sequenceID, parameter_1.\n" \
                            "The file should contain a header line with the parameter names\n" \
                            "and may contain more than one parameter column."
                    return sequences_params_dict, error

                params.append(param_name)
                sequences_params_dict[param_name] = dict()

            for row in reader:
                seq_ID = row[0]

                for i in range(1, col_num):
                    value = row[i]
                    sequences_params_dict[params[i-1]][seq_ID] = value

        # Verify that the provided number of sequences equals the dataset
        if len(sequences_params_dict[params[0]]) != cfg.run_params['total_sequences_num']:
            error = "The number of sequences in the metadata file does not match the number of sequences in the dataset."
            return sequences_params_dict, error

        # The file is valid, no error
        return sequences_params_dict, error






