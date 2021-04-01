import numpy as np
from vispy import app, scene, util, visuals
import clans.config as cfg
import clans.layouts.fruchterman_reingold as fr
import clans.data.sequences as seq
import clans.graphics.angles_calc as ac


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
        self.edges_color_scale = {1: (0.7, 0.7, 0.7, 0.9),
                                  2: (0.6, 0.6, 0.6, 0.9),
                                  3: (0.5, 0.5, 0.5, 0.9),
                                  4: (0.4, 0.4, 0.4, 0.9),
                                  5: (0.3, 0.3, 0.3, 0.9)}
        self.edges_width_scale = {1: 0.01,
                                  2: 0.01,
                                  3: 0.01,
                                  4: 0.01,
                                  5: 0.01}
        self.drag_rectangle_color = (0.3, 0.3, 0.3, 0.5)

        # Dictionaries for holding the selected points / groups
        self.selected_points = {}
        self.selected_groups = {}
        self.group_to_show = {}
        self.group_name_to_move = None

        # Arrays for holding coordinates / angles
        self.pos_array = []
        self.rotated_pos_array = []
        self.xy_vector = []
        self.yz_vector = []
        self.azimuth_angles = []
        self.elevation_angles = []
        self.affine_mtx = []
        self.inverse_affine_mtx = []

        # Initialize the camera parameters
        self.initial_azimuth = 0
        self.initial_elevation = 90
        self.center = (0, 0, 0)
        self.rotated_center = (0, 0, 0)
        view.camera = 'turntable'
        view.camera.elevation = self.initial_elevation
        view.camera.azimuth = self.initial_azimuth
        view.camera.fov = 0
        view.camera.center = self.center

        print("3D Camera initial parameters:")
        print(view.camera.get_state())

        # Create the scatter plot object (without data)
        self.scatter_plot = scene.visuals.Markers(parent=view.scene)
        self.scatter_plot.set_gl_state('translucent', blend=True, depth_test=True)
        self.scatter_plot.order = -1

        # Create line visual objects - one for each bin attraction-values bin (to create a gray-scale for the lines)
        # Because there is a problem to provide an array of line-colors, each line visual will present a different color
        self.lines = []
        j = 6
        for i in range(5):
            line = scene.visuals.Line()
            line.set_gl_state('translucent', blend=True, depth_test=True)
            line.order = j
            self.lines.append(line)
            j -= 1

        # Create a rectangle visual for mouse-dragging highlight
        self.drag_rectangle = scene.visuals.Rectangle(center=(0, 0, 0))
        self.drag_rectangle.set_gl_state('translucent', blend=True, depth_test=True)
        self.drag_rectangle.order = 0

        # Create a text visual object to present sequences names
        self.seq_text_visual = scene.visuals.Text(method='gpu', bold=True)
        self.seq_text_visual.set_gl_state('translucent', blend=True, depth_test=False)

        # Create a dict of text visuals to present all the groups names (separate visual to each group)
        self.groups_text_visual = {}

        self.axis = scene.visuals.XYZAxis(parent=view.scene)  # For debugging purposes

    # Set the plot data for the first time
    def init_data(self, view):

        # Initialise the coordinates array
        self.pos_array = fr.coordinates.copy()
        self.rotated_pos_array = self.pos_array.copy()
        if self.pos_array.shape[1] == 2:
            self.pos_array = np.column_stack((self.pos_array, cfg.sequences_array['z_coor']))
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
        elif 1000 < cfg.run_params['total_sequences_num'] <= 4000:
            self.nodes_size = 8
        else:
            self.nodes_size = 6
        self.selected_nodes_size = self.nodes_size + 5

        # Build the initial color arrays (for the nodes and their outline) and the nodes-size array
        for seq_index in range(cfg.run_params['total_sequences_num']):

            # Build the colors array of the nodes according to the groups information (if any)
            if cfg.sequences_array[seq_index]['in_group'] >= 0:
                group_index = cfg.sequences_array[seq_index]['in_group']
                if cfg.groups_list[group_index]['hide'] == '0':
                    self.nodes_colors_array[seq_index] = cfg.groups_list[group_index]['color_array']

            self.nodes_size_array[seq_index] = self.nodes_size
            self.nodes_outline_color_array[seq_index] = self.nodes_outline_default_color

        # Set the view-range of coordinates according to the data
        if cfg.run_params['dimensions_num_for_clustering'] == 2:
            self.set_range_turntable_camera(view, 2)
        else:
            self.set_range_turntable_camera(view, 3)

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

        # Build the text visuals of the group names
        for group_index in range(len(cfg.groups_list)):
            if cfg.groups_list[group_index]['hide'] == '0':
                self.group_to_show[group_index] = 1
        self.build_group_names_visual(view)

    # Update the nodes positions after calculation update or initialization
    def update_data(self, view, dim_num_view, set_range):

        # Update the coordinates array
        self.pos_array = fr.coordinates.copy()
        if self.pos_array.shape[1] == 2:
            self.pos_array = np.column_stack((self.pos_array, cfg.sequences_array['z_coor']))

        pos_array = self.pos_array.copy()
        self.rotated_pos_array = self.pos_array.copy()

        # Set the coor-range of the camera
        if set_range == 1:

            # Set the maximal range of the Turntable camera
            self.set_range_turntable_camera(view, dim_num_view)

        # View in 2D
        if dim_num_view == 2:

            # Zero the Z coordinate
            pos_array[:, 2] = 0

        self.scatter_plot.set_data(pos=pos_array, face_color=self.nodes_colors_array,
                                   size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                   edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)

        for i in range(5):
            line_color = self.edges_color_scale[i + 1]
            line_width = self.edges_width_scale[i + 1]
            self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
                                   connect=self.connections_by_bins[i])

        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.update_sequences_names(dim_num_view)
        else:
            self.update_sequences_names(3)

    def update_view(self, dim_num_view):

        if dim_num_view == 3:
            pos_array = self.pos_array.copy()
        else:
            pos_array = self.rotated_pos_array.copy()
            pos_array[:, 2] = 0  # Zero the Z-axis

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

        # Update the text visual of the sequences names with the correct positions
        self.update_sequences_names(dim_num_view)

    # Set a 3 dimensional view (accepts mode=data / view)
    def set_3d_view(self, view):
        print("Moved to 3D view")

        # Save the rotated coordinates as the normal ones from now on
        self.save_rotated_coordinates(view, 3)

        print("Camera parameters:")
        print(view.camera.get_state())

    def set_2d_view(self, view):

        print("Moved to 2D view")

        self.calculate_rotation(view)
        self.reset_rotation(view)
        self.set_rotated_center(view)

        # In case the clustering is done with 2D, save the rotated coordinates permanently in the sequences
        # main array (to continue the layout calculation from the same rotated angle)
        if cfg.run_params['dimensions_num_for_clustering'] == 2:
            self.save_rotated_coordinates(view, 2)

        self.update_view(2)
        self.reset_group_names_positions(view)

        print("Camera parameters:")
        print(view.camera.get_state())

    def save_rotated_coordinates(self, view, dim_num):
        seq.update_positions(self.rotated_pos_array.T)
        fr.init_variables()
        self.update_data(view, dim_num, 0)
        self.calculate_initial_angles()

    def set_2d_view_panzoom(self, view):

        print("Moved to 2D view")

        # Calculate the rotated coordinates array according to the rotation that was done in 3D (if was any)
        self.calculate_rotation(view)

        # In case the clustering is done with 2D, save the rotated coordinates permanently in the sequences main array
        # (to continue the layout calculation from the same rotated angle)
        if cfg.run_params['dimensions_num_for_clustering'] == 2:
            seq.update_positions(self.rotated_pos_array.T)
            fr.init_variables()

        # Turn the camera into 2D PanZoom camera
        view.camera = 'panzoom'
        view.camera.aspect = 1
        self.set_range_panzoom_camera(view, 'view')

        self.update_view(2)
        self.set_rotated_center(view)
        self.reset_group_names_positions(view)

    def set_selection_mode(self, view, dim_num_view):

        if dim_num_view == 2 and cfg.run_params['dimensions_num_for_clustering'] == 3:
            # Save the rotated coordinates as the normal ones from now on
            self.save_rotated_coordinates(view, 2)

        # Rotate the coordinates and bring the camera back to its initial position
        self.calculate_rotation(view)
        self.reset_rotation(view)
        self.update_view(2)
        self.set_rotated_center(view)

    def set_interactive_mode(self, view, dim_num_view):
        if dim_num_view == 3:
            self.set_3d_view(view)
        else:
            self.save_rotated_coordinates(view, 2)

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

        # Get the current 3D camera angles to extract the angles of the rotation made by the user (if any)
        azimuth_change = view.camera.azimuth - self.initial_azimuth
        azimuth_change_in_radians = np.radians(azimuth_change)
        elevation_change = view.camera.elevation - self.initial_elevation
        elevation_change_in_radians = np.radians(elevation_change)

        if azimuth_change != 0 or elevation_change != 0:
            print("Azimuth was changed in " + str(azimuth_change) + " degrees")
            print("Elevation was changed in " + str(elevation_change) + " degrees")
            print("The new azimuth is: " + str(view.camera.azimuth))
            print("The new elevation is: " + str(view.camera.elevation))

            # Correct the data coordinates (for display) according to the change in azimuth and/or elevation
            self.set_rotated_coordinates(azimuth_change_in_radians, elevation_change_in_radians)

        else:
            print("No change in Azimuth or Elevation")

        # Calculate the affine matrix and the inverse matrix between the two coordinate systems (original and rotated)
        self.calculate_affine_mtx()

    def set_rotated_coordinates(self, azimuth_change_in_radians, elevation_change_in_radians):

        #print("Coordinates before applying rotation changes (rotated_pos_array):")
        #print(self.rotated_pos_array[0])

        # Calculate the corrected coordinates after a movement in the XY plane (Azimuth)
        if azimuth_change_in_radians != 0:
            self.rotated_pos_array = ac.calcuate_positions_after_azimuth_change(self.rotated_pos_array,
                                     self.xy_vector, self.azimuth_angles, azimuth_change_in_radians)
            #print("New coordinates after applying azimuth change:")
            #print(self.rotated_pos_array[0])

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
            #print(self.rotated_pos_array[0])

    def calculate_affine_mtx(self):
        self.affine_mtx = util.transforms.affine_map(self.pos_array[:4, :], self.rotated_pos_array[:4, :])
        self.inverse_affine_mtx = util.transforms.affine_map(self.rotated_pos_array[:4, :], self.pos_array[:4, :])

    def show_connections(self, view):
        for i in range(5):
            self.lines[i].parent = view.scene

    # Update the connections plot after changes in P-value threshold or number of dimensions to view
    def update_connections(self, dim_num):

        pos_array = self.pos_array.copy()
        if dim_num == 2:
            pos_array[:, 2] = 0

        for i in range(5):
            line_color = self.edges_color_scale[i+1]
            line_width = self.edges_width_scale[i+1]
            self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
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

    def show_sequences_names(self, view):
        self.seq_text_visual.parent = view.scene

    def update_sequences_names(self, dim_num):
        text_list = []
        pos_list = []

        if dim_num == 3:
            pos_array = self.pos_array.copy()
        else:
            pos_array = self.rotated_pos_array.copy()
            pos_array[:, 2] = 0

        for key in self.selected_points:
            text_list.append('  '+cfg.sequences_array['seq_title'][key][1:])
            pos_list.append(tuple(pos_array[key]))

        # Update the text visual with the current selected sequences and their positions
        if len(pos_list) > 0:
            self.seq_text_visual.text = text_list
            self.seq_text_visual.pos = pos_list
            self.seq_text_visual.font_size = 6
            self.seq_text_visual.anchors = ['top', 'left']
            self.seq_text_visual.color = [0.0, 0.0, 0.0, 1.0]

        # No selected sequences => hide the text visual
        else:
            self.hide_sequences_names()

    def hide_sequences_names(self):
        self.seq_text_visual.parent = None

    def build_group_names_visual(self, view):
        trans = view.scene.transform
        upper_left_data_coor = trans.imap([50, 30, 0, 1])

        pos_x = upper_left_data_coor[0]
        pos_y = upper_left_data_coor[1]
        pos_z = 0

        ymin = np.amin(self.pos_array[:, 1])
        ymax = np.amax(self.pos_array[:, 1])
        interval = (ymax - ymin) / 28

        for group_index in self.group_to_show:
            text_vis = scene.visuals.Text(method='gpu', bold=True)
            text_vis.set_gl_state('opaque', blend=True, depth_test=False)
            text_vis.text = cfg.groups_list[group_index]['name']
            text_vis.pos = (pos_x, pos_y, pos_z)
            text_vis.font_size = 7
            text_vis.anchors = ['left', 'center']
            text_vis.color = cfg.groups_list[group_index]['color_array']
            self.groups_text_visual[group_index] = text_vis

            pos_y -= interval

    def show_group_names(self, view, mode):
        trans = view.scene.transform
        upper_left_data_coor = trans.imap([50, 30, 0, 1])

        pos_x = upper_left_data_coor[0]
        pos_y = upper_left_data_coor[1]
        pos_z = 0

        ymin = np.amin(self.pos_array[:, 1])
        ymax = np.amax(self.pos_array[:, 1])
        interval = (ymax - ymin) / 28

        # Show all group names
        if mode == 'all':
            # a loop over the groups
            for group_index in self.group_to_show:
                self.groups_text_visual[group_index].parent = view.scene

        # Mode is 'selected' => show only the selected group names
        else:
            # a loop over the groups
            for group_index in self.group_to_show:
                # If the group is selected => present it on the scene
                if group_index in self.selected_groups:
                    self.groups_text_visual[group_index].parent = view.scene
                else:
                    self.groups_text_visual[group_index].parent = None

    def reset_group_names_positions(self, view):

        trans = view.scene.transform
        upper_left_data_coor = trans.imap([50, 30, 0, 1])
        pos_x = upper_left_data_coor[0]
        pos_y = upper_left_data_coor[1]
        pos_z = 0

        pos_array = self.rotated_pos_array.copy()

        ymin = np.amin(pos_array[:, 1])
        ymax = np.amax(pos_array[:, 1])
        interval = (ymax - ymin) / 28

        for group_index in self.group_to_show:
            self.groups_text_visual[group_index].pos = (pos_x, pos_y, pos_z)
            pos_y -= interval

    def hide_group_names(self):
        # Remove all the group names from the scene
        for group_index in self.groups_text_visual:
            self.groups_text_visual[group_index].parent = None

    def find_selected_point(self, view, selection_type, clicked_screen_coor):

        # An array to hold the indices of the data points that are close enough to the clicked point
        points_in_radius = []
        groups_in_radius = {}
        deselect = 0

        # Define the radius (in pixels) around the clicked position to look for a data point(s)
        radius = self.nodes_size

        trans = view.scene.transform

        for seq_index in range(self.rotated_pos_array.shape[0]):

            # Translate the data coordinates into screen coordinates
            data_screen_coor = trans.map(self.rotated_pos_array[seq_index])
            data_screen_coor /= data_screen_coor[3]

            # Calculate the euclidean distances of all the points from the clicked point (in screen coor)
            distance_screen_coor = np.linalg.norm(data_screen_coor[:2] - clicked_screen_coor)

            # Found a data point in the radius of the clicked point
            if distance_screen_coor <= radius:

                # Select / deselect a data-point (sequence)
                if selection_type == 'sequences':
                    points_in_radius.append(seq_index)

                    # Deselect the data point
                    if seq_index in self.selected_points:
                        del self.selected_points[seq_index]
                        deselect = 1
                    # Select the data point
                    else:
                        self.selected_points[seq_index] = 1
                    print("Found matching point: Index = " + str(seq_index))
                    #print("Position in screen coor: " + str(data_screen_coor))
                    #print("Distance from clicked point: " + str(distance_screen_coor))

                # Select / deselect all the sequences belonging to the group of the selected data-point (if any)
                else:
                    if cfg.sequences_array[seq_index]['in_group'] >= 0:
                        group_index = cfg.sequences_array[seq_index]['in_group']
                        #print("Found matching group: Index = " + str(group_index))

                        # The first time we encounter this group
                        if group_index not in groups_in_radius:

                            points_in_radius = []

                            # A loop over all the sequences belonging to this group
                            for seqID in cfg.groups_list[group_index]['seqIDs']:
                                points_in_radius.append(seqID)

                                # Deselect the sequences
                                if group_index in self.selected_groups:
                                    del self.selected_points[seqID]
                                # Select the sequences
                                else:
                                    self.selected_points[seqID] = 1

                            # Deselect the group
                            if group_index in self.selected_groups:
                                del self.selected_groups[group_index]
                                # Unmark the sequences from the selected group
                                self.unmark_selected_points(points_in_radius)
                            # Select the group
                            else:
                                self.selected_groups[group_index] = 1
                                self.mark_selected_points(points_in_radius)

                            groups_in_radius[group_index] = 1

        if selection_type == 'sequences' and len(points_in_radius) > 0:
            #print("Selected point(s) indices:")
            #print(points_in_radius)

            # Points should be cleared from selection
            if deselect == 1:
                self.unmark_selected_points(points_in_radius)

            # Points should be added to selection
            else:
                self.mark_selected_points(points_in_radius)

            self.update_sequences_names(2)

    def find_selected_area(self, view, selection_type, drag_start_screen_coor, drag_end_screen_coor):

        points_in_area = []
        groups_in_area = {}

        trans = view.scene.transform

        for seq_index in range(self.rotated_pos_array.shape[0]):

            # Translate the data coordinates into screen coordinates
            data_screen_coor = trans.map(self.rotated_pos_array[seq_index])
            data_screen_coor /= data_screen_coor[3]


            # Data point is inside the selected area
            if drag_start_screen_coor[0] <= data_screen_coor[0] <= drag_end_screen_coor[0] and \
                    drag_start_screen_coor[1] <= data_screen_coor[1] <= drag_end_screen_coor[1]:

                # Sequences selection mode
                if selection_type == "sequences":
                    self.selected_points[seq_index] = 1
                    points_in_area.append(seq_index)

                # Groups selection mode
                else:
                    # Data point belongs to a group
                    if cfg.sequences_array[seq_index]['in_group'] >= 0:
                        group_index = cfg.sequences_array[seq_index]['in_group']
                        #print("Found matching group: Index = " + str(group_index))

                        # The first time we encounter this group
                        if group_index not in groups_in_area:
                            self.selected_groups[group_index] = 1

                            # A loop over all the sequences belonging to this group
                            for seqID in cfg.groups_list[group_index]['seqIDs']:
                                points_in_area.append(seqID)
                                self.selected_points[seqID] = 1

                            groups_in_area[group_index] = 1

        if len(points_in_area) > 0:
            #print("Point(s) in area indices:")
            #print(points_in_area)
            self.mark_selected_points(points_in_area)

            self.update_sequences_names(2)

    def mark_selected_points(self, selected_array):

        for i in range(len(selected_array)):
                self.nodes_outline_color_array[selected_array[i]] = self.selected_outline_color
                self.nodes_size_array[selected_array[i]] = self.selected_nodes_size

        self.update_view(2)

    def unmark_selected_points(self, selected_array):

        for i in range(len(selected_array)):
            self.nodes_outline_color_array[selected_array[i]] = self.nodes_outline_default_color
            self.nodes_size_array[selected_array[i]] = self.nodes_size

        self.update_view(2)

    def select_all(self, view, selection_type, dim_num):

        for seq_index in range(self.pos_array.shape[0]):
            self.selected_points[seq_index] = 1
            self.nodes_outline_color_array[seq_index] = self.selected_outline_color
            self.nodes_size_array[seq_index] = self.selected_nodes_size

        if selection_type == 'groups':
            for group_index in self.group_to_show:
                self.selected_groups[group_index] = 1

        self.update_view(dim_num)

        self.update_sequences_names(dim_num)

    def reset_selection(self, dim_num_view):

        for key in self.selected_points:
            self.nodes_outline_color_array[key] = self.nodes_outline_default_color
            self.nodes_size_array[key] = self.nodes_size

        # Empty the selected_points and the selected_groups dictionaries
        self.selected_points = {}
        self.selected_groups = {}

        self.hide_sequences_names()
        self.update_view(dim_num_view)

    def start_dragging_rectangle(self, view, drag_start_screen_coor):
        trans = view.scene.transform
        drag_start_data_coor = trans.imap(drag_start_screen_coor)
        if view.camera.fov != 0:
            drag_start_data_coor /= drag_start_data_coor[3]
        print("drag_start_data_coor:")
        print(drag_start_data_coor)

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
        if view.camera.fov != 0:
            drag_start_data_coor /= drag_start_data_coor[3]
            drag_end_data_coor /= drag_end_data_coor[3]

        width = abs(drag_end_data_coor[0] - drag_start_data_coor[0])
        height = abs(drag_end_data_coor[1] - drag_start_data_coor[1])
        center_x_data_coor = drag_start_data_coor[0] + (width / 2)
        center_y_data_coor = drag_start_data_coor[1] - (height / 2)

        self.drag_rectangle.center = (center_x_data_coor, center_y_data_coor, 0)
        self.drag_rectangle.height = height
        self.drag_rectangle.width = width

    def remove_dragging_rectangle(self):
        self.drag_rectangle.parent = None

    def move_selected_points(self, view, dim_num, start_move_screen_coor, end_move_screen_coor):
        trans = view.scene.transform
        start_move_data_coor = trans.imap(start_move_screen_coor)
        end_move_data_coor = trans.imap(end_move_screen_coor)
        if view.camera.fov != 0:
            start_move_data_coor /= start_move_data_coor[3]
            end_move_data_coor /= end_move_data_coor[3]
        distance_vec_data_coor = end_move_data_coor - start_move_data_coor

        #if dim_num == 3 or cfg.run_params['dimensions_num_for_clustering'] == 2:
        if dim_num == 3:
            for index in self.selected_points:
                self.pos_array[index, :] += distance_vec_data_coor[:3]
            self.update_view(3)
        else:
            for index in self.selected_points:
                self.rotated_pos_array[index, :] += distance_vec_data_coor[:3]
            self.update_view(2)
        #print("rotated_pos_array:")
        #print(self.rotated_pos_array)

    def update_moved_positions(self, dim_num):

        #if dim_num == 2 and cfg.run_params['dimensions_num_for_clustering'] == 3:
        if dim_num == 2:
            for index in self.selected_points:
                rotated_array = np.append(self.rotated_pos_array[index], 1)
                inverse_array = np.dot(self.inverse_affine_mtx, rotated_array)
                self.pos_array[index] = inverse_array[:3]

        seq.update_positions(self.pos_array.T)
        fr.init_variables()

        # Calculate the angles of each point for future use when having rotations
        self.calculate_initial_angles()

    def find_group_name_to_move(self, view, clicked_screen_coor):

        permitted_dist_x = 100
        permitted_dist_y = 3
        found_visual = 0

        trans = view.scene.transform

        for group_index in self.groups_text_visual:

            group_visual = self.groups_text_visual[group_index]

            # Translate the data coordinates into screen coordinates
            group_pos_screen_coor = trans.map(group_visual.pos)

            dist_x = clicked_screen_coor[0] - group_pos_screen_coor[0][0]
            dist_y = abs(clicked_screen_coor[1] - group_pos_screen_coor[0][1])

            if 0 <= dist_x <= permitted_dist_x and dist_y <= permitted_dist_y:
                found_visual = 1
                self.group_name_to_move = group_index
                group_visual.font_size = 9
                print("Found group name visual. Index=" + str(group_index))
                print("Clicked coor: " + str(clicked_screen_coor))
                print("Group name coor: " + str(group_pos_screen_coor[0]))
                break

    def move_group_name(self, view, start_move_screen_coor, end_move_screen_coor):
        # There is a selected group name to move
        if self.group_name_to_move is not None:
            trans = view.scene.transform
            end_move_data_coor = trans.imap(end_move_screen_coor)
            new_pos = (end_move_data_coor[0], end_move_data_coor[1], 0)
            self.groups_text_visual[self.group_name_to_move].pos = new_pos
            self.groups_text_visual[self.group_name_to_move].font_size = 7

    def finish_group_name_move(self):
        if self.group_name_to_move is not None:
            self.group_name_to_move = None

    def set_range_panzoom_camera(self, view):
        pos_array = self.pos_array.copy()

        xmin = np.amin(pos_array[:, 0])
        xmax = np.amax(pos_array[:, 0])
        ymin = np.amin(pos_array[:, 1])
        ymax = np.amax(pos_array[:, 1])
        view.camera.set_range(x=(xmin, xmax), y=(ymin, ymax), z=None, margin=0.1)

        #print("Camera coordinates range:")
        #print(xmin, xmax, ymin, ymax)

    def set_range_turntable_camera(self, view, dim_num_view):
        pos_array = self.pos_array.copy()

        xmin = np.amin(pos_array[:, 0])
        xmax = np.amax(pos_array[:, 0])
        ymin = np.amin(pos_array[:, 1])
        ymax = np.amax(pos_array[:, 1])

        if dim_num_view == 2:
            view.camera.set_range(x=(xmin, xmax), y=(ymin, ymax), z=None, margin=0.2)

        else:
            zmin = np.amin(pos_array[:, 2])
            zmax = np.amax(pos_array[:, 2])
            view.camera.set_range(x=(xmin, xmax), y=(ymin, ymax), z=(zmin, zmax), margin=0.1)

        #print("Camera coordinates range:")
        #print(xmin, xmax, ymin, ymax, zmin, zmax)

    def reset_rotation(self, view):
        view.camera.elevation = self.initial_elevation
        view.camera.azimuth = self.initial_azimuth

        print("Turntable camera was reset to original Azimuth and Elevation. Parameters:")
        print(view.camera.get_state())

    def reset_turntable_camera(self, view):
        #view.camera = 'turntable'
        view.camera.elevation = self.initial_elevation
        view.camera.azimuth = self.initial_azimuth
        view.camera.center = (0.0, 0.0, 0.0)

        print("Turntable camera was reset to original Azimuth and Elevation. Parameters:")
        print(view.camera.get_state())

    def set_rotated_center(self, view):
        self.center = view.camera.center

        center_array = np.append(np.array(self.center), 1)
        rotated_center_array = np.dot(self.affine_mtx, center_array)
        print("Rotated center array:")
        print(rotated_center_array)

        self.rotated_center = tuple(rotated_center_array[:3])

        # Set the new rotated center in the Turntable camera
        view.camera.center = self.rotated_center






