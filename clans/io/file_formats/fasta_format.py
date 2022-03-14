from Bio import SeqIO
import random
import re
import clans.config as cfg
import clans.data.sequences as seq


class FastaFormat:

    def __init__(self):
        self.sequences_list = []
        self.file_is_valid = 1
        self.error = ""

    def read_file(self, file_path):
        with open(file_path) as FH:

            seq_index = 0
            for record in SeqIO.parse(FH, "fasta"):
                seq_title = record.description

                # Extract the sequence_ID from the title (trim it at space character)
                m = re.search("^(\S+)", seq_title)
                seq_id = m.group(1)

                sequence = str(record.seq)
                seq_length = 0
                norm_seq_length = 0.0
                organism = ""
                tax_ID = ""
                x_coor = self.generate_rand_pos()
                y_coor = self.generate_rand_pos()
                z_coor = self.generate_rand_pos()
                coor_tuple = (seq_id, seq_title, sequence, seq_length, norm_seq_length, organism, tax_ID, x_coor, y_coor,
                              z_coor, False, x_coor, y_coor, z_coor)
                self.sequences_list.append(coor_tuple)
                cfg.sequences_ID_to_index[seq_id] = seq_index
                seq_index += 1

    def fill_values(self):
        cfg.run_params['total_sequences_num'] = len(self.sequences_list)
        print("total number of sequences is " + str(cfg.run_params['total_sequences_num']))

        # Create the structured NumPy array of sequences
        seq.create_sequences_array(self.sequences_list)
        seq.init_seuences_in_groups()

    # Returns a random coordinate between -1 and 1
    @staticmethod
    def generate_rand_pos():
        rand = random.random() * 2 - 1
        return '{:.3f}'.format(rand)



