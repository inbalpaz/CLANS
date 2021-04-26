import numpy as np
import time
from vispy import app, visuals, scene
import clans.config as cfg
import clans.layouts.fruchterman_reingold as fr


def set_camera_distance(max_dist):
    return max_dist * 1.5 + 1.5


class ScatterPlot3D:

    def __init__(self):
        self.app = app.use_app('pyqt5')
        self.rounds_num = 0
        if cfg.run_params['num_of_rounds'] > 0:
            self.iterations = cfg.run_params['num_of_rounds']
        else:
            self.iterations = -1
        self.timer = app.Timer(iterations=self.iterations)
        self.before = time.time()

        self.canvas = scene.SceneCanvas(keys='interactive', show=True, bgcolor='w', position=(50, 50))

        # Initialise the coordinates array
        self.pos_array = fr.coordinates
        self.dist = np.amax(fr.coordinates) - np.amin(fr.coordinates)

        # Add a ViewBox to let the user zoom/rotate
        self.view = self.canvas.central_widget.add_view()

        # Define the camera parameters according to the data
        self.view.camera = 'turntable'
        self.view.camera.distance = set_camera_distance(self.dist)
        #self.view.camera.azimuth = 45
        #self.view.camera.elevation = 45
        if cfg.run_params['num_of_dimensions'] == 2:
            self.view.camera.elevation = 90
            self.view.camera.azimuth = 0

        # Build the colors array according to the groups information (if any)
        self.colors_array = np.zeros((cfg.run_params['total_sequences_num'], 4), dtype=np.float32)
        self.colors_array[:, 3] = 1.0  # Set the alpha to 1 (opaque)
        for seq_index in range(cfg.run_params['total_sequences_num']):
            if cfg.sequences_array[seq_index]['in_group'] >= 0:
                self.outline = 1.0
                group_index = int(cfg.sequences_array[seq_index]['in_group'])
                color_str = cfg.groups_dict[group_index]['color']
                color_arr = color_str.split(';')
                for i in range(3):
                    self.colors_array[seq_index, i] = int(color_arr[i]) / 255
            else:
                self.outline = 0.1

        # Define the size of the dots according to the data size
        if cfg.run_params['total_sequences_num'] <= 1000:
            self.size = 10
        elif 1000 < cfg.run_params['total_sequences_num'] <= 5000:
            self.size = 7
        else:
            self.size = 5

        # build the visuals
        self.nodes = scene.visuals.create_visual_node(visuals.MarkersVisual)

        # Create the scatter plot
        self.scatter_plot = self.nodes(parent=self.view.scene)
        self.scatter_plot.set_gl_state('translucent', blend=True, depth_test=True)
        self.scatter_plot.set_data(pos=self.pos_array, face_color=self.colors_array, size=self.size, edge_width=self.outline)

        self.after = time.time()
        duration = (self.after - self.before)
        print("Initializing the plot took " + str(duration) + " seconds")

    # Start Qt event loop
    def start_timer(self):

        self.before = time.time()

        # Start the timer
        self.timer.connect(self.update)
        self.timer.start()
        self.app.run()

    def stop_timer(self):
        self.timer.stop()
        self.timer_started = False

        self.after = time.time()
        duration = (self.after - self.before)
        print("The calculation of " + str(self.rounds_num) + " rounds took " + str(duration) + " seconds")

    def update(self, ev):
        fr.calculate_new_positions()
        self.pos_array = fr.coordinates
        self.scatter_plot.set_data(pos=self.pos_array, face_color=self.colors_array, size=self.size, edge_width=self.outline)
        self.dist = np.amax(fr.coordinates) - np.amin(fr.coordinates)
        self.view.camera.distance = set_camera_distance(self.dist)
        self.rounds_num += 1
        #print("Rounds done: " + str(self.rounds_num))
        #if self.rounds_num == cfg.run_params['num_of_rounds']:
        if self.rounds_num % 100 == 0:
            self.after = time.time()
            duration = (self.after - self.before)
            print("The calculation of " + str(self.rounds_num) + " rounds took " + str(duration) + " seconds")


