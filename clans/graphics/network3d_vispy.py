import numpy as np
from vispy import app, scene, util
import clans.config as cfg
import clans.layouts.fruchterman_reingold as fr
import clans.graphics.angles_calc as ac


def set_camera_distance(max_dist):
    return max_dist * 1.5 + 1.5


class Network3D:

    def __init__(self, view):
        self.app = app.use_app('pyqt5')

        self.nodes_colors_array = []
        self.nodes_size_array = []
        self.nodes_outline_color_array = []
        self.nodes_outline_width = 1.0
        self.nodes_size = 7
        self.selected_nodes_size = self.nodes_size + 5
        self.nodes_symbol = 'disc'
        self.nodes_outline_default_color = [0.0, 0.0, 0.0, 1.0]
        self.selected_outline_color = [1.0, 0.0, 1.0, 1.0]
        self.connections_by_bins = []
        self.att_values_bins = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        self.edges_color_scale = {1: (0.8, 0.8, 0.8, 1.0),
                                  2: (0.6, 0.6, 0.6, 1.0),
                                  3: (0.4, 0.4, 0.4, 1.0),
                                  4: (0.2, 0.2, 0.2, 1.0),
                                  5: (0.0, 0.0, 0.0, 1.0)}
        self.edges_color = (0.5, 0.5, 0.5, 0.9)
        self.edges_width = 0
        self.edges_width_scale = {1: 0.2,
                                  2: 0.4,
                                  3: 0.6,
                                  4: 0.8,
                                  5: 1.0}
        self.drag_rectangle_color = (0.3, 0.3, 0.3, 0.5)

        self.selected_points = {}

        # Arrays for holding coordinates / angles
        self.pos_array = []
        self.rotated_pos_array = []
        self.xy_vector = []
        self.yz_vector = []
        self.azimuth_angles = []
        self.elevation_angles = []

        # Initialize the camera parameters
        self.initial_azimuth = 0
        self.initial_elevation = 90
        self.last_azimuth = 0
        self.last_elevation = 90
        if cfg.run_params['dimensions_num_for_clustering'] == 2:
            view.camera = 'panzoom'
            view.camera.aspect = 1
        else:
            view.camera = 'turntable'
            view.camera.elevation = self.initial_elevation
            view.camera.azimuth = self.initial_azimuth
            view.camera.fov = 0

        print("3D Camera initial parameters:")
        print("FOV: "+str(view.camera.fov))
        print("Elevation: " + str(view.camera.elevation))
        print("Azimuth: " + str(view.camera.azimuth))
        print(view.camera.get_state())

        # Create the scatter plot object (without data)
        self.scatter_plot = scene.visuals.Markers(parent=view.scene)
        self.scatter_plot.set_gl_state('translucent', blend=True, depth_test=True)

        # Create line visual objects - one for each bin attraction-values bin (to create a gray-scale for the lines)
        # Because there is a problem to provide an array of line-colors, each line visual will present a different color
        self.lines = []
        for i in range(5):
            line = scene.visuals.Line()
            line.set_gl_state('translucent', blend=True, depth_test=True)
            self.lines.append(line)

        # Create a rectangle visual for mouse-dragging highlight
        self.drag_rectangle = scene.visuals.Rectangle(center=(0, 0, 0))
        self.drag_rectangle.set_gl_state('translucent', blend=True, depth_test=True)

        #self.axis = scene.visuals.XYZAxis(parent=view.scene)  # For debugging purposes

    # Set the plot data for the first time
    def init_data(self, view):

        # Initialise the coordinates array
        self.pos_array = fr.coordinates.copy()
        #print("\nInitial coordinates:\n")
        #print(self.pos_array)

        # Calculate and save the initial azimuth and elevation angles of all the points
        self.calculate_initial_angles()

        self.nodes_colors_array = np.zeros((cfg.run_params['total_sequences_num'], 4), dtype=np.float32)
        self.nodes_colors_array[:, 3] = 1.0  # Set the alpha to 1 (opaque)
        self.nodes_outline_color_array = np.zeros((cfg.run_params['total_sequences_num'], 4), dtype=np.float32)
        self.nodes_size_array = np.zeros((cfg.run_params['total_sequences_num']), dtype=np.float32)

        # Define the size of the dots according to the data size
        if cfg.run_params['total_sequences_num'] <= 1000:
            self.nodes_size = 10
        elif 1000 < cfg.run_params['total_sequences_num'] <= 5000:
            self.nodes_size = 8
        else:
            self.nodes_size = 6
        self.selected_nodes_size = self.nodes_size + 5

        # Build the initial color arrays (for the nodes and their outline) and the nodes-size array
        for seq_index in range(cfg.run_params['total_sequences_num']):

            # Build the colors array of the nodes according to the groups information (if any)
            if cfg.sequences_array[seq_index]['in_group'] >= 0:
                group_index = cfg.sequences_array[seq_index]['in_group']
                color_str = cfg.groups_list[group_index]['color']
                color_arr = color_str.split(';')
                for i in range(3):
                    self.nodes_colors_array[seq_index, i] = int(color_arr[i]) / 255

            self.nodes_size_array[seq_index] = self.nodes_size
            self.nodes_outline_color_array[seq_index] = self.nodes_outline_default_color

        # Set the view-range of coordinates according to the data
        if cfg.run_params['dimensions_num_for_clustering'] == 2:
            self.set_range_panzoom_camera(view, 'data')
        else:
            self.set_range_turntable_camera(view, 'data')

        # Display the nodes
        self.scatter_plot.set_data(pos=self.pos_array, face_color=self.nodes_colors_array,
                                   size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                   edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)

        # Create the different bins of connections
        self.create_connections_by_bins()

        # Set the data for the connecting lines (without displaying them) -
        for i in range(5):
            line_color = self.edges_color_scale[i + 1]
            line_width = self.edges_width_scale[i + 1]
            self.lines[i].set_data(pos=self.pos_array, color=line_color, width=line_width,
                                   connect=self.connections_by_bins[i])

    # Update the nodes positions after calculation update or initialization
    def update_data(self, view, dim_num_view):

        # Update the coordinates array
        self.pos_array = fr.coordinates.copy()
        if self.pos_array.shape[1] == 2:
            self.pos_array = np.column_stack((self.pos_array, cfg.sequences_array['z_coor']))

        # View in 3D
        if dim_num_view == 3:

            # Set the maximal range of the Turntable camera
            self.set_range_turntable_camera(view, 'data')

        # View in 2D
        else:

            # Set the maximal range of the PanZoom camera
            self.set_range_panzoom_camera(view, 'data')

            # Zero the Z coordinate
            self.pos_array[:, 2] = 0

        self.scatter_plot.set_data(pos=self.pos_array, face_color=self.nodes_colors_array,
                                   size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                   edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)

        self.update_connections()

    def show_connections(self, view, dim_num_view):
        for i in range(5):
            self.lines[i].parent = view.scene

    # Update the connections plot after changes in P-value threshold or number of dimensions to view
    def update_connections(self):
        for i in range(5):
            line_color = self.edges_color_scale[i+1]
            line_width = self.edges_width_scale[i+1]
            self.lines[i].set_data(pos=self.pos_array, color=line_color, width=line_width,
                                   connect=self.connections_by_bins[i])

    def hide_connections(self):
        for i in range(5):
            self.lines[i].parent = None

    def create_connections_by_bins(self):
        self.connections_by_bins = []

        # (Divide the data to 5 color-bins, according to the attraction values.
        # lower att-values -> higher == lighter gray -> darker gray)
        edges_bins_array = np.digitize(cfg.att_values_for_connected_list, self.att_values_bins, right=True)

        # For each bin, build an array consisting only the connections that belong to the same bin
        for i in range(5):
            connections = cfg.connected_sequences_list[edges_bins_array == (i + 1)]
            self.connections_by_bins.append(connections)

    def set_3d_view(self, view):
        print("Moved to 3D view")

        view.camera = 'turntable'
        view.camera.elevation = self.last_elevation
        view.camera.azimuth = self.last_azimuth
        view.camera.fov = 0

        print("Camera parameters:")
        print(view.camera.get_state())

        self.set_range_turntable_camera(view, 'view')

        self.update_data(view, 3)

    def set_2d_view(self, view):

        print("Moved to 2D view")

        #print("3D camera state:")
        #zoom = view.camera.scale_factor
        #print("3D zoom: " + str(zoom))
        #center = view.camera.center
        #print("3D center: " + str(center))

        #zoom_corrected = self.calculate_scale_factor(zoom)
        #print("Corrected zoom: " + str(zoom_corrected))

        self.calculate_rotation(view)

        # Zero the Z axis to have 2D presentation
        self.rotated_pos_array[:, 2] = 0

        # Turn the camera into 2D PanZoom camera
        view.camera = 'panzoom'
        view.camera.aspect = 1
        self.set_range_panzoom_camera(view, 'view')
        #view.camera.zoom(zoom_corrected)
        #print("Center: " + str(view.camera.center))
        #print("Rect: " + str(view.camera.rect))

        self.update_view(2)

    def update_view(self, dim_num_view):

        if dim_num_view == 3:
            pos_array = self.pos_array.copy()
        else:
            pos_array = self.rotated_pos_array.copy()

        # Update the nodes with the updated rotation
        self.scatter_plot.set_data(pos=pos_array, face_color=self.nodes_colors_array,
                                   size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                   edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)

        # Update the lines with the updated rotation
        for i in range(5):
            line_color = self.edges_color_scale[i + 1]
            line_width = self.edges_width_scale[i + 1]
            self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
                                   connect=self.connections_by_bins[i])

    def calculate_initial_angles(self):

        #print("Calculating the initial angles for rotation purposes")
        #print("Initial Coordinates:")
        #print(self.pos_array)

        # Calculate the distance of the point from the origin on the XY and YZ planes
        self.xy_vector = np.sqrt(self.pos_array[:, 0] ** 2 + self.pos_array[:, 1] ** 2)
        self.yz_vector = np.sqrt(self.pos_array[:, 1] ** 2 + self.pos_array[:, 2] ** 2)

        # Calculate the initial azimuth angles (on XY plane, relative to X) and elevation angles
        # (on YZ plane, relative to Y) for all the points
        self.azimuth_angles, self.elevation_angles = ac.calculate_azimuth_elevation(self.pos_array)

    def calculate_rotation(self, view):
        self.rotated_pos_array = self.pos_array.copy()

        self.last_azimuth = view.camera.azimuth
        self.last_elevation = view.camera.elevation

        # Get the current 3D camera angles to extract the angles of the rotation made by the user (if any)
        azimuth_change = self.last_azimuth - self.initial_azimuth
        azimuth_change_in_radians = np.radians(azimuth_change)
        elevation_change = self.last_elevation - self.initial_elevation
        elevation_change_in_radians = np.radians(elevation_change)

        if azimuth_change != 0 or elevation_change != 0:
            print("Azimuth was changed in " + str(azimuth_change) + " degrees")
            print("Elevation was changed in " + str(elevation_change) + " degrees")
            print("The new azimuth is: " + str(self.last_azimuth))
            print("The new elevation is: " + str(self.last_elevation))

            # Correct the coordinates (for display) according to the change in azimuth and/or elevation
            self.set_rotated_coordinates(azimuth_change_in_radians, elevation_change_in_radians)

        else:
            print("No change in Azimuth or Elevation")

    def set_rotated_coordinates(self, azimuth_change_in_radians, elevation_change_in_radians):

        #print("Coordinates before applying rotation changes (rotated_pos_array):")
        #print(self.rotated_pos_array)

        # Calculate the corrected coordinates after a movement in the XY plane (Azimuth)
        if azimuth_change_in_radians != 0:
            self.rotated_pos_array = ac.calcuate_positions_after_azimuth_change(self.rotated_pos_array,
                                     self.xy_vector, self.azimuth_angles, azimuth_change_in_radians)
            #print("New coordinates after applying azimuth change:")
            #print(self.rotated_pos_array)

        # There was a change in elevation
        if elevation_change_in_radians != 0:

            # If there was already a change in the azimuth, the YZ angles were changed and should be recalculated
            if azimuth_change_in_radians != 0:
                self.elevation_angles = ac.calculate_elevation_angles(self.rotated_pos_array)
                #print("New elevation angles:")
                #print(self.elevation_angles)

            # Calculate the corrected coordinates after a movement in the YZ plane (Elevation)
            self.rotated_pos_array = ac.calcuate_positions_after_elevation_change(self.rotated_pos_array,
                                     self.yz_vector, self.elevation_angles, elevation_change_in_radians)

            #print("New coordinates after applying elevation change:")
            #print(self.rotated_pos_array)

    def set_range_panzoom_camera(self, view, mode):
        if mode == "data":
            xmin = np.amin(self.pos_array[:, 0])
            xmax = np.amax(self.pos_array[:, 0])
            ymin = np.amin(self.pos_array[:, 1])
            ymax = np.amax(self.pos_array[:, 1])
        elif mode == "view":
            xmin = np.amin(self.rotated_pos_array[:, 0])
            xmax = np.amax(self.rotated_pos_array[:, 0])
            ymin = np.amin(self.rotated_pos_array[:, 1])
            ymax = np.amax(self.rotated_pos_array[:, 1])
        view.camera.set_range(x=(xmin, xmax), y=(ymin, ymax), z=None, margin=0.1)

        #print("Camera coordinates range:")
        #print(xmin, xmax, ymin, ymax)

    def set_range_turntable_camera(self, view, mode):
        if mode == "data":
            xmin = np.amin(self.pos_array[:, 0])
            xmax = np.amax(self.pos_array[:, 0])
            ymin = np.amin(self.pos_array[:, 1])
            ymax = np.amax(self.pos_array[:, 1])
            zmin = np.amin(self.pos_array[:, 2])
            zmax = np.amax(self.pos_array[:, 2])
        elif mode == "view":
            xmin = np.amin(self.rotated_pos_array[:, 0])
            xmax = np.amax(self.rotated_pos_array[:, 0])
            ymin = np.amin(self.rotated_pos_array[:, 1])
            ymax = np.amax(self.rotated_pos_array[:, 1])
            zmin = np.amin(self.rotated_pos_array[:, 2])
            zmax = np.amax(self.rotated_pos_array[:, 2])
        view.camera.set_range(x=(xmin, xmax), y=(ymin, ymax), z=(zmin, zmax), margin=0.1)

        #print("Camera coordinates range:")
        #print(xmin, xmax, ymin, ymax, zmin, zmax)

    def reset_turntable_camera(self, view):
        view.camera = 'turntable'
        view.camera.elevation = self.initial_elevation
        view.camera.azimuth = self.initial_azimuth
        view.camera.fov = 0

        print("Turntable camera was reset. Parameters:")
        print(view.camera.get_state())

    def calculate_scale_factor(self, zoom):
        xmax = np.amax(np.abs(self.pos_array[:, 0]))
        corrected_zoom = zoom / xmax
        return corrected_zoom

    def find_selected_point(self, view, clicked_screen_coor):

        # An array to hold the indices of the data points that are close enough to the clicked point
        points_in_radius = []
        deselect = 0

        # Define the radius (in pixels) around the clicked position to look for a data point(s)
        radius = self.nodes_size

        trans = view.scene.transform

        for i in range(self.rotated_pos_array.shape[0]):

            # Translate the data coordinates into screen coordinates
            data_screen_coor = trans.map(self.rotated_pos_array[i])

            # Calculate the euclidean distances of all the points from the clicked point (in screen coor)
            distance_screen_coor = np.linalg.norm(data_screen_coor[:2] - clicked_screen_coor)

            if distance_screen_coor <= radius:
                points_in_radius.append(i)
                # Deselect the data point
                if i in self.selected_points:
                    del self.selected_points[i]
                    deselect = 1
                # Select the data point
                else:
                    self.selected_points[i] = 1
                print("Found matching point: Index = " + str(i))
                print("Position in screen coor: " + str(data_screen_coor))
                print("Distance from clicked point: " + str(distance_screen_coor))

        if len(points_in_radius) > 0:
            print("Selected point(s) indices:")
            print(points_in_radius)

            # Points should be cleared from selection
            if deselect == 1:
                self.unmark_selected_points(points_in_radius)
            # Points should be added to selection
            else:
                self.mark_selected_points(points_in_radius)

    def find_selected_area(self, view, drag_start_screen_coor, drag_end_screen_coor):

        points_in_area = []

        trans = view.scene.transform

        for i in range(self.rotated_pos_array.shape[0]):

            # Translate the data coordinates into screen coordinates
            data_screen_coor = trans.map(self.rotated_pos_array[i])

            # Data point is inside the selected area
            if drag_start_screen_coor[0] <= data_screen_coor[0] <= drag_end_screen_coor[0] and \
                    drag_start_screen_coor[1] <= data_screen_coor[1] <= drag_end_screen_coor[1]:
                self.selected_points[i] = 1
                points_in_area.append(i)

        if len(points_in_area) > 0:
            #print("Point(s) in area indices:")
            #print(points_in_area)
            self.mark_selected_points(points_in_area)

    def mark_selected_points(self, selected_array):

        for i in range(len(selected_array)):
                self.nodes_outline_color_array[selected_array[i]] = self.selected_outline_color
                self.nodes_size_array[selected_array[i]] = self.selected_nodes_size

        self.scatter_plot.set_data(pos=self.rotated_pos_array, face_color=self.nodes_colors_array,
                                   size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                   edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)

    def unmark_selected_points(self, selected_array):

        for i in range(len(selected_array)):
            self.nodes_outline_color_array[selected_array[i]] = self.nodes_outline_default_color
            self.nodes_size_array[selected_array[i]] = self.nodes_size

        self.scatter_plot.set_data(pos=self.rotated_pos_array, face_color=self.nodes_colors_array,
                                   size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                   edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)

    def reset_selection(self, dim_num_view):

        for key in self.selected_points:
                self.nodes_outline_color_array[key] = self.nodes_outline_default_color
                self.nodes_size_array[key] = self.nodes_size

        self.update_view(dim_num_view)

        # Empty the selected_points dictionary
        self.selected_points = {}

    def start_dragging_rectangle(self, view, drag_start_screen_coor):
        trans = view.scene.transform
        drag_start_data_coor = trans.imap(drag_start_screen_coor)

        self.drag_rectangle.center = (drag_start_data_coor[0], drag_start_data_coor[1], 0)
        self.drag_rectangle.color = self.drag_rectangle_color
        self.drag_rectangle.border_color = 'black'
        self.drag_rectangle.height = 0.01
        self.drag_rectangle.width = 0.01
        self.drag_rectangle.parent = view.scene

    def update_dragging_rectangle(self, view, drag_start_screen_coor, drag_end_screen_coor):
        trans = view.scene.transform
        drag_start_data_coor = trans.imap(drag_start_screen_coor)
        drag_end_data_coor = trans.imap(drag_end_screen_coor)

        width = abs(drag_end_data_coor[0] - drag_start_data_coor[0])
        height = abs(drag_end_data_coor[1] - drag_start_data_coor[1])
        center_x_data_coor = drag_start_data_coor[0] + (width / 2)
        center_y_data_coor = drag_start_data_coor[1] - (height / 2)

        self.drag_rectangle.center = (center_x_data_coor, center_y_data_coor, 0)
        self.drag_rectangle.height = height
        self.drag_rectangle.width = width

    def remove_dragging_rectangle(self):
        self.drag_rectangle.parent = None






