import numpy as np
import clans.config as cfg


def create_similarity_array(similarity_values_mtx):
    cfg.similarity_values_mtx = np.array(similarity_values_mtx)
    #print("similarity matrix:\n" + str(cfg.similarity_values_mtx))


def calculate_attraction_values():
    minus_log_similarity_values = np.where(cfg.similarity_values_mtx == 1, 0, -np.log10(cfg.similarity_values_mtx))
    max_value = np.amax(minus_log_similarity_values)
    cfg.attraction_values_mtx = np.true_divide(minus_log_similarity_values, max_value)
    #print("Attraction values:\n" + str(cfg.attraction_values_mtx))


def create_attraction_values_array(att_val_mtx):
    cfg.attraction_values_mtx = np.array(att_val_mtx)
    #print("Attraction values:\n" + str(cfg.attraction_values_mtx))


def define_connected_sequences(mode):
    if mode == 'hsp':
        cfg.connected_sequences = np.where(cfg.similarity_values_mtx <= cfg.run_params['similarity_cutoff'], 1, 0)
    elif mode == 'att':
        cfg.connected_sequences = np.where(cfg.attraction_values_mtx >= cfg.run_params['similarity_cutoff'], 1, 0)
    #print("Connected_sequences:\n" + str(cfg.connected_sequences))

