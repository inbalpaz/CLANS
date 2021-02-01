import re
import numpy as np
import clans.config as cfg
import clans.data.sequences as seq
import clans.data.sequence_pairs as sp


class ClansFormat:

    def __init__(self):
        self.sequences_list = []
        self.file_is_valid = 1
        self.error = ""
        self.type_of_values = ""
        self.is_groups = 0

    def read_file(self, file_path):

        in_seq_block = 0
        in_seqgroups_block = 0
        in_pos_block = 0
        in_hsp_block = 0
        in_att_block = 0
        found_seq_block = 0
        found_pos_block = 0
        found_hsp_block = 0
        found_att_block = 0

        # Open the CLANS file
        with open(file_path) as infile:
            # Read the first line (number of sequences)
            line = infile.readline()
            m = re.search("^sequences=(\d+)", line)
            if m:
                cfg.run_params['total_sequences_num'] = int(m.group(1))
                print("ClansFormat.read_file: Total number of sequences: " + str(cfg.run_params['total_sequences_num']))
            else:
                self.file_is_valid = 0
                self.error = "The first line in the clans file must be: \'sequences=<number of sequences>\'"
                return

            # Create a 2D Numpy array for the similarity values and initialize it with 1
            cfg.similarity_values_mtx = np.full([cfg.run_params['total_sequences_num'],
                                                  cfg.run_params['total_sequences_num']], 100, dtype=float)
            cfg.attraction_values_mtx = np.zeros([cfg.run_params['total_sequences_num'],
                                                   cfg.run_params['total_sequences_num']])

            # A loop over the rest of the lines
            for line in infile:
                if line.strip() == "<seq>":
                    in_seq_block = 1
                    found_seq_block = 1
                elif in_seq_block:
                    if line.strip() == "</seq>":
                        in_seq_block = 0
                    else:
                        if re.search("^>.+", line):
                            title = line.strip()
                        else:
                            sequence = line.strip()
                            t = (title, sequence)
                            self.sequences_list.append(t)
                elif line.strip() == "<seqgroups>":
                    in_seqgroups_block = 1
                    self.is_groups = 1
                elif in_seqgroups_block:
                    if line.strip() == "</seqgroups>":
                        in_seqgroups_block = 0
                    else:
                        m = re.search("^(\w+)\=(\S+)", line)
                        if m:
                            k = m.group(1)
                            v = m.group(2)
                            if k == 'name':
                                # Initialize the current group's dict
                                d = {k: v}
                            elif k == 'numbers':
                                d[k] = v
                                d['seqIDs'] = {}
                                for num in (v.split(';')):
                                    if num != '':
                                       d['seqIDs'][num] = 1
                                # Add the dictionary with the current group's info to the main groups list
                                cfg.groups_list.append(d.copy())
                            else:
                                d[k] = v
                elif line.strip() == "<pos>":
                    in_pos_block = 1
                    found_pos_block = 1
                elif in_pos_block:
                    if line.strip() == "</pos>":
                        in_pos_block = 0
                    else:
                        m = re.search("^(\d+)\s+(\S+)\s+(\S+)\s+(\S+)", line.strip())
                        if m:
                            index = int(m.group(1))
                            x_coor = m.group(2)
                            y_coor = m.group(3)
                            z_coor = m.group(4)
                            # Create a tuple with the coordinates information + initialization for the 'in_group field'
                            coor_tuple = (x_coor, y_coor, z_coor, -1)
                            self.sequences_list[index] += coor_tuple
                        else:
                            self.file_is_valid = 0
                            self.error = "The coordinates (<pos> block) cannot be read. The correct format is:\n" \
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
                            # Assign the Evalue to the pair + reciprocal pair
                            if float(evalue) == 0.0:
                                cfg.similarity_values_mtx[index1][index2] = 10 ** -180
                                cfg.similarity_values_mtx[index2][index1] = 10 ** -180
                            else:
                                cfg.similarity_values_mtx[index1][index2] = evalue
                                cfg.similarity_values_mtx[index2][index1] = evalue
                            cfg.similarity_values_list.append(line)
                        else:
                            self.file_is_valid = 0
                            self.error = "The HSPs cannot be read. The correct format is:\n" \
                                         "<sequence1 index> <sequence2 index>: <E-value>"
                            break
                elif line.strip() == "<att>":
                    in_att_block = 1
                    found_att_block = 1
                elif in_att_block == 1:
                    if line.strip() == "</att>":
                        in_att_block = 0
                    else:
                        m = re.search("^(\d+)\s+(\d+)\s(\S+)", line.strip())
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
                                self.error = "Attraction values must be numbers between 0 and 1"
                                break
                            cfg.attraction_values_list.append(line)
                        else:
                            self.file_is_valid = 0
                            self.error = "The attraction values cannot be read. The correct format is:\n" \
                                         "<sequence1 index> <sequence2 index>: <attraction value>"
                            break

        # Check whether there is either <hsp> block or <att>
        if self.file_is_valid:
            if found_seq_block == 0:
                self.file_is_valid = 0
                self.error = "The clans file must contain a sequences block - the original sequences in FASTA format"
            elif found_pos_block == 0:
                self.file_is_valid = 0
                self.error = "The clans file must contain a coordinates block (<pos>) with the positions of the " \
                             "sequences in the 3D space."
            elif found_hsp_block:
                if found_att_block:
                    self.file_is_valid = 0
                    self.error = "The clans file contains both <hsp> and <att> blocks. " \
                                 "Please remove one of them and load the file again"
                else:
                    self.type_of_values = "hsp"
            else:
                if found_att_block:
                    self.type_of_values = "att"
                else:
                    self.file_is_valid = 0
                    self.error = "The clans file must contains either HSPs (in <hsp> block) or attraction values " \
                                 "(in <att> block)"

    def fill_values(self):
        # Create the structured NumPy array of sequences
        seq.create_sequences_array(self.sequences_list)

        # If there sre groups - add the information to the sequences_list
        if self.is_groups:
            in_groups_array = np.full(cfg.run_params['total_sequences_num'], -1)
            for group_index in range(len(cfg.groups_list)):
                if cfg.groups_list[group_index]['color'] != "0;0;0;255":
                    for seq_num in cfg.groups_list[group_index]['seqIDs']:
                        seq_index = int(seq_num)
                        in_groups_array[seq_index] = group_index
            seq.add_in_group_column(in_groups_array)

        if self.type_of_values == "hsp":
            cfg.type_of_values = "hsp"
            sp.calculate_attraction_values()
            sp.define_connected_sequences('hsp')
        elif self.type_of_values == 'att':
            cfg.type_of_values = "att"
            # If the user forgot to set the P-value between 0-1 (to match attraction values), set it to 0.1
            if cfg.run_params['similarity_cutoff'] < 0.1:
                cfg.run_params['similarity_cutoff'] = 0.1
            sp.define_connected_sequences('att')

    def write_file(self, file_path):
        seq_block = ""
        pos_block = ""

        output = open(file_path, "w")
        output.write('sequences=' + str(cfg.run_params['total_sequences_num']) + '\n')

        for seq in range(cfg.run_params['total_sequences_num']):
            seq_block += cfg.sequences_array['seq_title'][seq] + '\n' + cfg.sequences_array['sequence'][seq] + '\n'
            pos_block += str(seq) + ' ' + str(cfg.sequences_array['x_coor'][seq]) + ' ' + \
                         str(cfg.sequences_array['y_coor'][seq]) + ' ' + str(cfg.sequences_array['z_coor'][seq]) + '\n'

        output.write('<seq>\n')
        output.write(seq_block)
        output.write('</seq>\n')

        if cfg.groups_list:
            groups_block = ""
            output.write('<seqgroups>\n')
            for i in range(len(cfg.groups_list)):
                groups_block += 'name=' + cfg.groups_list[i]['name'] + '\n'
                groups_block += 'type=' + cfg.groups_list[i]['type'] + '\n'
                groups_block += 'size=' + cfg.groups_list[i]['size'] + '\n'
                groups_block += 'hide=' + cfg.groups_list[i]['hide'] + '\n'
                groups_block += 'color=' + cfg.groups_list[i]['color'] + '\n'
                groups_block += 'numbers=' + cfg.groups_list[i]['numbers'] + '\n'
            output.write(groups_block)
            output.write('</seqgroups>\n')

        output.write('<pos>\n')
        output.write(pos_block)
        output.write('</pos>\n')

        # Write the HSPs (<hsp>) block
        if cfg.type_of_values == 'hsp':
            output.write('<hsp>\n')
            for i in range(len(cfg.similarity_values_list)):
                output.write(cfg.similarity_values_list[i])
            output.write('</hsp>')
        # Write the attraction values (<att>) block
        elif cfg.type_of_values == 'att':
            output.write('<att>\n')
            for i in range(len(cfg.attraction_values_list)):
                output.write(cfg.attraction_values_list[i])
            output.write('</att>')

        output.close()
