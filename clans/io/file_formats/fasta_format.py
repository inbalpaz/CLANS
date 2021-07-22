from Bio import SeqIO
import random
import clans.config as cfg
import clans.data.sequences as seq
import clans.data.sequence_pairs as sp


class FastaFormat:

    def __init__(self):
        self.sequences_list = []
        self.file_is_valid = 1
        self.error = ""

    def read_file(self, file_path):
        with open(file_path) as FH:
            for record in SeqIO.parse(FH, "fasta"):
                seq_title = record.description
                sequence = str(record.seq)
                x_coor = self.generate_rand_pos()
                y_coor = self.generate_rand_pos()
                z_coor = self.generate_rand_pos()
                coor_tuple = (seq_title, sequence, x_coor, y_coor, z_coor, -1, False, x_coor, y_coor, z_coor)
                self.sequences_list.append(coor_tuple)

    def fill_values(self):
        cfg.run_params['total_sequences_num'] = len(self.sequences_list)
        print("total number of sequences is " + str(cfg.run_params['total_sequences_num']))

        # Create the structured NumPy array of sequences
        seq.create_sequences_array(self.sequences_list)

    # Returns a random coordinate between -1 and 1
    @staticmethod
    def generate_rand_pos():
        rand = random.random() * 2 - 1
        return '{:.3f}'.format(rand)



