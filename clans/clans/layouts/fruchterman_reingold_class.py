import numpy as np
import clans.config as cfg
import clans.clans.layouts.fruchterman_reingold_numba as frn


class FruchtermanReingold:

    def __init__(self, coor_x, coor_y, coor_z):

        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.coordinates = np.column_stack((coor_x, coor_y, coor_z))
            self.dim_num = 3
        else:
            self.coordinates = np.column_stack((coor_x, coor_y))
            self.dim_num = 2

        self.total_seq_num = self.coordinates.shape[0]
        self.total_seq_last_movement = np.zeros((self.total_seq_num, self.dim_num))

        if 'current_temp' in cfg.run_params:
            self.current_temp = cfg.run_params['current_temp']
        else:
            self.current_temp = 1.0

        self.attraction_values = cfg.attraction_values_mtx
        self.connected_sequences = cfg.connected_sequences_mtx

    def init_calculation(self, coor_x, coor_y, coor_z):

        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.coordinates = np.column_stack((coor_x, coor_y, coor_z))
            self.dim_num = 3
        else:
            self.coordinates = np.column_stack((coor_x, coor_y))
            self.dim_num = 2

        self.total_seq_num = self.coordinates.shape[0]
        self.total_seq_last_movement = np.zeros((self.total_seq_num, self.dim_num))

        self.current_temp = 1.0
        self.attraction_values = cfg.attraction_values_mtx
        self.connected_sequences = cfg.connected_sequences_mtx

    def init_coordinates(self, coor_x, coor_y, coor_z):

        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.coordinates = np.column_stack((coor_x, coor_y, coor_z))
            self.dim_num = 3
        else:
            self.coordinates = np.column_stack((coor_x, coor_y))
            self.dim_num = 2

        self.total_seq_last_movement = np.zeros((self.total_seq_num, self.dim_num))

    def update_connections(self):
        self.attraction_values = cfg.attraction_values_mtx
        self.connected_sequences = cfg.connected_sequences_mtx

    def calculate_new_positions(self, is_subset_mode):

        movement = np.zeros((self.total_seq_num, self.dim_num))

        # Calculate the movement created by the attractive and repulsive forces between the pairs
        if not is_subset_mode:
            frn.calculate_pair_forces(self.coordinates, self.attraction_values, self.connected_sequences, movement,
                                      self.dim_num, cfg.run_params['att_val'], cfg.run_params['att_exp'],
                                      cfg.run_params['rep_val'], cfg.run_params['rep_exp'])

        # Subset mode - ignore pairs which are not in the subset
        else:
            frn.calculate_pair_forces_subset(self.coordinates, self.attraction_values, self.connected_sequences,
                                             movement, self.dim_num, cfg.run_params['att_val'],
                                             cfg.run_params['att_exp'], cfg.run_params['rep_val'],
                                             cfg.run_params['rep_exp'], cfg.sequences_array['in_subset'])
        # print("movement:" + str(movement))

        # Add the 'gravity' movement towards the origin
        movement -= self.coordinates * cfg.run_params['gravity']

        # Calculate the normalized movement vector for each sequence in each dimension
        # including the consideration of the last movement (according to the dampening parameter)
        # and the current temperature of the system.
        if not is_subset_mode:
            frn.calculate_total_sequence_movement(self.total_seq_last_movement, self.dim_num,
                                                  cfg.run_params['dampening'], cfg.run_params['maxmove'],
                                                  self.current_temp, movement)
        else:
            frn.calculate_total_sequence_movement_subset(self.total_seq_last_movement, self.dim_num,
                                                  cfg.run_params['dampening'], cfg.run_params['maxmove'],
                                                  self.current_temp, cfg.sequences_array['in_subset'], movement)
        # print("total_seq_movement:" + str(movement))

        # Move the position of all the sequences according to the total movement vector
        self.coordinates += movement
        # print("FR.calculate_new_positions: New coordinates including dampening and cooling:" + str(coordinates))

        # Save the current movement for the next iteration
        self.total_seq_last_movement = movement.copy()

        # Update the current temperature of the system (if cooling<1, the system gradually cools down until temp=0)
        self.current_temp *= cfg.run_params['cooling']
