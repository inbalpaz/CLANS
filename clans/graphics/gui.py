from PyQt5.QtCore import QThreadPool, Qt
from PyQt5.QtWidgets import *
from vispy import app, scene
import vispy.io
import numpy as np
import clans.config as cfg
import clans.io.io_gui as io
import clans.layouts.layout_gui as lg
import clans.layouts.fruchterman_reingold as fr
import clans.graphics.network3d_vispy as net
import clans.data.sequences as seq
import clans.data.sequence_pairs as sp
import time


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.threadpool = QThreadPool()
        # Define a runner that will be executed in a different thread
        self.run_calc_worker = None

        # Calculation-related variables
        self.before = None
        self.after = None
        self.is_running_calc = 0
        self.is_show_connections = 0
        self.is_show_selected_names = 0
        self.is_show_group_names = 0
        self.rounds_done = 0
        self.view_in_dimensions_num = cfg.run_params['dimensions_num_for_clustering']
        self.mode = "interactive"  # Modes of interaction: 'interactive' (rotate/pan) / 'selection'
        self.selection_type = "sequences"  # switch between 'sequences' and 'groups' modes
        self.ctrl_key_pressed = 0

        self.setWindowTitle("CLANS " + str(self.view_in_dimensions_num) + "D-View")
        self.setGeometry(50, 50, 900, 800)

        # Define layouts within the main window
        self.main_layout = QVBoxLayout()
        self.round_layout = QHBoxLayout()
        self.calc_layout = QHBoxLayout()
        self.mode_layout = QHBoxLayout()
        self.view_layout = QHBoxLayout()
        self.selection_layout = QHBoxLayout()
        self.save_layout = QHBoxLayout()

        self.main_layout.setSpacing(5)

        self.horizontal_spacer_long = QSpacerItem(18, 24, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer_short = QSpacerItem(10, 24, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.app = app.use_app('pyqt5')

        self.canvas = scene.SceneCanvas(size=(700, 700), keys='interactive', show=True, bgcolor='w')
        self.canvas.events.mouse_move.connect(self.on_canvas_mouse_move)
        self.canvas.events.key_press.connect(self.on_canvas_key_press)
        self.canvas.events.key_release.connect(self.on_canvas_key_release)
        self.main_layout.addWidget(self.canvas.native)

        # Add a ViewBox to let the user zoom/rotate
        self.view = self.canvas.central_widget.add_view()

        # Add a label for displaying the number of rounds done
        self.rounds_label = QLabel("Round: " + str(self.rounds_done))

        self.round_layout.addStretch()
        self.round_layout.addWidget(self.rounds_label)
        self.round_layout.addStretch()

        self.main_layout.addLayout(self.round_layout)

        self.calc_label = QLabel("Clustering options:")
        self.calc_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add calculation buttons (Init, Start, Stop)
        self.start_button = QPushButton("Start clustering")
        self.stop_button = QPushButton("Stop clustering")
        self.init_button = QPushButton("Initialize")

        self.start_button.pressed.connect(self.run_calc)
        self.stop_button.pressed.connect(self.stop_calc)
        self.init_button.pressed.connect(self.init_coor)

        # Add a button to switch between 3D and 2D clustering
        self.dimensions_clustering_combo = QComboBox()
        self.dimensions_clustering_combo.addItems(["Cluster in 3D", "Cluster in 2D"])
        self.dimensions_clustering_combo.currentIndexChanged.connect(self.change_dimensions_num_for_clustering)

        # Add a text-field for the P-value / attraction-value threshold
        self.pval_label = QLabel("P-value threshold:")
        self.pval_widget = QLineEdit()
        self.pval_widget.setFixedSize(60, 24)
        self.pval_widget.setPlaceholderText(str(cfg.run_params['similarity_cutoff']))
        self.pval_widget.returnPressed.connect(self.update_cutoff)

        # Add the widgets to the calc_layout
        self.calc_layout.addWidget(self.calc_label)
        self.calc_layout.addSpacerItem(self.horizontal_spacer_short)
        self.calc_layout.addWidget(self.init_button)
        self.calc_layout.addWidget(self.start_button)
        self.calc_layout.addWidget(self.stop_button)
        self.calc_layout.addSpacerItem(self.horizontal_spacer_short)
        self.calc_layout.addWidget(self.dimensions_clustering_combo)
        self.calc_layout.addSpacerItem(self.horizontal_spacer_long)
        self.calc_layout.addWidget(self.pval_label)
        self.calc_layout.addWidget(self.pval_widget)
        self.calc_layout.addStretch()


        # Add the calc_layout to the main layout
        self.main_layout.addLayout(self.calc_layout)

        # Add a combo-box to switch between user-interaction modes
        self.mode_label = QLabel("Interaction mode:")
        self.mode_label.setStyleSheet("color: maroon; font-weight: bold;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Move/Rotate/Pan", "Select data-points"])
        self.mode_combo.currentIndexChanged.connect(self.change_mode)

        #self.mode_layout.addWidget(self.mode_label)
        #self.mode_layout.addWidget(self.mode_combo)
        #self.mode_layout.addStretch()

        #self.main_layout.addLayout(self.mode_layout)

        self.selection_label = QLabel("Selection options:")
        self.selection_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add a combo-box to switch between sequences / groups selection
        self.selection_type_combo = QComboBox()
        self.selection_type_combo.addItems(["Sequences selection", "Groups selection"])
        self.selection_type_combo.currentIndexChanged.connect(self.change_selection_type)

        # Add a button to select all the sequences / groups
        self.select_all_button = QPushButton("Select all")
        self.select_all_button.released.connect(self.select_all)

        # Add a button to clear the current selection
        self.clear_selection_button = QPushButton("Clear selection")
        self.clear_selection_button.released.connect(self.clear_selection)

        # Add the widgets to the selection_layout
        self.selection_layout.addWidget(self.mode_label)
        self.selection_layout.addWidget(self.mode_combo)
        self.selection_layout.addSpacerItem(self.horizontal_spacer_long)
        self.selection_layout.addWidget(self.selection_label)
        self.selection_layout.addSpacerItem(self.horizontal_spacer_short)
        self.selection_layout.addWidget(self.selection_type_combo)
        self.selection_layout.addWidget(self.select_all_button)
        self.selection_layout.addWidget(self.clear_selection_button)
        self.selection_layout.addStretch()

        # Add the selection_layout to the main layout
        self.main_layout.addLayout(self.selection_layout)

        self.view_label = QLabel("Viewing options:")
        self.view_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add a combo-box to switch between 3D and 2D views
        self.dimensions_view_combo = QComboBox()
        self.dimensions_view_combo.addItems(["3D view", "2D view"])
        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.dimensions_view_combo.setCurrentIndex(0)
        else:
            self.dimensions_view_combo.setCurrentIndex(1)
            self.dimensions_view_combo.setEnabled(False)
        self.dimensions_view_combo.currentIndexChanged.connect(self.change_dimensions_view)

        # Add a button to show/hide the connections
        self.connections_button = QPushButton("Show connections")
        self.connections_button.setCheckable(True)
        self.connections_button.released.connect(self.manage_connections)

        # Add a button to show the selected sequences/groups names on screen
        self.show_selected_button = QPushButton("Show selected names")
        self.show_selected_button.setCheckable(True)
        #if self.view_in_dimensions_num == 3:
            #self.show_selected_button.setEnabled(False)
        self.show_selected_button.released.connect(self.show_selected_names)

        # Add a button to show all the groups names on screen
        self.show_group_names_button = QPushButton("Show all group names")
        self.show_group_names_button.setCheckable(True)
        if self.view_in_dimensions_num == 3:
            self.show_group_names_button.setEnabled(False)
        self.show_group_names_button.released.connect(self.manage_group_names)

        # Add a button to toggle 'move group names' mode
        self.move_group_names_button = QPushButton("Move group names")
        self.move_group_names_button.setCheckable(True)
        if self.view_in_dimensions_num == 3:
            self.move_group_names_button.setEnabled(False)
        self.move_group_names_button.released.connect(self.move_group_names)

        # Add the widgets to the view_layout
        self.view_layout.addWidget(self.view_label)
        self.view_layout.addSpacerItem(self.horizontal_spacer_short)
        self.view_layout.addWidget(self.dimensions_view_combo)
        self.view_layout.addWidget(self.connections_button)
        self.view_layout.addWidget(self.show_selected_button)
        self.view_layout.addWidget(self.show_group_names_button)
        self.view_layout.addWidget(self.move_group_names_button)
        self.view_layout.addStretch()

        # Add the view_layout to the main layout
        self.main_layout.addLayout(self.view_layout)

        # Add a 'save to file' button
        self.save_file_button = QPushButton("Save to file")
        self.save_file_button.released.connect(self.save_file)

        # Add a 'save as image' button
        self.save_image_button = QPushButton("Save image")
        self.save_image_button.released.connect(self.save_image)

        self.save_layout.addWidget(self.save_file_button)
        self.save_layout.addWidget(self.save_image_button)
        self.save_layout.addStretch()

        self.main_layout.addLayout(self.save_layout)

        self.widget = QWidget()
        self.widget.setLayout(self.main_layout)

        self.setCentralWidget(self.widget)

        self.show()

        # Create the graph object
        self.network_plot = net.Network3D(self.view)

        self.load_file_label = scene.widgets.Label("Loading the input file - please wait")

        # The file to load has been given in the command-line -> load and display it
        if cfg.run_params['input_file'] is not None:
            # Define a runner for loading the file that will be executed in a different thread
            self.load_file_worker = io.ReadInputWorker()
            self.load_input_file()

    def load_input_file(self):
        self.load_file_worker.signals.finished.connect(self.receive_load_status)

        self.before = time.time()

        # Execute
        self.threadpool.start(self.load_file_worker)

        # Put a 'loading file' message
        self.canvas.central_widget.add_widget(self.load_file_label)

    def receive_load_status(self, status):
        if status == 0:
            self.after = time.time()
            duration = (self.after - self.before)
            print("Finished loading the input file - file is valid")

            # Init the layout variables
            fr.init_variables()

            # Remove the 'loading file' message
            self.load_file_label.parent = None

            # Create and display the FR layout as scatter plot
            self.before = time.time()
            self.network_plot.init_data(self.view)
            self.after = time.time()
            duration = (self.after - self.before)
            print("Prepare and display the initial plot took " + str(duration) + " seconds")

            # Update the text-field for the threshold if the file contains attraction values
            if cfg.type_of_values == 'att':
                self.pval_label.setText("Attraction value threshold:")
                self.pval_widget.setPlaceholderText(str(cfg.run_params['similarity_cutoff']))

        else:
            print("Input file is not valid:\n"+cfg.run_params['error'])

    def run_calc(self):

        if self.rounds_done == 0:
            print("Start the calculation")
            self.before = time.time()
        elif self.is_running_calc == 0:
            print("Resume the calculation")

        # Create a new calculation worker and start it only if the system is in init/stop state
        if self.is_running_calc == 0:
            self.run_calc_worker = lg.LayoutCalculationWorker()
            self.run_calc_worker.signals.finished_iteration.connect(self.update_plot)
            self.run_calc_worker.signals.stopped.connect(self.stopped_state)
            self.is_running_calc = 1

            # Hide the connections
            self.connections_button.setChecked(False)
            self.is_show_connections = 0
            self.network_plot.hide_connections()

            # Hide the selected names
            self.show_selected_button.setChecked(False)
            self.is_show_selected_names = 0
            self.network_plot.hide_sequences_names()
            self.network_plot.hide_group_names()

            # Hide the group names
            self.show_group_names_button.setChecked(False)
            self.is_show_group_names = 0
            self.network_plot.hide_group_names()

            # Uncheck the 'Move group names' button and move back to rotating mode
            self.move_group_names_button.setChecked(False)
            self.move_group_names()

            # If the clustering is done in 3D -> Move back to 3D view
            if cfg.run_params['dimensions_num_for_clustering'] == 3 and self.view_in_dimensions_num == 2:
                self.dimensions_view_combo.setCurrentIndex(0)

            # Disable all setup changes while calculating
            self.dimensions_clustering_combo.setEnabled(False)
            self.pval_widget.setEnabled(False)
            self.dimensions_view_combo.setEnabled(False)
            self.connections_button.setEnabled(False)
            self.show_selected_button.setEnabled(False)
            self.show_group_names_button.setEnabled(False)
            self.move_group_names_button.setEnabled(False)
            self.mode_combo.setEnabled(False)
            self.selection_type_combo.setEnabled(False)
            self.select_all_button.setEnabled(False)
            self.clear_selection_button.setEnabled(False)
            self.save_file_button.setEnabled(False)
            self.save_image_button.setEnabled(False)

            # Execute
            self.threadpool.start(self.run_calc_worker)

    def update_plot(self):
        self.rounds_done += 1
        self.network_plot.update_data(self.view, self.view_in_dimensions_num, 1)
        self.rounds_label.setText("Round: "+str(self.rounds_done))

        if self.rounds_done % 100 == 0:
            self.after = time.time()
            duration = (self.after - self.before)
            print("The calculation of " + str(self.rounds_done) + " rounds took " + str(duration) + " seconds")

    def stop_calc(self):
        if self.is_running_calc == 1:
            self.run_calc_worker.stop()

    def stopped_state(self):
        self.after = time.time()
        duration = (self.after - self.before)
        print("The calculation has stopped at round no. " + str(self.rounds_done))
        print("The calculation of " + str(self.rounds_done) + " rounds took " + str(duration) + " seconds")

        self.start_button.setText("Resume")
        self.is_running_calc = 0

        # Enable all settings buttons
        self.dimensions_clustering_combo.setEnabled(True)
        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.dimensions_view_combo.setEnabled(True)
        self.pval_widget.setEnabled(True)
        self.connections_button.setEnabled(True)
        if self.view_in_dimensions_num == 2:
            self.show_group_names_button.setEnabled(True)
            self.move_group_names_button.setEnabled(True)
        self.show_selected_button.setEnabled(True)
        self.mode_combo.setEnabled(True)
        self.selection_type_combo.setEnabled(True)
        self.select_all_button.setEnabled(True)
        self.clear_selection_button.setEnabled(True)
        self.save_file_button.setEnabled(True)
        self.save_image_button.setEnabled(True)

        # Update the coordinates saved in the sequences_array
        seq.update_positions(fr.coordinates.T)

        # Calculate the azimuth and elevation angles of the new points positions
        self.network_plot.calculate_initial_angles()

        self.network_plot.reset_group_names_positions(self.view)

    def init_coor(self):
        # Initialize the coordinates only if the calculation is not running
        if self.is_running_calc == 0:
            self.start_button.setText("Start clustering")
            self.before = None
            self.after = None
            self.is_running_calc = 0

            # Reset the number of rounds
            self.rounds_done = 0
            self.rounds_label.setText("Round: " + str(self.rounds_done))

            seq.init_positions()
            fr.init_variables()
            self.network_plot.update_data(self.view, self.view_in_dimensions_num, 1)
            # Calculate the angles of each point for future use when having rotations
            self.network_plot.calculate_initial_angles()

            print("Coordinates are initiated.")

            # Move back to interactive mode
            self.mode_combo.setCurrentIndex(0)

            # If the clustering is done in 3D -> Move to 3D view and reset the turntable camera
            if cfg.run_params['dimensions_num_for_clustering'] == 3:
                self.dimensions_view_combo.setCurrentIndex(0)

            self.network_plot.reset_rotation(self.view)
            self.network_plot.reset_group_names_positions(self.view)

    def manage_connections(self):
        if self.connections_button.isChecked():
            self.is_show_connections = 1
            self.network_plot.show_connections(self.view)
        else:
            self.is_show_connections = 0
            self.network_plot.hide_connections()

    def update_cutoff(self):
        print("Similairy cutoff has changed to: " + self.pval_widget.text())
        cfg.run_params['similarity_cutoff'] = float(self.pval_widget.text())
        sp.define_connected_sequences(cfg.type_of_values)
        sp.define_connected_sequences_list()
        self.network_plot.create_connections_by_bins()

        # 3D view
        if self.view_in_dimensions_num == 3:
            self.network_plot.update_connections(3)

        # 2D view
        else:
            # 3D clustering -> need to present the rotated-coordinates
            if cfg.run_params['dimensions_num_for_clustering'] == 3:
                self.network_plot.update_view(2)
            # 2D clustering
            else:
                self.network_plot.update_connections(2)

    def save_file(self):
        file_dialog = QFileDialog()
        saved_file, _ = file_dialog.getSaveFileName()

        if saved_file != "":
            file_object = io.FileHandler(cfg.output_format)
            file_object.write_file(saved_file)

    def save_image(self):
        file_dialog = QFileDialog()
        saved_file, _ = file_dialog.getSaveFileName()

        if saved_file != "":
            img = self.canvas.render()
            vispy.io.write_png(saved_file, img)

    def change_dimensions_view(self):

        # 3D view
        if self.dimensions_view_combo.currentIndex() == 0:
            self.view_in_dimensions_num = 3

            if self.show_group_names_button.isChecked():
                self.network_plot.hide_group_names()
            self.show_group_names_button.setEnabled(False)
            self.show_group_names_button.setChecked(False)
            self.move_group_names_button.setEnabled(False)
            self.move_group_names_button.setChecked(False)
            self.move_group_names()

            self.network_plot.set_3d_view(self.view)

        # 2D view
        else:
            self.view_in_dimensions_num = 2

            self.show_group_names_button.setEnabled(True)
            self.move_group_names_button.setEnabled(True)

            self.network_plot.set_2d_view(self.view)

    def change_dimensions_num_for_clustering(self):

        # 3D clustering
        if self.dimensions_clustering_combo.currentIndex() == 0:
            cfg.run_params['dimensions_num_for_clustering'] = 3
            self.dimensions_view_combo.setCurrentIndex(0)
            self.dimensions_view_combo.setEnabled(True)

        # 2D clustering
        else:
            cfg.run_params['dimensions_num_for_clustering'] = 2
            self.dimensions_view_combo.setEnabled(False)

            # The view was already in 2D -> update the rotated positions
            if self.view_in_dimensions_num == 2:
                self.network_plot.save_rotated_coordinates(self.view, 2)

            # Set 2D view
            else:
                self.dimensions_view_combo.setCurrentIndex(1)

    def change_mode(self):

        # Interactive mode (rotate/pan)
        if self.mode_combo.currentIndex() == 0:
            self.mode = "interactive"
            print("Interactive mode")

            self.network_plot.set_interactive_mode(self.view, self.view_in_dimensions_num)

            self.init_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.dimensions_clustering_combo.setEnabled(True)
            self.pval_widget.setEnabled(True)
            if cfg.run_params['dimensions_num_for_clustering'] == 3:
                self.dimensions_view_combo.setEnabled(True)
            if self.view_in_dimensions_num == 2:
                self.move_group_names_button.setEnabled(True)

            # Disconnect the selection-special special mouse-events and connect back the default behaviour of the
            # viewbox when the mouse moves
            self.canvas.events.mouse_release.disconnect(self.on_canvas_mouse_release)
            self.view.camera._viewbox.events.mouse_move.connect(self.view.camera.viewbox_mouse_event)
            self.view.camera._viewbox.events.mouse_press.connect(self.view.camera.viewbox_mouse_event)

        # Manual selection mode
        elif self.mode_combo.currentIndex() == 1:
            self.mode = "selection"
            print("Selection mode")

            self.network_plot.set_selection_mode(self.view, self.view_in_dimensions_num)

            self.init_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.dimensions_clustering_combo.setEnabled(False)
            self.pval_widget.setEnabled(False)
            self.dimensions_view_combo.setEnabled(False)
            self.move_group_names_button.setChecked(False)
            self.move_group_names_button.setEnabled(False)

            # Disconnect the default behaviour of the viewbox when the mouse moves
            # and connect special callbacks for mouse_move and mouse_release
            self.view.camera._viewbox.events.mouse_move.disconnect(self.view.camera.viewbox_mouse_event)
            self.view.camera._viewbox.events.mouse_press.disconnect(self.view.camera.viewbox_mouse_event)
            self.canvas.events.mouse_release.connect(self.on_canvas_mouse_release)

    def change_selection_type(self):

        # Sequences selection
        if self.selection_type_combo.currentIndex() == 0:
            self.selection_type = "sequences"

            # In case the 'show selected names' button is on - show sequences names instead of group names
            if self.is_show_selected_names:
                self.network_plot.hide_group_names()
                self.network_plot.show_sequences_names(self.view)

        # Groups selection
        else:
            self.selection_type = "groups"

            # In case the 'show selected names' button is on - show group names instead of sequences names
            if self.is_show_selected_names:
                self.network_plot.hide_sequences_names()
                self.network_plot.show_group_names(self.view, 'selected')

    def select_all(self):
        if self.view_in_dimensions_num == 2 or self.mode == "selection":
            dim_num = 2
        else:
            dim_num = 3
        self.network_plot.select_all(self.view, self.selection_type, dim_num)

        # Update the presentation of group names
        if self.is_show_selected_names == 1 and self.selection_type == 'groups':
            self.network_plot.show_group_names(self.view, 'all')

    def clear_selection(self):
        if self.view_in_dimensions_num == 2 or self.mode == "selection":
            dim_num = 2
        else:
            dim_num = 3
        self.network_plot.reset_selection(dim_num)

        # Hide the sequences names and release the button (if was checked)
        self.show_selected_button.setChecked(False)
        self.is_show_selected_names = 0
        self.network_plot.hide_sequences_names()
        if self.is_show_group_names == 0:
            self.network_plot.hide_group_names()

    def show_selected_names(self):
        if self.show_selected_button.isChecked():
            self.is_show_selected_names = 1
            # Show sequence names
            if self.selection_type == 'sequences':
                self.network_plot.show_sequences_names(self.view)
            # Show group names
            else:
                self.show_group_names_button.setChecked(False)
                self.is_show_group_names = 0
                self.network_plot.show_group_names(self.view, 'selected')
        else:
            self.is_show_selected_names = 0
            self.network_plot.hide_sequences_names()
            if self.is_show_group_names == 0:
                self.network_plot.hide_group_names()

    def manage_group_names(self):
        if self.show_group_names_button.isChecked():
            self.is_show_group_names = 1
            if self.selection_type == 'groups':
                self.show_selected_button.setChecked(False)
                self.is_show_selected_names = 0
            self.network_plot.show_group_names(self.view, 'all')
        else:
            self.is_show_group_names = 0
            self.network_plot.hide_group_names()
            #self.move_group_names_button.setChecked(False)
            #self.move_group_names()

    def move_group_names(self):
        if self.move_group_names_button.isChecked():
            # Disconnect the default behaviour of the viewbox when the mouse moves
            # and connect selection-special callbacks for mouse_move and mouse_release
            self.view.camera._viewbox.events.mouse_move.disconnect(self.view.camera.viewbox_mouse_event)
            self.view.camera._viewbox.events.mouse_press.disconnect(self.view.camera.viewbox_mouse_event)
            self.canvas.events.mouse_release.connect(self.on_canvas_mouse_release)
        else:
            # Disconnect the selection-special special mouse-events and connect back the default behaviour of the
            # viewbox when the mouse moves
            self.canvas.events.mouse_release.disconnect(self.on_canvas_mouse_release)
            self.view.camera._viewbox.events.mouse_move.connect(self.view.camera.viewbox_mouse_event)
            self.view.camera._viewbox.events.mouse_press.connect(self.view.camera.viewbox_mouse_event)

    ## Callback functions to deal with mouse and key events

    def on_canvas_mouse_move(self, event):
        if event.button == 1:
            self.canvas_mouse_drag(event)

    def on_canvas_mouse_release(self, event):
        if event.button == 1:
            self.canvas_left_mouse_release(event)

    def on_canvas_key_press(self, event):
        if event.key == 'Control':
            self.ctrl_key_pressed = 1

    def on_canvas_key_release(self, event):
        if event.key == 'Control':
            self.canvas_CTRL_release(event)

    def canvas_left_mouse_release(self, event):

        pos_array = event.trail()

        # The event is part of a selection process (sequences / groups)
        if self.mode == 'selection':

            # One-click event -> find the selected point
            if len(pos_array) == 1 or len(pos_array) == 2 and pos_array[0][0] == pos_array[1][0] \
                    and pos_array[0][1] == pos_array[1][1]:
                self.network_plot.find_selected_point(self.view, self.selection_type, event.pos)

                # The 'Show selected names' is on and Selection type is 'Groups' => update the group names display
                if self.is_show_selected_names and self.selection_type == 'groups':
                    self.network_plot.show_group_names(self.view, 'selection')

            # Drag event
            else:
                self.network_plot.remove_dragging_rectangle()
                self.network_plot.find_selected_area(self.view, self.selection_type, pos_array[0], event.pos)

                # The 'Show selected names' is on
                if self.is_show_selected_names == 1:

                    # Selection type is 'Groups' => update the group names display
                    if self.selection_type == 'groups':
                        self.network_plot.show_group_names(self.view, 'selection')

        # Interactive mode
        else:
            if self.move_group_names_button.isChecked():
                self.network_plot.finish_group_name_move()

    def canvas_mouse_drag(self, event):

        pos_array = event.trail()

        # Regular dragging event for selection
        if self.mode == "selection":

            # Initiation of dragging -> create a rectangle visual
            if len(pos_array) == 3:
                print(pos_array[0])
                self.network_plot.start_dragging_rectangle(self.view, pos_array[0])

            # Mouse dragging continues -> update the rectangle
            elif len(pos_array) > 3:
                # Update the rectangle if the mouse position was actually changed
                if pos_array[-1][0] != pos_array[-2][0] and pos_array[-1][1] != pos_array[-2][1]:
                    self.network_plot.update_dragging_rectangle(self.view, pos_array[0], pos_array[-1])

        # Interactive mode
        elif self.mode == "interactive":

            # CTRL key is pressed - move the selected data points
            if self.ctrl_key_pressed and len(pos_array) >= 2:

                # Update points location if the mouse position was changed above a certain distance
                distance = np.linalg.norm(pos_array[-1] - pos_array[-2])
                if distance >= 1:
                    self.network_plot.move_selected_points(self.view, self.view_in_dimensions_num, pos_array[-2],
                                                           pos_array[-1])

            # 'Move group names' button is checked
            elif self.move_group_names_button.isChecked():

                # Initiation of dragging -> find the group name visual to move
                if len(pos_array) == 3:
                    self.network_plot.find_group_name_to_move(self.view, pos_array[0])

                # Mouse dragging continues -> move the clicked selected name visual
                elif len(pos_array) > 3:
                    # Update the selected group name location if the mouse position was changed above a certain distance
                    distance = np.linalg.norm(pos_array[-1] - pos_array[-2])
                    if distance >= 1:
                        self.network_plot.move_group_name(self.view, pos_array[-2], pos_array[-1])

    def canvas_CTRL_release(self, event):
        self.ctrl_key_pressed = 0

        if self.mode == "interactive":
            self.network_plot.update_moved_positions(self.view_in_dimensions_num)










