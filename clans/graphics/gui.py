from PyQt5.QtCore import QThreadPool, Qt
from PyQt5.QtWidgets import *
from vispy import app, scene
import vispy.io
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
        self.rounds_done = 0
        self.view_in_dimensions_num = cfg.run_params['dimensions_num_for_clustering']
        self.last_view_in_dimensions_num = cfg.run_params['dimensions_num_for_clustering']
        self.mode = "interactive"  # switch between 'interactive' and 'selection' modes

        self.setWindowTitle("CLANS " + str(cfg.run_params['dimensions_num_for_clustering']) + "D-View")
        self.setGeometry(50, 50, 900, 800)

        # Define layouts within the main window
        self.main_layout = QVBoxLayout()
        self.round_layout = QHBoxLayout()
        self.buttons_layout = QHBoxLayout()
        self.pval_layout = QHBoxLayout()
        self.save_layout = QHBoxLayout()

        self.main_layout.setSpacing(5)

        self.horizontal_spacer = QSpacerItem(15, 22, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.app = app.use_app('pyqt5')

        self.canvas = scene.SceneCanvas(size=(700, 700), keys='interactive', show=True, bgcolor='w')
        self.main_layout.addWidget(self.canvas.native)

        # Add a ViewBox to let the user zoom/rotate
        self.view = self.canvas.central_widget.add_view()

        # Add a label for displaying the number of rounds done
        self.rounds_label = QLabel("Round: " + str(self.rounds_done))

        self.round_layout.addStretch()
        self.round_layout.addWidget(self.rounds_label)
        self.round_layout.addStretch()

        self.main_layout.addLayout(self.round_layout)

        # Add buttons (Init, Start, Stop, Show connections)
        self.start_button = QPushButton("Start calculation")
        self.stop_button = QPushButton("Stop calculation")
        self.init_button = QPushButton("Initialize coordinates")
        self.connections_button = QPushButton("Show connections")
        self.connections_button.setCheckable(True)

        self.start_button.pressed.connect(self.run_calc)
        self.stop_button.pressed.connect(self.stop_calc)
        self.init_button.pressed.connect(self.init_coor)
        self.connections_button.released.connect(self.manage_connections)

        self.buttons_layout.addWidget(self.init_button)
        self.buttons_layout.addWidget(self.start_button)
        self.buttons_layout.addWidget(self.stop_button)
        self.buttons_layout.addWidget(self.connections_button)

        self.main_layout.addLayout(self.buttons_layout)

        # Add a button to switch between 3D and 2D clustering
        self.dimensions_clustering_combo = QComboBox()
        self.dimensions_clustering_combo.addItems(["Cluster in 3D", "Cluster in 2D"])
        self.dimensions_clustering_combo.currentIndexChanged.connect(self.change_dimensions_num_for_clustering)

        # Add a text-field for the P-value / attraction-value threshold
        self.pval_label = QLabel(" Use P-values better than:")

        self.pval_widget = QLineEdit()
        self.pval_widget.setFixedSize(60, 22)
        self.pval_widget.setPlaceholderText(str(cfg.run_params['similarity_cutoff']))
        self.pval_widget.returnPressed.connect(self.update_cutoff)

        self.pval_layout.addWidget(self.pval_label)
        self.pval_layout.addWidget(self.pval_widget)
        self.pval_layout.addSpacerItem(self.horizontal_spacer)
        self.pval_layout.addWidget(self.dimensions_clustering_combo)
        self.pval_layout.addStretch()

        self.main_layout.addLayout(self.pval_layout)

        # Add a button to switch between 3D and 2D views
        self.dimensions_view_combo = QComboBox()
        self.dimensions_view_combo.addItems(["3D view", "2D view"])
        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.dimensions_view_combo.setCurrentIndex(0)
        else:
            self.dimensions_view_combo.setCurrentIndex(1)
            self.dimensions_view_combo.setEnabled(False)

        self.dimensions_view_combo.currentIndexChanged.connect(self.change_dimensions_view)

        # Add a button to switch between rotation and selection modes
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Interactive mode", "Selection mode"])

        self.mode_combo.currentIndexChanged.connect(self.change_mode)

        # Add a button to clear the current selection (active in 'selection mode')
        self.clear_selection_button = QPushButton("Clear selection")
        self.clear_selection_button.released.connect(self.clear_selection)
        #self.clear_selection_button.setEnabled(False)

        # Add a 'save to file' button
        self.save_file_button = QPushButton("Save to file")
        self.save_file_button.released.connect(self.save_file)

        # Add a 'save as image' button
        self.save_image_button = QPushButton("Save image")
        self.save_image_button.released.connect(self.save_image)

        self.save_layout.addWidget(self.dimensions_view_combo)
        self.save_layout.addWidget(self.mode_combo)
        self.save_layout.addWidget(self.clear_selection_button)
        self.save_layout.addSpacerItem(self.horizontal_spacer)
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
                self.pval_label.setText("Use attraction values better than:")
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
            self.connections_button.setEnabled(False)
            if self.is_show_connections:
                self.connections_button.setChecked(False)
                self.manage_connections()
            # If the clustering is done in 3D -> Move to 3D view and reset the turntable camera
            if cfg.run_params['dimensions_num_for_clustering'] == 3:
                self.dimensions_view_combo.setCurrentIndex(0)
                self.network_plot.reset_turntable_camera(self.view)
            # If the clustering is in 2D -> move to 2D view
            else:
                self.dimensions_view_combo.setCurrentIndex(1)

            # Switch back to interactive mode
            self.mode_combo.setCurrentIndex(0)

            # Disable all setup changes while calculating
            self.dimensions_view_combo.setEnabled(False)
            self.mode_combo.setEnabled(False)
            self.dimensions_clustering_combo.setEnabled(False)
            self.pval_widget.setEnabled(False)

            # Execute
            self.threadpool.start(self.run_calc_worker)

    def update_plot(self):
        self.rounds_done += 1
        self.network_plot.update_data(self.view, self.view_in_dimensions_num)
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

        self.start_button.setText("Resume calculation")
        self.is_running_calc = 0

        # Enable all settings buttons
        self.connections_button.setEnabled(True)
        self.dimensions_clustering_combo.setEnabled(True)
        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.dimensions_view_combo.setEnabled(True)
        self.pval_widget.setEnabled(True)
        self.mode_combo.setEnabled(True)

        # Update the coordinates saved in the sequences_array
        seq.update_positions(fr.coordinates.T)

        # Calculate the azimuth and elevation angles of the new points positions
        self.network_plot.calculate_initial_angles()

    def init_coor(self):
        # Initialize the coordinates only if the calculation is not running
        if self.is_running_calc == 0:
            self.start_button.setText("Start calculation")
            self.before = None
            self.after = None
            self.is_running_calc = 0

            # Reset the number of rounds
            self.rounds_done = 0
            self.rounds_label.setText("Round: " + str(self.rounds_done))

            seq.init_positions()
            fr.init_variables()

            print("Coordinates are initiated.")

            # If the clustering is done in 3D -> Move to 3D view and reset the turntable camera
            if cfg.run_params['dimensions_num_for_clustering'] == 3:
                self.dimensions_view_combo.setCurrentIndex(0)
                self.network_plot.reset_turntable_camera(self.view)
            else:
                self.dimensions_view_combo.setCurrentIndex(1)

            # Update the positions of the nodes and lines
            self.network_plot.update_data(self.view, self.view_in_dimensions_num)
            self.network_plot.update_connections()

            # Calculate the angles of each point for future use when having rotations
            self.network_plot.calculate_initial_angles()

    def manage_connections(self):
        if self.connections_button.isChecked():
            self.is_show_connections = 1
            self.network_plot.show_connections(self.view, self.view_in_dimensions_num)
        else:
            self.is_show_connections = 0
            self.network_plot.hide_connections()

    def update_cutoff(self):
        print("Similairy cutoff has changed to: " + self.pval_widget.text())
        cfg.run_params['similarity_cutoff'] = float(self.pval_widget.text())
        sp.define_connected_sequences(cfg.type_of_values)
        sp.define_connected_sequences_list()
        self.network_plot.create_connections_by_bins()

        if self.view_in_dimensions_num == 3 or cfg.run_params['dimensions_num_for_clustering'] == 2:
            self.network_plot.update_connections()

        # 2D view with 3D clustering -> need to present the rotated-coordinates
        else:
            self.network_plot.update_view()

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
            self.last_view_in_dimensions_num = 3
            self.network_plot.set_3d_view(self.view)
        # 2D view
        else:
            self.view_in_dimensions_num = 2
            self.last_view_in_dimensions_num = 2
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
            self.dimensions_view_combo.setCurrentIndex(1)
            self.dimensions_view_combo.setEnabled(False)

        fr.init_variables()

    def change_mode(self):

        # Interactive mode
        if self.mode_combo.currentIndex() == 0:
            self.mode = "interactive"

            # If the view was 3D before switching to selection mode - move back to 3D
            if self.last_view_in_dimensions_num == 3:
                self.dimensions_view_combo.setCurrentIndex(0)
            self.dimensions_view_combo.setEnabled(True)

            # Disconnect the selection-special special mouse-events and connect back the default behavour of the
            # PanZoom camera when the mouse moves
            self.canvas.events.mouse_release.disconnect(self.on_canvas_mouse_release)
            self.canvas.events.mouse_move.disconnect(self.on_canvas_mouse_move)
            self.view.camera._viewbox.events.mouse_move.connect(self.view.camera.viewbox_mouse_event)

        # Selection mode
        else:
            self.mode = "selection"

            # Move to 2D view and remember that it was 3D view before
            if self.view_in_dimensions_num == 3:
                self.dimensions_view_combo.setCurrentIndex(1)
                self.dimensions_view_combo.setEnabled(False)
                self.last_view_in_dimensions_num = 3

            # Disconnect the default behaviour of the PanZoom camera when the mouse moves
            # and connect selection-special callbacks for mouse_move and mouse_release
            self.view.camera._viewbox.events.mouse_move.disconnect(self.view.camera.viewbox_mouse_event)
            self.canvas.events.mouse_release.connect(self.on_canvas_mouse_release)
            self.canvas.events.mouse_move.connect(self.on_canvas_mouse_move)

    def clear_selection(self):
        self.network_plot.reset_selection(self.view_in_dimensions_num)

    ## Events

    def on_canvas_mouse_move(self, event):
        if self.mode == "selection" and event.button == 1:
            self.canvas_mouse_drag(event)

    def on_canvas_mouse_release(self, event):
        if event.button == 1:
            self.canvas_left_mouse_release(event)

    def canvas_left_mouse_release(self, event):

        pos_array = event.trail()

        # One-click event -> find the selected point
        if len(pos_array) == 1 or len(pos_array) == 2 and pos_array[0][0] == pos_array[1][0] \
                and pos_array[0][1] == pos_array[1][1]:
            self.network_plot.find_selected_point(self.view, event.pos)

        # Drag event
        else:
            self.network_plot.remove_dragging_rectangle()
            self.network_plot.find_selected_area(self.view, pos_array[0], event.pos)

    def canvas_mouse_drag(self, event):

        pos_array = event.trail()

        # Initiation of dragging -> create a rectangle visual
        if len(pos_array) == 3:
            self.network_plot.start_dragging_rectangle(self.view, pos_array[0])

        # Mouse dragging continues -> update the rectangle
        elif len(pos_array) > 3:
            if pos_array[-1][0] != pos_array[-2][0] and pos_array[-1][1] != pos_array[-2][1]:
                self.network_plot.update_dragging_rectangle(self.view, pos_array[0], pos_array[-1])







