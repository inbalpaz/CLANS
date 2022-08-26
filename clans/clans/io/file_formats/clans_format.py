import re
import os
import numpy as np
import clans.config as cfg
import clans.clans.data.sequences as seq
import clans.clans.data.sequence_pairs as sp


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
        in_tax_block = 0
        in_pos_block = 0
        in_hsp_block = 0
        in_att_block = 0
        found_seq_block = 0
        found_pos_block = 0
        found_hsp_block = 0
        found_att_block = 0
        level = ""

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

                            # Use the whole header as the sequence_ID
                            seq_id = title

                            # Extract the sequence_ID from the title (trim it at space character)
                            #n = re.search("^(\S+)", title)
                            #seq_id = n.group(1)
                        else:
                            sequence = line.strip()
                            seq_length = 0
                            norm_seq_length = 0.0
                            organism = ""
                            tax_ID = ""
                            t = (seq_id, sequence, seq_length, norm_seq_length, organism, tax_ID)
                            self.sequences_list.append(t)
                            cfg.sequences_ID_to_index[seq_id] = seq_index
                            seq_index += 1

                elif line.strip() == "<seqgroups>":
                    in_seqgroups_block = 1
                    self.is_groups = 1
                    category_index = 0
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

                            # Format is full-clans - expect category names
                            if k == 'category':
                                level = 'category'
                                category_name = v
                                category_index += 1
                                if category_name == 'Manual definition' or category_name == 'manual':
                                    category_name = 'Manual - from file'
                                cfg.groups_by_categories.append({'name': category_name, 'groups': dict()})
                                group_ID = 1
                                order = 0

                            elif k == 'nodes_size':
                                cfg.groups_by_categories[category_index]['nodes_size'] = int(v)

                            elif k == 'text_size':
                                cfg.groups_by_categories[category_index]['text_size'] = int(v)

                            elif k == 'nodes_outline_width':
                                cfg.groups_by_categories[category_index]['nodes_outline_width'] = float(v)

                            elif k == 'nodes_outline_color':
                                cfg.groups_by_categories[category_index]['nodes_outline_color'] = \
                                    [int(c) / 255 for c in v.split(';')]

                            elif k == 'is_bold' and level == 'category':
                                if v == 'True':
                                    cfg.groups_by_categories[category_index]['is_bold'] = True
                                else:
                                    cfg.groups_by_categories[category_index]['is_bold'] = False

                            elif k == 'is_italic' and level == 'category':
                                if v == 'True':
                                    cfg.groups_by_categories[category_index]['is_italic'] = True
                                else:
                                    cfg.groups_by_categories[category_index]['is_italic'] = False

                            elif k == 'name':
                                level = 'group'
                                # Initialize the current group's dict
                                d = {k: v}

                                # In case the file is compatible with older versions and contains no categories,
                                # add the 'Input CLANS file' category and initiate it
                                if category_index == 0:
                                    cfg.groups_by_categories.append({'name': 'Input CLANS file',
                                                                     'groups': dict(),
                                                                     'nodes_size': cfg.run_params['nodes_size'],
                                                                     'text_size': cfg.run_params['text_size'],
                                                                     'nodes_outline_width': cfg.run_params['nodes_outline_width'],
                                                                     'nodes_outline_color': cfg.run_params['nodes_outline_color'],
                                                                     'is_bold': True,
                                                                     'is_italic': False
                                                                     })
                                    category_index += 1

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
                                cfg.groups_by_categories[category_index]['groups'][group_ID] = d.copy()
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

                            elif k == 'size' or k == 'name_size':
                                d[k] = int(v)

                            elif (k == 'is_bold' or k == 'is_italic') and level == 'group':
                                if v == 'True':
                                    d[k] = True
                                else:
                                    d[k] = False

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

                            if k == 'param':
                                param_name = v
                                self.params_dict[param_name] = dict()

                            elif k == 'values':
                                values_list = v.split()
                                self.params_dict[param_name][k] = values_list

                            else:
                                self.params_dict[param_name][k] = v

                elif line.strip() == "<taxonomy>":
                    in_tax_block = 1
                elif in_tax_block:
                    if line.strip() == "</taxonomy>":
                        in_tax_block = 0
                    else:
                        m = re.search("^(\w+)\=(.+)\n", line)
                        if m:
                            k = m.group(1)
                            v = m.group(2)

                            if k == 'tax_level':
                                tax_level = v
                                cfg.seq_by_tax_level_dict[tax_level] = dict()

                            elif k == 'name':
                                name = v
                                cfg.seq_by_tax_level_dict[tax_level][name] = dict()

                            elif k == 'numbers':
                                for num in (v.split(';')):
                                    if num != '':
                                        cfg.seq_by_tax_level_dict[tax_level][name][int(num)] = 1

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
        seq.init_groups_by_categories()

        # If there sre groups - add the information to the sequences array
        if self.is_groups:
            for category_index in range(len(cfg.groups_by_categories)):
                cfg.groups_by_categories[category_index]['sequences'] = np.full(cfg.run_params['total_sequences_num'],
                                                                                -1)
                for group_ID in cfg.groups_by_categories[category_index]['groups']:
                    for seq_num in cfg.groups_by_categories[category_index]['groups'][group_ID]['seqIDs']:
                        seq_index = int(seq_num)
                        cfg.groups_by_categories[category_index]['sequences'][seq_index] = group_ID

                # Add defaults for the category parameters (in case they are not written in the clans file)
                if 'nodes_size' not in cfg.groups_by_categories[category_index]:
                    cfg.groups_by_categories[category_index]['nodes_size'] = cfg.run_params['nodes_size']
                if 'text_size' not in cfg.groups_by_categories[category_index]:
                    cfg.groups_by_categories[category_index]['text_size'] = cfg.run_params['text_size']
                if 'nodes_outline_color' not in cfg.groups_by_categories[category_index]:
                    cfg.groups_by_categories[category_index]['nodes_outline_color'] = \
                        cfg.run_params['nodes_outline_color']
                if 'nodes_outline_width' not in cfg.groups_by_categories[category_index]:
                    cfg.groups_by_categories[category_index]['nodes_outline_width'] = \
                        cfg.run_params['nodes_outline_width']
                if 'is_bold' not in cfg.groups_by_categories[category_index]:
                    cfg.groups_by_categories[category_index]['is_bold'] = cfg.run_params['is_bold']
                if 'is_italic' not in cfg.groups_by_categories[category_index]:
                    cfg.groups_by_categories[category_index]['is_italic'] = cfg.run_params['is_italic']

        # calculate the sequence_length column
        seq.add_seq_length_param()

        # If there is saved metadata - add the information to the main dict
        if self.is_seq_params:
            seq.add_saved_numeric_params(self.params_dict)

        # If parameters were defined in the file - save them in the 'run_params' dict
        if 'rounds_done' in self.params:
            cfg.run_params['rounds_done'] = int(self.params['rounds_done'])
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

        if 'nodes_size' in self.params:
            cfg.run_params['nodes_size'] = int(self.params['nodes_size'])

            # Update default / compatible categories
            cfg.groups_by_categories[0]['nodes_size'] = cfg.run_params['nodes_size']
            if len(cfg.groups_by_categories) > 1 and cfg.groups_by_categories[1]['name'] == 'Input CLANS file':
                cfg.groups_by_categories[1]['nodes_size'] = cfg.run_params['nodes_size']

        # The nodes size is not defined in the parameters -> define according to the data size
        else:
            if cfg.run_params['total_sequences_num'] <= 1000:
                cfg.run_params['nodes_size'] = cfg.nodes_size_large
            elif 1000 < cfg.run_params['total_sequences_num'] <= 4000:
                cfg.run_params['nodes_size'] = cfg.nodes_size_medium
            elif 4000 < cfg.run_params['total_sequences_num'] <= 10000:
                cfg.run_params['nodes_size'] = cfg.nodes_size_small
            else:
                cfg.run_params['nodes_size'] = cfg.nodes_size_tiny

        if 'nodes_color' in self.params:
            cfg.run_params['nodes_color'] = [int(c) / 255 for c in self.params['nodes_color'].split(';')]

        if 'nodes_outline_color' in self.params:
            cfg.run_params['nodes_outline_color'] = [int(c) / 255 for c in self.params['nodes_outline_color'].split(';')]

            # Update default / compatible categories
            cfg.groups_by_categories[0]['nodes_outline_color'] = cfg.run_params['nodes_outline_color']
            if len(cfg.groups_by_categories) > 1 and cfg.groups_by_categories[1]['name'] == 'Input CLANS file':
                cfg.groups_by_categories[1]['nodes_outline_color'] = cfg.run_params['nodes_outline_color']

        if 'nodes_outline_width' in self.params:
            cfg.run_params['nodes_outline_width'] = float(self.params['nodes_outline_width'])

            # Update default / compatible categories
            cfg.groups_by_categories[0]['nodes_outline_width'] = cfg.run_params['nodes_outline_width']
            if len(cfg.groups_by_categories) > 1 and cfg.groups_by_categories[1]['name'] == 'Input CLANS file':
                cfg.groups_by_categories[1]['nodes_outline_width'] = cfg.run_params['nodes_outline_width']

        if 'is_taxonomy_available' in self.params:
            cfg.run_params['is_taxonomy_available'] = True
            cfg.run_params['finished_taxonomy_search'] = True
            cfg.run_params['found_taxa_num'] = int(self.params['found_taxa_number'])

        # Apply the similarity cutoff
        if self.type_of_values == "hsp":
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

        # Sort the connection pairs
        cfg.similarity_values_list = sorted(cfg.similarity_values_list)

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
            seq_block += '>' + cfg.sequences_array['seq_ID'][seq] + '\n' + cfg.sequences_array['sequence'][seq] + '\n'
            pos_block += str(seq) + ' ' + str(cfg.sequences_array['x_coor'][seq]) + ' ' + \
                         str(cfg.sequences_array['y_coor'][seq]) + ' ' + str(cfg.sequences_array['z_coor'][seq]) + '\n'

        output.write('<seq>\n')
        output.write(seq_block)
        output.write('</seq>\n')

        # Write the groups block
        if len(cfg.groups_by_categories[group_by]['groups']) > 0:
            groups_block = ""
            output.write('<seqgroups>\n')
            for group_ID in cfg.groups_by_categories[group_by]['groups']:

                seq_ids_str = ""
                for seq_index in cfg.groups_by_categories[group_by]['groups'][group_ID]['seqIDs']:
                    seq_ids_str += str(seq_index) + ";"
                groups_block += 'name=' + cfg.groups_by_categories[group_by]['groups'][group_ID]['name'] + '\n'
                groups_block += 'size=' + cfg.groups_by_categories[group_by]['groups'][group_ID]['size'] + '\n'
                groups_block += 'color=' + cfg.groups_by_categories[group_by]['groups'][group_ID]['color'] + '\n'
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

        # Sort the connection pairs
        cfg.similarity_values_list = sorted(cfg.similarity_values_list)

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
        output.write('nodes_size=' + str(cfg.run_params['nodes_size']) + '\n')
        output.write('nodes_color=' + ';'.join([str(int(c * 255)) for c in cfg.run_params['nodes_color']]) + '\n')
        output.write('nodes_outline_color=' + ';'.join([str(int(c * 255))
                                                        for c in cfg.run_params['nodes_outline_color']]) + '\n')
        output.write('nodes_outline_width=' + str(cfg.run_params['nodes_outline_width']) + '\n')
        if cfg.run_params['is_taxonomy_available']:
            output.write('is_taxonomy_available=' + str(cfg.run_params['is_taxonomy_available']) + '\n')
            output.write('found_taxa_number=' + str(cfg.run_params['found_taxa_num']) + '\n')
        output.write('</param>\n')

        # Write the sequences block
        for seq in range(cfg.run_params['total_sequences_num']):
            seq_block += '>' + cfg.sequences_array['seq_ID'][seq] + '\n' + cfg.sequences_array['sequence'][
                seq] + '\n'
            pos_block += str(seq) + ' ' + str(cfg.sequences_array['x_coor'][seq]) + ' ' + \
                         str(cfg.sequences_array['y_coor'][seq]) + ' ' + str(cfg.sequences_array['z_coor'][seq]) + '\n'

        output.write('<seq>\n')
        output.write(seq_block)
        output.write('</seq>\n')

        # Write the groups block: write the groups for each category, including new parameters
        if len(cfg.groups_by_categories) > 1 or len(cfg.groups_by_categories[0]['groups']) > 0:
            output.write('<seqgroups>\n')

            # A loop over the grouping categories
            for category_index in range(len(cfg.groups_by_categories)):

                if len(cfg.groups_by_categories[category_index]['groups']) > 0:
                    groups_block = ""

                    category_str = "category=" + cfg.groups_by_categories[category_index]['name'] + "\n"
                    output.write(category_str)

                    nodes_size_str = "nodes_size=" + str(cfg.groups_by_categories[category_index]['nodes_size']) + "\n"
                    output.write(nodes_size_str)

                    text_size_str = "text_size=" + str(cfg.groups_by_categories[category_index]['text_size']) + "\n"
                    output.write(text_size_str)

                    nodes_outline_color_str = "nodes_outline_color=" + ';'.join([str(int(c * 255)) for c in
                                               cfg.groups_by_categories[category_index]['nodes_outline_color']]) \
                                              + "\n"
                    output.write(nodes_outline_color_str)

                    nodes_outline_width_str = "nodes_outline_width=" + \
                                              str(cfg.groups_by_categories[category_index]['nodes_outline_width']) + \
                                              "\n"
                    output.write(nodes_outline_width_str)

                    is_bold_str = "is_bold=" + str(cfg.groups_by_categories[category_index]['is_bold']) + "\n"
                    output.write(is_bold_str)

                    is_italic_str = "is_italic=" + str(cfg.groups_by_categories[category_index]['is_italic']) + "\n"
                    output.write(is_italic_str)

                    ordered_groups = sorted(cfg.groups_by_categories[category_index]['groups'].keys(),
                                            key=lambda k: cfg.groups_by_categories[category_index]['groups'][k]['order'])

                    # a loop over the groups
                    for group_ID in ordered_groups:

                        seq_ids_str = ""
                        for seq_index in cfg.groups_by_categories[category_index]['groups'][group_ID]['seqIDs']:
                            seq_ids_str += str(seq_index) + ";"

                        outline_color = ';'.join([str(int(c * 255))
                                                  for c in cfg.groups_by_categories[category_index]['groups'][group_ID]['outline_color']])

                        groups_block += 'name=' + cfg.groups_by_categories[category_index]['groups'][group_ID]['name'] + '\n'
                        groups_block += 'size=' + str(cfg.groups_by_categories[category_index]['groups'][group_ID]['size']) + '\n'
                        groups_block += 'name_size=' + str(cfg.groups_by_categories[category_index]['groups'][group_ID]['name_size']) + '\n'
                        groups_block += 'color=' + cfg.groups_by_categories[category_index]['groups'][group_ID]['color'] + '\n'
                        groups_block += 'outline_color=' + outline_color + '\n'
                        groups_block += 'is_bold=' + str(cfg.groups_by_categories[category_index]['groups'][group_ID]['is_bold']) + '\n'
                        groups_block += 'is_italic=' + str(cfg.groups_by_categories[category_index]['groups'][group_ID]['is_italic']) + '\n'
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

        # Write the taxonomy block (if any)
        if cfg.run_params['is_taxonomy_available']:
            output.write('<taxonomy>\n')

            for tax_level in cfg.seq_by_tax_level_dict:
                tax_level_str = "tax_level=" + tax_level + "\n"
                output.write(tax_level_str)

                for name in cfg.seq_by_tax_level_dict[tax_level]:
                    name_str = "name=" + name + "\n"
                    numbers_str = ";".join([str(k) for k in cfg.seq_by_tax_level_dict[tax_level][name].keys()])
                    name_str += "numbers=" + numbers_str + "\n"
                    output.write(name_str)

            output.write('</taxonomy>\n')

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

