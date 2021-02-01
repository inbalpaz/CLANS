import numpy as np
from vispy import app, scene
import clans.config as cfg
import clans.layouts.fruchterman_reingold as fr


def set_camera_distance(max_dist):
    return max_dist * 1.5 + 1.5


class ScatterPlot3D:

    def __init__(self, view):
        self.app = app.use_app('pyqt5')
        self.colors_array = []
        self.outline = 0.1
        self.size = 7
        self.pos_array = []
        self.dist = 2

        # Define the camera parameters according to the data
        view.camera = 'turntable'
        if cfg.run_params['num_of_dimensions'] == 2:
            view.camera.elevation = 90
            view.camera.azimuth = 0

        # Create the scatter plot (without data)
        self.scatter_plot = scene.visuals.Markers()
        self.scatter_plot.set_gl_state('translucent', blend=True, depth_test=True)

    def set_data(self, view):

        # Initialise the coordinates array
        self.pos_array = fr.coordinates

        # Set the distance of the camera according to the maximal distance between the coordinates
        self.dist = np.amax(fr.coordinates) - np.amin(fr.coordinates)
        view.camera.distance = set_camera_distance(self.dist)

        # Build the colors array according to the groups information (if any)
        self.colors_array = np.zeros((cfg.run_params['total_sequences_num'], 4), dtype=np.float32)
        self.colors_array[:, 3] = 1.0  # Set the alpha to 1 (opaque)
        for seq_index in range(cfg.run_params['total_sequences_num']):
            if cfg.sequences_array[seq_index]['in_group'] >= 0:
                self.outline = 1.0
                group_index = cfg.sequences_array[seq_index]['in_group']
                color_str = cfg.groups_list[group_index]['color']
                color_arr = color_str.split(';')
                for i in range(3):
                    self.colors_array[seq_index, i] = int(color_arr[i]) / 255

        # Define the size of the dots according to the data size
        if cfg.run_params['total_sequences_num'] <= 1000:
            self.size = 10
        elif 1000 < cfg.run_params['total_sequences_num'] <= 5000:
            self.size = 7
        elif 5000 < cfg.run_params['total_sequences_num'] <= 10000:
            self.size = 5
        else:
            self.size = 3

        self.scatter_plot.set_data(pos=self.pos_array, face_color=self.colors_array, size=self.size,
                                   edge_width=self.outline, symbol='disc')

    def update_positions(self, view):
        # Update the coordinates array
        self.pos_array = fr.coordinates

        # Update the distance of the camera according to the new maximal distance between the coordinates
        self.dist = np.amax(fr.coordinates) - np.amin(fr.coordinates)
        view.camera.distance = set_camera_distance(self.dist)

        self.scatter_plot.set_data(pos=self.pos_array, face_color=self.colors_array, size=self.size,
                                   edge_width=self.outline)



