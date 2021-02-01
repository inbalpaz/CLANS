import numpy as np
import numba
import clans.config as cfg

coordinates = []
total_seq_last_movement = []
current_temp = 1.0


def init_variables():
    global coordinates
    global total_seq_last_movement

    if cfg.run_params['dimensions_num_for_clustering'] == 2:
        coordinates = np.column_stack((cfg.sequences_array['x_coor'], cfg.sequences_array['y_coor']))
    else:
        coordinates = np.column_stack(
            (cfg.sequences_array['x_coor'], cfg.sequences_array['y_coor'], cfg.sequences_array['z_coor']))

    total_seq_last_movement = np.zeros((cfg.run_params['total_sequences_num'], cfg.run_params['dimensions_num_for_clustering']))


#@profile
def calculate_new_positions():
    global coordinates
    global total_seq_last_movement
    global current_temp
    attraction_values = cfg.attraction_values_mtx
    connected_sequences = cfg.connected_sequences_mtx
    movement = np.zeros((cfg.run_params['total_sequences_num'], cfg.run_params['dimensions_num_for_clustering']))

    # Calculate the movement created by the attractive and repulsive forces between the pairs
    calculate_pair_forces(coordinates, attraction_values, connected_sequences, movement,
                          cfg.run_params['dimensions_num_for_clustering'], cfg.run_params['att_val'], cfg.run_params['att_exp'],
                          cfg.run_params['rep_val'], cfg.run_params['rep_exp'])
    #print("movement:" + str(movement))

    # Add the 'gravity' movement towards the origin
    movement -= coordinates * cfg.run_params['gravity']

    # Calculate the normalized movement vector for each sequence in each dimension
    # including the consideration of the last movement (according to the dampening parameter)
    # and the current temperature of the system.
    calculate_total_sequence_movement(total_seq_last_movement, cfg.run_params['dimensions_num_for_clustering'],
                                      cfg.run_params['dampening'], cfg.run_params['maxmove'], movement)
    #print("total_seq_movement:" + str(movement))

    # Move the position of all the sequences according to the total movement vector
    coordinates += movement
    #print("FR.calculate_new_positions: New coordinates including dampening and cooling:" + str(coordinates))

    # Save the current movement for the next iteration
    total_seq_last_movement = movement.copy()

    # Update the current temperature of the system (if cooling<1, the system gradually cools down until temp=0)
    current_temp *= cfg.run_params['cooling']


@numba.njit
def square_num(num):
    return num ** 2


@numba.njit
def sqrt_num(num):
    return num ** 0.5


@numba.njit
def calc_att_force(att_val, att_factor, euc_dist, att_exp):
    att_forces = att_val * att_factor * (euc_dist ** att_exp)
    return att_forces


@numba.njit
def calc_rep_force(rep_val, euc_dist, rep_exp):
    rep_forces = rep_val / (euc_dist ** rep_exp)
    return rep_forces


@numba.njit
def calc_pair_move(pair_dist_1d, euc_dist, pair_force):
    pair_moves = pair_dist_1d / euc_dist * pair_force
    return pair_moves


@numba.njit
def calc_moves_per_seq(pair_moves):
    seq_moves = np.sum(pair_moves)
    return seq_moves


@numba.njit(parallel=True)
def calculate_pair_forces(coor, attraction_values, connected_sequences, movement, n_dims, att_val, att_exp, rep_val, rep_exp):
    n_sequences = coor.shape[0]
    dist_array = np.zeros(n_dims)

    for i in range(n_sequences-1):
        for j in range(i+1, n_sequences):
            euclidean_dist = 0

            # Calculate the pair-distances in each dimension and the Euclidean distance for each pair
            for dim in range(n_dims):
                dist_array[dim] = coor[i][dim] - coor[j][dim]
                euclidean_dist += square_num(dist_array[dim])
            if euclidean_dist == 0:
                euclidean_dist = 0.000001
            else:
                euclidean_dist = sqrt_num(euclidean_dist)

            # Calculate the pairwise repulsive forces between all the sequences
            rep_force = calc_rep_force(rep_val, euclidean_dist, rep_exp)

            # Calculate the pairwise attractive forces between the connected sequences only
            if connected_sequences[i][j] == 1:
                att_force = calc_att_force(attraction_values[i][j], att_val, euclidean_dist, att_exp)

            for dim in range(n_dims):
                # Calculate the pairwise movement, resulted from the repulsive force, in each dimension separately
                rep_movement = calc_pair_move(dist_array[dim], euclidean_dist, rep_force)

                # add the repulsive movement to both sequences in opposite directions
                movement[i][dim] += rep_movement
                movement[j][dim] -= rep_movement

                if connected_sequences[i][j] == 1:
                    # Calculate the pairwise movement, resulted from the attractive force, in each dimension separately
                    att_movement = calc_pair_move(dist_array[dim], euclidean_dist, att_force)

                    # add the attractive movement to both sequences in opposite directions (towards each other)
                    movement[i][dim] -= att_movement
                    movement[j][dim] += att_movement


@numba.guvectorize([(numba.float64[:, :], numba.int64, numba.float64, numba.float64, numba.float64[:, :])],
                   '(m, n), (), (), () -> (m, n)', nopython=True, target='parallel')
def calculate_total_sequence_movement(last_movement, n_dims, dampening, maxmove, movement):
    n_sequences = movement.shape[0]

    for i in range(n_sequences):
        xyz_movement = 0

        for dim in range(n_dims):
            # The last movement is added to the current movement with the weight of (1-dampening)
            movement[i][dim] += last_movement[i][dim] * (1 - dampening)

            # The sum of the last movement and the current movement is multiplied by the current temperature
            movement[i][dim] *= current_temp

            # Normalizing the movement by the number of sequences
            movement[i][dim] /= n_sequences

            # Calculate the euclidean movement
            xyz_movement += square_num(movement[i][dim])

        if xyz_movement == 0:
            xyz_movement = 0.000001
        else:
            xyz_movement = sqrt_num(xyz_movement)

        # In case the 3D movement-vector is bigger than the maximum allowed movement ('maxmove'),
        # multiply the movement in each dimension by a limiting factor (maxmove / movement_vector)
        limit_movement_factor = maxmove / xyz_movement
        if xyz_movement > maxmove:
            for dim in range(n_dims):
                movement[i][dim] *= limit_movement_factor


