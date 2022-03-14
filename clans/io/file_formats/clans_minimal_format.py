import re
import os
import numpy as np
import clans.config as cfg
import clans.data.sequences as seq
import clans.data.sequence_pairs as sp


class ClansMinimalFormat:

    def __init__(self):
        self.sequences_list = []
        self.file_is_valid = 1
        self.error = ""
        self.type_of_values = ""
        self.file_name = ""
        self.is_groups = 0

    def read_file(self, file_path):

        in_pos_block = 0
        in_hsp_block = 0
        in_att_block = 0
        in_seqgroups_block = 0
        found_pos_block = 0
        found_hsp_block = 0
        found_att_block = 0

        self.file_name = os.path.basename(file_path)

        # Verify that the file exists
        if not os.path.isfile(file_path):
            self.file_is_valid = 0
            self.error = "The file \'" + file_path + "\' does not exist"
            return

        # Open the CLANS file
        with open(file_path) as infile:
            # Read the first line (number of sequences)
            line = infile.readline()
            m = re.search("^sequences=(\d+)", line)
            if m:
                cfg.run_params['total_sequences_num'] = int(m.group(1))
                print("Total number of sequences: " + str(cfg.run_params['total_sequences_num']))
            else:
                self.file_is_valid = 0
                self.error = "The file " + self.file_name + " has invalid minimal-clans format:\n"
                self.error += "The first line in the clans file must be: \'sequences=<number of sequences>\'"
                return

            # Create a 2D Numpy array for the similarity values and initialize it with 100
            cfg.similarity_values_mtx = np.full([cfg.run_params['total_sequences_num'],
                                                 cfg.run_params['total_sequences_num']], 100, dtype=float)
            cfg.attraction_values_mtx = np.zeros([cfg.run_params['total_sequences_num'],
                                                  cfg.run_params['total_sequences_num']])

            # A loop over the rest of the lines
            seq_index = 0
            for line in infile:

                if line.strip() == "<pos>":
                    in_pos_block = 1
                    found_pos_block = 1
                elif in_pos_block:
                    if line.strip() == "</pos>":
                        in_pos_block = 0
                    else:
                        m = re.search("^(\d+)\s+(\S+)\s+(\S+)\s+(\S+)", line.strip())
                        if m:
                            seq_id = m.group(1)
                            x_coor = m.group(2)
                            y_coor = m.group(3)
                            z_coor = m.group(4)
                            # Create a tuple with the coordinates information + initialization for the 'in_group'
                            # and 'in_subset' fields
                            sequence = ""
                            seq_length = 0
                            norm_seq_length = 0.0
                            organism = ""
                            tax_ID = ""
                            coor_tuple = (seq_id, seq_id, sequence, seq_length, norm_seq_length, organism, tax_ID,
                                          x_coor, y_coor, z_coor, False, x_coor, y_coor, z_coor)
                            self.sequences_list.append(coor_tuple)
                            cfg.sequences_ID_to_index[seq_id] = seq_index
                            seq_index += 1
                        else:
                            self.file_is_valid = 0
                            self.error = "The file " + self.file_name + " has invalid minimal-clans format:\n"
                            self.error += "The coordinates (<pos> block) cannot be read. The correct format is:\n" \
                                         "<sequence index> <coor_x> <coor_y> <coor_z>"
                            break

                elif line.strip() == "<hsp>":
                    in_hsp_block = 1
                    found_hsp_block = 1
                elif in_hsp_block == 1:
                    if line.strip() == "</hsp>":
                        in_hsp_block = 0
                    else:
                        m = re.search("^(\d+)\s+(\d+):(\S+)", line.strip())
                        if m:
                            index1 = int(m.group(1))
                            index2 = int(m.group(2))
                            evalue = m.group(3)

                            if index1 < index2:

                                # Assign the Evalue to the pair + reciprocal pair
                                if float(evalue) == 0.0:
                                    cfg.similarity_values_mtx[index1][index2] = 10 ** -180
                                    cfg.similarity_values_mtx[index2][index1] = 10 ** -180
                                else:
                                    cfg.similarity_values_mtx[index1][index2] = evalue
                                    cfg.similarity_values_mtx[index2][index1] = evalue

                                pair_tuple = (index1, index2, evalue)
                                cfg.similarity_values_list.append(pair_tuple)
                        else:
                            self.file_is_valid = 0
                            self.error = "The file " + self.file_name + " has invalid minimal-clans format:\n"
                            self.error += "The HSPs cannot be read. The correct format is:\n" \
                                         "<sequence1 index> <sequence2 index>: <E-value>"
                            break

                elif line.strip() == "<att>":
                    in_att_block = 1
                    found_att_block = 1
                elif in_att_block == 1:
                    if line.strip() == "</att>":
                        in_att_block = 0
                    else:
                        m = re.search("^(\d+)\s+(\d+)\s+(\S+)", line.strip())
                        if m:
                            index1 = int(m.group(1))
                            index2 = int(m.group(2))
                            att = m.group(3)
                            # Assign the attraction value to the pair + reciprocal pair
                            if 0.0 <= float(att) <= 1.0:
                                cfg.attraction_values_mtx[index1][index2] = att
                                cfg.attraction_values_mtx[index2][index1] = att
                            else:
                                self.file_is_valid = 0
                                self.error = "The file " + self.file_name + " has invalid minimal-clans format:\n"
                                self.error += "Attraction values must be numbers between 0 and 1"
                                break
                            pair_tuple = (index1, index2, att)
                            cfg.similarity_values_list.append(pair_tuple)
                        else:
                            self.file_is_valid = 0
                            self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
                            self.error += "The attraction values cannot be read. The correct format is:\n" \
                                         "<sequence1 index> <sequence2 index>: <attraction value>"
                            break

                elif line.strip() == "<seqgroups>":
                    in_seqgroups_block = 1
                    self.is_groups = 1
                    group_ID = 1
                    order = 0
                elif in_seqgroups_block:
                    if line.strip() == "</seqgroups>":
                        in_seqgroups_block = 0
                    else:
                        m = re.search("^(\w+)\=(.+)\n", line)
                        if m:
                            k = m.group(1)
                            v = m.group(2)
                            if k == 'name':
                                # Initialize the current group's dict
                                d = {k: v}
                            elif k == 'numbers':
                                d['seqIDs'] = {}
                                for num in (v.split(';')):
                                    if num != '':
                                        d['seqIDs'][int(num)] = 1
                                # Add the dictionary with the current group's info to the groups dictionary
                                cfg.groups_dict['input_file'][group_ID] = d.copy()
                                group_ID += 1
                                order += 1
                            elif k == 'color':
                                d[k] = v
                                color_arr = v.split(';')
                                d['color_rgb'] = color_arr[0] + "," + color_arr[1] + "," + color_arr[2] + ",255"
                                d['color_array'] = []
                                for i in range(3):
                                    d['color_array'].append(int(color_arr[i]) / 255)
                                d['color_array'].append(1.0)
                            else:
                                d[k] = v
                                d['order'] = order
                                # Add a default for the group-name size, bold and italic states
                                # (these parameters are not written in the clans file)
                                d['name_size'] = 10
                                d['is_bold'] = True
                                d['is_italic'] = False

        # Check whether there is either <hsp> block or <att>
        if self.file_is_valid:
            if found_pos_block == 0:
                self.file_is_valid = 0
                self.error = "The file " + self.file_name + " has invalid minimal-clans format:\n"
                self.error += "The minimal-clans file must contain a coordinates block (<pos>) with the positions of " \
                              "the sequences in the 3D space"
            elif found_hsp_block:
                if found_att_block:
                    self.file_is_valid = 0
                    self.error = "The file " + self.file_name + " has invalid minimal-clans format:\n"
                    self.error += "The minimal-clans file contains both <hsp> and <att> blocks. " \
                                  "Please remove one of them and load the file again"
                else:
                    self.type_of_values = "hsp"
            else:
                if found_att_block:
                    self.type_of_values = "att"
                else:
                    self.file_is_valid = 0
                    self.error = "The file " + self.file_name + " has invalid minimal-clans format:\n"
                    self.error += "The minimal-clans file must contain either HSPs (in <hsp> block) or attraction values " \
                                  "(in <att> block)"

        else:
            print(self.error)

    def fill_values(self):
        # Create the structured NumPy array of sequences
        seq.create_sequences_array(self.sequences_list)
        seq.init_seuences_in_groups()

        # If there sre groups - add the information to the sequences_list
        if self.is_groups:
            #in_groups_array = np.full(cfg.run_params['total_sequences_num'], -1)
            cfg.sequences_in_groups['input_file'] = np.full(cfg.run_params['total_sequences_num'], -1)
            for group_ID in cfg.groups_dict:
                for seq_num in cfg.groups_dict['input_file'][group_ID]['seqIDs']:
                    seq_index = int(seq_num)
                    cfg.sequences_in_groups['input_file'][seq_index] = group_ID
                    #in_groups_array[seq_index] = group_ID
            #seq.add_in_group_column(in_groups_array)

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

    def write_file(self, file_path, group_by):
        pos_block = ""

        output = open(file_path, "w")
        output.write('sequences=' + str(cfg.run_params['total_sequences_num']) + '\n')

        # Write the coordinates (<pos>) block
        for seq_index in range(cfg.run_params['total_sequences_num']):
            pos_block += cfg.sequences_array['seq_ID'][seq_index] + ' ' + str(cfg.sequences_array['x_coor'][seq_index]) \
                         + ' ' + str(cfg.sequences_array['y_coor'][seq_index]) + ' ' \
                         + str(cfg.sequences_array['z_coor'][seq_index]) + '\n'

        output.write('<pos>\n')
        output.write(pos_block)
        output.write('</pos>\n')

        # Write the HSPs (<hsp>) block
        if cfg.run_params['type_of_values'] == 'hsp':
            output.write('<hsp>\n')
            for i in range(len(cfg.similarity_values_list)):
                index1 = cfg.similarity_values_list[i][0]
                index2 = cfg.similarity_values_list[i][1]
                eval = cfg.similarity_values_list[i][2]
                pair_str = str(index1) + " " + str(index2) + ":" + str(eval) + "\n"
                output.write(pair_str)
            output.write('</hsp>')
        # Write the attraction values (<att>) block
        elif cfg.run_params['type_of_values'] == 'att':
            output.write('<att>\n')
            for i in range(len(cfg.similarity_values_list)):
                index1 = cfg.similarity_values_list[i][0]
                index2 = cfg.similarity_values_list[i][1]
                att = cfg.similarity_values_list[i][2]
                pair_str = str(index1) + " " + str(index2) + " " + str(att) + "\n"
                output.write(pair_str)
            output.write('</att>')

        output.write('\n')

        # Write the groups block
        if len(cfg.groups_dict[group_by]) > 0:
            groups_block = ""
            output.write('<seqgroups>\n')
            for group_ID in cfg.groups_dict[group_by]:
                seq_ids_str = ""
                for seq_index in cfg.groups_dict[group_by][group_ID]['seqIDs']:
                    seq_ids_str += str(seq_index) + ";"
                groups_block += 'name=' + cfg.groups_dict[group_by][group_ID]['name'] + '\n'
                groups_block += 'size=' + cfg.groups_dict[group_by][group_ID]['size'] + '\n'
                groups_block += 'color=' + cfg.groups_dict[group_by][group_ID]['color'] + '\n'
                groups_block += 'numbers=' + seq_ids_str + '\n'
            output.write(groups_block)
            output.write('</seqgroups>\n')

        output.close()
