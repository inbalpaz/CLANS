import re
import os
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
        self.is_seq_params = 0
        self.file_name = ""
        self.params = dict()
        self.params_dict = dict()

    def read_file(self, file_path):

        in_param_block = 0
        in_seq_block = 0
        in_seqgroups_block = 0
        in_seqparams_block = 0
        in_pos_block = 0
        in_hsp_block = 0
        in_att_block = 0
        found_seq_block = 0
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
                self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
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
                if line.strip() == "<param>":
                    in_param_block = 1
                elif in_param_block:
                    if line.strip() == "</param>":
                        in_param_block = 0
                    else:
                        m = re.search("^(\w+)\=(.+)\n", line)
                        if m:
                            k = m.group(1)
                            v = m.group(2)
                            self.params[k] = v

                elif line.strip() == "<seq>":
                    in_seq_block = 1
                    found_seq_block = 1
                elif in_seq_block:
                    if line.strip() == "</seq>":
                        in_seq_block = 0
                    else:
                        m = re.search("^>(.+)", line)
                        if m:
                            title = m.group(1)
                            title.strip()

                            # Extract the sequence_ID from the title (trim it at space character)
                            n = re.search("^(\S+)", title)
                            seq_id = n.group(1)
                        else:
                            sequence = line.strip()
                            seq_length = 0
                            norm_seq_length = 0.0
                            organism = ""
                            tax_ID = ""
                            t = (seq_id, title, sequence, seq_length, norm_seq_length, organism, tax_ID)
                            self.sequences_list.append(t)
                            cfg.sequences_ID_to_index[seq_id] = seq_index
                            seq_index += 1

                elif line.strip() == "<seqgroups>":
                    in_seqgroups_block = 1
                    self.is_groups = 1
                    group_ID = 1
                    order = 0
                    category_name = "input_file"
                elif in_seqgroups_block:
                    if line.strip() == "</seqgroups>":
                        in_seqgroups_block = 0
                    else:
                        m = re.search("^(\w+)\=(.+)\n", line)
                        if m:
                            k = m.group(1)
                            v = m.group(2)

                            # Format is full-clans - expect category names
                            if k == 'category':
                                category_name = v
                                if category_name == 'manual':
                                    category_name = 'manual_file'
                                cfg.groups_dict[category_name] = dict()
                                group_ID = 1
                                order = 0

                            elif k == 'name':
                                # Initialize the current group's dict
                                d = {k: v}

                            elif k == 'numbers':
                                d['seqIDs'] = {}
                                for num in (v.split(';')):
                                    if num != '':
                                        d['seqIDs'][int(num)] = 1

                                d['order'] = order

                                # Add a default for the group-name size, bold and italic states
                                # (in case they are not written in the clans file)
                                if 'name_size' not in d:
                                    d['name_size'] = 10
                                if 'is_bold' not in d:
                                    d['is_bold'] = True
                                if 'is_italic' not in d:
                                    d['is_italic'] = False
                                if 'outline_color' not in d:
                                    d['outline_color'] = [0.0, 0.0, 0.0, 1.0]

                                # Add the dictionary with the current group's info to the groups dictionary
                                cfg.groups_dict[category_name][group_ID] = d.copy()
                                group_ID += 1
                                order += 1

                            elif k == 'color':
                                d[k] = v
                                color_arr = v.split(';')
                                d['color_array'] = []
                                for i in range(4):
                                    d['color_array'].append(int(color_arr[i]) / 255)

                            elif k == 'outline_color':
                                d['outline_color'] = [int(c) / 255 for c in v.split(';')]

                            else:
                                d[k] = v

                elif line.strip() == "<seqparams>":
                    in_seqparams_block = 1
                    self.is_seq_params = 1
                elif in_seqparams_block:
                    if line.strip() == "</seqparams>":
                        in_seqparams_block = 0
                    else:
                        m = re.search("^(\w+)\=(.+)\n", line)
                        if m:
                            k = m.group(1)
                            v = m.group(2)

                            # Format is full-clans - expect category names
                            if k == 'param':
                                param_name = v
                                self.params_dict[param_name] = dict()

                            elif k == 'values':
                                values_list = v.split()
                                self.params_dict[param_name][k] = values_list

                            else:
                                self.params_dict[param_name][k] = v

                elif line.strip() == "<pos>":
                    in_pos_block = 1
                    found_pos_block = 1
                elif in_pos_block:
                    if line.strip() == "</pos>":
                        in_pos_block = 0
                    else:

                        # If there was no <seq> lock, probably it's the minimal-clans format -> print an error
                        if found_seq_block == 0:
                            self.file_is_valid = 0
                            self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
                            self.error += "The full CLANS format must contain a sequences block (<seq>)\n" \
                                          "including the original sequences in FASTA format\n" \
                                          "Alternatively, load a file in 'minimal-clans' format"
                            break

                        m = re.search("^(\d+)\s+(\S+)\s+(\S+)\s+(\S+)", line.strip())
                        if m:
                            index = int(m.group(1))
                            x_coor = m.group(2)
                            y_coor = m.group(3)
                            z_coor = m.group(4)
                            # Create a tuple with the coordinates information + initialization for the 'in_group'
                            # and 'in_subset' fields
                            coor_tuple = (x_coor, y_coor, z_coor, False, x_coor, y_coor, z_coor)
                            self.sequences_list[index] += coor_tuple
                        else:
                            self.file_is_valid = 0
                            self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
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
                            self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
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
                                self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
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

        # Check whether there is either <hsp> block or <att>
        if self.file_is_valid:
            if found_seq_block == 0:
                self.file_is_valid = 0
                self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
                self.error += "It must contain a sequences block (<seq>) " \
                              "containing the original sequences in FASTA format"
            elif found_pos_block == 0:
                self.file_is_valid = 0
                self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
                self.error += "The clans file must contain a coordinates block (<pos>) with the positions of the " \
                             "sequences in the 3D space"
            elif found_hsp_block:
                if found_att_block:
                    self.file_is_valid = 0
                    self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
                    self.error += "The clans file contains both <hsp> and <att> blocks. " \
                                 "Please remove one of them and load the file again"
                else:
                    self.type_of_values = "hsp"
            else:
                if found_att_block:
                    self.type_of_values = "att"
                else:
                    self.file_is_valid = 0
                    self.error = "The file " + self.file_name + " has invalid CLANS format:\n"
                    self.error += "The clans file must contain either HSPs (in <hsp> block) or attraction values " \
                                 "(in <att> block)"

        else:
            print(self.error)

    def fill_values(self):
        # Create the structured NumPy array of sequences
        seq.create_sequences_array(self.sequences_list)
        seq.init_seuences_in_groups()

        # If there sre groups - add the information to the sequences array
        if self.is_groups:
            for category in cfg.groups_dict:
                # A category filled with groups
                if len(cfg.groups_dict[category]) > 0:
                    cfg.sequences_in_groups[category] = np.full(cfg.run_params['total_sequences_num'], -1)
                    for group_ID in cfg.groups_dict[category]:
                        for seq_num in cfg.groups_dict[category][group_ID]['seqIDs']:
                            seq_index = int(seq_num)
                            cfg.sequences_in_groups[category][seq_index] = group_ID

        # calculate the sequence_length column
        seq.add_seq_length_param()

        # If there is saved metadata - add the information to the main dict
        if self.is_seq_params:
            seq.add_saved_numeric_params(self.params_dict)

        # If parameters were defined in the file - save them in the 'run_params' dict
        if 'rounds_done' in self.params:
            cfg.run_params['num_of_rounds'] = int(self.params['rounds_done'])
        if 'cluster2d' in self.params:
            if self.params['cluster2d'] == 'true':
                cfg.run_params['dimensions_num_for_clustering'] = 2
                print("dim num of clustering: " + str(cfg.run_params['dimensions_num_for_clustering']))
            else:
                cfg.run_params['dimensions_num_for_clustering'] = 3
        if 'pval' in self.params:
            cfg.run_params['similarity_cutoff'] = float(self.params['pval'])
        if 'attfactor' in self.params:
            cfg.run_params['att_val'] = float(self.params['attfactor'])
        if 'attvalpow' in self.params:
            cfg.run_params['att_exp'] = int(self.params['attvalpow'])
        if 'repfactor' in self.params:
            cfg.run_params['rep_val'] = float(self.params['repfactor'])
        if 'repvalpow' in self.params:
            cfg.run_params['rep_exp'] = int(self.params['repvalpow'])
        if 'cooling' in self.params:
            cfg.run_params['cooling'] = float(self.params['cooling'])
        if 'currcool' in self.params:
            cfg.run_params['current_temp'] = float(self.params['currcool'])
        if 'dampening' in self.params:
            cfg.run_params['dampening'] = float(self.params['dampening'])
        if 'maxmove' in self.params:
            cfg.run_params['maxmove'] = float(self.params['maxmove'])
        if 'minattract' in self.params:
            cfg.run_params['gravity'] = float(self.params['minattract'])

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

    # Prints the session into a CLANS-formatted file, which is compatible with the java program
    def write_file(self, file_path, is_param, group_by):
        seq_block = ""
        pos_block = ""

        output = open(file_path, "w")
        output.write('sequences=' + str(cfg.run_params['total_sequences_num']) + '\n')

        # Write the parameters block
        if is_param:
            output.write('<param>\n')
            output.write('rounds_done='+str(cfg.run_params['rounds_done'])+'\n')
            if cfg.run_params['dimensions_num_for_clustering'] == 2:
                output.write('cluster2d=true\n')
            else:
                output.write('cluster2d=false\n')
            output.write('pval=' + str(cfg.run_params['similarity_cutoff']) + '\n')
            output.write('attfactor=' + str(cfg.run_params['att_val']) + '\n')
            output.write('attvalpow=' + str(cfg.run_params['att_exp']) + '\n')
            output.write('repfactor=' + str(cfg.run_params['rep_val']) + '\n')
            output.write('repvalpow=' + str(cfg.run_params['rep_exp']) + '\n')
            output.write('cooling=' + str(cfg.run_params['cooling']) + '\n')
            if 'current_temp' in cfg.run_params and cfg.run_params['cooling'] < 1:
                output.write('currcool=' + str(cfg.run_params['current_temp']) + '\n')
            output.write('dampening=' + str(cfg.run_params['dampening']) + '\n')
            output.write('maxmove=' + str(cfg.run_params['maxmove']) + '\n')
            output.write('minattract=' + str(cfg.run_params['gravity']) + '\n')
            output.write('</param>\n')

        # Write the sequences block
        for seq in range(cfg.run_params['total_sequences_num']):
            seq_block += '>' + cfg.sequences_array['seq_title'][seq] + '\n' + cfg.sequences_array['sequence'][seq] + '\n'
            pos_block += str(seq) + ' ' + str(cfg.sequences_array['x_coor'][seq]) + ' ' + \
                         str(cfg.sequences_array['y_coor'][seq]) + ' ' + str(cfg.sequences_array['z_coor'][seq]) + '\n'

        output.write('<seq>\n')
        output.write(seq_block)
        output.write('</seq>\n')

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

        output.close()

    # Print the session, including sequences information, metadata and running parameters into a file in CLANS format
    def write_full_file(self, file_path):
        seq_block = ""
        pos_block = ""

        output = open(file_path, "w")
        output.write('sequences=' + str(cfg.run_params['total_sequences_num']) + '\n')

        # Write the parameters block
        output.write('<param>\n')
        output.write('rounds_done=' + str(cfg.run_params['rounds_done']) + '\n')
        if cfg.run_params['dimensions_num_for_clustering'] == 2:
            output.write('cluster2d=true\n')
        else:
            output.write('cluster2d=false\n')
        output.write('pval=' + str(cfg.run_params['similarity_cutoff']) + '\n')
        output.write('attfactor=' + str(cfg.run_params['att_val']) + '\n')
        output.write('attvalpow=' + str(cfg.run_params['att_exp']) + '\n')
        output.write('repfactor=' + str(cfg.run_params['rep_val']) + '\n')
        output.write('repvalpow=' + str(cfg.run_params['rep_exp']) + '\n')
        output.write('cooling=' + str(cfg.run_params['cooling']) + '\n')
        if 'current_temp' in cfg.run_params and cfg.run_params['cooling'] < 1:
            output.write('currcool=' + str(cfg.run_params['current_temp']) + '\n')
        output.write('dampening=' + str(cfg.run_params['dampening']) + '\n')
        output.write('maxmove=' + str(cfg.run_params['maxmove']) + '\n')
        output.write('minattract=' + str(cfg.run_params['gravity']) + '\n')
        output.write('</param>\n')

        # Write the sequences block
        for seq in range(cfg.run_params['total_sequences_num']):
            seq_block += '>' + cfg.sequences_array['seq_title'][seq] + '\n' + cfg.sequences_array['sequence'][
                seq] + '\n'
            pos_block += str(seq) + ' ' + str(cfg.sequences_array['x_coor'][seq]) + ' ' + \
                         str(cfg.sequences_array['y_coor'][seq]) + ' ' + str(cfg.sequences_array['z_coor'][seq]) + '\n'

        output.write('<seq>\n')
        output.write(seq_block)
        output.write('</seq>\n')

        # Write the groups block: write the groups for each category, including new parameters
        if len(cfg.groups_dict) > 2 or len(cfg.groups_dict['input_file']) > 0 or len(cfg.groups_dict['manual']) > 0:
            output.write('<seqgroups>\n')

            # A loop over the grouping categories
            for category in cfg.groups_dict:

                if len(cfg.groups_dict[category]) > 0:
                    groups_block = ""
                    category_str = "category=" + category + "\n"
                    output.write(category_str)

                    ordered_groups = sorted(cfg.groups_dict[category].keys(),
                                            key=lambda k: cfg.groups_dict[category][k]['order'])

                    # a loop over the groups
                    for group_ID in ordered_groups:

                        seq_ids_str = ""
                        for seq_index in cfg.groups_dict[category][group_ID]['seqIDs']:
                            seq_ids_str += str(seq_index) + ";"

                        outline_color = ';'.join([str(int(c * 255)) for c in cfg.groups_dict[category][group_ID]['outline_color']])

                        groups_block += 'name=' + cfg.groups_dict[category][group_ID]['name'] + '\n'
                        groups_block += 'size=' + str(cfg.groups_dict[category][group_ID]['size']) + '\n'
                        groups_block += 'name_size=' + str(cfg.groups_dict[category][group_ID]['name_size']) + '\n'
                        groups_block += 'color=' + cfg.groups_dict[category][group_ID]['color'] + '\n'
                        groups_block += 'outline_color=' + outline_color + '\n'
                        groups_block += 'is_bold=' + str(cfg.groups_dict[category][group_ID]['is_bold']) + '\n'
                        groups_block += 'is_italic=' + str(cfg.groups_dict[category][group_ID]['is_italic']) + '\n'
                        groups_block += 'numbers=' + seq_ids_str + '\n'

                    output.write(groups_block)

            output.write('</seqgroups>\n')

        # Write the numeric parameters block, including the color-range
        if len(cfg.sequences_numeric_params) > 0:
            output.write('<seqparams>\n')

            for param in cfg.sequences_numeric_params:

                param_str = "param=" + param + "\n"

                min_color = ";".join([str(c) for c in cfg.sequences_numeric_params[param]['min_color'].RGBA[0].tolist()])
                max_color = ";".join([str(c) for c in cfg.sequences_numeric_params[param]['max_color'].RGBA[0].tolist()])
                values = " ".join([str(c) for c in cfg.sequences_numeric_params[param]['raw'].tolist()])

                param_str += "min_color=" + min_color + "\n"
                param_str += "max_color=" + max_color + "\n"
                param_str += "values=" + values + "\n"

                output.write(param_str)

            output.write('</seqparams>\n')

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

        output.close()

