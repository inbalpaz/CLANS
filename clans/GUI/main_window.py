from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import *
from vispy import app, scene
from vispy.color import ColorArray
import numpy as np
from PIL import Image
import time
import re
import clans.config as cfg
import clans.io.io_gui as io
import clans.io.file_formats as ff
import clans.layouts.layout_gui as lg
import clans.layouts.fruchterman_reingold_class as fr_class
import clans.graphics.network3d as net
import clans.graphics.colorbar as colorbar
import clans.data.sequences as seq
import clans.data.sequence_pairs as sp
import clans.data.groups as groups
import clans.GUI.group_dialogs as gd
import clans.GUI.windows as windows
import clans.GUI.metadata_dialogs as md
import clans.GUI.message_dialogs as mes_dialogs
#import clans.GUI.text_dialogs as td
import clans.GUI.conf_dialogs as cd
import clans.graphics.colors as colors
#import clans.io.try_io as try_io


class Button(QPushButton):

    def __init__(self, title):
        super().__init__()

        self.setText(title)
        self.setStyleSheet("font-size: 11px; height: 15px")


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.app = app.use_app('pyqt5')

        self.threadpool = QThreadPool()

        # Define a runner that will be executed in a different thread
        self.run_calc_worker = None

        # Define an object to hold the fruchterman-reingold calculation information
        self.fr_object = None

        # To hold the loaded / saved file-name
        self.file_name = ""

        # Calculation-related variables
        self.before = None
        self.after = None
        self.is_running_calc = 0
        self.is_show_connections = 0
        self.is_show_selected_names = 0
        self.is_show_group_names = 0
        self.group_names_display = 'all'
        self.rounds_done = 0
        self.rounds_done_subset = 0
        self.view_in_dimensions_num = cfg.run_params['dimensions_num_for_clustering']
        self.dim_num = self.view_in_dimensions_num  # The effective view (set by the user / selection mode / move data mode)
        self.mode = "interactive"  # Modes of interaction: 'interactive' (rotate/pan) / 'selection'
        self.selection_type = "sequences"  # switch between 'sequences' and 'groups' modes
        self.color_by = "groups"  # Color the nodes according to: 'groups' / 'param'
        self.group_by = "manual"  # Determines which grouping methos is active. ('manual', 'input_file', 'taxonomy', etc...)
        self.is_subset_mode = 0  # In subset mode, only the selected data-points are displayed
        self.z_indexing_mode = "auto"  # Switch between 'auto' and 'groups' modes
        self.ctrl_key_pressed = 0
        self.visual_to_move = None
        self.is_init = 0
        self.done_color_by_length = 0
        self.added_user_param = 0
        self.load_file_worker = None

        self.setWindowTitle("CLANS " + str(self.view_in_dimensions_num) + "D-View")
        self.setGeometry(50, 50, 900, 850)

        # Define layouts within the main window
        self.main_layout = QVBoxLayout()
        self.round_layout = QHBoxLayout()
        self.calc_layout = QHBoxLayout()
        self.selection_layout = QHBoxLayout()
        self.view_layout = QHBoxLayout()
        self.groups_layout = QHBoxLayout()
        self.display_layout = QHBoxLayout()

        self.main_layout.setSpacing(4)

        self.horizontal_spacer_long = QSpacerItem(18, 24, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer_short = QSpacerItem(10, 24, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer_tiny = QSpacerItem(5, 24, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Define a menu-bar
        self.main_menu = QMenuBar()
        self.setMenuBar(self.main_menu)
        self.main_menu.setNativeMenuBar(False)
        #self.main_menu.setStyleSheet("border-bottom: 1px solid black; background-color: gray;")

        # Create the File menu
        self.file_menu = self.main_menu.addMenu("File")

        self.load_file_submenu = self.file_menu.addMenu("Load file")
        self.load_clans_file_sumenu = self.load_file_submenu.addMenu("CLANS format")

        self.load_clans_file_action = QAction("Standard CLANS (compatible)", self)
        self.load_clans_file_action.triggered.connect(self.load_clans_file)

        self.load_mini_clans_file_action = QAction("Minimal CLANS (without sequences)", self)
        self.load_mini_clans_file_action.triggered.connect(self.load_mini_clans_file)

        self.load_delimited_file_action = QAction("Tab-delimited format", self)
        self.load_delimited_file_action.triggered.connect(self.load_delimited_file)

        self.load_clans_file_sumenu.addAction(self.load_clans_file_action)
        self.load_clans_file_sumenu.addAction(self.load_mini_clans_file_action)
        self.load_file_submenu.addAction(self.load_delimited_file_action)

        self.save_file_submenu = self.file_menu.addMenu("Save to file")
        self.save_clans_submenu = self.save_file_submenu.addMenu("CLANS format")

        self.save_clans_file_action = QAction("Standard CLANS (compatible)", self)
        self.save_clans_file_action.triggered.connect(self.save_clans_file)

        self.save_mini_clans_file_action = QAction("Minimal CLANS (without sequences)", self)
        self.save_mini_clans_file_action.triggered.connect(self.save_mini_clans_file)

        self.save_delimited_file_action = QAction("Tab-delimited format", self)
        self.save_delimited_file_action.triggered.connect(self.save_delimited_file)

        self.save_clans_submenu.addAction(self.save_clans_file_action)
        self.save_clans_submenu.addAction(self.save_mini_clans_file_action)
        self.save_file_submenu.addAction(self.save_delimited_file_action)

        self.save_image_action = QAction("Save as image", self)
        self.save_image_action.triggered.connect(self.save_image)

        self.quit_action = QAction("Quit", self)
        self.quit_action.triggered.connect(qApp.quit)

        self.file_menu.addAction(self.save_image_action)
        self.file_menu.addAction(self.quit_action)

        # Create the Edit menu
        #self.edit_menu = self.main_menu.addMenu("Edit")

        # Create the View menu
        #self.view_menu = self.main_menu.addMenu("View")

        # Create the Configuration menu
        self.conf_menu = self.main_menu.addMenu("Configure")

        self.conf_layout_submenu = self.conf_menu.addMenu("Layout parameters")
        self.conf_FR_layout_action = QAction("Fruchterman-Reingold", self)
        self.conf_FR_layout_action.triggered.connect(self.conf_FR_layout)
        self.conf_layout_submenu.addAction(self.conf_FR_layout_action)

        self.conf_nodes_action = QAction("Data-points default parameters", self)
        self.conf_nodes_action.triggered.connect(self.conf_nodes)
        self.conf_menu.addAction(self.conf_nodes_action)

        # Create the Tools menu
        self.tools_menu = self.main_menu.addMenu("Tools")
        self.group_by_submenu = self.tools_menu.addMenu("Group data by:")
        self.color_by_submenu = self.tools_menu.addMenu("Color data by:")

        # Group by taxonomy action
        self.group_by_tax_action = QAction("NCBI Taxonomy", self)
        self.group_by_tax_action.setEnabled(False)
        self.group_by_tax_action.triggered.connect(self.group_by_taxonomy)

        self.group_by_submenu.addAction(self.group_by_tax_action)

        # Group-by user-defined param action
        self.add_groups_from_metadata_action = QAction("Add custom grouping category", self)
        self.add_groups_from_metadata_action.triggered.connect(self.add_groups_from_metadata)

        self.group_by_submenu.addAction(self.add_groups_from_metadata_action)

        # Color by seq_length action
        self.color_by_length_action = QAction("Sequence length", self)
        self.color_by_length_action.setEnabled(False)
        self.color_by_length_action.triggered.connect(self.open_color_by_length_dialog)

        self.color_by_submenu.addAction(self.color_by_length_action)

        # Color-by user-defined param action
        self.color_by_param_action = QAction("Add/Configure custom parameter", self)
        self.color_by_param_action.triggered.connect(self.open_color_by_param_dialog)

        self.color_by_submenu.addAction(self.color_by_param_action)

        # Create the canvas (the graph area)
        self.canvas = scene.SceneCanvas(size=(800, 750), keys='interactive', show=True, bgcolor='w')
        self.canvas.events.mouse_move.connect(self.on_canvas_mouse_move)
        self.canvas.events.mouse_double_click.connect(self.on_canvas_mouse_double_click)
        self.canvas.events.key_press.connect(self.on_canvas_key_press)
        self.canvas.events.key_release.connect(self.on_canvas_key_release)
        self.main_layout.addWidget(self.canvas.native)

        # Add a grid for two view-boxes
        self.grid = self.canvas.central_widget.add_grid()
        self.view = self.grid.add_view(0, 0, col_span=4)  # Add the graph area viewbox
        self.colorbar_view = self.grid.add_view(0, 4)  # Add a viewbox for a colorbar legend

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")

        # Add a label for displaying the number of rounds done
        self.rounds_label = QLabel("Round: " + str(self.rounds_done))

        self.round_layout.addStretch()
        self.round_layout.addWidget(self.rounds_label)
        self.round_layout.addStretch()

        self.main_layout.addLayout(self.round_layout)

        self.calc_label = QLabel("Clustering:")
        self.calc_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add calculation buttons (Init, Start, Stop)
        self.start_button = QPushButton("Start")
        self.start_button.setEnabled(False)
        self.start_button.pressed.connect(self.run_calc)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.pressed.connect(self.stop_calc)

        self.init_button = QPushButton("Initialize")
        self.init_button.setEnabled(False)
        self.init_button.pressed.connect(self.init_coor)

        # Add a button to switch between 3D and 2D clustering
        self.dimensions_clustering_combo = QComboBox()
        self.dimensions_clustering_combo.addItems(["3D Clustering", "2D Clustering"])
        self.dimensions_clustering_combo.setEnabled(False)
        self.dimensions_clustering_combo.currentIndexChanged.connect(self.change_dimensions_num_for_clustering)

        # Add a text-field for the P-value / attraction-value threshold
        self.pval_label = QLabel("P-value threshold:")
        self.pval_widget = QLineEdit()
        self.pval_widget.setFixedSize(60, 24)
        self.pval_widget.setText(str(cfg.run_params['similarity_cutoff']))
        self.pval_widget.setEnabled(False)
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
        self.calc_layout.addWidget(self.error_label)
        self.calc_layout.addStretch()

        # Add the calc_layout to the main layout
        self.main_layout.addLayout(self.calc_layout)

        # Add a combo-box to switch between user-interaction modes
        self.mode_label = QLabel("Interaction mode:")
        self.mode_label.setStyleSheet("color: maroon; font-weight: bold;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Rotate/Pan graph", "Select data-points", "Move/Edit text"])
        self.mode_combo.setEnabled(False)
        self.mode_combo.currentIndexChanged.connect(self.change_mode)

        self.view_label = QLabel("View:")
        self.view_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add a combo-box to switch between 3D and 2D views
        self.dimensions_view_combo = QComboBox()
        self.dimensions_view_combo.addItems(["3D", "2D"])
        self.dimensions_view_combo.setEnabled(False)
        self.dimensions_view_combo.currentIndexChanged.connect(self.change_dimensions_view)

        # Add a button to change the Z-indexing of nodes in 2D presentation
        self.z_index_mode_combo = QComboBox()
        self.z_index_mode_combo.addItems(["Auto Z-index", "By groups order"])
        if self.dim_num == 3 or len(cfg.groups_dict[self.group_by]) < 2:
            self.z_index_mode_combo.setEnabled(False)
        self.z_index_mode_combo.currentIndexChanged.connect(self.manage_z_indexing)

        # Add a combo-box to move between full-data mode and selected subset mode
        self.data_mode_combo = QComboBox()
        self.data_mode_combo.addItems(["Full dataset", "Selected subset"])
        self.data_mode_combo.setEnabled(False)
        self.data_mode_combo.currentIndexChanged.connect(self.manage_subset_presentation)

        # Add the widgets to the view_layout
        self.view_layout.addWidget(self.mode_label)
        self.view_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.view_layout.addWidget(self.mode_combo)
        self.view_layout.addSpacerItem(self.horizontal_spacer_long)
        self.view_layout.addWidget(self.view_label)
        self.view_layout.addSpacerItem(self.horizontal_spacer_short)
        self.view_layout.addWidget(self.dimensions_view_combo)
        self.view_layout.addWidget(self.data_mode_combo)
        self.view_layout.addWidget(self.z_index_mode_combo)
        self.view_layout.addStretch()

        # Add the view_layout to the main layout
        self.main_layout.addLayout(self.view_layout)

        self.display_label = QLabel("Display:")
        self.display_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add a button to show/hide the connections
        self.connections_button = QPushButton("Connections")
        self.connections_button.setCheckable(True)
        self.connections_button.setEnabled(False)
        self.connections_button.released.connect(self.manage_connections)

        # Add a button to show the selected sequences names on screen
        self.show_selected_names_button = QPushButton("Selected names")
        self.show_selected_names_button.setCheckable(True)
        self.show_selected_names_button.setEnabled(False)
        self.show_selected_names_button.released.connect(self.show_selected_names)

        # Add a button to show the group names on screen
        self.show_group_names_button = QPushButton("Group names")
        self.show_group_names_button.setCheckable(True)
        if len(cfg.groups_dict[self.group_by]) == 0:
            self.show_group_names_button.setEnabled(False)
        self.show_group_names_button.released.connect(self.manage_group_names)

        # Add a combo-box to choose whether showing the selected group names only or all the group names
        self.show_groups_combo = QComboBox()
        self.show_groups_combo.addItems(["All", "Selected"])
        self.show_groups_combo.setEnabled(False)
        self.show_groups_combo.currentIndexChanged.connect(self.change_group_names_display)

        # Add 'reset group names' button
        self.reset_group_names_button = QPushButton("Init names")
        self.reset_group_names_button.setEnabled(False)
        self.reset_group_names_button.pressed.connect(self.reset_group_names_positions)

        # Add a combo-box to switch between color-by options
        self.color_by_label = QLabel("Color by:")
        self.color_by_label.setStyleSheet("color: maroon; font-weight: bold;")

        self.color_by_combo = QComboBox()
        self.color_by_combo.addItem("Groups/Default")
        self.color_by_combo.setEnabled(False)
        self.color_by_combo.currentIndexChanged.connect(self.change_coloring)

        # Add 'Add text' button
        #self.add_text_button = QPushButton("Add text")
        #self.add_text_button.setEnabled(False)
        #self.add_text_button.pressed.connect(self.add_text)

        # Add the widgets to the view_layout
        self.display_layout.addWidget(self.display_label)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.connections_button)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.show_selected_names_button)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.show_group_names_button)
        self.display_layout.addWidget(self.show_groups_combo)
        self.display_layout.addWidget(self.reset_group_names_button)
        self.display_layout.addSpacerItem(self.horizontal_spacer_short)
        self.display_layout.addWidget(self.color_by_label)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.color_by_combo)
        #self.display_layout.addWidget(self.add_text_button)
        self.display_layout.addStretch()

        # Add the view_layout to the main layout
        self.main_layout.addLayout(self.display_layout)

        self.selection_label = QLabel("Selection:")
        self.selection_label.setStyleSheet("color: maroon; font-weight: bold;")

        self.selection_mode_label = QLabel("Mode:")

        # Add a combo-box to switch between sequences / groups selection
        self.selection_type_combo = QComboBox()
        self.selection_type_combo.addItems(["Data-points", "Groups"])
        self.selection_type_combo.setEnabled(False)
        self.selection_type_combo.currentIndexChanged.connect(self.change_selection_type)

        # Add a button to select all the sequences / groups
        self.select_all_button = QPushButton("Select all")
        self.select_all_button.setEnabled(False)
        self.select_all_button.released.connect(self.select_all)

        # Add a button to clear the current selection
        self.clear_selection_button = QPushButton("Clear")
        self.clear_selection_button.setEnabled(False)
        self.clear_selection_button.released.connect(self.clear_selection)

        # Add a button to show the selected sequences/groups names on screen
        self.open_selected_button = QPushButton("Edit selected sequences")
        self.open_selected_button.setEnabled(False)
        self.open_selected_button.released.connect(self.open_selected_window)

        # Add a button to show the selected sequences/groups names on screen
        self.select_by_name_button = QPushButton("Select by name")
        self.select_by_name_button.setEnabled(False)
        self.select_by_name_button.released.connect(self.select_by_name)

        # Add the widgets to the selection_layout
        self.selection_layout.addWidget(self.selection_label)
        self.selection_layout.addSpacerItem(self.horizontal_spacer_short)
        self.selection_layout.addWidget(self.selection_mode_label)
        self.selection_layout.addWidget(self.selection_type_combo)
        self.selection_layout.addSpacerItem(self.horizontal_spacer_short)
        self.selection_layout.addWidget(self.select_all_button)
        self.selection_layout.addWidget(self.clear_selection_button)
        self.selection_layout.addWidget(self.select_by_name_button)
        self.selection_layout.addWidget(self.open_selected_button)
        self.selection_layout.addStretch()

        # Add the selection_layout to the main layout
        self.main_layout.addLayout(self.selection_layout)

        self.groups_label = QLabel("Groups:")
        self.groups_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add a button to edit the groups (opens the editing-groups window)
        self.edit_groups_button = QPushButton("Edit groups")
        self.edit_groups_button.setEnabled(False)
        self.edit_groups_button.released.connect(self.edit_groups)

        # Add a button for adding the selected sequences to a new / existing (opens a dialog)
        self.add_to_group_button = QPushButton("Add selected to group")
        self.add_to_group_button.released.connect(self.open_add_to_group_dialog)
        self.add_to_group_button.setEnabled(False)

        # Add a button for removing the selected sequences from their group(s)
        self.remove_selected_button = QPushButton("Remove selected from group(s)")
        self.remove_selected_button.released.connect(self.remove_selected_from_group)
        self.remove_selected_button.setEnabled(False)

        # Add a combo-box to switch between group-by options
        self.group_by_label = QLabel("Group by:")
        self.group_by_label.setStyleSheet("color: maroon; font-weight: bold;")

        self.group_by_combo = QComboBox()
        self.group_by_combo.addItem("Manual definition")
        self.group_by_combo.setEnabled(False)
        self.group_by_combo.currentIndexChanged.connect(self.change_grouping)

        self.groups_layout.addWidget(self.groups_label)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_short)
        self.groups_layout.addWidget(self.edit_groups_button)
        self.groups_layout.addWidget(self.add_to_group_button)
        self.groups_layout.addWidget(self.remove_selected_button)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_long)
        self.groups_layout.addWidget(self.group_by_label)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.groups_layout.addWidget(self.group_by_combo)
        self.groups_layout.addStretch()

        self.main_layout.addLayout(self.groups_layout)

        self.widget = QWidget()
        self.widget.setLayout(self.main_layout)
        self.setCentralWidget(self.widget)

        self.show()

        # Create the graph object
        self.network_plot = net.Network3D(self.view)

        # Create the colorbar object
        self.colorbar_plot = colorbar.Colorbar(self.colorbar_view)

        # Create a window for the selected sequences (without showing it)
        self.selected_seq_window = windows.SelectedSeqWindow(self, self.network_plot)

        # Create a window to display sequence search results (without showing it)
        self.search_window = windows.SearchResultsWindow(self, self.network_plot)

        # Create a text visual to display the 'loading file' message
        self.load_file_label = scene.widgets.Label("Loading the input file - please wait", bold=True,
                                                   font_size=15)

        # Create a text visual to display an error message when any
        self.file_error_label = scene.widgets.Label("", bold=True, font_size=12, color='red')

        # The file to load has been given in the command-line -> load and display it
        if cfg.run_params['input_file'] is not None:
            # Define a runner for loading the file that will be executed in a different thread
            self.load_file_worker = io.ReadInputWorker(cfg.run_params['input_format'])
            self.load_input_file()

    # Bring all the buttons to their default state
    def reset_window(self):

        self.is_init = 1

        self.file_error_label.text = ""
        self.file_error_label.parent = None
        self.error_label.setText("")

        self.color_by_length_action.setEnabled(False)
        self.group_by_tax_action.setEnabled(False)

        self.start_button.setText("Start")
        self.dimensions_clustering_combo.setCurrentIndex(0)

        self.mode_combo.setCurrentIndex(0)
        self.selection_type_combo.setCurrentIndex(0)
        self.open_selected_button.setEnabled(False)

        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.dimensions_view_combo.setCurrentIndex(0)
        else:
            self.dimensions_view_combo.setCurrentIndex(1)
            self.dimensions_view_combo.setEnabled(False)

        self.z_index_mode_combo.setEnabled(False)
        self.z_index_mode_combo.setCurrentIndex(0)

        self.connections_button.setChecked(False)
        self.show_selected_names_button.setChecked(False)
        self.show_selected_names_button.setEnabled(False)
        self.data_mode_combo.setEnabled(False)
        self.data_mode_combo.setCurrentIndex(0)

        self.add_to_group_button.setEnabled(False)
        self.remove_selected_button.setEnabled(False)
        self.edit_groups_button.setEnabled(False)
        self.show_group_names_button.setChecked(False)
        self.show_group_names_button.setEnabled(False)
        self.reset_group_names_button.setEnabled(False)
        self.show_groups_combo.setCurrentIndex(0)
        self.show_groups_combo.setEnabled(False)

        # Remove all the color-by options except 'groups' (the default)
        self.color_by_combo.clear()
        self.color_by_combo.addItem("Groups/Default")
        self.color_by_combo.setEnabled(False)
        self.colorbar_plot.hide_colorbar()

        # Remove all the group-by options except 'Manual' (the default)
        self.group_by_combo.clear()
        self.group_by_combo.addItem("Manual definition")
        self.group_by_combo.setEnabled(False)

        # Reset the list of sequences in the 'selected sequences' window
        self.selected_seq_window.clear_list()
        # Close the window
        self.selected_seq_window.close_window()

        self.is_init = 0

    def reset_variables(self):

        # Reset global variables
        cfg.groups_dict = dict()
        cfg.groups_dict['input_file'] = dict()
        cfg.groups_dict['manual'] = dict()
        cfg.sequences_in_groups = dict()
        cfg.sequences_in_groups['input_file'] = []
        cfg.sequences_in_groups['manual'] = []
        cfg.taxonomy_dict = {}
        cfg.organisms_dict = {}
        cfg.sequences_ID_to_index = {}
        cfg.sequences_numeric_params = {}
        cfg.sequences_discrete_params = {}
        cfg.seq_by_tax_level_dict['Family'] = {}
        cfg.seq_by_tax_level_dict['Order'] = {}
        cfg.seq_by_tax_level_dict['Class'] = {}
        cfg.seq_by_tax_level_dict['Phylum'] = {}
        cfg.seq_by_tax_level_dict['Kingdom'] = {}
        cfg.seq_by_tax_level_dict['Domain'] = {}
        cfg.similarity_values_list = []
        cfg.similarity_values_mtx = []
        cfg.attraction_values_mtx = []
        cfg.connected_sequences_mtx = []
        cfg.connected_sequences_list = []
        cfg.att_values_for_connected_list = []
        cfg.connected_sequences_list_subset = []
        cfg.att_values_for_connected_list_subset = []

        cfg.run_params['num_of_rounds'] = 0
        cfg.run_params['rounds_done'] = 0
        cfg.run_params['is_problem'] = False
        cfg.run_params['error'] = None
        cfg.run_params['input_format'] = cfg.input_format
        cfg.run_params['output_format'] = cfg.output_format
        cfg.run_params['type_of_values'] = cfg.type_of_values
        cfg.run_params['similarity_cutoff'] = cfg.similarity_cutoff
        cfg.run_params['is_taxonomy_available'] = False
        cfg.run_params['finished_taxonomy_search'] = False
        cfg.run_params['cooling'] = cfg.layouts['FR']['params']['cooling']
        cfg.run_params['maxmove'] = cfg.layouts['FR']['params']['maxmove']
        cfg.run_params['att_val'] = cfg.layouts['FR']['params']['att_val']
        cfg.run_params['att_exp'] = cfg.layouts['FR']['params']['att_exp']
        cfg.run_params['rep_val'] = cfg.layouts['FR']['params']['rep_val']
        cfg.run_params['rep_exp'] = cfg.layouts['FR']['params']['rep_exp']
        cfg.run_params['dampening'] = cfg.layouts['FR']['params']['dampening']
        cfg.run_params['gravity'] = cfg.layouts['FR']['params']['gravity']
        cfg.min_param_color = ColorArray([1.0, 1.0, 0.0, 1.0])
        cfg.max_param_color = ColorArray([1.0, 0.0, 0.0, 1.0])
        cfg.short_color = ColorArray([1.0, 1.0, 0.0, 1.0])
        cfg.long_color = ColorArray([1.0, 0.0, 0.0, 1.0])

        # Reset MainWindow class variables
        self.is_running_calc = 0
        self.is_show_connections = 0
        self.is_show_selected_names = 0
        self.is_show_group_names = 0
        self.group_names_display = 'all'
        self.rounds_done = 0
        self.rounds_done_subset = 0
        self.view_in_dimensions_num = cfg.run_params['dimensions_num_for_clustering']
        self.dim_num = self.view_in_dimensions_num
        self.mode = "interactive"  # Modes of interaction: 'interactive' (rotate/pan) / 'selection'
        self.selection_type = "sequences"  # switch between 'sequences' and 'groups' modes
        self.is_subset_mode = 0  # In subset mode, only the selected data-points are displayed
        self.z_indexing_mode = "auto"  # Switch between 'auto' and 'groups' modes
        self.ctrl_key_pressed = 0
        self.done_color_by_length = 0
        self.added_user_param = 0
        self.color_by = 'groups'

    def load_input_file(self):
        self.load_file_worker.signals.finished.connect(self.receive_load_status)

        self.before = time.time()

        # Execute
        self.threadpool.start(self.load_file_worker)

        # Put a 'loading file' message
        self.canvas.central_widget.add_widget(self.load_file_label)

    def receive_load_status(self, status, file_name):

        self.is_init = 1

        self.file_name = file_name

        # Loaded file is valid
        if status == 0:

            if cfg.run_params['is_debug_mode']:
                print("Finished loading the input file - file is valid")

                # Print the parameters
                print("Run parameters:")
                for i in cfg.run_params:
                    print(i, cfg.run_params[i])

            # Create a new Fruchterman-Reingold object to be able to start the calculation
            self.fr_object = fr_class.FruchtermanReingold(cfg.sequences_array['x_coor'], cfg.sequences_array['y_coor'],
                                                          cfg.sequences_array['z_coor'])

            # Remove the 'loading file' message
            self.load_file_label.parent = None

            # Set the window title to include the file name
            self.setWindowTitle("CLANS " + str(self.view_in_dimensions_num) + "D-View of " + self.file_name)

            # Enable the controls
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.init_button.setEnabled(True)
            self.dimensions_clustering_combo.setEnabled(True)
            self.dimensions_view_combo.setEnabled(True)
            self.pval_widget.setEnabled(True)
            self.mode_combo.setEnabled(True)
            self.select_all_button.setEnabled(True)
            self.clear_selection_button.setEnabled(True)
            self.select_by_name_button.setEnabled(True)
            self.connections_button.setEnabled(True)
            #self.add_text_button.setEnabled(True)

            groups_num = len(cfg.groups_dict['input_file'])
            if groups_num > 0:

                # Pop up an error message
                if groups_num > 100:
                    message = "The Number of groups exceeds 100 (" + str(groups_num) + " groups).\n" \
                                                                                   "Continue without loading groups."
                    print(message)
                    dlg = mes_dialogs.MessageDialog(message)

                    if dlg.exec_():
                        cfg.groups_dict['input_file'] = {}

                # The number of groups is ok
                else:
                    self.edit_groups_button.setEnabled(True)
                    self.show_group_names_button.setEnabled(True)
                    self.group_by = 'input_file'
                    self.group_by_combo.addItem("Input CLANS file")
                    self.group_by_combo.setCurrentIndex(1)
                    self.group_by_combo.setEnabled(True)

            # Update the file name in the selected sequences window
            self.selected_seq_window.update_window_title(self.file_name)

            # Create and display the FR layout as scatter plot
            self.before = time.time()
            self.network_plot.init_data(self.fr_object)

            if cfg.run_params['is_debug_mode']:
                self.after = time.time()
                duration = (self.after - self.before)
                print("Prepare and display the initial plot took " + str(duration) + " seconds")

            # Update the number of rounds label
            self.rounds_done = cfg.run_params['rounds_done']
            self.rounds_label.setText("Round: " + str(self.rounds_done))
            if self.rounds_done > 0:
                self.start_button.setText("Resume")

            # Update the text-field for the threshold according to the type of values
            if cfg.run_params['type_of_values'] == 'att':
                self.pval_label.setText("Attraction value threshold:")
            else:
                self.pval_label.setText("P-value threshold:")
            self.pval_widget.setText(str(cfg.run_params['similarity_cutoff']))

            if cfg.run_params['dimensions_num_for_clustering'] == 2:
                self.dimensions_clustering_combo.setCurrentIndex(1)

            # Calculate the sequence length parameter for this dataset (if input contains sequences)
            if cfg.run_params['input_format'] == 'clans':
                self.color_by_length_action.setEnabled(True)
                self.group_by_tax_action.setEnabled(True)

            ## Debug
            #try_io.create_artificial_metadata_groups_file_with_seq_name(self.file_name)
            #try_io.create_artificial_metadata_groups_file_with_seq_index(self.file_name)

        else:
            # Remove the 'loading file' message from the scene and put an error message instead
            self.load_file_label.parent = None
            self.file_error_label.text = cfg.run_params['error'] + "\n\nPlease load a new file and select the correct format"
            self.canvas.central_widget.add_widget(self.file_error_label)

        self.is_init = 0

    def load_clans_file(self):

        opened_file, _ = QFileDialog.getOpenFileName(self, "Open file", "", "Clans files (*.clans)")

        if opened_file:
            print("Loading " + opened_file)

            # Bring the controls to their initial state
            self.reset_window()

            # Clear the canvas
            self.network_plot.reset_data()

            # Initialize all the global data-structures
            self.reset_variables()

            cfg.run_params['input_file'] = opened_file
            cfg.run_params['input_format'] = 'clans'
            self.setWindowTitle("CLANS " + str(self.view_in_dimensions_num) + "D-View")

            # Define a runner for loading the file that will be executed in a different thread
            self.load_file_worker = io.ReadInputWorker(cfg.run_params['input_format'])
            self.load_input_file()

    def load_mini_clans_file(self):

        opened_file, _ = QFileDialog.getOpenFileName(self, "Open file", "", "Clans files (*.clans)")

        if opened_file:
            print("Loading " + opened_file)

            # Bring the controls to their initial state
            self.reset_window()

            # Clear the canvas
            self.network_plot.reset_data()

            # Initialize all the global data-structures
            self.reset_variables()

            cfg.run_params['input_file'] = opened_file
            cfg.run_params['input_format'] = 'mini_clans'
            self.setWindowTitle("CLANS " + str(self.view_in_dimensions_num) + "D-View")

            # Define a runner for loading the file that will be executed in a different thread
            self.load_file_worker = io.ReadInputWorker(cfg.run_params['input_format'])
            self.load_input_file()

    def load_delimited_file(self):

        opened_file, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All files (*.*)")

        if opened_file:
            print("Loading " + opened_file)

            # Bring the controls to their initial state
            self.reset_window()

            # Clear the canvas
            self.network_plot.reset_data()

            # Initialize all the global data-structures
            self.reset_variables()

            cfg.run_params['input_file'] = opened_file
            cfg.run_params['input_format'] = 'delimited'
            self.setWindowTitle("CLANS " + str(self.view_in_dimensions_num) + "D-View")

            # Define a runner for loading the file that will be executed in a different thread
            self.load_file_worker = io.ReadInputWorker(cfg.run_params['input_format'])
            self.load_input_file()

    def upload_metadata_file(self):

        opened_file, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All files (*.*)")

        if opened_file:
            print("Loading Metadata file " + opened_file)
            metadata_worker = io.ReadMetadataWorker(opened_file)
            self.threadpool.start(metadata_worker)
            metadata_worker.signals.finished.connect()

    def run_calc(self):

        # Full data mode
        if self.is_subset_mode == 0:
            if self.rounds_done == 0:
                print("Start the calculation")
                self.before = time.time()
            elif self.is_running_calc == 0:
                print("Resume the calculation")

        # Subset mode
        else:
            if self.rounds_done_subset == 0:
                print("Start the calculation")
                self.before = time.time()
            elif self.is_running_calc == 0:
                print("Resume the calculation")

        # Create a new calculation worker and start it only if the system is in init/stop state
        if self.is_running_calc == 0:

            # Create a new calculation worker
            self.run_calc_worker = lg.LayoutCalculationWorker(self.fr_object, self.is_subset_mode)
            self.run_calc_worker.signals.finished_iteration.connect(self.update_plot)
            self.run_calc_worker.signals.stopped.connect(self.stopped_state)
            self.is_running_calc = 1

            # Hide the connections
            self.connections_button.setChecked(False)
            self.manage_connections()

            # Hide the selected names
            self.show_selected_names_button.setChecked(False)
            self.is_show_selected_names = 0
            self.network_plot.hide_sequences_names()

            # Hide the group names
            self.show_group_names_button.setChecked(False)
            self.reset_group_names_button.setEnabled(False)
            self.is_show_group_names = 0
            self.network_plot.hide_group_names()

            # Disable the 'Add text' button
            #self.add_text_button.setEnabled(False)

            # If the clustering is done in 3D -> Move back to 3D view
            if cfg.run_params['dimensions_num_for_clustering'] == 3:
                if self.view_in_dimensions_num == 2:
                    self.dimensions_view_combo.setCurrentIndex(0)
            # 2D clustering
            else:
                # Move to automatic z-indexing
                self.z_index_mode_combo.setCurrentIndex(0)

            # Disable all setup changes while calculating
            self.init_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.dimensions_clustering_combo.setEnabled(False)
            self.pval_widget.setEnabled(False)
            self.dimensions_view_combo.setEnabled(False)
            self.connections_button.setEnabled(False)
            self.show_selected_names_button.setEnabled(False)
            self.open_selected_button.setEnabled(False)
            self.data_mode_combo.setEnabled(False)
            self.show_group_names_button.setEnabled(False)
            self.reset_group_names_button.setEnabled(False)
            #self.add_text_button.setEnabled(False)
            self.show_groups_combo.setEnabled(False)
            self.mode_combo.setEnabled(False)
            self.selection_type_combo.setEnabled(False)
            self.select_all_button.setEnabled(False)
            self.clear_selection_button.setEnabled(False)
            self.select_by_name_button.setEnabled(False)
            self.edit_groups_button.setEnabled(False)
            self.add_to_group_button.setEnabled(False)
            self.remove_selected_button.setEnabled(False)
            self.z_index_mode_combo.setEnabled(False)
            self.color_by_combo.setEnabled(False)
            self.group_by_combo.setEnabled(False)

            # Execute
            self.threadpool.start(self.run_calc_worker)

    def update_plot(self):

        self.network_plot.update_data(self.view_in_dimensions_num, self.fr_object, 1, self.color_by)

        # Full data mode
        if self.is_subset_mode == 0:
            self.rounds_done += 1
            self.rounds_label.setText("Round: " + str(self.rounds_done))

            if cfg.run_params['is_debug_mode']:
                if self.rounds_done % 100 == 0:
                    self.after = time.time()
                    duration = (self.after - self.before)
                    print("The calculation of " + str(self.rounds_done) + " rounds took " + str(duration) + " seconds")

        # Subset mode
        else:
            self.rounds_done_subset += 1
            self.rounds_label.setText("Round: " + str(self.rounds_done_subset))

    def stop_calc(self):
        if self.is_running_calc == 1:
            self.run_calc_worker.stop()

    def stopped_state(self):
        if self.is_subset_mode == 0:
            self.after = time.time()
            duration = (self.after - self.before)
            print("The calculation has stopped at round no. " + str(self.rounds_done))

            if cfg.run_params['is_debug_mode']:
                print("The calculation of " + str(self.rounds_done) + " rounds took " + str(duration) + " seconds")

        self.start_button.setText("Resume")
        self.is_running_calc = 0

        # Enable all settings buttons
        self.init_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.dimensions_clustering_combo.setEnabled(True)
        if cfg.run_params['dimensions_num_for_clustering'] == 3:
            self.dimensions_view_combo.setEnabled(True)
        self.pval_widget.setEnabled(True)
        self.connections_button.setEnabled(True)
        #self.add_text_button.setEnabled(True)

        if len(cfg.groups_dict[self.group_by]) > 0 and self.color_by == 'groups':
            self.show_group_names_button.setEnabled(True)
            if len(self.network_plot.selected_groups) > 0:
                self.show_groups_combo.setEnabled(True)
            self.edit_groups_button.setEnabled(True)

            if self.is_subset_mode == 0 and self.view_in_dimensions_num == 2 and self.color_by == 'groups' and \
                    len(cfg.groups_dict[self.group_by]) > 1:
                self.z_index_mode_combo.setEnabled(True)

        # Enable selection-related buttons only in full data mode
        if self.is_subset_mode == 0:
            self.mode_combo.setEnabled(True)
            self.select_all_button.setEnabled(True)
            self.clear_selection_button.setEnabled(True)
            self.select_by_name_button.setEnabled(True)

        # If at least one point is selected -> enable all buttons related to actions on selected points
        if self.network_plot.selected_points != {}:
            self.show_selected_names_button.setEnabled(True)
            self.open_selected_button.setEnabled(True)
            self.add_to_group_button.setEnabled(True)
            self.remove_selected_button.setEnabled(True)
            if len(self.network_plot.selected_points) >= 4:
                self.data_mode_combo.setEnabled(True)

        # Enable the 'color by' combo box if the color-by-param was already done once
        if self.done_color_by_length or self.added_user_param:
            self.color_by_combo.setEnabled(True)

        # Enable the 'group-by' combo box if is more than one grouping option
        if self.group_by_combo.count() > 1 and self.color_by == 'groups':
            self.group_by_combo.setEnabled(True)

        # Whole data calculation mode
        if self.is_subset_mode == 0:
            # Update the coordinates saved in the sequences_array
            seq.update_positions(self.fr_object.coordinates.T, 'full')

            self.network_plot.reset_group_names_positions(self.group_by)

        # Subset calculation mode
        else:
            # Update the subset-coordinates saved in the sequences_array
            seq.update_positions(self.fr_object.coordinates.T, 'subset')

        # Calculate the azimuth and elevation angles of the new points positions
        self.network_plot.calculate_initial_angles()

        # Update the global variable of number of rounds
        cfg.run_params['rounds_done'] = self.rounds_done

    def init_coor(self):
        # Initialize the coordinates only if the calculation is not running
        if self.is_running_calc == 0:
            self.start_button.setText("Start")
            self.before = None
            self.after = None
            self.is_running_calc = 0

            # Reset the number of rounds
            if self.is_subset_mode == 0:
                self.rounds_done = 0
            else:
                self.rounds_done_subset = 0

            self.rounds_label.setText("Round: 0")

            # Generate random positions to be saved in the main sequences array
            # Subset mode -> only for the sequences in the subset
            if self.is_subset_mode:
                cfg.sequences_array['x_coor_subset'], cfg.sequences_array['y_coor_subset'], \
                cfg.sequences_array['z_coor_subset'] = seq.init_positions(cfg.run_params['total_sequences_num'])

                # Update the coordinates in the fruchterman-reingold object
                self.fr_object.init_calculation(cfg.sequences_array['x_coor_subset'],
                                                cfg.sequences_array['y_coor_subset'],
                                                cfg.sequences_array['z_coor_subset'])

            # Full mode -> Init the whole dataset
            else:
                cfg.sequences_array['x_coor'], cfg.sequences_array['y_coor'], cfg.sequences_array['z_coor'] = \
                    seq.init_positions(cfg.run_params['total_sequences_num'])

                # Update the coordinates in the fruchterman-reingold object
                self.fr_object.init_calculation(cfg.sequences_array['x_coor'],
                                                cfg.sequences_array['y_coor'],
                                                cfg.sequences_array['z_coor'])

            self.network_plot.update_data(self.view_in_dimensions_num, self.fr_object, 1, self.color_by)
            # Calculate the angles of each point for future use when having rotations
            self.network_plot.calculate_initial_angles()

            print("Coordinates were initiated.")

            # Move back to interactive mode
            self.mode_combo.setCurrentIndex(0)

            # If the clustering is done in 3D -> Move to 3D view and reset the turntable camera
            if cfg.run_params['dimensions_num_for_clustering'] == 3:
                self.dimensions_view_combo.setCurrentIndex(0)

            else:
                if self.z_indexing_mode == 'groups':
                    self.z_index_mode_combo.setCurrentIndex(0)

            self.network_plot.reset_rotation()
            self.network_plot.reset_group_names_positions(self.group_by)

    def manage_connections(self):

        # Show the connections
        if self.connections_button.isChecked():
            self.is_show_connections = 1

            # Display the connecting lines
            self.network_plot.show_connections()

        # Hide the connections
        else:
            self.is_show_connections = 0
            self.network_plot.hide_connections()

    def update_cutoff(self):

        entered_pval = self.pval_widget.text()

        # The user entered a float number
        if re.search("^\d+\.?\d*(e-\d+)*$", entered_pval):

            # The number is not between 0 and 1 => print error
            if float(entered_pval) < 0 or float(entered_pval) > 1:
                self.error_label.setText("Enter 0 <= threshold <= 1")
                self.pval_widget.setText("")
                self.pval_widget.setFocus()

            # The number is valid
            else:

                self.error_label.setText("")

                print("Similairy cutoff has changed to: " + entered_pval)
                cfg.run_params['similarity_cutoff'] = float(entered_pval)
                sp.define_connected_sequences(cfg.run_params['type_of_values'])
                sp.define_connected_sequences_list()
                self.network_plot.create_connections_by_bins()

                # If in subset mode, update the connections also for the subset
                if self.is_subset_mode:
                    sp.define_connected_sequences_list_subset()
                    self.network_plot.create_connections_by_bins_subset()

                # Update the connections matrix in the fruchterman-reingold object
                self.fr_object.update_connections()

                # 3D view
                if self.view_in_dimensions_num == 3:
                    self.network_plot.update_connections(3)

                # 2D view
                else:
                    # 3D clustering -> need to present the rotated-coordinates
                    if cfg.run_params['dimensions_num_for_clustering'] == 3:
                        self.network_plot.update_view(2, self.color_by)
                    # 2D clustering
                    else:
                        self.network_plot.update_connections(2)

        # The user entered invalid characters
        else:
            self.error_label.setText("Invalid characters")
            self.pval_widget.setText("")
            self.pval_widget.setFocus()

    # Save a standard (full) clans file
    def save_clans_file(self):
        saved_file, _ = QFileDialog.getSaveFileName()

        if saved_file:
            file_object = ff.ClansFormat()
            file_object.write_file(saved_file, True, self.group_by)

    # Save a minimal clans file (without the sequences)
    def save_mini_clans_file(self):
        saved_file, _ = QFileDialog.getSaveFileName()

        if saved_file:
            file_object = ff.ClansMinimalFormat()
            file_object.write_file(saved_file, self.group_by)

    def save_delimited_file(self):

        saved_file, _ = QFileDialog.getSaveFileName()

        if saved_file:
            file_object = ff.DelimitedFormat()
            file_object.write_file(saved_file)

    def save_image(self):

        # Convert the canvas to numpy image array
        img_array = self.canvas.render(alpha=False)

        # Create a PIL.Image object from the array
        img = Image.fromarray(img_array)

        # Open a save file dialog with the following format options:  png, tiff, jpeg, eps
        saved_file, _ = QFileDialog.getSaveFileName(self, "Save image", "", "PNG (*.png);; Tiff (*.tiff);; "
                                                                            "Jpeg (*.jpg);; EPS (*.eps)")

        if saved_file:

            # Save the image array in the format specified by the file extension
            img.save(saved_file)

            print("Image was saved in file " + str(saved_file))

    def conf_FR_layout(self):

        conf_dlg = cd.FruchtermanReingoldConfig()

        if conf_dlg.exec_():
            cfg.run_params['att_val'], cfg.run_params['att_exp'], cfg.run_params['rep_val'], \
            cfg.run_params['rep_exp'], cfg.run_params['gravity'], cfg.run_params['dampening'], \
            cfg.run_params['maxmove'], cfg.run_params['cooling'] = conf_dlg.get_parameters()

    def conf_nodes(self):

        conf_nodes_dlg = cd.NodesConfig(self.network_plot.nodes_size, self.network_plot.nodes_default_color,
                                        self.network_plot.nodes_outline_default_color,
                                        self.network_plot.nodes_outline_width)

        if conf_nodes_dlg.exec_():
            size, color, outline_color, outline_width = conf_nodes_dlg.get_parameters()

            self.network_plot.set_defaults(size, color, outline_color, outline_width, self.dim_num, self.color_by,
                                           self.group_by)

    def change_dimensions_view(self):

        # 3D view
        if self.dimensions_view_combo.currentIndex() == 0:
            self.view_in_dimensions_num = 3
            self.dim_num = self.view_in_dimensions_num

            # Update the window title
            self.setWindowTitle("CLANS " + str(self.view_in_dimensions_num) + "D-View of " + self.file_name)

            self.z_index_mode_combo.setEnabled(False)

            # Not in init file mode
            if self.is_init == 0:
                self.network_plot.set_3d_view(self.fr_object, self.color_by)

        # 2D view
        else:
            self.view_in_dimensions_num = 2
            self.dim_num = self.view_in_dimensions_num

            # Update the window title
            self.setWindowTitle("CLANS " + str(self.view_in_dimensions_num) + "D-View of " + self.file_name)

            # Only in full data and color-by groups modes
            if self.is_subset_mode == 0 and len(cfg.groups_dict[self.group_by]) > 1 and self.color_by == 'groups':
                self.z_index_mode_combo.setEnabled(True)

            # Not in init file mode
            if self.is_init == 0:
                self.network_plot.set_2d_view(self.z_indexing_mode, self.fr_object, self.color_by, self.group_by)

    def change_dimensions_num_for_clustering(self):

        # 3D clustering
        if self.dimensions_clustering_combo.currentIndex() == 0:
            cfg.run_params['dimensions_num_for_clustering'] = 3

            # Update the coordinates in the Fruchterman-Reingold object
            # Full data mode
            if self.is_subset_mode == 0:
                self.fr_object.init_coordinates(cfg.sequences_array['x_coor'],
                                                cfg.sequences_array['y_coor'],
                                                cfg.sequences_array['z_coor'])
            # Subset mode
            else:
                self.fr_object.init_coordinates(cfg.sequences_array['x_coor_subset'],
                                                cfg.sequences_array['y_coor_subset'],
                                                cfg.sequences_array['z_coor_subset'])

            self.dimensions_view_combo.setCurrentIndex(0)
            self.dimensions_view_combo.setEnabled(True)

        # 2D clustering
        else:
            cfg.run_params['dimensions_num_for_clustering'] = 2

            self.dimensions_view_combo.setEnabled(False)

            # The view was already in 2D -> update the rotated positions
            if self.view_in_dimensions_num == 2:
                self.network_plot.save_rotated_coordinates(2, self.fr_object, self.color_by)

            # Set 2D view
            else:
                self.dimensions_view_combo.setCurrentIndex(1)

    def manage_z_indexing(self):

        # Automatic Z-indexing
        if self.z_index_mode_combo.currentIndex() == 0:
            self.z_indexing_mode = 'auto'

        # Z-indexing by groups order
        else:
            self.z_indexing_mode = 'groups'

        if self.z_index_mode_combo.isEnabled():
            self.network_plot.update_2d_view(self.z_indexing_mode, self.color_by, self.group_by)

    def change_mode(self):

        # Interactive mode (rotate/pan)
        if self.mode_combo.currentIndex() == 0:
            self.mode = "interactive"

            self.dim_num = self.view_in_dimensions_num

            if cfg.run_params['is_debug_mode']:
                print("Interactive mode")

            # Not in init file mode
            if self.is_init == 0:
                self.network_plot.set_interactive_mode(self.view_in_dimensions_num, self.fr_object,
                                                       self.color_by)

            self.init_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.dimensions_clustering_combo.setEnabled(True)
            self.pval_widget.setEnabled(True)
            self.selection_type_combo.setEnabled(False)
            if cfg.run_params['dimensions_num_for_clustering'] == 3:
                self.dimensions_view_combo.setEnabled(True)
            if self.view_in_dimensions_num == 3:
                self.z_index_mode_combo.setEnabled(False)

            # Disconnect the selection-special special mouse-events and connect back the default behaviour of the
            # viewbox when the mouse moves
            self.canvas.events.mouse_release.disconnect(self.on_canvas_mouse_release)
            self.view.camera._viewbox.events.mouse_move.connect(self.view.camera.viewbox_mouse_event)
            self.view.camera._viewbox.events.mouse_press.connect(self.view.camera.viewbox_mouse_event)

        else:

            self.dim_num = 2

            # Selection mode
            if self.mode_combo.currentIndex() == 1:
                self.mode = "selection"

                if cfg.run_params['is_debug_mode']:
                    print("Selection mode")

            # Move visuals mode
            elif self.mode_combo.currentIndex() == 2:
                self.mode = "move_visuals"

                if cfg.run_params['is_debug_mode']:
                    print("move_visuals mode")

            self.network_plot.set_selection_mode(self.view_in_dimensions_num, self.z_indexing_mode,
                                                 self.fr_object, self.color_by, self.group_by)

            self.init_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.dimensions_clustering_combo.setEnabled(False)
            self.pval_widget.setEnabled(False)
            self.dimensions_view_combo.setEnabled(False)

            if len(cfg.groups_dict[self.group_by]) > 1 and self.color_by == 'groups':
                self.z_index_mode_combo.setEnabled(True)

            if len(cfg.groups_dict[self.group_by]) > 0:
                self.selection_type_combo.setEnabled(True)

            # Disconnect the default behaviour of the viewbox when the mouse moves
            # and connect special callbacks for mouse_move and mouse_release
            self.view.camera._viewbox.events.mouse_move.disconnect(self.view.camera.viewbox_mouse_event)
            self.view.camera._viewbox.events.mouse_press.disconnect(self.view.camera.viewbox_mouse_event)
            self.canvas.events.mouse_release.connect(self.on_canvas_mouse_release)

    def color_by_groups(self):

        self.network_plot.color_by_groups(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)

        self.colorbar_plot.hide_colorbar()

    def color_by_seq_length(self):

        # First time per data-det
        if self.done_color_by_length == 0:
            self.done_color_by_length = 1
            self.color_by_combo.addItem('Seq. length')
            self.color_by_combo.setCurrentText('Seq. length')
            self.color_by_combo.setEnabled(True)

        else:
            gradient_colormap = colors.generate_colormap_gradient_2_colors(cfg.short_color, cfg.long_color)

            self.network_plot.color_by_param(gradient_colormap, cfg.sequences_array['norm_seq_length'],
                                             self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)

            self.colorbar_plot.show_colorbar(gradient_colormap, cfg.sequences_array['seq_length'], 'Sequences length')

    def open_color_by_length_dialog(self):

        dlg = md.ColorByLengthDialog()

        if dlg.exec_():
            cfg.short_color, cfg.long_color = dlg.get_colors()

            self.color_by_seq_length()

    def change_coloring(self):

        # Color the data by groups (if none - color all in black)
        if self.color_by_combo.currentIndex() == 0:
            self.color_by = "groups"

            if self.is_init == 0:

                # Enable all the group-related controls (if there are groups)
                if len(cfg.groups_dict[self.group_by]) > 0:
                    self.edit_groups_button.setEnabled(True)
                    self.show_group_names_button.setEnabled(True)
                    self.selection_type_combo.setEnabled(True)

                if self.dim_num == 2 and len(cfg.groups_dict[self.group_by]) > 1:
                    self.z_index_mode_combo.setEnabled(True)

                # Enable the 'group-by' combo box if is more than one grouping option
                if self.group_by_combo.count() > 1:
                    self.group_by_combo.setEnabled(True)

                self.color_by_groups()

        # Color the data by some numeric parameter
        else:
            self.color_by = "param"

            # Disable all the group-related controls and hide the group names
            self.edit_groups_button.setEnabled(False)
            self.show_group_names_button.setChecked(False)
            self.network_plot.hide_group_names()
            self.reset_group_names_button.setEnabled(False)
            self.is_show_group_names = 0
            self.show_group_names_button.setEnabled(False)
            self.selection_type_combo.setEnabled(False)
            self.group_by_combo.setEnabled(False)

            if self.is_init == 0:
                # Color the data by sequence length
                if self.color_by_combo.currentText() == 'Seq. length':
                    self.color_by_seq_length()

                # Color the data by other parameter
                else:
                    self.color_by_user_param(self.color_by_combo.currentText())

            if self.dim_num == 2:
                if self.z_indexing_mode == 'groups':
                    self.z_index_mode_combo.setCurrentIndex(0)

                self.z_index_mode_combo.setEnabled(False)

    def color_by_user_param(self, param):

        min_param_color = cfg.sequences_numeric_params[param]['min_color']
        max_param_color = cfg.sequences_numeric_params[param]['max_color']
        gradient_colormap = colors.generate_colormap_gradient_2_colors(min_param_color, max_param_color)

        self.network_plot.color_by_param(gradient_colormap, cfg.sequences_numeric_params[param]['norm'],
                                         self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)

        self.colorbar_plot.show_colorbar(gradient_colormap, cfg.sequences_numeric_params[param]['raw'], param)

    def open_color_by_param_dialog(self):

        dlg = md.ColorByParamDialog()

        if dlg.exec_():
            selected_param, added_params_list, min_param_color, max_param_color = dlg.get_param()

            if selected_param:

                # At least one new parameter was added
                if len(added_params_list) > 0:
                    self.added_user_param = 1

                    for param_name in added_params_list:
                        self.color_by_combo.addItem(param_name)

                self.color_by_combo.setCurrentText(selected_param)
                self.color_by_combo.setEnabled(True)

                # Update the colors of the selected parameter
                cfg.sequences_numeric_params[selected_param]['min_color'] = min_param_color
                cfg.sequences_numeric_params[selected_param]['max_color'] = max_param_color

                self.color_by_user_param(selected_param)

    def change_grouping(self):

        # Group the data by manual definition (by selection)
        if self.group_by_combo.currentText() == 'Manual definition':
            self.group_by = "manual"

        # Group the data according to the <Seqgoups> section in the input file
        elif self.group_by_combo.currentText() == 'Input CLANS file':
            self.group_by = "input_file"

        # Group the data by some user-defined parameter
        else:
            self.group_by = self.group_by_combo.currentText()

        if not self.is_init:

            if self.dim_num == 2:
                self.z_index_mode_combo.setCurrentIndex(0)
                if len(cfg.groups_dict[self.group_by]) > 1:
                    self.z_index_mode_combo.setEnabled(True)
                else:
                    self.z_index_mode_combo.setEnabled(False)

            if len(self.network_plot.selected_groups) > 0:
                self.clear_selection()

            self.network_plot.hide_group_names()

            if len(cfg.groups_dict[self.group_by]) == 0:
                self.selection_type_combo.setCurrentIndex(0)

            self.network_plot.update_group_by(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)

            # Enable all groups-related controls (in case there are groups)
            if len(cfg.groups_dict[self.group_by]) > 0:
                self.edit_groups_button.setEnabled(True)
                self.show_group_names_button.setEnabled(True)
                self.selection_type_combo.setEnabled(True)

                # The group names are displayed -> update them including the new group
                if self.is_show_group_names:
                    self.network_plot.show_group_names('all')

            # If there are no group (in 'manual' group-by, for example)
            else:
                self.edit_groups_button.setEnabled(False)
                self.show_group_names_button.setChecked(False)
                self.reset_group_names_button.setEnabled(False)
                self.is_show_group_names = 0
                self.show_group_names_button.setEnabled(False)
                self.selection_type_combo.setEnabled(False)

    def change_selection_type(self):

        # Sequences selection
        if self.selection_type_combo.currentIndex() == 0:
            self.selection_type = "sequences"

        # Groups selection
        else:
            self.selection_type = "groups"

    def select_all(self):

        self.network_plot.select_all(self.selection_type, self.dim_num, self.z_indexing_mode, self.color_by,
                                     self.group_by, self.is_show_group_names, self.group_names_display)

        # Update the selected sequences window
        self.selected_seq_window.update_sequences()

        # Enable the selection-related buttons
        self.show_selected_names_button.setEnabled(True)
        self.open_selected_button.setEnabled(True)
        self.add_to_group_button.setEnabled(True)
        self.remove_selected_button.setEnabled(True)

        # Disable the 'Show selected only' option (make no sense if selecting all)
        self.data_mode_combo.setEnabled(False)

    def clear_selection(self):

        self.network_plot.reset_selection(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by,
                                          self.is_show_group_names, self.group_names_display)

        # Update the selected sequences window
        self.selected_seq_window.update_sequences()

        # Hide the sequences names and release the button (if was checked)
        self.show_selected_names_button.setChecked(False)
        self.show_selected_names_button.setEnabled(False)
        self.open_selected_button.setEnabled(False)
        self.data_mode_combo.setCurrentIndex(0)
        self.data_mode_combo.setEnabled(False)
        self.add_to_group_button.setEnabled(False)
        self.remove_selected_button.setEnabled(False)
        self.is_show_selected_names = 0
        self.network_plot.hide_sequences_names()

        # Disable the show all/selected group names combo
        if self.is_show_group_names:
            self.show_groups_combo.setCurrentIndex(0)
            self.show_groups_combo.setEnabled(False)

    def show_selected_names(self):
        if self.show_selected_names_button.isChecked():
            self.is_show_selected_names = 1

            # Display the names
            self.network_plot.show_sequences_names()

        else:
            self.is_show_selected_names = 0
            self.network_plot.hide_sequences_names()

    def open_selected_window(self):

        self.selected_seq_window.update_sequences()

        if self.selected_seq_window.is_visible == 0:
            self.selected_seq_window.open_window()

    def select_by_name(self):

        self.search_window.open_window()

    def manage_subset_presentation(self):

        # Subset mode
        if self.data_mode_combo.currentIndex() == 1:
            self.is_subset_mode = 1

            print("Displaying selected subset")

            self.start_button.setText("Start")
            self.rounds_label.setText("Round: 0")
            self.rounds_done_subset = 0

            # Disable all selection-related buttons
            self.mode_combo.setEnabled(False)
            self.mode_combo.setCurrentIndex(0)
            self.select_all_button.setEnabled(False)
            self.clear_selection_button.setEnabled(False)
            self.z_index_mode_combo.setCurrentIndex(0)
            self.z_index_mode_combo.setEnabled(False)

            self.network_plot.set_subset_view(self.view_in_dimensions_num, self.color_by)

            if self.is_show_group_names:
                self.network_plot.show_group_names('selected')

        # Full data mode
        else:
            self.is_subset_mode = 0

            print("Back to full-data view")

            if self.rounds_done > 0:
                self.start_button.setText("Resume")
            else:
                self.start_button.setText("Start")
            self.rounds_label.setText("Round: " + str(self.rounds_done))

            # Enable all selection-related buttons
            self.mode_combo.setEnabled(True)
            self.select_all_button.setEnabled(True)
            self.clear_selection_button.setEnabled(True)

            if self.view_in_dimensions_num == 2 and len(cfg.groups_dict[self.group_by]) > 1:
                self.z_index_mode_combo.setEnabled(True)

            # Update the coordinates in the fruchterman-reingold object
            self.fr_object.init_coordinates(cfg.sequences_array['x_coor'],
                                            cfg.sequences_array['y_coor'],
                                            cfg.sequences_array['z_coor'])

            self.network_plot.set_full_view(self.view_in_dimensions_num, self.color_by)

            if self.is_show_group_names:
                self.network_plot.show_group_names('all')

    def change_group_names_display(self):

        # Show all the group names
        if self.show_groups_combo.currentIndex() == 0:
            self.group_names_display = 'all'

        # Show the selected group names only
        else:
            self.group_names_display = 'selected'

        self.network_plot.hide_group_names()
        self.network_plot.show_group_names(self.group_names_display)

    def reset_group_names_positions(self):
        self.network_plot.reset_group_names_positions(self.group_by)

    def manage_group_names(self):

        # The 'show group names' button is checked
        if self.show_group_names_button.isChecked():
            self.is_show_group_names = 1
            self.reset_group_names_button.setEnabled(True)

            # Full data mode
            if self.is_subset_mode == 0:

                if len(self.network_plot.selected_groups) > 0:
                    self.show_groups_combo.setEnabled(True)
                else:
                    self.show_groups_combo.setCurrentIndex(0)
                    self.show_groups_combo.setEnabled(False)

                self.change_group_names_display()

            # Subset mode
            else:
                self.network_plot.show_group_names('selected')

            #self.network_plot.reset_group_names_positions(self.group_by)

        # The 'show group names' button is not checked
        else:
            self.is_show_group_names = 0
            self.show_groups_combo.setEnabled(False)
            self.reset_group_names_button.setEnabled(False)
            self.network_plot.hide_group_names()

    #def add_text(self):

        # Open the 'Enter new text element' dialog
        #dlg = td.NewTextDialog(self.network_plot)

        # The user has entered text
        #if dlg.exec_():
            ## Get all the text definitions entered by the user
            #text, size, color_array = dlg.get_text_info()

    def edit_groups(self):

        dlg = gd.ManageGroupsDialog(self.network_plot, self.view, self.dim_num, self.z_indexing_mode, self.color_by,
                                    self.group_by)

        if dlg.exec_():

            # The order of the groups has changed
            if dlg.changed_order_flag:
                self.network_plot.update_groups_order(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)

    def open_add_to_group_dialog(self):

        dlg = gd.AddToGroupDialog(self.group_by)

        if dlg.exec_():
            choice, group_ID = dlg.get_choice()

            if choice == 'new':

                print("Creating a new group")
                self.create_group_from_selected()

            # The user chose to add the selected sequences to an existing group
            else:
                print("Adding the sequences to group " + cfg.groups_dict[self.group_by][group_ID]['name'])
                self.add_sequences_to_group(group_ID)

    def add_sequences_to_group(self, group_ID):

        # Add the sequences to the main group_list array
        groups.add_to_group(self.group_by, self.network_plot.selected_points, group_ID)

        # Update the look of the selected data-points according to the new group definitions
        self.network_plot.add_to_group(self.network_plot.selected_points, group_ID, self.dim_num,
                                       self.z_indexing_mode, self.color_by, self.group_by)

    def create_group_from_selected(self):

        # Open the 'Create group from selected' dialog
        dlg = gd.CreateGroupDialog(self.network_plot, self.group_by)

        # The user defined a new group
        if dlg.exec_():
            # Get all the group definitions entered by the user
            group_name, group_name_size, size, color_clans, color_array, is_bold, is_italic, outline_color = \
                dlg.get_group_info()

            # Add the new group to the main groups array
            group_dict = dict()
            group_dict['name'] = group_name
            group_dict['size'] = size
            group_dict['name_size'] = group_name_size
            group_dict['color'] = color_clans
            group_dict['color_array'] = color_array
            group_dict['is_bold'] = is_bold
            group_dict['is_italic'] = is_italic
            group_dict['order'] = len(cfg.groups_dict[self.group_by]) - 1
            group_dict['outline_color'] = outline_color
            group_ID = groups.add_group_with_sequences(self.group_by, self.network_plot.selected_points.copy(),
                                                       group_dict)

            # Add the new group to the graph
            self.network_plot.add_group(self.group_by, group_ID)

            # Update the look of the selected data-points according to the new group definitions
            if self.dim_num == 2 and len(cfg.groups_dict[self.group_by]) > 1:
                self.z_index_mode_combo.setEnabled(True)

            self.network_plot.add_to_group(self.network_plot.selected_points, group_ID, self.dim_num,
                                           self.z_indexing_mode, self.color_by, self.group_by)

            self.edit_groups_button.setEnabled(True)
            self.show_group_names_button.setEnabled(True)
            self.selection_type_combo.setEnabled(True)

            # The group names are displayed -> update them including the new group
            if self.is_show_group_names:
                self.network_plot.show_group_names('all')

    def remove_selected_from_group(self):

        # Remove the selected sequences group-assignment in the main group_list array
        groups_with_deleted_members = groups.remove_from_group(self.group_by, self.network_plot.selected_points.copy())

        # Update the look of the selected data-points to the default look (without group assignment)
        self.network_plot.remove_from_group(self.network_plot.selected_points, self.dim_num, self.z_indexing_mode,
                                            self.color_by, self.group_by)

        # Check if there is an empty group among the groups with removed members
        for group_ID in groups_with_deleted_members:
            if len(cfg.groups_dict[self.group_by][group_ID]['seqIDs']) == 0:

                # 1. Delete it from the group_names visual and other graph-related data-structures
                self.network_plot.delete_empty_group(group_ID, self.dim_num, self.z_indexing_mode, self.color_by,
                                                     self.group_by)

                # 2. Delete the group
                groups.delete_group(self.group_by, group_ID)

        # Check if there are groups left. If not, disable the related groups controls
        if len(cfg.groups_dict[self.group_by]) == 0:
            self.show_group_names_button.setChecked(False)
            self.show_group_names_button.setEnabled(False)
            self.show_groups_combo.setEnabled(False)
            self.reset_group_names_button.setEnabled(False)
            self.selection_type_combo.setCurrentIndex(0)
            self.selection_type_combo.setEnabled(False)
            self.edit_groups_button.setEnabled(False)

    def group_by_taxonomy(self):

        # Open the 'Group by taxonomy' dialog
        dlg = md.GroupByTaxDialog(self.network_plot)

        # Create and execute the taxonomy worker to get the organism names and their taxonomy hierarchy
        # (only the first time)
        if not cfg.run_params['finished_taxonomy_search']:
            taxonomy_worker = io.TaxonomyWorker()
            self.threadpool.start(taxonomy_worker)
            taxonomy_worker.signals.finished.connect(dlg.finished_tax_search)

        if dlg.exec_():
            tax_level, points_size, group_names_size, is_bold, is_italic = dlg.get_tax_level()

            self.group_by = "Taxonomy - " + tax_level

            # First time for this taxonomic level
            if self.group_by not in cfg.groups_dict:
                cfg.groups_dict[self.group_by] = dict()
                cfg.sequences_in_groups[self.group_by] = np.full(cfg.run_params['total_sequences_num'], -1)

                # Generate distinct colors according to the number of groups in the chosen level
                color_map = colors.generate_distinct_colors(len(cfg.seq_by_tax_level_dict[tax_level])-1)
                color_index = 0

                # Sort the groups alphabetically and move the 'Not assigned' group to the end
                tax_groups = sorted(cfg.seq_by_tax_level_dict[tax_level])
                tax_groups.append(tax_groups.pop(tax_groups.index('Not assigned')))

                # A loop over the groups in the chosen taxonomic level
                for tax_group in tax_groups:

                    if tax_group != "Not assigned":

                        color = color_map[color_index].RGBA[0]
                        r = color[0]
                        g = color[1]
                        b = color[2]
                        color_clans = str(r) + ";" + str(g) + ";" + str(b) + ";255"
                        color_array = color / 255

                        color_index += 1

                    else:
                        color_clans = "217;217;217;255"
                        color_array = [0.85, 0.85, 0.85, 1]

                    # Add the new group to the main groups array
                    group_dict = dict()
                    group_dict['name'] = tax_group
                    group_dict['size'] = points_size
                    group_dict['name_size'] = group_names_size
                    group_dict['color'] = color_clans
                    group_dict['color_array'] = color_array
                    group_dict['outline_color'] = [0.0, 0.0, 0.0, 1.0]
                    group_dict['is_bold'] = is_bold
                    group_dict['is_italic'] = is_italic
                    group_dict['order'] = len(cfg.groups_dict[self.group_by]) - 1
                    seq_dict = cfg.seq_by_tax_level_dict[tax_level][tax_group].copy()
                    group_ID = groups.add_group_with_sequences(self.group_by, seq_dict, group_dict)

                # Add the new group-type to the group-by combo-box, enable it and update the grouping
                self.group_by_combo.addItem(self.group_by)
                self.group_by_combo.setCurrentText(self.group_by)
                self.group_by_combo.setEnabled(True)

    def add_groups_from_metadata(self):

        # Open the 'Add custom grouping category' dialog
        dlg = md.GroupByParamDialog(self.network_plot)

        if dlg.exec_():
            groups_dict, points_size, group_names_size, is_bold, is_italic, is_error = dlg.get_categories()

            if not is_error:

                for category in groups_dict:

                    # This category is new
                    if category not in cfg.groups_dict:
                        cfg.groups_dict[category] = dict()
                        cfg.sequences_in_groups[category] = np.full(cfg.run_params['total_sequences_num'], -1)

                        # Generate distinct colors according to the number of groups in the chosen level
                        if "Not assigned" in groups_dict[category]:
                            colors_num = len(groups_dict[category]) - 1
                        else:
                            colors_num = len(groups_dict[category])
                        color_map = colors.generate_distinct_colors(colors_num)
                        color_index = 0

                        # Sort the groups alphabetically and move the 'Not assigned' group to the end
                        sorted_groups = sorted(groups_dict[category])

                        # If there is group 'Not assigned', move it to the end
                        if "Not assigned" in groups_dict[category]:
                            sorted_groups.append(sorted_groups.pop(sorted_groups.index('Not assigned')))

                        # A loop over the groups in the chosen taxonomic level
                        for group in sorted_groups:

                            if group != "Not assigned":

                                color = color_map[color_index].RGBA[0]
                                r = color[0]
                                g = color[1]
                                b = color[2]
                                color_clans = str(r) + ";" + str(g) + ";" + str(b) + ";255"
                                color_array = color / 255

                                color_index += 1

                            else:
                                color_clans = "217;217;217;255"
                                color_array = [0.85, 0.85, 0.85, 1]

                            # Add the new group to the main groups array
                            group_dict = dict()
                            group_dict['name'] = group
                            group_dict['size'] = points_size
                            group_dict['name_size'] = group_names_size
                            group_dict['color'] = color_clans
                            group_dict['color_array'] = color_array
                            group_dict['outline_color'] = [0.0, 0.0, 0.0, 1.0]
                            group_dict['is_bold'] = is_bold
                            group_dict['is_italic'] = is_italic
                            group_dict['order'] = len(cfg.groups_dict[category]) - 1
                            seq_dict = groups_dict[category][group].copy()
                            group_ID = groups.add_group_with_sequences(category, seq_dict, group_dict)

                        # Add the new group-type to the group-by combo-box, enable it and update the grouping
                        self.group_by_combo.addItem(category)
                        self.group_by_combo.setCurrentText(category)
                        self.group_by_combo.setEnabled(True)

                self.group_by = category

    ## Callback functions to deal with mouse and key events

    def on_canvas_mouse_move(self, event):
        if event.button == 1:
            self.canvas_mouse_drag(event)

    def on_canvas_mouse_double_click(self, event):
        if event.button == 1:
            self.canvas_mouse_double_click(event)

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
                self.network_plot.find_selected_point(self.selection_type, event.pos, self.z_indexing_mode,
                                                      self.color_by, self.group_by, self.is_show_group_names,
                                                      self.group_names_display)

            # Drag event
            else:
                self.network_plot.remove_dragging_rectangle()
                self.network_plot.find_selected_area(self.selection_type, pos_array[0], event.pos, self.z_indexing_mode,
                                                     self.color_by, self.group_by, self.is_show_group_names,
                                                     self.group_names_display)

            # If at least one point is selected -> enable all buttons related to actions on selected points
            if self.network_plot.selected_points != {}:
                self.show_selected_names_button.setEnabled(True)
                self.open_selected_button.setEnabled(True)
                self.add_to_group_button.setEnabled(True)
                self.remove_selected_button.setEnabled(True)
                if len(self.network_plot.selected_points) >= 4:
                    self.data_mode_combo.setEnabled(True)

            # Enable the show all/selected group names combo if there is at least one selected group
            if self.is_show_group_names:
                if len(self.network_plot.selected_groups) > 0:
                    self.show_groups_combo.setEnabled(True)
                else:
                    self.show_groups_combo.setCurrentIndex(0)
                    self.show_groups_combo.setEnabled(False)

            # Update the selected sequences window
            self.selected_seq_window.update_sequences()

        # The event is done in the 'Move visuals' mode
        elif self.mode == 'move_visuals':

            # Finish the move of a group name
            if self.visual_to_move == "text":
                self.network_plot.finish_group_name_move()

            ## Disabled currently
            #elif self.visual_to_move == "data":
                #self.network_plot.finish_points_move(self.view_in_dimensions_num, self.fr_object)

            self.visual_to_move = None

    def canvas_mouse_drag(self, event):

        pos_array = event.trail()

        # Regular dragging event for selection
        if self.mode == "selection":

            # Initiation of dragging -> create a rectangle visual
            if len(pos_array) == 3:
                self.network_plot.start_dragging_rectangle(pos_array[0])

            # Mouse dragging continues -> update the rectangle
            elif len(pos_array) > 3:
                # Update the rectangle if the mouse position was actually changed
                if pos_array[-1][0] != pos_array[-2][0] and pos_array[-1][1] != pos_array[-2][1]:
                    self.network_plot.update_dragging_rectangle(pos_array[0], pos_array[-1])

        # Interactive mode
        elif self.mode == "interactive":

            # CTRL key is pressed - move the selected data points
            if self.ctrl_key_pressed and len(pos_array) >= 2:

                # Update points location if the mouse position was changed above a certain distance
                distance = np.linalg.norm(pos_array[-1] - pos_array[-2])
                if distance >= 1:
                    self.network_plot.move_selected_points(self.view_in_dimensions_num, pos_array[-2],
                                                           pos_array[-1], self.z_indexing_mode, self.color_by,
                                                           self.group_by)

        # Move visuals mode
        else:

            # Initiation of dragging -> find the visual to move
            if len(pos_array) == 3:
                self.visual_to_move = self.network_plot.find_visual(self.canvas, pos_array[0])

                # The visual to move is a group name
                if self.visual_to_move == "text":
                    self.network_plot.find_group_name_to_move(pos_array[0], self.group_by, self.group_names_display)

                ## Disabled currently
                # The visual to move is a data-point(s)
                #elif self.visual_to_move == "data":
                    #self.network_plot.find_points_to_move(pos_array[0])

            # Mouse dragging continues -> move the clicked selected visual
            elif len(pos_array) > 3:

                # If the mouse position was changed above a certain distance
                distance = np.linalg.norm(pos_array[-1] - pos_array[-2])
                if distance >= 1:

                    # Move group name
                    if self.visual_to_move == "text":
                        self.network_plot.move_group_name(pos_array[-1], self.group_names_display)

                    ## Disabled currently
                    # Move data-point(s)
                    #elif self.visual_to_move == "data":
                        #self.network_plot.move_points(pos_array[-2], pos_array[-1], self.z_indexing_mode,
                                                    # self.color_by, self.group_by)

    def canvas_mouse_double_click(self, event):

        pos_array = event.pos
        #print(pos_array)
        #print(pos_array[0])

        if self.mode == 'move_visuals':
            visual_to_edit = self.network_plot.find_visual(self.canvas, pos_array)

            # The visual to move is a group name
            if visual_to_edit == "text":
                group_ID = self.network_plot.find_group_name_to_edit(pos_array, self.group_by)

                edit_group_name_dlg = gd.EditGroupNameDialog(self.group_by, group_ID, self.network_plot)

                if edit_group_name_dlg.exec_():
                    group_name, group_name_size, clans_color, color_array, is_bold, is_italic = \
                        edit_group_name_dlg.get_group_info()

                    # Update the group information in the main dict
                    cfg.groups_dict[self.group_by][group_ID]['name'] = group_name
                    cfg.groups_dict[self.group_by][group_ID]['name_size'] = group_name_size
                    cfg.groups_dict[self.group_by][group_ID]['color'] = clans_color
                    cfg.groups_dict[self.group_by][group_ID]['color_array'] = color_array
                    cfg.groups_dict[self.group_by][group_ID]['is_bold'] = is_bold
                    cfg.groups_dict[self.group_by][group_ID]['is_italic'] = is_italic

                    # Update the plot with the new group parameters
                    self.network_plot.edit_group_parameters(group_ID, 2, self.z_indexing_mode, self.color_by,
                                                            self.group_by)

    def canvas_CTRL_release(self, event):
        self.ctrl_key_pressed = 0

        if self.mode == "interactive":
            self.network_plot.update_moved_positions(self.network_plot.selected_points, self.view_in_dimensions_num)

            # Update the coordinates in the fruchterman-reingold object
            self.fr_object.init_coordinates(cfg.sequences_array['x_coor'],
                                            cfg.sequences_array['y_coor'],
                                            cfg.sequences_array['z_coor'])














