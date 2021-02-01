import numpy as np
from vispy import app, scene
import clans.config as cfg
import clans.layouts.fruchterman_reingold as fr


def set_camera_distance(max_dist):
    return max_dist * 1.5 + 1.5


def return_color(bin_num):
    edges_color_map = {1: 0.9,
                        2: 0.8,
                        3: 0.7,
                        4: 0.6,
                        5: 0.5,
                        6: 0.4,
                        7: 0.3,
                        8: 0.2,
                        9: 0.1,
                        10: 0.0}
    return edges_color_map[bin_num]


class LinePlot3D:

    def __init__(self, view):
        self.app = app.use_app('pyqt5')
        self.nodes_colors_array = []
        self.nodes_outline = 0.1
        self.nodes_size = 7
        self.nodes_symbol = 'disc'
        self.edges_colors_array = []
        self.att_values_bins = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        self.edges_color_map = {1: 0.9,
                                2: 0.8,
                                3: 0.7,
                                4: 0.6,
                                5: 0.5,
                                6: 0.4,
                                7: 0.3,
                                8: 0.2,
                                9: 0.1,
                                10: 0.0}
        self.edges_color = (0.5, 0.5, 0.5, 0.7)
        self.edges_width = 0
        self.pos_array = []
        self.dist = 2

        # Define the camera parameters according to the data
        view.camera = 'turntable'
        if cfg.run_params['num_of_dimensions'] == 2:
            view.camera.elevation = 90
            view.camera.azimuth = 0

        # Create the line plot (without data)
        self.line_plot = scene.visuals.LinePlot()
        self.line_plot.set_gl_state('translucent', blend=True, depth_test=True)

    ## Mode: init / update / connections
    def set_data(self, view, is_show_connections, mode):

        if mode is not 'connections':
            # Initialise the coordinates array
            self.pos_array = fr.coordinates

            # Set the distance of the camera according to the maximal distance between the coordinates
            self.dist = np.amax(fr.coordinates) - np.amin(fr.coordinates)
            view.camera.distance = set_camera_distance(self.dist)

        # If it's the first setting of the data - define the size and colors
        if mode is 'init':

            # Build the colors array of the nodes according to the groups information (if any)
            self.nodes_colors_array = np.zeros((cfg.run_params['total_sequences_num'], 4), dtype=np.float32)
            self.nodes_colors_array[:, 3] = 1.0  # Set the alpha to 1 (opaque)
            for seq_index in range(cfg.run_params['total_sequences_num']):
                if cfg.sequences_array[seq_index]['in_group'] >= 0:
                    self.nodes_outline = 1.0
                    group_index = cfg.sequences_array[seq_index]['in_group']
                    color_str = cfg.groups_list[group_index]['color']
                    color_arr = color_str.split(';')
                    for i in range(3):
                        self.nodes_colors_array[seq_index, i] = int(color_arr[i]) / 255

            # Build the colors array of the edges according to the attraction values
            # (Divide the data to 9 color-bins. lower att-values -> higher == lighter gray -> darker gray)
            #self.edges_colors_array = np.zeros((cfg.run_params['connections_num'], 4), dtype=np.float32)
            #self.edges_colors_array[:, 3] = 0.9  # Set the alpha
            #edges_bins_array = np.digitize(cfg.att_values_for_connected_list, self.att_values_bins, right=True)
            #for connection_index in range(cfg.run_params['connections_num']):
                #for i in range(3):
                    #self.edges_colors_array[connection_index, i] = self.edges_color_map[edges_bins_array[connection_index]]

            # Define the size of the dots according to the data size
            if cfg.run_params['total_sequences_num'] <= 1000:
                self.nodes_size = 10
            elif 1000 < cfg.run_params['total_sequences_num'] <= 5000:
                self.nodes_size = 7
            else:
                self.nodes_size = 5

        # Set the color of the edges (gray / transparent) according to the 'show connections' state
        if is_show_connections:
            self.edges_width = 0.01

            # Define the size of the dots according to the data size
            if cfg.run_params['total_sequences_num'] <= 5000:
                self.nodes_size = 12
            else:
                self.nodes_size = 8
        else:
            self.edges_width = 0

            # Define the size of the dots according to the data size
            if cfg.run_params['total_sequences_num'] <= 1000:
                self.nodes_size = 10
            elif 1000 < cfg.run_params['total_sequences_num'] <= 5000:
                self.nodes_size = 7
            else:
                self.nodes_size = 5

        self.line_plot.set_data(data=self.pos_array, symbol=self.nodes_symbol, marker_size=self.nodes_size,
                                face_color=self.nodes_colors_array, edge_width=self.nodes_outline,
                                color=self.edges_color, width=self.edges_width, connect=cfg.connected_sequences_list)
