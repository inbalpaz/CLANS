import re
import numpy as np
from vispy import app, scene, util
import clans.config as cfg
import clans.data.sequences as seq
import clans.data.sequence_pairs as sp
import clans.graphics.angles_calc as ac


class Network3D:

    def __init__(self, view):
        self.app = app.use_app('pyqt5')

        self.view = view

        self.nodes_colors_array = []
        self.nodes_colors_array_by_param = []
        self.nodes_size_array = []
        self.selected_nodes_colors_array = []
        self.selected_nodes_colors_array_by_param = []
        self.selected_nodes_size_array = []
        self.nodes_outline_color_array = []
        self.nodes_outline_width = 0.5
        self.nodes_size_large = 10
        self.nodes_size_medium = 8
        self.nodes_size_small = 6
        self.nodes_size_tiny = 4
        self.nodes_size = self.nodes_size_medium
        self.text_size_large = 12
        self.text_size_medium = 10
        self.text_size_small = 8
        self.text_size = self.text_size_medium
        self.selected_nodes_size = self.nodes_size + 5
        self.highlighted_nodes_size = self.selected_nodes_size + 5
        self.nodes_symbol = 'disc'
        self.nodes_default_color = [0.0, 0.0, 0.0, 1.0]
        self.nodes_highlight_color = [0.0, 1.0, 1.0, 1.0]  # Turquoise
        self.nodes_outline_default_color = [0.0, 0.0, 0.0, 1.0]
        self.selected_outline_color = [1.0, 0.0, 1.0, 1.0]
        self.highlighted_outline_color = [1.0, 0.0, 1.0, 1.0]
        self.att_values_bins = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        self.edges_color_scale = {1: (0.8, 0.8, 0.8, 1.0),
                                  2: (0.6, 0.6, 0.6, 1.0),
                                  3: (0.4, 0.4, 0.4, 1.0),
                                  4: (0.2, 0.2, 0.2, 1.0),
                                  5: (0.0, 0.0, 0.0, 1.0)}
        self.edges_width_scale = {1: 0.01,
                                  2: 0.01,
                                  3: 0.01,
                                  4: 0.01,
                                  5: 0.01}
        self.drag_rectangle_color = (0.3, 0.3, 0.3, 0.5)

        # Dictionaries for holding the selected points / groups
        self.selected_points = {}
        self.selected_groups = {}
        self.groups_to_show = {}
        self.ordered_groups_to_show = []
        self.group_name_to_move = None
        self.points_to_move = {}

        self.is_subset_mode = 0

        # Arrays for holding coordinates / angles
        self.pos_array = []  # To hold the positions of the whole dataset
        self.rotated_pos_array = []  # To hold the rotated-positions of the whole dataset (for 2D view)
        self.selected_pos_array = []  # To hold the positions of the selected subset
        self.selected_rotated_pos_array = []  # To hold the rotated-positions of the selected subset
        self.connections_by_bins = []  # To hold the connected-pairs divided into bins
        self.selected_connections_by_bins = []  # To hold the connected-pairs among the selected subset, divided into bins
        self.xy_vector = []
        self.yz_vector = []
        self.azimuth_angles = []
        self.elevation_angles = []
        self.affine_mtx = []
        self.inverse_affine_mtx = []
        self.selected_xy_vector = []
        self.selected_yz_vector = []
        self.selected_azimuth_angles = []
        self.selected_elevation_angles = []
        self.selected_affine_mtx = []
        self.selected_inverse_affine_mtx = []

        # Initialize the camera parameters
        self.initial_azimuth = 0
        self.initial_elevation = 90
        self.last_azimuth = self.initial_azimuth
        self.last_elevation = self.initial_elevation
        self.center = (0, 0, 0)
        self.rotated_center = (0, 0, 0)
        self.view.camera = 'turntable'
        self.view.camera.elevation = self.initial_elevation
        self.view.camera.azimuth = self.initial_azimuth
        self.view.camera.fov = 0
        self.view.camera.center = self.center

        #print("3D Camera initial parameters:")
        #print(self.view.camera.get_state())

        # Create the scatter plot object (without data)
        self.scatter_plot = scene.visuals.Markers(parent=self.view.scene)
        self.scatter_plot.set_gl_state('translucent', blend=True, depth_test=True)
        self.scatter_plot.order = -1
        self.scatter_plot.interactive = True

        # Create a dict to hold the scatter_by_groups visuals (in 2D presentation,
        # display the different groups as separate visuals, to enable control of the order in which they are displayed)
        self.scatter_by_groups = {}
        self.members_array_by_groups = {}
        self.pos_array_by_groups = {}
        self.size_array_by_groups = {}
        self.nodes_outline_color_array_by_groups = {}

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

        # Create a text visual object to present sequences numbers
        self.seq_number_visual = scene.visuals.Text(method='gpu', bold=True)
        self.seq_number_visual.set_gl_state('translucent', blend=True, depth_test=False)

        # Create a dict of text visuals to present all the groups names (separate visual to each group)
        self.groups_text_visual = {}

        # Create a dict of text visuals that the user can add to the scene
        #self.general_text_visual = {}

    # Set the plot data for the first time
    def init_data(self, fr_object):

        # Initialise the coordinates array
        self.pos_array = fr_object.coordinates.copy()
        self.rotated_pos_array = self.pos_array.copy()
        if self.pos_array.shape[1] == 2:
            self.pos_array = np.column_stack((self.pos_array, cfg.sequences_array['z_coor']))

        # Calculate and save the initial azimuth and elevation angles of all the points
        self.calculate_initial_angles()

        self.nodes_colors_array = np.zeros((cfg.run_params['total_sequences_num'], 4), dtype=np.float32)
        self.nodes_colors_array[:, ] = self.nodes_default_color
        self.nodes_colors_array_by_param = self.nodes_colors_array.copy()
        self.nodes_outline_color_array = np.zeros((cfg.run_params['total_sequences_num'], 4), dtype=np.float32)
        self.nodes_outline_color_array[:, ] = self.nodes_outline_default_color

        # Define the size of the dots according to the data size
        if cfg.run_params['total_sequences_num'] <= 1000:
            self.nodes_size = self.nodes_size_large
        elif 1000 < cfg.run_params['total_sequences_num'] <= 4000:
            self.nodes_size = self.nodes_size_medium
        elif 4000 < cfg.run_params['total_sequences_num'] <= 10000:
            self.nodes_size = self.nodes_size_small
        else:
            self.nodes_size = self.nodes_size_tiny
        self.selected_nodes_size = self.nodes_size + 5

        self.nodes_size_array = np.full((cfg.run_params['total_sequences_num']), self.nodes_size, dtype=np.int8)

        # If the input file contained groups
        if len(cfg.groups_dict['input_file']) > 0:

            # Build a dictionary of the groups that should be displayed
            for group_ID in cfg.groups_dict['input_file']:
                self.groups_to_show[group_ID] = cfg.groups_dict['input_file'][group_ID]['order']
            self.ordered_groups_to_show = sorted(self.groups_to_show, key=self.groups_to_show.get)

            # Build the text visuals of the group names
            self.build_group_names_visual('input_file')

            for seq_index in range(cfg.run_params['total_sequences_num']):

                # Update the colors and size of the nodes that belongs to a group according to the group's information
                if cfg.sequences_in_groups['input_file'][seq_index] > -1:
                    group_ID = cfg.sequences_in_groups['input_file'][seq_index]
                    self.nodes_colors_array[seq_index] = cfg.groups_dict['input_file'][group_ID]['color_array']
                    self.nodes_size_array[seq_index] = cfg.groups_dict['input_file'][group_ID]['size']

            self.build_scatter_by_groups('input_file')

        # No groups in the input -> initiate the 'manual' group-by
        else:
            self.build_scatter_by_groups('manual')

        # Set the view-range of coordinates according to the data
        if cfg.run_params['dimensions_num_for_clustering'] == 2:
            self.set_range_turntable_camera(2)
        else:
            self.set_range_turntable_camera(3)

        # Display the nodes
        self.scatter_plot.set_data(pos=self.pos_array, face_color=self.nodes_colors_array,
                                   size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                   edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)
        self.scatter_plot.parent = self.view.scene

        # Create the different bins of connections
        self.create_connections_by_bins()

        # Set the data for the connecting lines (without displaying them) -
        for i in range(5):
            line_color = self.edges_color_scale[i + 1]
            line_width = self.edges_width_scale[i + 1]
            self.lines[i].set_data(pos=self.pos_array, color=line_color, width=line_width,
                                   connect=self.connections_by_bins[i])

    # Initialize all main variables and clear the canvas to enable loading a new file
    def reset_data(self):

        # Remove al the visuals from the scene
        self.scatter_plot.parent = None
        self.seq_text_visual.parent = None
        self.seq_number_visual.parent = None
        self.hide_scatter_by_groups()
        self.hide_connections()
        self.hide_group_names()
        self.reset_rotation()

        self.pos_array = []
        self.rotated_pos_array = []
        self.selected_pos_array = []
        self.selected_rotated_pos_array = []
        self.connections_by_bins = []
        self.selected_connections_by_bins = []
        self.xy_vector = []
        self.yz_vector = []
        self.azimuth_angles = []
        self.elevation_angles = []
        self.affine_mtx = []
        self.inverse_affine_mtx = []
        self.selected_xy_vector = []
        self.selected_yz_vector = []
        self.selected_azimuth_angles = []
        self.selected_elevation_angles = []
        self.selected_affine_mtx = []
        self.selected_inverse_affine_mtx = []
        self.nodes_colors_array = []
        self.nodes_colors_array_by_param = []
        self.nodes_size_array = []
        self.selected_nodes_colors_array = []
        self.selected_nodes_colors_array_by_param = []
        self.selected_nodes_size_array = []
        self.nodes_outline_color_array = []
        self.selected_points = {}
        self.selected_groups = {}
        self.groups_to_show = {}
        self.ordered_groups_to_show = []
        self.group_name_to_move = None
        self.is_subset_mode = 0
        self.scatter_by_groups = {}
        self.members_array_by_groups = {}
        self.pos_array_by_groups = {}
        self.size_array_by_groups = {}
        self.nodes_outline_color_array_by_groups = {}
        self.nodes_default_color = [0.0, 0.0, 0.0, 1.0]

    def set_defaults(self, nodes_size, nodes_color, dim_num, color_by, group_by):
        self.nodes_size = int(nodes_size)
        self.nodes_default_color = nodes_color

        for seq_index in range(cfg.run_params['total_sequences_num']):
            if cfg.sequences_in_groups[group_by][seq_index] == -1:
                self.nodes_colors_array[seq_index] = self.nodes_default_color
                self.nodes_size_array[seq_index] = self.nodes_size

        self.update_view(dim_num, color_by, group_by)

    # Update the nodes positions after calculation update or initialization
    def update_data(self, dim_num_view, fr_object, set_range, color_by, group_by):

        # Full-data mode
        if self.is_subset_mode == 0:
            # Update the coordinates array
            self.pos_array = fr_object.coordinates.copy()
            if self.pos_array.shape[1] == 2:
                self.pos_array = np.column_stack((self.pos_array, cfg.sequences_array['z_coor']))

            self.rotated_pos_array = self.pos_array.copy()
            pos_array = self.pos_array.copy()

            # View in 2D
            if dim_num_view == 2:
                # Zero the Z coordinate
                pos_array[:, 2] = 0

            if color_by == 'groups':
                nodes_color_array = self.nodes_colors_array
            else:
                nodes_color_array = self.nodes_colors_array_by_param

            # Update the scatter-plot
            self.scatter_plot.set_data(pos=pos_array, face_color=nodes_color_array,
                                       size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                       edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)

            # In 2D view, put the lines at the back of the scatter plot (since the ordering is not enough)
            if dim_num_view == 2:
                pos_array[:, 2] = -1

            # Update the connecting lines
            for i in range(5):
                line_color = self.edges_color_scale[i + 1]
                line_width = self.edges_width_scale[i + 1]
                self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
                                       connect=self.connections_by_bins[i])

        # Subset mode
        else:
            # Update the coordinates array
            self.selected_pos_array = fr_object.coordinates[cfg.sequences_array['in_subset']]
            if self.selected_pos_array.shape[1] == 2:
                z_coor_subset = cfg.sequences_array['z_coor_subset']
                self.selected_pos_array = np.column_stack((self.selected_pos_array,
                                                           z_coor_subset[cfg.sequences_array['in_subset']]))

            self.selected_rotated_pos_array = self.selected_pos_array.copy()
            selected_pos_array = self.selected_pos_array.copy()

            # View in 2D
            if dim_num_view == 2:
                # Zero the Z coordinate
                selected_pos_array[:, 2] = 0

            if color_by == 'groups':
                selected_nodes_color_array = self.selected_nodes_colors_array
            else:
                selected_nodes_color_array = self.selected_nodes_colors_array_by_param

            # Display the scatter-plot for the subset
            self.scatter_plot.set_data(pos=selected_pos_array, face_color=selected_nodes_color_array,
                                       size=self.selected_nodes_size_array, edge_width=self.nodes_outline_width,
                                       edge_color=self.nodes_outline_default_color, symbol=self.nodes_symbol)

            # In 2D view, put the lines at the back of the scatter plot (since the ordering is not enough)
            if dim_num_view == 2:
                selected_pos_array[:, 2] = -1

            # Update the connecting lines
            for i in range(5):
                line_color = self.edges_color_scale[i + 1]
                line_width = self.edges_width_scale[i + 1]
                self.lines[i].set_data(pos=selected_pos_array, color=line_color, width=line_width,
                                       connect=self.selected_connections_by_bins[i])

        # Set the coor-range of the camera
        if set_range == 1:

            # Set the maximal range of the Turntable camera
            self.set_range_turntable_camera(dim_num_view)

        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.update_sequences_names(dim_num_view)
            self.update_sequences_numbers(dim_num_view)
        else:
            self.update_sequences_names(3)
            self.update_sequences_numbers(3)

    def update_view(self, dim_num_view, color_by, group_by):

        # Full-data mode
        if self.is_subset_mode == 0:
            if dim_num_view == 3:
                pos_array = self.pos_array.copy()

            else:
                pos_array = self.rotated_pos_array.copy()
                pos_array[:, 2] = 0  # Zero the Z-axis

            if color_by == 'groups':
                nodes_color_array = self.nodes_colors_array
            else:
                nodes_color_array = self.nodes_colors_array_by_param

            # Update the nodes with the updated rotation
            self.scatter_plot.set_data(pos=pos_array, face_color=nodes_color_array,
                                       size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                       edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)

            # In 2D view, put the lines at the back of the scatter plot (since the ordering is not enough)
            if dim_num_view == 2:
                pos_array[:, 2] = -1

            # Update the lines with the updated rotation
            for i in range(5):
                line_color = self.edges_color_scale[i + 1]
                line_width = self.edges_width_scale[i + 1]
                self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
                                       connect=self.connections_by_bins[i])

        # Subset mode
        else:
            if dim_num_view == 3:
                pos_array = self.selected_pos_array.copy()

            else:
                pos_array = self.selected_rotated_pos_array.copy()
                pos_array[:, 2] = 0  # Zero the Z-axis

            if color_by == 'groups':
                selected_nodes_color_array = self.selected_nodes_colors_array
            else:
                selected_nodes_color_array = self.selected_nodes_colors_array_by_param

            # Display the scatter-plot for the subset
            self.scatter_plot.set_data(pos=pos_array, face_color=selected_nodes_color_array,
                                       size=self.selected_nodes_size_array, edge_width=self.nodes_outline_width,
                                       edge_color=self.nodes_outline_default_color, symbol=self.nodes_symbol)

            # In 2D view, put the lines at the back of the scatter plot (since the ordering is not enough)
            if dim_num_view == 2:
                pos_array[:, 2] = -1

            # Update the connecting lines
            for i in range(5):
                line_color = self.edges_color_scale[i + 1]
                line_width = self.edges_width_scale[i + 1]
                self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
                                       connect=self.selected_connections_by_bins[i])

        # Update the text visual of the sequences names with the correct positions
        self.update_sequences_names(dim_num_view)
        self.update_sequences_numbers(dim_num_view)

    # Set a 3 dimensional view
    def set_3d_view(self, fr_object, color_by, group_by):
        print("Moved to 3D view")

        # Save the rotated coordinates as the normal ones from now on
        self.save_rotated_coordinates(3, fr_object, color_by, group_by)

        self.hide_scatter_by_groups()
        self.scatter_plot.parent = self.view.scene

        #print("Camera parameters:")
        #print(self.view.camera.get_state())

    def update_3d_view(self, color_by, group_by):

        # Full-data mode
        if self.is_subset_mode == 0:

            if color_by == 'groups':
                nodes_color_array = self.nodes_colors_array
            else:
                nodes_color_array = self.nodes_colors_array_by_param

            # Update the nodes with the updated rotation
            self.scatter_plot.set_data(pos=self.pos_array, face_color=nodes_color_array,
                                       size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                       edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)

            # Update the lines with the updated rotation
            for i in range(5):
                line_color = self.edges_color_scale[i + 1]
                line_width = self.edges_width_scale[i + 1]
                self.lines[i].set_data(pos=self.pos_array, color=line_color, width=line_width,
                                       connect=self.connections_by_bins[i])
        # Subset mode
        else:

            if color_by == 'groups':
                selected_nodes_color_array = self.selected_nodes_colors_array
            else:
                selected_nodes_color_array = self.selected_nodes_colors_array_by_param

            # Display the scatter-plot for the subset
            self.scatter_plot.set_data(pos=self.selected_pos_array, face_color=selected_nodes_color_array,
                                       size=self.selected_nodes_size_array, edge_width=self.nodes_outline_width,
                                       edge_color=self.nodes_outline_default_color, symbol=self.nodes_symbol)

            # Set the data for the connecting lines (without displaying them) -
            for i in range(5):
                line_color = self.edges_color_scale[i + 1]
                line_width = self.edges_width_scale[i + 1]
                self.lines[i].set_data(pos=self.selected_pos_array, color=line_color, width=line_width,
                                       connect=self.selected_connections_by_bins[i])

        # Update the text visual of the sequences names with the correct positions
        self.update_sequences_names(3)
        self.update_sequences_numbers(3)

    def set_2d_view(self, z_index_mode, fr_object, color_by, group_by):

        print("Moved to 2D view")

        self.calculate_rotation()
        self.reset_rotation()
        self.set_rotated_center()

        # In case the clustering is done with 2D, save the rotated coordinates permanently in the sequences
        # main array (to continue the layout calculation from the same rotated angle)
        if cfg.run_params['dimensions_num_for_clustering'] == 2:
            self.save_rotated_coordinates(2, fr_object, color_by, group_by)

        self.update_2d_view(z_index_mode, color_by, group_by)
        self.reset_group_names_positions(group_by)

        #print("Camera parameters:")
        #print(view.camera.get_state())

    def update_2d_view(self, z_index_mode, color_by, group_by):

        # Full-data mode
        if self.is_subset_mode == 0:
            pos_array = self.rotated_pos_array.copy()
            pos_array[:, 2] = 0  # Zero the Z-axis

            if color_by == 'groups':
                nodes_color_array = self.nodes_colors_array
            else:
                nodes_color_array = self.nodes_colors_array_by_param

            # Update the nodes with the updated rotation
            # One scatter-plot visual - no control of the Z-indexing
            if z_index_mode == "auto" or color_by == 'param':
                self.scatter_plot.set_data(pos=pos_array, face_color=nodes_color_array,
                                           size=self.nodes_size_array, edge_width=self.nodes_outline_width,
                                           edge_color=self.nodes_outline_color_array, symbol=self.nodes_symbol)
                self.hide_scatter_by_groups()
                self.scatter_plot.parent = self.view.scene

                # Update the lines with the updated rotation. Set the correct order
                pos_array[:, 2] = -1  # Put the lines at the back of the scatter plot (since the ordering is not enough)
                order = 6
                for i in range(5):
                    line_color = self.edges_color_scale[i + 1]
                    line_width = self.edges_width_scale[i + 1]
                    self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
                                           connect=self.connections_by_bins[i])
                    self.lines[i].order = order
                    order -= 1

                self.drag_rectangle.order = 0

            # Display separate scatter-plot visual for each group
            # to enable Z-indexing the nodes according to the groups order
            else:
                self.scatter_plot.parent = None
                self.show_scatter_by_groups(group_by)

                # Update the lines with the updated rotation. Set the correct order
                pos_array[:, 2] = -1  # Put the lines at the back of the scatter plot (since the ordering is not enough)
                order = len(self.groups_to_show) + 6
                for i in range(5):
                    line_color = self.edges_color_scale[i + 1]
                    line_width = self.edges_width_scale[i + 1]
                    self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
                                           connect=self.connections_by_bins[i])
                    self.lines[i].order = order
                    order -= 1

                self.drag_rectangle.order = len(self.groups_to_show)

        # Subset mode
        else:
            pos_array = self.selected_rotated_pos_array.copy()
            pos_array[:, 2] = 0  # Zero the Z-axis

            if color_by == 'groups':
                selected_nodes_color_array = self.selected_nodes_colors_array
            else:
                selected_nodes_color_array = self.selected_nodes_colors_array_by_param

            # Display the scatter-plot for the subset
            self.scatter_plot.set_data(pos=pos_array, face_color=selected_nodes_color_array,
                                       size=self.selected_nodes_size_array, edge_width=self.nodes_outline_width,
                                       edge_color=self.nodes_outline_default_color, symbol=self.nodes_symbol)
            self.hide_scatter_by_groups()
            self.scatter_plot.parent = self.view.scene

            # Update the connecting lines
            pos_array[:, 2] = -1  # Put the lines at the back of the scatter plot (since the ordering is not enough)
            order = 6
            for i in range(5):
                line_color = self.edges_color_scale[i + 1]
                line_width = self.edges_width_scale[i + 1]
                self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
                                       connect=self.selected_connections_by_bins[i])
                self.lines[i].order = order
                order -= 1

            self.drag_rectangle.order = 0

        # Update the text visual of the sequences names with the correct positions
        self.update_sequences_names(2)
        self.update_sequences_numbers(2)

    def set_subset_view(self, dim_num, color_by, group_by):
        self.is_subset_mode = 1

        subset_size = len(self.selected_points)

        # Build the selected positions (and rotated positions) arrays
        self.selected_pos_array = np.zeros((subset_size, 3), dtype=np.float32)
        self.selected_rotated_pos_array = np.zeros((subset_size, 3), dtype=np.float32)
        self.selected_nodes_colors_array = np.zeros((subset_size, 4), dtype=np.float32)
        self.selected_nodes_colors_array_by_param = np.zeros((subset_size, 4), dtype=np.float32)
        self.selected_nodes_size_array = np.zeros(subset_size, dtype=np.float32)

        i = 0
        for seq_index in sorted(self.selected_points):
            self.selected_pos_array[i] = self.pos_array[seq_index]
            self.selected_rotated_pos_array[i] = self.rotated_pos_array[seq_index]
            self.selected_nodes_colors_array[i] = self.nodes_colors_array[seq_index]
            self.selected_nodes_colors_array_by_param[i] = self.nodes_colors_array_by_param[seq_index]
            self.selected_nodes_size_array[i] = self.nodes_size_array[seq_index] - 5
            i += 1

        # Create a list of connections between the subset sequences only
        sp.define_connected_sequences_list_subset()
        # Divide the connections into 5 bins
        self.create_connections_by_bins_subset()

        # Calculate the initial azimuth and elevation angles of the points in the subset (for future rotation)
        if dim_num == 3:
            self.calculate_initial_angles()

        self.update_view(dim_num, color_by, group_by)

    def set_full_view(self, dim_num, color_by, group_by):
        self.is_subset_mode = 0

        self.set_range_turntable_camera(dim_num)

        self.update_view(dim_num, color_by, group_by)

    def save_rotated_coordinates(self, dim_num, fr_object, color_by, group_by):

        # Full data mode
        if self.is_subset_mode == 0:
            seq.update_positions(self.rotated_pos_array.T, 'full')

            fr_object.init_coordinates(cfg.sequences_array['x_coor'], cfg.sequences_array['y_coor'],
                                        cfg.sequences_array['z_coor'])

            self.pos_array = self.rotated_pos_array.copy()

        # Subset mode
        else:
            seq.update_positions_subset(self.selected_rotated_pos_array, self.selected_points)

            fr_object.init_coordinates(cfg.sequences_array['x_coor_subset'], cfg.sequences_array['y_coor_subset'],
                                        cfg.sequences_array['z_coor_subset'])

            self.selected_pos_array = self.selected_rotated_pos_array.copy()

        self.update_view(dim_num, color_by, group_by)
        self.calculate_initial_angles()

    def set_selection_mode(self, dim_num_view, z_index_mode, fr_object, color_by, group_by):

        if dim_num_view == 2 and cfg.run_params['dimensions_num_for_clustering'] == 3:
            # Save the rotated coordinates as the normal ones from now on
            self.save_rotated_coordinates(2, fr_object, color_by, group_by)

        # Rotate the coordinates and bring the camera back to its initial position
        self.calculate_rotation()
        self.reset_rotation()
        self.set_rotated_center()

        self.update_2d_view(z_index_mode, color_by, group_by)

    def set_interactive_mode(self, dim_num_view, fr_object, color_by, group_by):
        if dim_num_view == 3:
            self.set_3d_view(fr_object, color_by, group_by)
        else:
            self.save_rotated_coordinates(2, fr_object, color_by, group_by)

    def calculate_initial_angles(self):

        #print("Calculating the initial angles for rotation purposes")
        #print("Initial Coordinates:")
        #print(self.pos_array)

        # Full data mode
        if self.is_subset_mode == 0:

            # Calculate the distance of the point from the origin on the XY and YZ planes
            self.xy_vector = np.sqrt(self.pos_array[:, 0] ** 2 + self.pos_array[:, 1] ** 2)
            self.yz_vector = np.sqrt(self.pos_array[:, 1] ** 2 + self.pos_array[:, 2] ** 2)

            # Calculate the initial azimuth angles (on XY plane, relative to X) and elevation angles
            # (on YZ plane, relative to Y) for all the points
            self.azimuth_angles, self.elevation_angles = ac.calculate_azimuth_elevation(self.pos_array)

        # Subset mode
        else:
            # Calculate the distance of the point from the origin on the XY and YZ planes
            self.selected_xy_vector = np.sqrt(self.selected_pos_array[:, 0] ** 2 + self.selected_pos_array[:, 1] ** 2)
            self.selected_yz_vector = np.sqrt(self.selected_pos_array[:, 1] ** 2 + self.selected_pos_array[:, 2] ** 2)

            # Calculate the initial azimuth angles (on XY plane, relative to X) and elevation angles
            # (on YZ plane, relative to Y) for all the points
            self.selected_azimuth_angles, self.selected_elevation_angles = ac.calculate_azimuth_elevation(self.selected_pos_array)

    def calculate_rotation(self):

        # Full data mode
        if self.is_subset_mode == 0:
            self.rotated_pos_array = self.pos_array.copy()
        # Subset mode
        else:
            self.selected_rotated_pos_array = self.selected_pos_array.copy()

        # Get the current 3D camera angles to extract the angles of the rotation made by the user (if any)
        self.last_azimuth = self.view.camera.azimuth
        azimuth_change = self.last_azimuth - self.initial_azimuth
        azimuth_change_in_radians = np.radians(azimuth_change)
        self.last_elevation = self.view.camera.elevation
        elevation_change = self.last_elevation - self.initial_elevation
        elevation_change_in_radians = np.radians(elevation_change)

        if azimuth_change != 0 or elevation_change != 0:
            #print("Azimuth was changed in " + str(azimuth_change) + " degrees")
            #print("Elevation was changed in " + str(elevation_change) + " degrees")
            #print("The new azimuth is: " + str(self.view.camera.azimuth))
            #print("The new elevation is: " + str(self.view.camera.elevation))

            # Correct the data coordinates (for display) according to the change in azimuth and/or elevation
            self.set_rotated_coordinates(azimuth_change_in_radians, elevation_change_in_radians)

        # Calculate the affine matrix and the inverse matrix between the two coordinate systems (original and rotated)
        self.calculate_affine_mtx()

    def set_rotated_coordinates(self, azimuth_change_in_radians, elevation_change_in_radians):

        # Full data mode
        if self.is_subset_mode == 0:

            # Calculate the corrected coordinates after a movement in the XY plane (Azimuth)
            if azimuth_change_in_radians != 0:
                self.rotated_pos_array = ac.calcuate_positions_after_azimuth_change(self.rotated_pos_array,
                                                                                    self.xy_vector,
                                                                                    self.azimuth_angles,
                                                                                    azimuth_change_in_radians)

            # There was a change in elevation
            if elevation_change_in_radians != 0:

                # If there was already a change in the azimuth, the YZ angles were changed and should be recalculated
                if azimuth_change_in_radians != 0:
                    self.elevation_angles = ac.calculate_elevation_angles(self.rotated_pos_array)

                # Calculate the corrected coordinates after a movement in the YZ plane (Elevation)
                self.rotated_pos_array = ac.calcuate_positions_after_elevation_change(self.rotated_pos_array,
                                                                                      self.yz_vector,
                                                                                      self.elevation_angles,
                                                                                      elevation_change_in_radians)

        # Subset mode
        else:
            # Calculate the corrected coordinates after a movement in the XY plane (Azimuth)
            if azimuth_change_in_radians != 0:
                self.selected_rotated_pos_array = ac.calcuate_positions_after_azimuth_change(self.selected_rotated_pos_array,
                                                                                             self.selected_xy_vector,
                                                                                             self.selected_azimuth_angles,
                                                                                             azimuth_change_in_radians)

            # There was a change in elevation
            if elevation_change_in_radians != 0:

                # If there was already a change in the azimuth, the YZ angles were changed and should be recalculated
                if azimuth_change_in_radians != 0:
                    self.selected_elevation_angles = ac.calculate_elevation_angles(self.selected_rotated_pos_array)
                    # print("New elevation angles:")
                    # print(self.elevation_angles)

                # Calculate the corrected coordinates after a movement in the YZ plane (Elevation)
                self.selected_rotated_pos_array = ac.calcuate_positions_after_elevation_change(self.selected_rotated_pos_array,
                                                                                               self.selected_yz_vector,
                                                                                               self.selected_elevation_angles,
                                                                                               elevation_change_in_radians)

    def calculate_affine_mtx(self):

        # Full data mode
        if self.is_subset_mode == 0:
            self.affine_mtx = util.transforms.affine_map(self.pos_array[:4, :], self.rotated_pos_array[:4, :])
            self.inverse_affine_mtx = util.transforms.affine_map(self.rotated_pos_array[:4, :], self.pos_array[:4, :])

        # Subset mode
        else:
            self.selected_affine_mtx = util.transforms.affine_map(self.selected_pos_array[:4, :],
                                                                  self.selected_rotated_pos_array[:4, :])
            self.selected_inverse_affine_mtx = util.transforms.affine_map(self.selected_rotated_pos_array[:4, :],
                                                                          self.selected_pos_array[:4, :])

    def show_connections(self):

        if cfg.run_params['connections_num'] > 0:

            for i in range(5):
                self.lines[i].parent = self.view.scene

    # Update the connections plot after changes in P-value threshold or number of dimensions to view
    def update_connections(self, dim_num):

        # Full data mode
        if self.is_subset_mode == 0:
            pos_array = self.pos_array.copy()

            # Put the lines at the back of the scatter plot (since the ordering is not enough)
            if dim_num == 2:
                pos_array[:, 2] = -1

            for i in range(5):
                line_color = self.edges_color_scale[i+1]
                line_width = self.edges_width_scale[i+1]
                self.lines[i].set_data(pos=pos_array, color=line_color, width=line_width,
                                       connect=self.connections_by_bins[i])
        # Subset mode
        else:
            selected_pos_array = self.selected_pos_array.copy()

            # Put the lines at the back of the scatter plot (since the ordering is not enough)
            if dim_num == 2:
                selected_pos_array[:, 2] = -1

            for i in range(5):
                line_color = self.edges_color_scale[i + 1]
                line_width = self.edges_width_scale[i + 1]
                self.lines[i].set_data(pos=selected_pos_array, color=line_color, width=line_width,
                                       connect=self.selected_connections_by_bins[i])

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

    def create_connections_by_bins_subset(self):
        self.selected_connections_by_bins = []

        # (Divide the data to 5 color-bins, according to the attraction values.
        # lower att-values -> higher == lighter gray -> darker gray)
        edges_bins_array = np.digitize(cfg.att_values_for_connected_list_subset, self.att_values_bins, right=True)

        # For each bin, build an array consisting only the connections that belong to the same bin
        for i in range(5):
            connections = cfg.connected_sequences_list_subset[edges_bins_array == (i + 1)]
            self.selected_connections_by_bins.append(connections)

    def color_by_param(self, colormap, param_norm_array, dim_num, z_index_mode, color_by, group_by):

        # Color the data according to the colormap
        self.nodes_colors_array_by_param = colormap.map(param_norm_array)

        if dim_num == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

    def color_by_groups(self, dim_num, z_index_mode, color_by, group_by):

        if dim_num == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

    def update_group_by(self, dim_num, z_index_mode, color_by, group_by):

        # Initiate all groups-related variables
        self.groups_to_show = {}
        self.ordered_groups_to_show = []
        self.scatter_by_groups = {}
        self.members_array_by_groups = {}
        self.groups_text_visual = {}

        for group_ID in cfg.groups_dict[group_by]:
            self.groups_to_show[group_ID] = cfg.groups_dict[group_by][group_ID]['order']
        self.ordered_groups_to_show = sorted(self.groups_to_show, key=self.groups_to_show.get)

        for seq_index in range(cfg.run_params['total_sequences_num']):

            # First set the default size and colors
            self.nodes_size_array[seq_index] = self.nodes_size
            self.nodes_colors_array[seq_index] = self.nodes_default_color
            self.nodes_outline_color_array[seq_index] = self.nodes_outline_default_color

            # Change the size and color according to the groups definition (if any)
            if cfg.sequences_in_groups[group_by][seq_index] > -1:
                group_ID = cfg.sequences_in_groups[group_by][seq_index]
                if group_ID in self.groups_to_show:
                    self.nodes_colors_array[seq_index] = cfg.groups_dict[group_by][group_ID]['color_array']
                    self.nodes_size_array[seq_index] = cfg.groups_dict[group_by][group_ID]['size']

        # Build the text visuals of the group names
        self.build_group_names_visual(group_by)

        # Build the scatter plots by groups visuals
        self.build_scatter_by_groups(group_by)

        if dim_num == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

    def build_scatter_by_groups(self, group_by):

        order = -1
        for group_ID in self.ordered_groups_to_show:

            # Build a scatter-plot visual
            scatter = scene.visuals.Markers()
            scatter.set_gl_state('translucent', blend=True, depth_test=True)
            scatter.order = order
            self.scatter_by_groups[group_ID] = scatter
            order += 1

            # Build an array holding the sequences-indices of the members of this group
            members_array = []
            for seqID in cfg.groups_dict[group_by][group_ID]['seqIDs']:
                members_array.append(seqID)
            self.members_array_by_groups[group_ID] = members_array.copy()

        # Add a scatter visual for the sequences that do not belong to any group
        group_ID = 'none'
        scatter = scene.visuals.Markers()
        scatter.set_gl_state('translucent', blend=True, depth_test=True)
        scatter.order = order
        self.scatter_by_groups[group_ID] = scatter

        # Build an array holding the sequences-indices of the members of the 'none' group
        members_array = []
        for seqID in range(len(cfg.sequences_array)):
            if cfg.sequences_in_groups[group_by][seqID] == -1:
                members_array.append(seqID)
        self.members_array_by_groups[group_ID] = members_array.copy()

    def add_to_scatter_by_groups(self, group_ID):

        scatter = scene.visuals.Markers()
        scatter.set_gl_state('translucent', blend=True, depth_test=True)
        scatter.order = len(self.ordered_groups_to_show) - 2
        self.scatter_by_groups[group_ID] = scatter
        self.pos_array_by_groups[group_ID] = np.zeros((len(self.members_array_by_groups[group_ID]), 3),
                                                      dtype=np.float32)
        self.size_array_by_groups[group_ID] = np.zeros(len(self.members_array_by_groups[group_ID]),
                                                       dtype=np.float32)
        self.nodes_outline_color_array_by_groups[group_ID] = np.zeros((len(self.members_array_by_groups[group_ID]), 4),
                                                                      dtype=np.float32)

        # Move group 'none' to the bottom (increase order)
        self.scatter_by_groups['none'].order = len(self.ordered_groups_to_show) - 1

    def update_members_by_groups(self, group_by):

        # Update the member sequences of each group
        for group_ID in self.groups_to_show:
            members_array = []
            for seqID in cfg.groups_dict[group_by][group_ID]['seqIDs']:
                members_array.append(seqID)
            self.members_array_by_groups[group_ID] = members_array.copy()

        # Update the members of the 'none' group
        members_array = []
        for seqID in range(len(cfg.sequences_array)):
            if cfg.sequences_in_groups[group_by][seqID] == -1:
                members_array.append(seqID)
        self.members_array_by_groups['none'] = members_array.copy()

    def remove_from_scatter_by_groups(self, group_ID, dim_num, z_index_mode, color_by, group_by):

        self.scatter_by_groups[group_ID].parent = None

        current_order = int(self.scatter_by_groups[group_ID].order)

        # Move up the order of all the groups after the group to delete
        for i in range(current_order+2, len(self.ordered_groups_to_show)):
            group_index = self.ordered_groups_to_show[i]
            self.scatter_by_groups[group_index].order -= 1

        # Update the order of group 'none'
        self.scatter_by_groups['none'].order = len(self.ordered_groups_to_show) - 1

        # Delete the entry of this group from all the dictionaries related to the scatter_by_groups
        if group_ID in self.scatter_by_groups:
            del self.scatter_by_groups[group_ID]

        if dim_num == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

    def show_scatter_by_groups(self, group_by):

        pos_array = self.rotated_pos_array.copy()
        pos_array[:, 2] = 0  # Zero the Z-axis

        for group_ID in self.scatter_by_groups:
            if len(self.members_array_by_groups[group_ID]) > 0:
                self.pos_array_by_groups[group_ID] = np.zeros((len(self.members_array_by_groups[group_ID]), 3),
                                                              dtype=np.float32)
                self.size_array_by_groups[group_ID] = np.zeros(len(self.members_array_by_groups[group_ID]),
                                                               dtype=np.float32)
                self.nodes_outline_color_array_by_groups[group_ID] = np.zeros((len(self.members_array_by_groups[group_ID]), 4),
                                                                              dtype=np.float32)

                for i in range(len(self.members_array_by_groups[group_ID])):
                    self.pos_array_by_groups[group_ID][i] = pos_array[self.members_array_by_groups[group_ID][i]]
                    self.size_array_by_groups[group_ID][i] = self.nodes_size_array[self.members_array_by_groups[group_ID][i]]
                    self.nodes_outline_color_array_by_groups[group_ID][i] = self.nodes_outline_color_array[
                        self.members_array_by_groups[group_ID][i]]

                if group_ID == 'none':
                    color = self.nodes_default_color
                else:
                    color = cfg.groups_dict[group_by][group_ID]['color_array']
                self.scatter_by_groups[group_ID].set_data(pos=self.pos_array_by_groups[group_ID],
                                                          face_color=color,
                                                          size=self.size_array_by_groups[group_ID],
                                                          edge_width=self.nodes_outline_width,
                                                          edge_color=self.nodes_outline_color_array_by_groups[group_ID],
                                                          symbol=self.nodes_symbol)
                self.scatter_by_groups[group_ID].parent = None
                self.scatter_by_groups[group_ID].parent = self.view.scene

    def hide_scatter_by_groups(self):

        for group_ID in self.scatter_by_groups:
            self.scatter_by_groups[group_ID].parent = None

    def show_sequences_names(self):
        self.seq_text_visual.parent = self.view.scene

    def update_sequences_names(self, dim_num):
        text_list = []
        pos_list = []

        # Full data mode
        if self.is_subset_mode == 0:
            if dim_num == 3:
                pos_array = self.pos_array.copy()
            else:
                pos_array = self.rotated_pos_array.copy()
                pos_array[:, 2] = 0

            for key in self.selected_points:
                text_list.append('  ' + cfg.sequences_array['seq_ID'][key])
                pos_list.append(tuple(pos_array[key]))

        # Subset mode
        else:
            if dim_num == 3:
                pos_array = self.selected_pos_array.copy()
            else:
                pos_array = self.selected_rotated_pos_array.copy()
                pos_array[:, 2] = 0

            i = 0
            for seq_index in sorted(self.selected_points):
                text_list.append('  ' + cfg.sequences_array['seq_ID'][seq_index])
                pos_list.append(tuple(pos_array[i]))
                i += 1

        # Update the text visual with the current selected sequences and their positions
        if len(pos_list) > 0:
            self.seq_text_visual.text = text_list
            self.seq_text_visual.pos = pos_list
            self.seq_text_visual.font_size = self.text_size_small
            self.seq_text_visual.anchors = ['top', 'left']
            self.seq_text_visual.color = [0.0, 0.0, 0.0, 1.0]

        # No selected sequences => hide the text visual
        else:
            self.hide_sequences_names()

    def hide_sequences_names(self):
        self.seq_text_visual.parent = None

    def show_sequences_numbers(self):
        self.seq_number_visual.parent = self.view.scene

    def update_sequences_numbers(self, dim_num):
        text_list = []
        pos_list = []

        # Full data mode
        if self.is_subset_mode == 0:
            if dim_num == 3:
                pos_array = self.pos_array.copy()
            else:
                pos_array = self.rotated_pos_array.copy()
                pos_array[:, 2] = 0

            for key in self.selected_points:
                text_list.append('  '+str(key))
                pos_list.append(tuple(pos_array[key]))

        # Subset mode
        else:
            if dim_num == 3:
                pos_array = self.selected_pos_array.copy()
            else:
                pos_array = self.selected_rotated_pos_array.copy()
                pos_array[:, 2] = 0

            i = 0
            for seq_index in sorted(self.selected_points):
                text_list.append('  '+str(seq_index))
                pos_list.append(tuple(pos_array[i]))
                i += 1

        # Update the text visual with the current selected sequences and their positions
        if len(pos_list) > 0:
            self.seq_number_visual.text = text_list
            self.seq_number_visual.pos = pos_list
            self.seq_number_visual.font_size = self.text_size - 2
            self.seq_number_visual.anchors = ['top', 'left']
            self.seq_number_visual.color = [0.0, 0.0, 0.0, 1.0]

        # No selected sequences => hide the text visual
        else:
            self.hide_sequences_names()

    def hide_sequences_numbers(self):
        self.seq_number_visual.parent = None

    def build_group_names_visual(self, group_by):

        for group_ID in self.ordered_groups_to_show:
            text_vis = scene.visuals.Text(method='gpu', bold=True)
            text_vis.set_gl_state('translucent', blend=True, depth_test=False)
            text_vis.text = cfg.groups_dict[group_by][group_ID]['name']
            text_vis.font_size = cfg.groups_dict[group_by][group_ID]['name_size']
            text_vis.anchors = ['left', 'center']
            text_vis.color = cfg.groups_dict[group_by][group_ID]['color_array']
            text_vis.interactive = True
            self.groups_text_visual[group_ID] = text_vis

        self.reset_group_names_positions(group_by)

    def add_to_group_names_visual(self, group_by, group_ID):

        # Build a visual for the new group and add it
        text_vis = scene.visuals.Text(method='gpu', bold=True)
        text_vis.set_gl_state('translucent', blend=True, depth_test=False)
        text_vis.text = cfg.groups_dict[group_by][group_ID]['name']
        text_vis.pos = (0, 0, 0)
        text_vis.anchors = ['left', 'center']
        text_vis.color = cfg.groups_dict[group_by][group_ID]['color_array']
        text_vis.font_size = cfg.groups_dict[group_by][group_ID]['name_size']
        text_vis.interactive = True
        self.groups_text_visual[group_ID] = text_vis

        # Update the positions of all the group names, including the new one
        self.reset_group_names_positions(group_by)

    def remove_from_group_names_visual(self, group_by, group_index):

        if group_index in self.groups_text_visual:
            self.groups_text_visual[group_index].parent = None
            del self.groups_text_visual[group_index]

        # Update the positions of all the group names, without the deleted one
        self.reset_group_names_positions(group_by)

    def update_text_group_name_visual(self, group_by, group_ID):
        self.groups_text_visual[group_ID].text = cfg.groups_dict[group_by][group_ID]['name']
        self.groups_text_visual[group_ID].color = cfg.groups_dict[group_by][group_ID]['color_array']
        self.groups_text_visual[group_ID].font_size = cfg.groups_dict[group_by][group_ID]['name_size']
        self.groups_text_visual[group_ID].bold = cfg.groups_dict[group_by][group_ID]['is_bold']
        self.groups_text_visual[group_ID].italic = cfg.groups_dict[group_by][group_ID]['is_italic']

    def show_group_names(self, mode):

        # Show all group names
        if mode == 'all':
            # a loop over the groups
            for group_index in self.groups_to_show:
                self.groups_text_visual[group_index].parent = self.view.scene

        # Mode is 'selected' => show only the selected group names
        else:
            # a loop over the groups
            for group_index in self.groups_to_show:
                # If the group is selected => present it on the scene
                if group_index in self.selected_groups:
                    self.groups_text_visual[group_index].parent = self.view.scene
                else:
                    self.groups_text_visual[group_index].parent = None

    def reset_group_names_positions(self, group_by):

        x_init = 20
        y_init = 20
        y_interval = 15

        trans = self.view.scene.transform

        x = x_init
        y = y_init
        for group_ID in self.ordered_groups_to_show:
            # Verify that the group is not empty
            if len(cfg.groups_dict[group_by][group_ID]['seqIDs']) > 0:
                data_coor = trans.imap([x, y, 0, 1])
                pos_data_coor = (data_coor[0], data_coor[1], data_coor[2])
                self.groups_text_visual[group_ID].pos = pos_data_coor
                y += y_interval

    def hide_group_names(self):
        # Remove all the group names from the scene
        for group_index in self.groups_text_visual:
            self.groups_text_visual[group_index].parent = None

    def add_group(self, group_by, group_ID):

        # If the group should be presented, add it to the 'groups_to_show' dict
        self.groups_to_show[group_ID] = cfg.groups_dict[group_by][group_ID]['order']
        self.ordered_groups_to_show.append(group_ID)

        self.add_to_group_names_visual(group_by, group_ID)

        # Update the member sequences of all the groups
        self.update_members_by_groups(group_by)

        # Add the group to the scatter-plot visual
        self.add_to_scatter_by_groups(group_ID)

    def delete_group(self, group_ID, seq_dict, dim_num, z_index_mode, color_by, group_by):

        # 1. Empty the group from its members
        self.remove_from_group(seq_dict, dim_num, z_index_mode, color_by, group_by)

        # 2. Remove the group from the scatter-plot visual
        self.remove_from_scatter_by_groups(group_ID, dim_num, z_index_mode, color_by, group_by)

        # 3. Remove the group from the groups_to_show dict and from the ordered_groups_to_show list
        if group_ID in self.groups_to_show:
            del self.groups_to_show[group_ID]
            self.ordered_groups_to_show.remove(group_ID)

        # 4. Update the group_names_visual
        self.remove_from_group_names_visual(group_by, group_ID)

    def delete_empty_group(self, group_ID, dim_num, z_index_mode, color_by, group_by):

        # 1. Remove the group from the scatter-plot visual
        self.remove_from_scatter_by_groups(group_ID, dim_num, z_index_mode, color_by, group_by)

        # 2. Remove the group from the groups_to_show dict and from the ordered_groups_to_show list
        if group_ID in self.groups_to_show:
            del self.groups_to_show[group_ID]
            self.ordered_groups_to_show.remove(group_ID)

        # 3. Update the group_names_visual
        self.remove_from_group_names_visual(group_by, group_ID)

    def edit_group_parameters(self, group_ID, dim_num, z_index_mode, color_by, group_by):

        # The group is not empty
        if len(cfg.groups_dict[group_by][group_ID]['seqIDs']) > 0:

            # Update the group nodes with the new color and size
            for seq_index in cfg.groups_dict[group_by][group_ID]['seqIDs']:
                self.nodes_colors_array[seq_index] = cfg.groups_dict[group_by][group_ID]['color_array']
                self.nodes_size_array[seq_index] = cfg.groups_dict[group_by][group_ID]['size']

            # Update the group name visual
            self.update_text_group_name_visual(group_by, group_ID)

        # The group is empty
        else:
            self.remove_from_group_names_visual(group_by, group_ID)

        if dim_num == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

    def update_groups_order(self, dim_num, z_index_mode, group_by):

        # Update the order in groups_to_show dict
        for group_ID in self.groups_to_show:
            self.groups_to_show[group_ID] = cfg.groups_dict[group_by][group_ID]['order']

        # Re-sort the groups array according to the updated order
        self.ordered_groups_to_show = sorted(self.groups_to_show, key=self.groups_to_show.get)

        # Update the positions of the group names
        self.reset_group_names_positions(group_by)

        # Update the order in the scatter-by-groups visual
        for i in range(len(self.ordered_groups_to_show)):
            group_ID = self.ordered_groups_to_show[i]
            self.scatter_by_groups[group_ID].order = i - 1
        self.scatter_by_groups['none'].order = i

        if dim_num == 2 and z_index_mode == 'groups':
            self.update_2d_view(z_index_mode, group_by)

    def add_to_group(self, points_dict, group_ID, dim_num, z_index_mode, color_by, group_by):

        if group_ID in self.groups_to_show:
            for seq_index in points_dict:
                self.nodes_colors_array[seq_index] = cfg.groups_dict[group_by][group_ID]['color_array']
                #self.nodes_size_array[seq_index] = cfg.groups_dict[group_by][group_ID]['size']

        self.update_members_by_groups(group_by)

        if dim_num == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

    def remove_from_group(self, points_dict, dim_num, z_index_mode, color_by, group_by):
        for seq_index in points_dict:
            self.nodes_colors_array[seq_index] = self.nodes_default_color

        self.update_members_by_groups(group_by)

        if dim_num == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

    def find_selected_point(self, selection_type, clicked_screen_coor, z_index_mode, color_by, group_by):

        # An array to hold the indices of the data points that are close enough to the clicked point
        points_in_radius = []
        groups_in_radius = {}
        deselect = 0

        trans = self.view.scene.transform

        for seq_index in range(self.rotated_pos_array.shape[0]):

            # Define the radius (in pixels) around the clicked position to look for a data point(s)
            radius = self.nodes_size_array[seq_index]

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
                        cfg.sequences_array[seq_index]['in_subset'] = False
                        deselect = 1
                    # Select the data point
                    else:
                        self.selected_points[seq_index] = 1
                        cfg.sequences_array[seq_index]['in_subset'] = True
                    #print("Found matching point: Index = " + str(seq_index))
                    #print("Position in screen coor: " + str(data_screen_coor))
                    #print("Distance from clicked point: " + str(distance_screen_coor))

                # Select / deselect all the sequences belonging to the group of the selected data-point (if any)
                else:
                    if cfg.sequences_in_groups[group_by][seq_index] > -1:
                        group_ID = cfg.sequences_in_groups[group_by][seq_index]
                        #print("Found matching group: Index = " + str(group_index))

                        # The first time we encounter this group
                        if group_ID not in groups_in_radius:

                            points_in_radius = []

                            # A loop over all the sequences belonging to this group
                            for seqID in cfg.groups_dict[group_by][group_ID]['seqIDs']:
                                points_in_radius.append(seqID)

                                # Deselect the sequences
                                if group_ID in self.selected_groups:
                                    del self.selected_points[seqID]
                                    cfg.sequences_array[seqID]['in_subset'] = False
                                # Select the sequences
                                else:
                                    self.selected_points[seqID] = 1
                                    cfg.sequences_array[seqID]['in_subset'] = True

                            # Deselect the group
                            if group_ID in self.selected_groups:
                                del self.selected_groups[group_ID]
                                # Unmark the sequences from the selected group
                                self.unmark_selected_points(points_in_radius, 2, z_index_mode, color_by, group_by)
                            # Select the group
                            else:
                                self.selected_groups[group_ID] = 1
                                self.mark_selected_points(points_in_radius, z_index_mode, color_by, group_by)

                            groups_in_radius[group_ID] = 1

        if selection_type == 'sequences' and len(points_in_radius) > 0:
            #print("Selected point(s) indices:")
            #print(points_in_radius)

            # Points should be cleared from selection
            if deselect == 1:
                self.unmark_selected_points(points_in_radius, 2, z_index_mode, color_by, group_by)

            # Points should be added to selection
            else:
                self.mark_selected_points(points_in_radius, z_index_mode, color_by, group_by)

            self.update_sequences_names(2)
            self.update_sequences_numbers(2)

    def find_selected_area(self, selection_type, drag_start_screen_coor, drag_end_screen_coor, z_index_mode,
                           color_by, group_by):

        points_in_area = []
        groups_in_area = {}

        trans = self.view.scene.transform

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
                    cfg.sequences_array[seq_index]['in_subset'] = True
                    points_in_area.append(seq_index)

                # Groups selection mode
                else:
                    # Data point belongs to a group
                    if cfg.sequences_in_groups[group_by][seq_index] > -1:
                        group_ID = cfg.sequences_in_groups[group_by][seq_index]
                        #print("Found matching group: Index = " + str(group_index))

                        # The first time we encounter this group
                        if group_ID not in groups_in_area:
                            self.selected_groups[group_ID] = 1

                            # A loop over all the sequences belonging to this group
                            for seqID in cfg.groups_dict[group_by][group_ID]['seqIDs']:
                                points_in_area.append(seqID)
                                self.selected_points[seqID] = 1
                                cfg.sequences_array[seqID]['in_subset'] = True

                            groups_in_area[group_ID] = 1

        if len(points_in_area) > 0:
            #print("Point(s) in area indices:")
            #print(points_in_area)
            self.mark_selected_points(points_in_area, z_index_mode, color_by, group_by)

            self.update_sequences_names(2)
            self.update_sequences_numbers(2)

    def remove_from_selected(self, selected_dict, dim_num, z_index_mode, color_by, group_by):

        points_array = []

        for seq_index in selected_dict:
            points_array.append(seq_index)

            if seq_index in self.selected_points:
                del self.selected_points[seq_index]
                cfg.sequences_array[seq_index]['in_subset'] = False

        self.unmark_selected_points(points_array, dim_num, z_index_mode, color_by, group_by)

    def mark_selected_points(self, selected_array, z_index_mode, color_by, group_by):

        for i in range(len(selected_array)):
                self.nodes_outline_color_array[selected_array[i]] = self.selected_outline_color
                self.nodes_size_array[selected_array[i]] = self.selected_nodes_size

        self.update_2d_view(z_index_mode, color_by, group_by)

    def unmark_selected_points(self, selected_array, dim_num, z_index_mode, color_by, group_by):

        for i in range(len(selected_array)):
            self.nodes_outline_color_array[selected_array[i]] = self.nodes_outline_default_color
            self.nodes_size_array[selected_array[i]] = self.nodes_size

        if dim_num == 2:
            self.update_2d_view(z_index_mode, color_by, group_by)
        else:
            self.update_3d_view(color_by, group_by)

    def select_all(self, selection_type, dim_num, z_index_mode, color_by, group_by):

        for seq_index in range(self.pos_array.shape[0]):
            self.selected_points[seq_index] = 1
            cfg.sequences_array[seq_index]['in_subset'] = True
            self.nodes_outline_color_array[seq_index] = self.selected_outline_color
            self.nodes_size_array[seq_index] = self.selected_nodes_size

        if selection_type == 'groups':
            for group_index in self.groups_to_show:
                self.selected_groups[group_index] = 1

        if dim_num == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

        self.update_sequences_names(dim_num)
        self.update_sequences_numbers(dim_num)

    def select_subset(self, selected_dict, dim_num, z_index_mode, color_by, group_by):

        for seq_index in selected_dict:
            if seq_index not in self.selected_points:
                self.selected_points[seq_index] = 1
                cfg.sequences_array[seq_index]['in_subset'] = True
                self.nodes_outline_color_array[seq_index] = self.selected_outline_color
                self.nodes_size_array[seq_index] = self.selected_nodes_size

        if dim_num == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

    def reset_selection(self, dim_num_view, z_index_mode, color_by, group_by):

        for seq_index in self.selected_points:
            cfg.sequences_array[seq_index]['in_subset'] = False
            self.nodes_outline_color_array[seq_index] = self.nodes_outline_default_color

            group_ID = cfg.sequences_in_groups[group_by][seq_index]

            # If the sequence belongs to a group - set the size according to the group definitions
            if group_ID > -1 and group_ID in self.groups_to_show:
                self.nodes_size_array[seq_index] = int(cfg.groups_dict[group_by][group_ID]['size'])

            # Set the default size
            else:
                self.nodes_size_array[seq_index] = self.nodes_size

        # Empty the selected_points and the selected_groups dictionaries
        self.selected_points = {}
        self.selected_groups = {}

        self.hide_sequences_names()

        if dim_num_view == 3:
            self.update_3d_view(color_by, group_by)
        else:
            self.update_2d_view(z_index_mode, color_by, group_by)

    def highlight_selected_points(self, selected_dict, dim_num, z_index_mode, color_by, group_by):

        for seq_index in selected_dict:
            self.nodes_colors_array[seq_index] = self.nodes_highlight_color
            self.nodes_outline_color_array[seq_index] = self.highlighted_outline_color
            self.nodes_size_array[seq_index] = self.highlighted_nodes_size

            if dim_num == 3:
                self.update_3d_view(color_by, group_by)
            else:
                self.update_2d_view(z_index_mode, color_by, group_by)

    def unhighlight_selected_points(self, selected_dict, dim_num, z_index_mode, color_by, group_by):

        for seq_index in selected_dict:

            if cfg.sequences_in_groups[group_by][seq_index] > -1:
                group_ID = cfg.sequences_in_groups[group_by][seq_index]
                if group_ID in self.groups_to_show:
                    self.nodes_colors_array[seq_index] = cfg.groups_dict[group_by][group_ID]['color_array']
            else:
                self.nodes_colors_array[seq_index] = self.nodes_default_color

            if seq_index in self.selected_points:
                self.nodes_size_array[seq_index] = self.selected_nodes_size
                self.nodes_outline_color_array[seq_index] = self.selected_outline_color
            else:
                self.nodes_size_array[seq_index] = self.nodes_size
                self.nodes_outline_color_array[seq_index] = self.nodes_outline_default_color

            if dim_num == 3:
                self.update_3d_view(color_by, group_by)
            else:
                self.update_2d_view(z_index_mode, color_by, group_by)

    def start_dragging_rectangle(self, drag_start_screen_coor):
        trans = self.view.scene.transform
        drag_start_data_coor = trans.imap(drag_start_screen_coor)
        if self.view.camera.fov != 0:
            drag_start_data_coor /= drag_start_data_coor[3]

        self.drag_rectangle.center = (drag_start_data_coor[0], drag_start_data_coor[1], 0)
        self.drag_rectangle.color = self.drag_rectangle_color
        self.drag_rectangle.border_color = 'black'
        self.drag_rectangle.height = 0.01
        self.drag_rectangle.width = 0.01
        self.drag_rectangle.parent = self.view.scene

    def update_dragging_rectangle(self, drag_start_screen_coor, drag_end_screen_coor):
        trans = self.view.scene.transform
        drag_start_data_coor = trans.imap(drag_start_screen_coor)
        drag_end_data_coor = trans.imap(drag_end_screen_coor)
        if self.view.camera.fov != 0:
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

    def move_selected_points(self, dim_num, start_move_screen_coor, end_move_screen_coor, z_index_mode, color_by, group_by):
        trans = self.view.scene.transform
        start_move_data_coor = trans.imap(start_move_screen_coor)
        end_move_data_coor = trans.imap(end_move_screen_coor)

        if self.view.camera.fov != 0:
            start_move_data_coor /= start_move_data_coor[3]
            end_move_data_coor /= end_move_data_coor[3]

        distance_vec_data_coor = end_move_data_coor - start_move_data_coor

        if dim_num == 3:
            for index in self.selected_points:
                self.pos_array[index, :] += distance_vec_data_coor[:3]
            self.update_3d_view(color_by, group_by)
        else:
            for index in self.selected_points:
                self.rotated_pos_array[index, :] += distance_vec_data_coor[:3]
            self.update_2d_view(z_index_mode, color_by, group_by)
        #print("rotated_pos_array:")
        #print(self.rotated_pos_array)

    def update_moved_positions(self, moved_pos_dict, dim_num):

        if dim_num == 2:
            for index in moved_pos_dict:
                rotated_array = np.append(self.rotated_pos_array[index], 1)
                inverse_array = np.dot(self.inverse_affine_mtx, rotated_array)
                self.pos_array[index] = inverse_array[:3]

        seq.update_positions(self.pos_array.T, 'full')

        # Calculate the angles of each point for future use when having rotations
        self.calculate_initial_angles()

    def find_points_to_move(self, clicked_screen_coor):

        trans = self.view.scene.transform

        for seq_index in range(self.rotated_pos_array.shape[0]):

            # Translate the data coordinates into screen coordinates
            data_screen_coor = trans.map(self.rotated_pos_array[seq_index])
            data_screen_coor /= data_screen_coor[3]

            # Calculate the euclidean distances of all the points from the clicked point (in screen coor)
            distance_screen_coor = np.linalg.norm(data_screen_coor[:2] - clicked_screen_coor)

            # Define the radius (in pixels) around the clicked position to look for a data point(s)
            radius = self.nodes_size_array[seq_index]

            # Found a data point in the radius of the clicked point
            if distance_screen_coor <= radius:
                self.points_to_move[seq_index] = 1

        if cfg.run_params['is_debug_mode']:
            print("Found point(s) to move:")
            print(self.points_to_move)

    def move_points(self, start_move_screen_coor, end_move_screen_coor, z_index_mode, color_by, group_by):

        trans = self.view.scene.transform
        start_move_data_coor = trans.imap(start_move_screen_coor)
        end_move_data_coor = trans.imap(end_move_screen_coor)

        if self.view.camera.fov != 0:
            start_move_data_coor /= start_move_data_coor[3]
            end_move_data_coor /= end_move_data_coor[3]

        distance_vec_data_coor = end_move_data_coor - start_move_data_coor

        for index in self.points_to_move:
            self.rotated_pos_array[index, :] += distance_vec_data_coor[:3]
        self.update_2d_view(z_index_mode, color_by, group_by)

    def finish_points_move(self, dim_num, fr_object):

        #self.update_moved_positions(self.points_to_move, dim_num)

        # Update the coordinates in the fruchterman-reingold object
        #fr_object.init_coordinates(cfg.sequences_array['x_coor'],
                                        #cfg.sequences_array['y_coor'],
                                        #cfg.sequences_array['z_coor'])

        self.points_to_move = {}

    def find_visual(self, canvas, clicked_screen_coor):

        visual = canvas.visual_at(clicked_screen_coor)

        if re.search("Markers", str(visual)):
            visual_type = "data"

            if cfg.run_params['is_debug_mode']:
                print("Found data-point visual to move")

        elif re.search("Text", str(visual)):
            visual_type = "text"

            if cfg.run_params['is_debug_mode']:
                print("Found text visual to move")

        else:
            visual_type = None

        return visual_type

    def find_group_name_to_move(self, clicked_screen_coor, group_by):

        permitted_dist_x = 100

        trans = self.view.scene.transform

        for group_index in self.groups_text_visual:

            group_visual = self.groups_text_visual[group_index]

            # Translate the data coordinates into screen coordinates
            group_pos_screen_coor = trans.map(group_visual.pos)

            dist_x = clicked_screen_coor[0] - group_pos_screen_coor[0][0]
            dist_y = abs(clicked_screen_coor[1] - group_pos_screen_coor[0][1])

            # Define the permitted distance in the Y axis according to the group-name size
            permitted_dist_y = int(cfg.groups_dict[group_by][group_index]['name_size'])

            if 0 <= dist_x <= permitted_dist_x and dist_y <= permitted_dist_y:
                self.group_name_to_move = group_index

                if cfg.run_params['is_debug_mode']:
                    print("Found group name visual. Index=" + str(group_index))
                    #print("Clicked coor: " + str(clicked_screen_coor))
                    #print("Group name coor: " + str(group_pos_screen_coor[0]))

                break

    def find_group_name_to_edit(self, clicked_screen_coor, group_by):

        permitted_dist_x = 100

        trans = self.view.scene.transform

        for group_index in self.groups_text_visual:

            group_visual = self.groups_text_visual[group_index]

            # Translate the data coordinates into screen coordinates
            group_pos_screen_coor = trans.map(group_visual.pos)

            dist_x = clicked_screen_coor[0] - group_pos_screen_coor[0][0]
            dist_y = abs(clicked_screen_coor[1] - group_pos_screen_coor[0][1])

            # Define the permitted distance in the Y axis according to the group-name size
            permitted_dist_y = int(cfg.groups_dict[group_by][group_index]['name_size'])

            if 0 <= dist_x <= permitted_dist_x and dist_y <= permitted_dist_y:

                if cfg.run_params['is_debug_mode']:
                    print("Found group name visual. Index=" + str(group_index))
                    #print("Clicked coor: " + str(clicked_screen_coor))
                    #print("Group name coor: " + str(group_pos_screen_coor[0]))

                return group_index


    def move_group_name(self, start_move_screen_coor, end_move_screen_coor):
        # There is a selected group name to move
        if self.group_name_to_move is not None:
            trans = self.view.scene.transform
            end_move_data_coor = trans.imap(end_move_screen_coor)
            new_pos = (end_move_data_coor[0], end_move_data_coor[1], 0)
            self.groups_text_visual[self.group_name_to_move].pos = new_pos

    def finish_group_name_move(self):
        if self.group_name_to_move is not None:
            self.group_name_to_move = None

    def set_range_panzoom_camera(self):
        pos_array = self.pos_array.copy()

        xmin = np.amin(pos_array[:, 0])
        xmax = np.amax(pos_array[:, 0])
        ymin = np.amin(pos_array[:, 1])
        ymax = np.amax(pos_array[:, 1])
        self.view.camera.set_range(x=(xmin, xmax), y=(ymin, ymax), z=None, margin=0.1)

        #print("Camera coordinates range:")
        #print(xmin, xmax, ymin, ymax)

    def set_range_turntable_camera(self, dim_num_view):

        # Full data mode
        if self.is_subset_mode == 0:
            pos_array = self.pos_array.copy()
        # Subset mode
        else:
            pos_array = self.selected_pos_array.copy()

        xmin = np.amin(pos_array[:, 0])
        xmax = np.amax(pos_array[:, 0])
        ymin = np.amin(pos_array[:, 1])
        ymax = np.amax(pos_array[:, 1])

        if dim_num_view == 2:
            self.view.camera.set_range(x=(xmin, xmax), y=(ymin, ymax), z=None, margin=0.2)

        else:
            zmin = np.amin(pos_array[:, 2])
            zmax = np.amax(pos_array[:, 2])
            self.view.camera.set_range(x=(xmin, xmax), y=(ymin, ymax), z=(zmin, zmax), margin=0.1)

        #print("Camera coordinates range:")
        #print(xmin, xmax, ymin, ymax, zmin, zmax)

    def reset_rotation(self):
        self.view.camera.elevation = self.initial_elevation
        self.view.camera.azimuth = self.initial_azimuth

        #print("Turntable camera was reset to original Azimuth and Elevation. Parameters:")
        #print(self.view.camera.get_state())

    def reset_turntable_camera(self):
        self.view.camera.elevation = self.initial_elevation
        self.view.camera.azimuth = self.initial_azimuth
        self.view.camera.center = (0.0, 0.0, 0.0)

        #print("Turntable camera was reset to original Azimuth and Elevation. Parameters:")
        #print(self.view.camera.get_state())

    def set_rotated_center(self):
        self.center = self.view.camera.center

        center_array = np.append(np.array(self.center), 1)

        if self.is_subset_mode == 0:
            rotated_center_array = np.dot(self.affine_mtx, center_array)
        else:
            rotated_center_array = np.dot(self.selected_affine_mtx, center_array)
        #print("Rotated center array:")
        #print(rotated_center_array)

        self.rotated_center = tuple(rotated_center_array[:3])

        # Set the new rotated center in the Turntable camera
        self.view.camera.center = self.rotated_center






