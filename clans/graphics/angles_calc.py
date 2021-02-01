import numpy as np
import numba


@numba.njit(parallel=True)
def calculate_azimuth_elevation(coor_array):
    n_coor = coor_array.shape[0]
    azimuth_array = np.zeros(n_coor)
    elevation_array = np.zeros(n_coor)

    for i in range(n_coor):

        # Calculate azimuth angles
        if coor_array[i, 0] == 0:
            azimuth_array[i] = np.radians(90)
        else:
            azimuth_array[i] = np.arctan(coor_array[i, 1] / coor_array[i, 0])

        # Calculate elevation angles
        if coor_array[i, 1] == 0:
            elevation_array[i] = np.radians(90)
        else:
            elevation_array[i] = np.arctan(coor_array[i, 2] / coor_array[i, 1])

    return azimuth_array, elevation_array


@numba.njit(parallel=True)
def calculate_elevation_angles(coor_array):
    n_coor = coor_array.shape[0]
    elevation_array = np.zeros(n_coor)

    for i in range(n_coor):
        # Calculate elevation angles
        if coor_array[i, 1] == 0:
            elevation_array[i] = np.radians(90)
        else:
            elevation_array[i] = np.arctan(coor_array[i, 2] / coor_array[i, 1])

    return elevation_array


@numba.njit
def calcuate_positions_after_azimuth_change(coor_array, xy_vectors_array, azimuth_angles_array, azimuth_change):
    n_coor = coor_array.shape[0]
    new_coor_array = coor_array.copy()

    for i in range(n_coor):
        # Calculate new X after azimuth change
        if coor_array[i, 0] == 0:
            new_coor_array[i, 0] = xy_vectors_array[i] * np.cos(azimuth_angles_array[i] - azimuth_change)
        else:
            new_coor_array[i, 0] = np.cos(azimuth_angles_array[i] - azimuth_change) * coor_array[i, 0] \
                                   / np.cos(azimuth_angles_array[i])

        # Calculate new Y after azimuth change
        if coor_array[i, 1] == 0:
            # Calculate new Y
            new_coor_array[i, 1] = xy_vectors_array[i] * np.cos(azimuth_angles_array[i] - azimuth_change)
        else:
            # Calculate new Y
            new_coor_array[i, 1] = np.sin(azimuth_angles_array[i] - azimuth_change) * coor_array[i, 1] \
                                   / np.sin(azimuth_angles_array[i])

    return new_coor_array


@numba.njit
def calcuate_positions_after_elevation_change(coor_array, yz_vectors_array, elevation_angles_array, elevation_change):
    n_coor = coor_array.shape[0]
    new_coor_array = coor_array.copy()

    # Calculate the new Y coor
    for i in range(n_coor):
        if coor_array[i, 1] == 0:
            new_coor_array[i, 1] = yz_vectors_array[i] * np.cos(elevation_angles_array[i] + elevation_change)
        else:
            new_coor_array[i, 1] = np.cos(elevation_angles_array[i] + elevation_change) * coor_array[i, 1] \
                                   / np.cos(elevation_angles_array[i])

    return new_coor_array

