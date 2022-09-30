from PyQt5.QtCore import QThreadPool, QUrl
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDesktopServices
from vispy import app, scene
from vispy.color import ColorArray
import numpy as np
from PIL import Image
import time
import re
import os
import clans.config as cfg
import clans.clans.io.io_gui as io
import clans.clans.io.file_formats.clans_format as clans_format
import clans.clans.io.file_formats.tab_delimited_format as tab_format
import clans.clans.layouts.layout_gui as lg
import clans.clans.layouts.fruchterman_reingold_class as fr_class
import clans.clans.graphics.network3d as net
import clans.clans.graphics.colorbar as colorbar
import clans.clans.graphics.colors as colors
import clans.clans.data.sequences as seq
import clans.clans.data.sequence_pairs as sp
import clans.clans.data.groups as groups
import clans.clans.GUI.group_dialogs as gd
import clans.clans.GUI.windows as windows
import clans.clans.GUI.metadata_dialogs as md
#import clans.clans.GUI.text_dialogs as td
import clans.clans.GUI.conf_dialogs as cd


def error_occurred(method, method_name, exception_err, error_msg):

    if cfg.run_params['is_debug_mode']:
        print("\nError in " + method.__globals__['__file__'] + " (" + method_name + "):")
        print(exception_err)

    msg_box = QMessageBox()
    msg_box.setText(error_msg)
    if msg_box.exec_():
        return


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
        self.is_hide_singeltons = 0
        self.is_show_selected_names = 0
        self.is_show_group_names = 0
        self.group_names_display = 'all'
        self.rounds_done = 0
        self.rounds_done_subset = 0
        self.view_in_dimensions_num = cfg.run_params['dimensions_num_for_clustering']
        self.dim_num = cfg.run_params['dimensions_num_for_clustering']  # The effective dimensions: 2D in case of
        # selection and image modes
        self.mode = "interactive"  # Modes of interaction with the graph: 'interactive' / 'selection' / 'text'
        self.selection_type = "sequences"  # switch between 'sequences' and 'groups' modes
        self.color_by = "groups"  # Color the nodes according to: 'groups' / 'param'
        self.group_by = 0  # The category_index of the active grouping category (default is 0 - 'Manual definition').
        self.is_subset_mode = 0  # In subset mode, only the selected data-points are displayed
        self.z_indexing_mode = "auto"  # Switch between 'auto' and 'groups' modes
        self.ctrl_key_pressed = 0
        self.is_selection_drag_event = 0
        self.visual_to_move = None
        self.is_init = 0
        self.done_color_by_length = 0
        self.load_file_worker = None

        self.setWindowTitle("CLANS " + str(self.dim_num) + "D-View")
        self.setGeometry(50, 50, 1400, 1000)

        # Define layouts within the main window
        self.main_layout = QVBoxLayout()
        self.calc_layout = QHBoxLayout()
        self.mode_layout = QHBoxLayout()
        self.display_layout = QHBoxLayout()
        self.groups_layout = QHBoxLayout()

        self.main_layout.setSpacing(4)

        self.horizontal_spacer_long = QSpacerItem(18, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer_short = QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer_tiny = QSpacerItem(6, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Define a menu-bar
        self.main_menu = QMenuBar()
        self.setMenuBar(self.main_menu)
        self.main_menu.setNativeMenuBar(False)

        # Create the File menu
        self.file_menu = self.main_menu.addMenu("File")

        self.load_file_submenu = self.file_menu.addMenu("Load input file")

        self.load_clans_file_action = QAction("CLANS format", self)
        self.load_clans_file_action.triggered.connect(self.load_clans_file)

        self.load_delimited_file_action = QAction("Network format (tab-delimited)", self)
        self.load_delimited_file_action.triggered.connect(self.load_delimited_file)

        self.load_file_submenu.addAction(self.load_clans_file_action)
        self.load_file_submenu.addAction(self.load_delimited_file_action)

        self.save_file_submenu = self.file_menu.addMenu("Save to file")
        self.save_file_submenu.setEnabled(False)
        self.save_clans_submenu = self.save_file_submenu.addMenu("CLANS format")
        self.save_clans_submenu.setEnabled(False)

        self.save_full_clans_file_action = QAction("CLANS", self)
        self.save_full_clans_file_action.setEnabled(False)
        self.save_full_clans_file_action.triggered.connect(self.save_full_clans_file)

        self.save_clans_file_action = QAction("Legacy CLANS", self)
        self.save_clans_file_action.setEnabled(False)
        self.save_clans_file_action.triggered.connect(self.save_clans_file)

        self.save_delimited_file_action = QAction("Network format (tab-delimited)", self)
        self.save_delimited_file_action.setEnabled(False)
        self.save_delimited_file_action.triggered.connect(self.save_delimited_file)

        self.save_clans_submenu.addAction(self.save_full_clans_file_action)
        self.save_clans_submenu.addAction(self.save_clans_file_action)
        self.save_file_submenu.addAction(self.save_delimited_file_action)

        self.save_image_submenu = self.file_menu.addMenu("Save as image")
        self.save_image_submenu.setEnabled(False)

        self.save_image_action = QAction("Current graph view", self)
        self.save_image_action.setEnabled(False)
        self.save_image_action.triggered.connect(self.save_image)

        self.save_image_connections_backwards_action = QAction("Move connections backwards", self)
        self.save_image_connections_backwards_action.setEnabled(False)
        self.save_image_connections_backwards_action.triggered.connect(self.save_image_connections_backwards)

        self.save_stereo_image_action = QAction("Create stereo image", self)
        if cfg.run_params['dimensions_num_for_clustering'] == 2:
            self.save_stereo_image_action.setEnabled(False)
        self.save_stereo_image_action.triggered.connect(self.create_stereo_image)

        self.save_image_submenu.addAction(self.save_image_action)
        self.save_image_submenu.addAction(self.save_image_connections_backwards_action)
        self.save_image_submenu.addAction(self.save_stereo_image_action)

        self.quit_action = QAction("Quit", self)
        self.quit_action.triggered.connect(qApp.quit)

        self.file_menu.addAction(self.quit_action)

        # Create the Configuration menu
        self.conf_menu = self.main_menu.addMenu("Configure")

        # Configure layout parameters
        self.conf_layout_submenu = self.conf_menu.addMenu("Layout parameters")
        self.conf_menu.addSeparator()
        self.conf_FR_layout_action = QAction("Fruchterman-Reingold", self)
        self.conf_FR_layout_action.triggered.connect(self.conf_FR_layout)
        self.conf_layout_submenu.addAction(self.conf_FR_layout_action)

        # Configure nodes settings
        self.conf_nodes_action = QAction("Data-points general settings", self)
        self.conf_nodes_action.setEnabled(False)
        self.conf_nodes_action.triggered.connect(self.conf_nodes)
        self.conf_menu.addAction(self.conf_nodes_action)

        # Configure edges settings
        self.conf_edges_action = QAction("Connections (edges) settings", self)
        self.conf_edges_action.setEnabled(False)
        self.conf_edges_action.triggered.connect(self.conf_edges)
        self.conf_menu.addAction(self.conf_edges_action)

        self.conf_menu.addSeparator()

        # Configure grouping-categories
        self.manage_categories_action = QAction("Manage grouping categories", self)
        self.manage_categories_action.setEnabled(False)
        self.manage_categories_action.triggered.connect(self.edit_categories)
        self.conf_menu.addAction(self.manage_categories_action)

        # Configure numerical parameters
        self.manage_params_action = QAction("Manage numerical features", self)
        self.manage_params_action.setEnabled(False)
        self.manage_params_action.triggered.connect(self.edit_params)
        self.conf_menu.addAction(self.manage_params_action)

        # Create the Tools menu
        self.tools_menu = self.main_menu.addMenu("Tools")
        self.group_by_submenu = self.tools_menu.addMenu("Group data by:")
        self.group_by_submenu.setEnabled(False)
        self.color_by_submenu = self.tools_menu.addMenu("Color data by:")
        self.color_by_submenu.setEnabled(False)

        # Group by taxonomy action
        self.group_by_tax_action = QAction("NCBI Taxonomy", self)
        self.group_by_tax_action.setEnabled(False)
        self.group_by_tax_action.triggered.connect(self.group_by_taxonomy)

        self.group_by_submenu.addAction(self.group_by_tax_action)

        self.add_category_submenu = self.group_by_submenu.addMenu("Add custom grouping category")
        self.add_category_submenu.setEnabled(False)

        # Group-by user-defined param (from metadata file) action
        self.add_groups_from_metadata_action = QAction("From metadata file", self)
        self.add_groups_from_metadata_action.setEnabled(False)
        self.add_groups_from_metadata_action.triggered.connect(self.add_groups_from_metadata)

        self.add_category_submenu.addAction(self.add_groups_from_metadata_action)

        # Add empty category action
        self.add_category_action = QAction("Add empty category (define groups manually)", self)
        self.add_category_action.setEnabled(False)
        self.add_category_action.triggered.connect(self.add_empty_category)

        self.add_category_submenu.addAction(self.add_category_action)

        # Color by seq_length action
        self.color_by_length_action = QAction("Sequence length", self)
        self.color_by_length_action.setEnabled(False)
        self.color_by_length_action.triggered.connect(self.open_color_by_length_dialog)

        self.color_by_submenu.addAction(self.color_by_length_action)

        # Color-by user-defined param action
        self.color_by_param_action = QAction("Upload numerical metadata", self)
        self.color_by_param_action.setEnabled(False)
        self.color_by_param_action.triggered.connect(self.open_color_by_param_dialog)

        self.color_by_submenu.addAction(self.color_by_param_action)

        # Create the Help menu
        self.help_menu = self.main_menu.addMenu("Help")

        self.about_action = QAction("About CLANS", self)
        self.about_action.triggered.connect(self.open_about_window)

        self.manual_action = QAction("CLANS manual", self)
        self.manual_action.triggered.connect(self.open_manual)

        self.help_menu.addAction(self.about_action)
        self.help_menu.addAction(self.manual_action)

        # Create the canvas (the graph area)
        self.canvas = scene.SceneCanvas(size=(1150, 900), keys='interactive', show=True, bgcolor='w')
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

        self.calc_label = QLabel("Clustering:")
        self.calc_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add calculation buttons (Init, Start, Stop)
        self.start_button = QPushButton("Start clustering")
        self.start_button.setEnabled(False)
        self.start_button.pressed.connect(self.run_calc)

        self.stop_button = QPushButton("Stop clustering")
        self.stop_button.setEnabled(False)
        self.stop_button.pressed.connect(self.stop_calc)

        self.init_button = QPushButton("Initialize coordinates")
        self.init_button.setEnabled(False)
        self.init_button.pressed.connect(self.init_coor)

        # Add a button to switch between 3D and 2D clustering
        self.dimensions_clustering_combo = QComboBox()
        self.dimensions_clustering_combo.addItems(["3D Clustering", "2D Clustering"])
        self.dimensions_clustering_combo.setEnabled(False)
        self.dimensions_clustering_combo.currentIndexChanged.connect(self.change_dimensions_num_for_clustering)

        # Add a text-field for the P-value / attraction-value threshold
        self.pval_label = QLabel("P-value threshold:")
        self.pval_label.setStyleSheet("color: " + cfg.inactive_color + ";")
        self.pval_widget = QLineEdit()
        self.pval_widget.setFixedSize(90, 20)
        self.pval_widget.setText(str(cfg.run_params['similarity_cutoff']))
        self.pval_widget.setEnabled(False)
        self.pval_widget.returnPressed.connect(self.update_cutoff)

        # Add a label for displaying the number of rounds done
        self.rounds_label = QLabel("Round: ")
        self.rounds_label.setStyleSheet("color: " + cfg.title_color + ";")
        self.round_num_label = QLabel(str(self.rounds_done))
        self.round_num_label.setFixedSize(90, 20)
        self.round_num_label.setStyleSheet("color: " + cfg.inactive_color + ";")

        # Add the widgets to the calc_layout
        self.calc_layout.addStretch()
        self.calc_layout.addWidget(self.calc_label)
        self.calc_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.calc_layout.addWidget(self.init_button)
        self.calc_layout.addWidget(self.start_button)
        self.calc_layout.addWidget(self.stop_button)
        self.calc_layout.addSpacerItem(self.horizontal_spacer_long)
        self.calc_layout.addWidget(self.dimensions_clustering_combo)
        self.calc_layout.addSpacerItem(self.horizontal_spacer_long)
        self.calc_layout.addWidget(self.pval_label)
        self.calc_layout.addWidget(self.pval_widget)
        self.calc_layout.addWidget(self.error_label)
        self.calc_layout.addSpacerItem(self.horizontal_spacer_long)
        self.calc_layout.addWidget(self.rounds_label)
        self.calc_layout.addWidget(self.round_num_label)
        self.calc_layout.addStretch()

        # Add the calc_layout to the main layout
        self.main_layout.addLayout(self.calc_layout)

        self.separator_line1 = QFrame()
        self.separator_line1.setFrameShape(QFrame.HLine)
        self.separator_line1.setFrameShadow(QFrame.Raised)
        self.main_layout.addWidget(self.separator_line1)

        # Add a combo-box to switch between user-interaction modes
        self.mode_label = QLabel("Interaction mode:")
        self.mode_label.setStyleSheet("color: maroon; font-weight: bold;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Rotate/Pan graph", "Select data-points", "Move/Edit text"])
        self.mode_combo.setEnabled(False)
        self.mode_combo.currentIndexChanged.connect(self.change_mode)

        self.selection_mode_label = QLabel("Selection mode:")
        self.selection_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")

        # Add a combo-box to switch between sequences / groups selection
        self.selection_type_combo = QComboBox()
        self.selection_type_combo.addItems(["Sequences", "Groups"])
        self.selection_type_combo.setEnabled(False)
        self.selection_type_combo.currentIndexChanged.connect(self.change_selection_type)

        self.selection_label = QLabel("Selection:")
        self.selection_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add a button to select all the sequences / groups
        self.select_all_button = QPushButton("Select all")
        self.select_all_button.setEnabled(False)
        self.select_all_button.released.connect(self.select_all)

        # Add a button to inverse the selection (select the non-selected)
        self.inverse_selection_button = QPushButton("Inverse selection")
        self.inverse_selection_button.setEnabled(False)
        self.inverse_selection_button.released.connect(self.inverse_selection)

        # Add a button to clear the current selection
        self.clear_selection_button = QPushButton("Clear")
        self.clear_selection_button.setEnabled(False)
        self.clear_selection_button.released.connect(self.clear_selection)

        # Add a button to open the text-search window
        self.select_by_text_button = QPushButton("Select by text")
        self.select_by_text_button.setEnabled(False)
        self.select_by_text_button.released.connect(self.select_by_text)

        # Add a button to open the searching by groups window
        self.select_by_groups_button = QPushButton("Select by groups")
        self.select_by_groups_button.setEnabled(False)
        self.select_by_groups_button.released.connect(self.select_by_groups)

        # Add a button to open the Selected Sequences window
        self.open_selected_button = QPushButton("Edit selected")
        self.open_selected_button.setEnabled(False)
        self.open_selected_button.released.connect(self.open_selected_window)

        # Add the widgets to the mode layout
        self.mode_layout.addStretch()
        self.mode_layout.addWidget(self.mode_label)
        self.mode_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.mode_layout.addWidget(self.mode_combo)
        self.mode_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.mode_layout.addWidget(self.selection_mode_label)
        self.mode_layout.addWidget(self.selection_type_combo)
        self.mode_layout.addSpacerItem(self.horizontal_spacer_long)
        self.mode_layout.addWidget(self.selection_label)
        self.mode_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.mode_layout.addWidget(self.select_all_button)
        self.mode_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.mode_layout.addWidget(self.inverse_selection_button)
        self.mode_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.mode_layout.addWidget(self.clear_selection_button)
        self.mode_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.mode_layout.addWidget(self.select_by_text_button)
        self.mode_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.mode_layout.addWidget(self.select_by_groups_button)
        self.mode_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.mode_layout.addWidget(self.open_selected_button)
        self.mode_layout.addStretch()

        # Add the mode_layout to the main layout
        self.main_layout.addLayout(self.mode_layout)

        self.separator_line2 = QFrame()
        self.separator_line2.setFrameShape(QFrame.HLine)
        self.separator_line2.setFrameShadow(QFrame.Raised)
        self.main_layout.addWidget(self.separator_line2)

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
        if len(cfg.groups_by_categories[self.group_by]['groups']) == 0:
            self.show_group_names_button.setEnabled(False)
        self.show_group_names_button.released.connect(self.manage_group_names)

        # Add a combo-box to choose whether showing the selected group names only or all the group names
        self.show_groups_combo = QComboBox()
        self.show_groups_combo.addItems(["All", "Selected"])
        self.show_groups_combo.setEnabled(False)
        self.show_groups_combo.currentIndexChanged.connect(self.change_group_names_display)

        # Add 'reset group names' button
        self.reset_group_names_button = QPushButton("Init names positions")
        self.reset_group_names_button.setEnabled(False)
        self.reset_group_names_button.pressed.connect(self.reset_group_names_positions)

        self.view_label = QLabel("View:")
        self.view_label.setStyleSheet("color: maroon; font-weight: bold;")

        # Add a button to change the Z-indexing of nodes in 2D presentation
        self.z_index_mode_label = QLabel("Z-index:")
        self.z_index_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")

        self.z_index_mode_combo = QComboBox()
        self.z_index_mode_combo.addItems(["Automatic", "By groups order"])
        if self.dim_num == 3 or len(cfg.groups_by_categories[self.group_by]['groups']) == 0:
            self.z_index_mode_combo.setEnabled(False)
        self.z_index_mode_combo.currentIndexChanged.connect(self.manage_z_indexing)

        # Add a combo-box to move between full-data mode and selected subset mode
        self.data_mode_combo = QComboBox()
        self.data_mode_combo.addItems(["Full dataset", "Selected subset"])
        self.data_mode_combo.setEnabled(False)
        self.data_mode_combo.currentIndexChanged.connect(self.manage_subset_presentation)

        # Add a button to hide singeltons
        self.hide_singeltons_button = QPushButton("Hide singeltons")
        self.hide_singeltons_button.setCheckable(True)
        self.hide_singeltons_button.setEnabled(False)
        self.hide_singeltons_button.released.connect(self.hide_singeltons)

        self.display_layout.addStretch()
        self.display_layout.addWidget(self.display_label)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.connections_button)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.show_selected_names_button)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.show_group_names_button)
        self.display_layout.addWidget(self.show_groups_combo)
        self.display_layout.addWidget(self.reset_group_names_button)
        self.display_layout.addSpacerItem(self.horizontal_spacer_long)
        self.display_layout.addWidget(self.view_label)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.z_index_mode_label)
        self.display_layout.addWidget(self.z_index_mode_combo)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.data_mode_combo)
        self.display_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.display_layout.addWidget(self.hide_singeltons_button)
        self.display_layout.addStretch()

        # Add the view_layout to the main layout
        self.main_layout.addLayout(self.display_layout)

        self.separator_line3 = QFrame()
        self.separator_line3.setFrameShape(QFrame.HLine)
        self.separator_line3.setFrameShadow(QFrame.Raised)
        self.main_layout.addWidget(self.separator_line3)

        # Add a combo-box to switch between color-by options
        self.color_by_label = QLabel("Color data by:")
        self.color_by_label.setStyleSheet("color: maroon;font-weight: bold;")

        self.color_by_combo = QComboBox()
        self.color_by_combo.addItem("Groups/Default")
        self.color_by_combo.setEnabled(False)
        self.color_by_combo.currentIndexChanged.connect(self.change_coloring)

        # Add a combo-box to switch between group-by options
        self.group_by_label = QLabel("Grouping category:")
        self.group_by_label.setStyleSheet("color: maroon; font-weight: bold;")

        self.group_by_combo = QComboBox()
        self.group_by_combo.addItem("Manual definition")
        self.group_by_combo.setEnabled(False)
        self.group_by_combo.currentIndexChanged.connect(self.change_grouping)

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

        self.groups_layout.addStretch()
        self.groups_layout.addWidget(self.color_by_label)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.groups_layout.addWidget(self.color_by_combo)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_long)
        self.groups_layout.addWidget(self.group_by_label)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.groups_layout.addWidget(self.group_by_combo)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_long)
        self.groups_layout.addWidget(self.groups_label)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.groups_layout.addWidget(self.edit_groups_button)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.groups_layout.addWidget(self.add_to_group_button)
        self.groups_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.groups_layout.addWidget(self.remove_selected_button)
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

        # Create the 'about' window
        self.about_window = windows.AboutWindow()

        # Create a window to display sequence search results (without showing it)
        self.search_window = windows.SearchResultsWindow(self, self.network_plot)

        # Create a window to display the selection by groups (without showing it)
        self.select_by_groups_window = windows.SelectByGroupsWindow(self, self.network_plot)

        # Create a window for the stereo presentation
        self.stereo_window = windows.StereoImageWindow(self)

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
        self.add_groups_from_metadata_action.setEnabled(False)
        self.color_by_param_action.setEnabled(False)

        self.start_button.setText("Start clustering")
        self.dimensions_clustering_combo.setCurrentIndex(0)

        self.mode_combo.setCurrentIndex(0)
        self.selection_type_combo.setCurrentIndex(0)
        self.open_selected_button.setEnabled(False)
        self.clear_selection_button.setEnabled(False)
        self.inverse_selection_button.setEnabled(False)

        self.z_index_mode_combo.setEnabled(False)
        self.z_index_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")
        self.z_index_mode_combo.setCurrentIndex(0)

        self.connections_button.setChecked(False)
        self.hide_singeltons_button.setChecked(False)
        self.show_selected_names_button.setChecked(False)
        self.show_selected_names_button.setEnabled(False)
        self.data_mode_combo.setEnabled(False)
        self.data_mode_combo.setCurrentIndex(0)

        self.add_to_group_button.setEnabled(False)
        self.remove_selected_button.setEnabled(False)
        self.edit_groups_button.setEnabled(False)
        self.select_by_groups_button.setEnabled(False)
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
        self.manage_params_action.setEnabled(False)

        # Remove all the group-by options except 'Manual' (the default)
        self.group_by_combo.clear()
        self.group_by_combo.addItem("Manual definition")
        self.group_by_combo.setEnabled(False)
        self.manage_categories_action.setEnabled(False)

        # Reset the list of sequences in the 'selected sequences' window
        self.selected_seq_window.clear_list()
        # Close the windows
        self.selected_seq_window.close_window()
        self.select_by_groups_window.close_window()
        self.search_window.close_window()
        self.stereo_window.close_window()

        self.is_init = 0

    def reset_variables(self):

        # Reset global variables
        cfg.groups_by_categories = list()
        cfg.groups_by_categories.append({
            'name': 'Manual definition',
            'groups': dict(),
            'sequences': list(),
            'nodes_size': cfg.run_params['nodes_size'],
            'nodes_outline_color': cfg.run_params['nodes_outline_color'],
            'text_size': cfg.run_params['text_size'],
            'nodes_outline_width': cfg.run_params['nodes_outline_width'],
            'is_bold': True,
            'is_italic': False
        })
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
        cfg.connected_sequences_mtx_subset = []
        cfg.connected_sequences_list = []
        cfg.att_values_for_connected_list = []
        cfg.connected_sequences_list_subset = []
        cfg.att_values_for_connected_list_subset = []
        cfg.singeltons_list = []
        cfg.singeltons_list_subset = []

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
        cfg.run_params['found_taxa_num'] = 0
        cfg.run_params['cooling'] = cfg.layouts['FR']['params']['cooling']
        cfg.run_params['maxmove'] = cfg.layouts['FR']['params']['maxmove']
        cfg.run_params['att_val'] = cfg.layouts['FR']['params']['att_val']
        cfg.run_params['att_exp'] = cfg.layouts['FR']['params']['att_exp']
        cfg.run_params['rep_val'] = cfg.layouts['FR']['params']['rep_val']
        cfg.run_params['rep_exp'] = cfg.layouts['FR']['params']['rep_exp']
        cfg.run_params['dampening'] = cfg.layouts['FR']['params']['dampening']
        cfg.run_params['gravity'] = cfg.layouts['FR']['params']['gravity']
        cfg.run_params['nodes_size'] = 8
        cfg.run_params['nodes_color'] = [0.0, 0.0, 0.0, 1.0]
        cfg.run_params['nodes_outline_color'] = [0.0, 0.0, 0.0, 1.0]
        cfg.run_params['nodes_outline_width'] = 0.5
        cfg.min_param_color = ColorArray([1.0, 1.0, 0.0, 1.0])
        cfg.max_param_color = ColorArray([1.0, 0.0, 0.0, 1.0])
        cfg.short_color = ColorArray([1.0, 1.0, 0.0, 1.0])
        cfg.long_color = ColorArray([1.0, 0.0, 0.0, 1.0])

        # Reset MainWindow class variables
        self.is_running_calc = 0
        self.is_show_connections = 0
        self.is_hide_singeltons = 0
        self.is_show_selected_names = 0
        self.is_show_group_names = 0
        self.group_names_display = 'all'
        self.rounds_done = 0
        self.rounds_done_subset = 0
        self.view_in_dimensions_num = cfg.run_params['dimensions_num_for_clustering']
        self.dim_num = cfg.run_params['dimensions_num_for_clustering']
        self.mode = "interactive"  # Modes of interaction: 'interactive' (rotate/pan) / 'selection'
        self.selection_type = "sequences"  # switch between 'sequences' and 'groups' modes
        self.is_subset_mode = 0  # In subset mode, only the selected data-points are displayed
        self.z_indexing_mode = "auto"  # Switch between 'auto' and 'groups' modes
        self.ctrl_key_pressed = 0
        self.is_selection_drag_event = 0
        self.done_color_by_length = 0
        self.color_by = 'groups'

    def load_input_file(self):
        self.load_file_worker.signals.finished.connect(self.receive_load_status)

        self.before = time.time()

        # Execute
        self.threadpool.start(self.load_file_worker)

        # Put a 'loading file' message
        self.canvas.central_widget.add_widget(self.load_file_label)

    def receive_load_status(self, status):

        self.is_init = 1

        self.file_name = os.path.basename(cfg.run_params['input_file'])

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

            # Update the dim_num with the parameter from the file
            self.dim_num = cfg.run_params['dimensions_num_for_clustering']

            # Remove the 'loading file' message
            self.load_file_label.parent = None

            # Set the window title to include the file name
            self.setWindowTitle("CLANS " + str(self.dim_num) + "D-View of " + self.file_name)

            # Enable the menu items
            self.save_file_submenu.setEnabled(True)
            self.save_clans_submenu.setEnabled(True)
            self.save_full_clans_file_action.setEnabled(True)
            self.save_clans_file_action.setEnabled(True)
            self.save_delimited_file_action.setEnabled(True)
            self.save_image_submenu.setEnabled(True)
            self.save_image_action.setEnabled(True)
            self.conf_nodes_action.setEnabled(True)
            self.conf_edges_action.setEnabled(True)
            self.group_by_submenu.setEnabled(True)
            self.group_by_tax_action.setEnabled(True)
            self.add_category_submenu.setEnabled(True)
            self.add_groups_from_metadata_action.setEnabled(True)
            self.add_category_action.setEnabled(True)
            self.color_by_submenu.setEnabled(True)
            self.color_by_param_action.setEnabled(True)

            if cfg.run_params['input_format'] == 'clans':
                self.color_by_length_action.setEnabled(True)

            # Enable the controls
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.init_button.setEnabled(True)
            self.dimensions_clustering_combo.setEnabled(True)
            self.pval_widget.setEnabled(True)
            self.pval_label.setStyleSheet("color: black;")
            self.round_num_label.setStyleSheet("color: black;")
            self.mode_combo.setEnabled(True)
            self.select_all_button.setEnabled(True)
            self.select_by_text_button.setEnabled(True)
            self.connections_button.setEnabled(True)
            self.hide_singeltons_button.setEnabled(True)
            #self.add_text_button.setEnabled(True)

            # Check if there are any defined groups
            groups_ok = 0
            for category_index in range(len(cfg.groups_by_categories)):
                groups_num = len(cfg.groups_by_categories[category_index]['groups'])
                if groups_num > 0:

                    # Pop up an error message
                    if groups_num > cfg.max_groups_num:
                        msg_box = QMessageBox()
                        message = "The Number of groups in the \'" + cfg.groups_by_categories[category_index]['name'] + \
                                  "\' grouping-category exceeds " + str(cfg.max_groups_num) + " (" + str(groups_num) + \
                                  " groups).\nContinue without loading groups in this category."

                        msg_box.setText(message)
                        if msg_box.exec_():
                            return

                        try:
                            groups.delete_grouping_category(category_index)
                        except Exception as err:
                            error_msg = "An error occurred: cannot delete the grouping category"
                            error_occurred(groups.delete_grouping_category, 'delete_grouping_category', err, error_msg)

                    # The number of groups is ok
                    else:
                        groups_ok = 1
                        self.group_by_combo.addItem(cfg.groups_by_categories[category_index]['name'])

            # There is at least one valid pre-defined grouping category
            if groups_ok:
                self.select_by_groups_button.setEnabled(True)
                self.manage_categories_action.setEnabled(True)
                self.edit_groups_button.setEnabled(True)
                self.show_group_names_button.setEnabled(True)
                self.group_by_combo.setEnabled(True)
                self.group_by_combo.setCurrentIndex(1)
                self.group_by = 1
                if self.dim_num == 2:
                    self.z_index_mode_combo.setEnabled(True)
                    self.z_index_mode_label.setStyleSheet("color: black;")

            # If there are uploaded numeric parameters - enable the color-by combo-box
            if len(cfg.sequences_numeric_params) > 0:
                self.color_by_combo.setEnabled(True)
                self.manage_params_action.setEnabled(True)
                for param in cfg.sequences_numeric_params:
                    self.color_by_combo.addItem(param)

            # Update the file name in the selected sequences window
            #self.selected_seq_window.update_window_title(self.file_name)

            # Create and display the FR layout as scatter plot
            try:
                self.network_plot.init_data(self.fr_object, self.group_by)
            except Exception as err:
                error_msg = "An error occurred: cannot initialize the data.\n" \
                            "Try to reload the input file or load another file."
                error_occurred(self.network_plot.init_data, 'init_data', err, error_msg)
                return

            # Update the number of rounds label
            self.rounds_done = cfg.run_params['rounds_done']
            self.round_num_label.setText(str(self.rounds_done))
            if self.rounds_done > 0:
                self.start_button.setText("Resume clustering")

            # Update the text-field for the threshold according to the type of values
            if cfg.run_params['type_of_values'] == 'att':
                self.pval_label.setText("Score threshold:")
            else:
                self.pval_label.setText("P-value threshold:")
            self.pval_widget.setText(str(cfg.run_params['similarity_cutoff']))

            if cfg.run_params['dimensions_num_for_clustering'] == 2:
                self.dimensions_clustering_combo.setCurrentIndex(1)

            # Init the plots in the stereo window
            try:
                self.stereo_window.init_plot()
            except Exception as err:
                error_msg = "An error occurred: cannot initialize the data in the stereo window.\n"
                error_occurred(self.stereo_window.init_plot, 'init_plot', err, error_msg)
                return

        else:
            # Remove the 'loading file' message from the scene and put an error message instead
            self.load_file_label.parent = None
            msg_box = QMessageBox()
            error_msg = cfg.run_params['error'] + "\nPlease load a new file and select the correct format."
            msg_box.setText(error_msg)
            if msg_box.exec_():
                return

        self.is_init = 0

    def load_clans_file(self):

        opened_file, _ = QFileDialog.getOpenFileName(self, "Open file", "", "Clans files (*.clans)")

        if opened_file:
            print("Loading " + opened_file)

            # Bring the controls to their initial state
            self.reset_window()

            # Clear the canvas
            try:
                self.network_plot.reset_data()
            except Exception as err:
                error_msg = "An error occurred: cannot reset the graph"
                error_occurred(self.network_plot.reset_data, 'reset_data', err, error_msg)
                return

            # Clear the canvas of the stereo window
            try:
                self.stereo_window.reset_plot()
            except Exception as err:
                error_msg = "An error occurred: cannot reset the stereo canvas"
                error_occurred(self.stereo_window.reset_plot, 'reset_plot', err, error_msg)
                return

            # Initialize all the global data-structures
            self.reset_variables()

            cfg.run_params['input_file'] = opened_file
            cfg.run_params['input_format'] = 'clans'
            self.setWindowTitle("CLANS " + str(self.dim_num) + "D-View")

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
            try:
                self.network_plot.reset_data()
            except Exception as err:
                error_msg = "An error occurred: cannot reset the graph"
                error_occurred(self.network_plot.reset_data, 'reset_data', err, error_msg)
                return

            # Clear the canvas of the stereo window
            try:
                self.stereo_window.left_plot.reset_data()
                self.stereo_window.right_plot.reset_data()
            except Exception as err:
                error_msg = "An error occurred: cannot reset the stereo canvas"
                error_occurred(self.stereo_window.left_plot.reset_data, 'reset_data', err, error_msg)
                return

            # Initialize all the global data-structures
            self.reset_variables()

            cfg.run_params['input_file'] = opened_file
            cfg.run_params['input_format'] = 'delimited'
            self.setWindowTitle("CLANS " + str(self.dim_num) + "D-View")

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

            # Show the singeltons
            self.hide_singeltons_button.setChecked(False)
            self.hide_singeltons()

            try:
                self.network_plot.hide_sequences_names()
            except Exception as err:
                error_msg = "An error occurred: cannot clear the seuences names"
                error_occurred(self.network_plot.hide_sequences_names, 'hide_sequences_names', err, error_msg)

            # Hide the group names
            self.show_group_names_button.setChecked(False)
            self.reset_group_names_button.setEnabled(False)
            self.is_show_group_names = 0

            try:
                self.network_plot.hide_group_names()
            except Exception as err:
                error_msg = "An error occurred: cannot clear the group names"
                error_occurred(self.network_plot.hide_group_names, 'hide_group_names', err, error_msg)

            # Disable the 'Add text' button
            #self.add_text_button.setEnabled(False)

            # 2D clustering
            if cfg.run_params['dimensions_num_for_clustering'] == 2:
                # Move to automatic z-indexing
                self.z_index_mode_combo.setCurrentIndex(0)

            # Move back to rotation interaction mode
            self.mode_combo.setCurrentIndex(0)

            # Disable all setup changes while calculating
            self.init_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.dimensions_clustering_combo.setEnabled(False)
            self.pval_widget.setEnabled(False)
            self.pval_label.setStyleSheet("color: " + cfg.inactive_color + ";")
            self.connections_button.setEnabled(False)
            self.hide_singeltons_button.setEnabled(False)
            self.show_selected_names_button.setEnabled(False)
            self.open_selected_button.setEnabled(False)
            self.clear_selection_button.setEnabled(False)
            self.inverse_selection_button.setEnabled(False)
            self.data_mode_combo.setEnabled(False)
            self.show_group_names_button.setEnabled(False)
            self.reset_group_names_button.setEnabled(False)
            #self.add_text_button.setEnabled(False)
            self.show_groups_combo.setEnabled(False)
            self.mode_combo.setEnabled(False)
            self.selection_type_combo.setEnabled(False)
            self.select_all_button.setEnabled(False)
            self.select_by_text_button.setEnabled(False)
            self.select_by_groups_button.setEnabled(False)
            self.edit_groups_button.setEnabled(False)
            self.add_to_group_button.setEnabled(False)
            self.remove_selected_button.setEnabled(False)
            self.z_index_mode_combo.setEnabled(False)
            self.z_index_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")
            self.color_by_combo.setEnabled(False)
            self.group_by_combo.setEnabled(False)

            # Execute
            self.threadpool.start(self.run_calc_worker)

    def update_plot(self):

        try:
            self.network_plot.update_data(self.dim_num, self.fr_object, 1, self.color_by)
        except Exception as err:
            error_msg = "An error occurred: cannot update the graph"
            error_occurred(self.network_plot.update_data, 'update_data', err, error_msg)
            return

        # Full data mode
        if self.is_subset_mode == 0:
            self.rounds_done += 1
            self.round_num_label.setText(str(self.rounds_done))

            if cfg.run_params['is_debug_mode']:
                if self.rounds_done % 100 == 0:
                    self.after = time.time()
                    duration = (self.after - self.before)
                    print("The calculation of " + str(self.rounds_done) + " rounds took " + str(duration) + " seconds")

        # Subset mode
        else:
            self.rounds_done_subset += 1
            self.round_num_label.setText(str(self.rounds_done_subset))

    def stop_calc(self):
        if self.is_running_calc == 1:
            self.run_calc_worker.stop()

    def stopped_state(self, error):
        if self.is_subset_mode == 0:
            self.after = time.time()
            duration = (self.after - self.before)
            print("The calculation has stopped at round no. " + str(self.rounds_done))

            if cfg.run_params['is_debug_mode']:
                print("The calculation of " + str(self.rounds_done) + " rounds took " + str(duration) + " seconds")

        self.start_button.setText("Resume clustering")
        self.is_running_calc = 0

        # Enable all settings buttons
        self.init_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.dimensions_clustering_combo.setEnabled(True)
        self.pval_widget.setEnabled(True)
        self.pval_label.setStyleSheet("color: black;")
        self.connections_button.setEnabled(True)
        self.hide_singeltons_button.setEnabled(True)
        #self.add_text_button.setEnabled(True)

        # Enable group-related options
        if len(cfg.groups_by_categories[self.group_by]['groups']) > 0 and self.color_by == 'groups':
            self.show_group_names_button.setEnabled(True)
            self.edit_groups_button.setEnabled(True)
            if len(self.network_plot.selected_groups) > 0:
                self.show_groups_combo.setEnabled(True)

            if self.is_subset_mode == 0 and self.dim_num == 2:
                self.z_index_mode_combo.setEnabled(True)
                self.z_index_mode_label.setStyleSheet("color: black;")

        # Enable selection-related buttons only in full data mode
        if self.is_subset_mode == 0:
            self.mode_combo.setEnabled(True)
            self.select_all_button.setEnabled(True)

        self.select_by_text_button.setEnabled(True)

        if len(cfg.groups_by_categories) > 0 or len(cfg.groups_by_categories[0]['groups']) > 0:
            self.select_by_groups_button.setEnabled(True)

        # If at least one point is selected -> enable all buttons related to actions on selected points
        if self.network_plot.selected_points != {}:
            self.show_selected_names_button.setEnabled(True)
            self.open_selected_button.setEnabled(True)
            self.clear_selection_button.setEnabled(True)
            self.inverse_selection_button.setEnabled(True)
            self.add_to_group_button.setEnabled(True)
            self.remove_selected_button.setEnabled(True)
            self.data_mode_combo.setEnabled(True)

        # Enable the 'color by' combo box if the color-by-param was already done once
        if self.done_color_by_length or len(cfg.sequences_numeric_params) > 0:
            self.color_by_combo.setEnabled(True)
            self.manage_params_action.setEnabled(True)

        # Enable the 'group-by' combo box if is more than one grouping option
        if self.group_by_combo.count() > 1 and self.color_by == 'groups':
            self.group_by_combo.setEnabled(True)

        # Whole data calculation mode
        if self.is_subset_mode == 0:

            # Update the coordinates saved in the sequences_array
            try:
                seq.update_positions(self.fr_object.coordinates.T, 'full')
            except Exception as err:
                error_msg = "An error occurred: cannot update the coordinates"
                error_occurred(seq.update_positions, 'update_positions', err, error_msg)
                return

            # Reset the group-names positions
            try:
                self.network_plot.reset_group_names_positions(self.group_by)
            except Exception as err:
                error_msg = "An error occurred: cannot reset the group-names positions"
                error_occurred(self.network_plot.reset_group_names_positions, 'reset_group_names_positions', err,
                               error_msg)

        # Subset calculation mode
        else:

            # Update the subset-coordinates saved in the sequences_array
            try:
                seq.update_positions(self.fr_object.coordinates.T, 'subset')
            except Exception as err:
                error_msg = "An error occurred: cannot update the coordinates"
                error_occurred(seq.update_positions, 'update_positions', err, error_msg)
                return

        # Calculate the azimuth and elevation angles of the new points positions
        try:
            self.network_plot.calculate_initial_angles()
        except Exception as err:
            error_msg = "An error occurred: cannot calculate angles"
            error_occurred(self.network_plot.calculate_initial_angles, 'calculate_initial_angles', err, error_msg)
            return

        # Update the global variable of number of rounds
        cfg.run_params['rounds_done'] = self.rounds_done

    def init_coor(self):
        # Initialize the coordinates only if the calculation is not running
        if self.is_running_calc == 0:
            self.start_button.setText("Start clustering")
            self.before = None
            self.after = None
            self.is_running_calc = 0

            # Reset the number of rounds
            if self.is_subset_mode == 0:
                self.rounds_done = 0
            else:
                self.rounds_done_subset = 0

            self.round_num_label.setText("0")

            # Generate random positions to be saved in the main sequences array
            # Subset mode -> only for the sequences in the subset
            if self.is_subset_mode:
                cfg.sequences_array['x_coor_subset'], cfg.sequences_array['y_coor_subset'], \
                cfg.sequences_array['z_coor_subset'] = seq.init_positions(cfg.run_params['total_sequences_num'])

                # Update the coordinates in the fruchterman-reingold object
                try:
                    self.fr_object.init_calculation(cfg.sequences_array['x_coor_subset'],
                                                    cfg.sequences_array['y_coor_subset'],
                                                    cfg.sequences_array['z_coor_subset'])
                except Exception as err:
                    error_msg = "An error occurred: cannot initialize the coordinates"
                    error_occurred(self.fr_object.init_calculation, 'init_calculation', err, error_msg)
                    return

            # Full mode -> Init the whole dataset
            else:
                cfg.sequences_array['x_coor'], cfg.sequences_array['y_coor'], cfg.sequences_array['z_coor'] = \
                    seq.init_positions(cfg.run_params['total_sequences_num'])

                # Update the coordinates in the fruchterman-reingold object
                try:
                    self.fr_object.init_calculation(cfg.sequences_array['x_coor'],
                                                    cfg.sequences_array['y_coor'],
                                                    cfg.sequences_array['z_coor'])
                except Exception as err:
                    error_msg = "An error occurred: cannot initialize the coordinates"
                    error_occurred(self.fr_object.init_calculation, 'init_calculation', err, error_msg)
                    return

            try:
                self.network_plot.update_data(self.dim_num, self.fr_object, 1, self.color_by)
            except Exception as err:
                error_msg = "An error occurred: cannot update the graph"
                error_occurred(self.network_plot.update_data, 'update_data', err, error_msg)
                return

            # Calculate the angles of each point for future use when having rotations
            try:
                self.network_plot.calculate_initial_angles()
            except Exception as err:
                error_msg = "An error occurred: cannot calculate angles"
                error_occurred(self.network_plot.calculate_initial_angles, 'calculate_initial_angles', err, error_msg)
                return

            print("Coordinates were initiated.")

            # Move back to interactive mode
            self.mode_combo.setCurrentIndex(0)

            if cfg.run_params['dimensions_num_for_clustering'] == 2 and self.z_indexing_mode == 'groups':
                self.z_index_mode_combo.setCurrentIndex(0)

            try:
                self.network_plot.reset_rotation()
            except Exception as err:
                error_msg = "An error occurred: cannot reset the rotation of the graph"
                error_occurred(self.network_plot.reset_rotation, 'reset_rotation', err, error_msg)

            try:
                self.network_plot.reset_group_names_positions(self.group_by)
            except Exception as err:
                error_msg = "An error occurred: cannot reset the positions of the group names"
                error_occurred(self.network_plot.reset_group_names_positions, 'reset_group_names_positions', err,
                               error_msg)

    def manage_connections(self):

        # Show the connections
        if self.connections_button.isChecked():
            self.is_show_connections = 1

            # Display the connecting lines
            try:
                self.network_plot.show_connections()
            except Exception as err:
                error_msg = "An error occurred: cannot display the connecting lines"
                error_occurred(self.network_plot.show_connections, 'show_connections', err, error_msg)

            if self.dim_num == 3:
                self.save_image_connections_backwards_action.setEnabled(True)

        # Hide the connections
        else:
            self.is_show_connections = 0

            try:
                self.network_plot.hide_connections()
            except Exception as err:
                error_msg = "An error occurred: cannot hide the connecting lines"
                error_occurred(self.network_plot.hide_connections, 'hide_connections', err, error_msg)

            self.save_image_connections_backwards_action.setEnabled(False)

    def hide_singeltons(self):

        # Hide the singeltons
        if self.hide_singeltons_button.isChecked():
            self.is_hide_singeltons = 1

            try:
                self.network_plot.hide_singeltons(self.dim_num, self.color_by, self.group_by,
                                                  self.z_indexing_mode)
            except Exception as err:
                error_msg = "An error occurred: cannot display the connecting lines"
                error_occurred(self.network_plot.hide_singeltons, 'hide_singeltons', err, error_msg)

        # Hide the connections
        else:
            self.is_hide_singeltons = 0

            try:
                self.network_plot.show_singeltons(self.dim_num, self.color_by, self.group_by,
                                                  self.z_indexing_mode)
            except Exception as err:
                error_msg = "An error occurred: cannot hide the connecting lines"
                error_occurred(self.network_plot.show_singeltons, 'show_singeltons', err, error_msg)

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

                # Update the main matrix of connected pairs
                try:
                    sp.define_connected_sequences(cfg.run_params['type_of_values'])
                except Exception as err:
                    error_msg = "An error occurred: cannot update the connected sequences"
                    error_occurred(sp.define_connected_sequences, 'define_connected_sequences', err, error_msg)
                    return

                # Update the main list of connected pairs
                try:
                    sp.define_connected_sequences_list()
                except Exception as err:
                    error_msg = "An error occurred: cannot update the list of connected sequences"
                    error_occurred(sp.define_connected_sequences_list, 'define_connected_sequences_list', err, error_msg)
                    return

                # Update the connections-by-bins visual
                try:
                    self.network_plot.create_connections_by_bins()
                except Exception as err:
                    error_msg = "An error occurred: cannot update the connecting lines"
                    error_occurred(self.network_plot.create_connections_by_bins, 'create_connections_by_bins', err,
                                   error_msg)
                    return

                # If in subset mode, update the connections also for the subset
                if self.is_subset_mode:

                    subset_size = len(self.network_plot.selected_points)

                    try:
                        sp.define_connected_sequences_list_subset(subset_size)
                    except Exception as err:
                        error_msg = "An error occurred: cannot update the list of connected sequences in the subset"
                        error_occurred(sp.define_connected_sequences_list_subset,
                                       'define_connected_sequences_list_subset', err, error_msg)
                        return

                    try:
                        self.network_plot.create_connections_by_bins_subset()
                    except Exception as err:
                        error_msg = "An error occurred: cannot update the connecting lines of the subset"
                        error_occurred(self.network_plot.create_connections_by_bins_subset,
                                       'create_connections_by_bins_subset', err, error_msg)
                        return

                # Update the connections matrix in the fruchterman-reingold object
                try:
                    self.fr_object.update_connections()
                except Exception as err:
                    error_msg = "An error occurred: cannot update the connections for the FR calculation"
                    error_occurred(self.fr_object.update_connections, 'update_connections', err, error_msg)
                    return

                # Update the connections and singeltons (if needed) in the plot
                try:
                    self.network_plot.update_view(self.dim_num, self.color_by, self.group_by,
                                                  self.z_indexing_mode)
                except Exception as err:
                    error_msg = "An error occurred: cannot update the graph view to 2D"
                    error_occurred(self.network_plot.update_view, 'update_view', err, error_msg)

        # The user entered invalid characters
        else:
            self.error_label.setText("Invalid characters")
            self.pval_widget.setText("")
            self.pval_widget.setFocus()

    # Save a compatible clans file
    def save_clans_file(self):
        saved_file, _ = QFileDialog.getSaveFileName()

        if saved_file:
            if saved_file[-6:] != '.clans':
                saved_file += '.clans'

            file_object = clans_format.ClansFormat()

            try:
                file_object.write_file(saved_file, True, self.group_by)
            except Exception as err:
                error_msg = "An error occurred: cannot write the clans file."
                error_occurred(file_object.write_file, 'write_file', err, error_msg)
                return

            print("Session is successfully saved to " + saved_file + " in CLANS format")

    # Save a full clans file
    def save_full_clans_file(self):

        saved_file, _ = QFileDialog.getSaveFileName()

        if saved_file:
            if saved_file[-6:] != '.clans':
                saved_file += '.clans'

            file_object = clans_format.ClansFormat()

            try:
                file_object.write_full_file(saved_file)
            except Exception as err:
                error_msg = "An error occurred: cannot write the clans file."
                error_occurred(file_object.write_full_file, 'write_full_file', err, error_msg)
                return

            print("Session is successfully saved to " + saved_file + " in full-CLANS format")

    def save_delimited_file(self):

        saved_file, _ = QFileDialog.getSaveFileName()

        if saved_file:
            file_object = tab_format.DelimitedFormat()

            try:
                file_object.write_file(saved_file)
            except Exception as err:
                error_msg = "An error occurred: cannot write the tab-delimited file."
                error_occurred(file_object.write_file, 'write_file', err, error_msg)
                return

            print("Session is successfully saved to " + saved_file + " in tab-delimited format")

    def save_image(self):

        try:
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

        except Exception as err:
            error_msg = "An error occurred: cannot save the session as an image."
            error_occurred(self.save_image, 'save_image', err, error_msg)

    def save_image_connections_backwards(self):

        # Move view to 2D in order to display the connections at the back
        self.dim_num = 2
        self.change_dimensions_view()
        self.z_index_mode_combo.setCurrentIndex(1)

        self.save_image()

        # Move view back to 3D
        self.dim_num = 3
        self.change_dimensions_view()
        #self.z_index_mode_combo.setCurrentIndex(0)

    def create_stereo_image(self):

        self.stereo_window.open_window()

    def conf_FR_layout(self):

        try:
            conf_dlg = cd.FruchtermanReingoldConfig()

            if conf_dlg.exec_():
                cfg.run_params['att_val'], cfg.run_params['att_exp'], cfg.run_params['rep_val'], \
                cfg.run_params['rep_exp'], cfg.run_params['gravity'], cfg.run_params['dampening'], \
                cfg.run_params['maxmove'], cfg.run_params['cooling'] = conf_dlg.get_parameters()

        except Exception as err:
            error_msg = "An error occurred: cannot update the Fruchterman-Reingold layout parameters."
            error_occurred(self.conf_FR_layout, 'conf_FR_layout', err, error_msg)

    def conf_nodes(self):

        try:

            conf_nodes_dlg = cd.NodesConfig()

            if conf_nodes_dlg.exec_():
                size, color, outline_color, outline_width = conf_nodes_dlg.get_parameters()

                cfg.run_params['nodes_size'] = size
                cfg.run_params['nodes_color'] = color
                cfg.run_params['nodes_outline_color'] = outline_color
                cfg.run_params['nodes_outline_width'] = outline_width

                # Update also the parameters of the 'Manual definition' grouping-category
                cfg.groups_by_categories[0]['nodes_size'] = size
                cfg.groups_by_categories[0]['nodes_color'] = color
                cfg.groups_by_categories[0]['nodes_outline_color'] = outline_color
                cfg.groups_by_categories[0]['nodes_outline_width'] = outline_width

                # Update the other grouping categories (if any) with all parameters except nodes color
                for category_index in range(1, len(cfg.groups_by_categories)):
                    cfg.groups_by_categories[category_index]['nodes_size'] = size
                    cfg.groups_by_categories[category_index]['nodes_outline_color'] = outline_color
                    cfg.groups_by_categories[category_index]['nodes_outline_width'] = outline_width

                    # Update also the groups definitions of nodes-size and outline nodes color
                    for group_ID in cfg.groups_by_categories[category_index]['groups']:
                        cfg.groups_by_categories[category_index]['groups'][group_ID]['size'] = size
                        cfg.groups_by_categories[category_index]['groups'][group_ID]['outline_color'] = outline_color

                try:
                    self.network_plot.set_defaults(self.dim_num, self.color_by, self.group_by, self.z_indexing_mode)
                except Exception as err:
                    error_msg = "An error occurred: cannot update the default nodes parameters."
                    error_occurred(self.network_plot.set_defaults, 'set_defaults', err, error_msg)
                    return

        except Exception as err:
            error_msg = "An error occurred: cannot update the nodes parameters."
            error_occurred(self.conf_nodes, 'conf_nodes', err, error_msg)

    def conf_edges(self):

        try:
            conf_edges_dlg = cd.EdgesConfig()

            if conf_edges_dlg.exec_():
                cfg.run_params['is_uniform_edges_color'], cfg.run_params['edges_color'], \
                cfg.run_params['edges_color_scale'], cfg.run_params['is_uniform_edges_width'], \
                cfg.run_params['edges_width'], cfg.run_params['edges_width_scale'] = conf_edges_dlg.get_parameters()

                try:
                    self.network_plot.update_view(self.dim_num, self.color_by, self.group_by, self.z_indexing_mode)
                except Exception as err:
                    error_msg = "An error occurred: cannot update the default nodes parameters."
                    error_occurred(self.network_plot.set_defaults, 'set_defaults', err, error_msg)
                    return

        except Exception as err:
            error_msg = "An error occurred: cannot update the edges parameters."
            error_occurred(self.conf_edges, 'conf_edges', err, error_msg)

    def change_dimensions_view(self):

        # Update the window title
        self.setWindowTitle("CLANS " + str(self.dim_num) + "D-View of " + self.file_name)

        # 3D view
        if self.dim_num == 3:
            self.z_index_mode_combo.setEnabled(False)
            self.z_index_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")

            # Not in init file mode
            if self.is_init == 0:
                try:
                    self.network_plot.set_3d_view(self.fr_object, self.color_by, self.group_by, self.z_indexing_mode)
                except Exception as err:
                    error_msg = "An error occurred: cannot set the graph to 3D view."
                    error_occurred(self.network_plot.set_3d_view, 'set_3d_view', err, error_msg)

        # 2D view
        else:
            # Only in full data and color-by groups modes
            if self.is_subset_mode == 0 and len(cfg.groups_by_categories[self.group_by]['groups']) > 0 \
                    and self.color_by == 'groups':
                self.z_index_mode_combo.setEnabled(True)
                self.z_index_mode_label.setStyleSheet("color: black;")

            # Not in init file mode
            if self.is_init == 0:
                try:
                    self.network_plot.set_2d_view(self.z_indexing_mode, self.fr_object, self.color_by, self.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot set the graph to 2D view."
                    error_occurred(self.network_plot.set_2d_view, 'set_2d_view', err, error_msg)

    def change_dimensions_num_for_clustering(self):

        # 3D clustering
        if self.dimensions_clustering_combo.currentIndex() == 0:
            cfg.run_params['dimensions_num_for_clustering'] = 3

            if self.is_show_connections:
                self.save_image_connections_backwards_action.setEnabled(True)

            # Update the coordinates in the Fruchterman-Reingold object
            # Full data mode
            if self.is_subset_mode == 0:
                self.save_stereo_image_action.setEnabled(True)

                try:
                    self.fr_object.init_coordinates(cfg.sequences_array['x_coor'],
                                                    cfg.sequences_array['y_coor'],
                                                    cfg.sequences_array['z_coor'])
                except Exception as err:
                    error_msg = "An error occurred: cannot change the clustering to 3D"
                    error_occurred(self.fr_object.init_coordinates, 'init_coordinates', err, error_msg)

            # Subset mode
            else:
                try:
                    self.fr_object.init_coordinates(cfg.sequences_array['x_coor_subset'],
                                                    cfg.sequences_array['y_coor_subset'],
                                                    cfg.sequences_array['z_coor_subset'])
                except Exception as err:
                    error_msg = "An error occurred: cannot change the clustering to 3D"
                    error_occurred(self.fr_object.init_coordinates, 'init_coordinates', err, error_msg)

        # 2D clustering
        else:
            cfg.run_params['dimensions_num_for_clustering'] = 2

            self.save_image_connections_backwards_action.setEnabled(False)
            self.save_stereo_image_action.setEnabled(False)

        # Update the effective dim_num parameter if found in interactive mode
        if self.mode == 'interactive':
            self.dim_num = cfg.run_params['dimensions_num_for_clustering']

        # Update the graph view according to the dimensions
        self.change_dimensions_view()

    def manage_z_indexing(self):

        # Automatic Z-indexing
        if self.z_index_mode_combo.currentIndex() == 0:
            self.z_indexing_mode = 'auto'

        # Z-indexing by groups order
        else:
            self.z_indexing_mode = 'groups'

        if self.z_index_mode_combo.isEnabled():
            try:
                self.network_plot.update_2d_view(self.z_indexing_mode, self.color_by, self.group_by)
            except Exception as err:
                error_msg = "An error occurred: cannot update the view"
                error_occurred(self.network_plot.update_2d_view, 'update_2d_view', err, error_msg)

    def change_mode(self):

        # Interactive mode (rotate/pan)
        if self.mode_combo.currentIndex() == 0:
            self.mode = "interactive"

            self.dim_num = cfg.run_params['dimensions_num_for_clustering']

            if cfg.run_params['is_debug_mode']:
                print("Interactive mode")

            # Not in init file mode
            if self.is_init == 0:
                try:
                    self.network_plot.set_interactive_mode(self.dim_num, self.fr_object,
                                                           self.color_by, self.group_by, self.z_indexing_mode)
                except Exception as err:
                    error_msg = "An error occurred: cannot change the mode to \'Rotate/Pan graph\'"
                    error_occurred(self.network_plot.set_interactive_mode, 'set_interactive_mode', err, error_msg)
                    return

            self.init_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.dimensions_clustering_combo.setEnabled(True)
            self.pval_widget.setEnabled(True)
            self.pval_label.setStyleSheet("color: black;")
            self.selection_type_combo.setEnabled(False)
            self.selection_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")

            if self.dim_num == 3:
                self.z_index_mode_combo.setEnabled(False)
                self.z_index_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")

                if self.is_show_connections:
                    self.save_image_connections_backwards_action.setEnabled(True)

                if self.is_subset_mode == 0:
                    self.save_stereo_image_action.setEnabled(True)

            else:
                self.save_image_connections_backwards_action.setEnabled(False)
                self.save_stereo_image_action.setEnabled(False)

            # Disconnect the selection-special special mouse-events and connect back the default behaviour of the
            # viewbox when the mouse moves
            try:
                self.canvas.events.mouse_release.disconnect(self.on_canvas_mouse_release)
                self.view.camera._viewbox.events.mouse_move.connect(self.view.camera.viewbox_mouse_event)
                self.view.camera._viewbox.events.mouse_press.connect(self.view.camera.viewbox_mouse_event)
            except Exception as err:
                error_msg = "An error occurred: cannot set the mouse default behaviour"
                error_occurred(self.change_mode, 'change_mode', err, error_msg)

        # Selection / Text modes
        else:
            self.dim_num = 2

            self.save_image_connections_backwards_action.setEnabled(False)
            self.save_stereo_image_action.setEnabled(False)

            # Selection mode
            if self.mode_combo.currentIndex() == 1:
                self.mode = "selection"

                self.selection_mode_label.setStyleSheet("color: black;")

                if len(cfg.groups_by_categories[self.group_by]['groups']) > 0:
                    self.selection_type_combo.setEnabled(True)

                if cfg.run_params['is_debug_mode']:
                    print("Selection mode")

            # Move visuals mode
            elif self.mode_combo.currentIndex() == 2:
                self.mode = "text"

                self.selection_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")

                self.selection_type_combo.setEnabled(False)

                if cfg.run_params['is_debug_mode']:
                    print("Move/Edit text mode")

            try:
                self.network_plot.set_selection_mode(self.z_indexing_mode, self.color_by, self.group_by)
            except Exception as err:
                error_msg = "An error occurred: cannot set the selection mode"
                error_occurred(self.network_plot.set_selection_mode, 'set_selection_mode', err, error_msg)
                return

            if len(cfg.groups_by_categories[self.group_by]['groups']) > 0 and self.color_by == 'groups':
                self.z_index_mode_combo.setEnabled(True)
                self.z_index_mode_label.setStyleSheet("color: black;")

            # Disconnect the default behaviour of the viewbox when the mouse moves
            # and connect special callbacks for mouse_move and mouse_release
            try:
                self.view.camera._viewbox.events.mouse_move.disconnect(self.view.camera.viewbox_mouse_event)
                self.view.camera._viewbox.events.mouse_press.disconnect(self.view.camera.viewbox_mouse_event)
                self.canvas.events.mouse_release.connect(self.on_canvas_mouse_release)
            except Exception as err:
                error_msg = "An error occurred: cannot set the mouse moves of the selection mode"
                error_occurred(self.change_mode, 'change_mode', err, error_msg)

    def color_by_groups(self):

        try:
            self.network_plot.color_by_groups(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
        except Exception as err:
            error_msg = "An error occurred: cannot color the graph by groups"
            error_occurred(self.network_plot.color_by_groups, 'color_by_groups', err, error_msg)

        try:
            self.colorbar_plot.hide_colorbar()
        except Exception as err:
            error_msg = "An error occurred: cannot hide the colorbar"
            error_occurred(self.colorbar_plot.hide_colorbar, 'hide_colorbar', err, error_msg)

    def color_by_seq_length(self):

        # First time per data-det
        if self.done_color_by_length == 0:
            self.done_color_by_length = 1
            self.color_by_combo.addItem('Seq. length')
            self.color_by_combo.setCurrentText('Seq. length')
            self.color_by_combo.setEnabled(True)
            self.manage_params_action.setEnabled(True)

        # Produce the real colormap
        try:
            gradient_colormap = colors.generate_colormap_gradient_2_colors(cfg.short_color, cfg.long_color)
        except Exception as err:
            error_msg = "An error occurred: cannot generate colormap"
            error_occurred(colors.generate_colormap_gradient_2_colors, 'generate_colormap_gradient_2_colors', err,
                           error_msg)
            return

        # Produce an opposite colormap just for the colorbar presentation (workaround a bug in the colorbar visual)
        try:
            opposite_gradient_colormap = colors.generate_colormap_gradient_2_colors(cfg.long_color, cfg.short_color)
        except Exception as err:
            error_msg = "An error occurred: cannot generate colormap"
            error_occurred(colors.generate_colormap_gradient_2_colors, 'generate_colormap_gradient_2_colors', err,
                           error_msg)
            return

        try:
            seq.normalize_seq_length()
        except Exception as err:
            error_msg = "An error occurred: cannot normalize the new range of sequence length"
            error_occurred(seq.normalize_seq_length, 'normalize_seq_length', err, error_msg)
            return

        try:
            self.network_plot.color_by_param(gradient_colormap, cfg.sequences_array['norm_seq_length'],
                                             self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
        except Exception as err:
            error_msg = "An error occurred: cannot color the data by sequence-length"
            error_occurred(self.network_plot.color_by_param, 'color_by_param', err, error_msg)
            return

        try:
            self.colorbar_plot.show_colorbar(opposite_gradient_colormap, 'Sequences length',
                                             cfg.run_params['min_seq_length'], cfg.run_params['max_seq_length'])
        except Exception as err:
            error_msg = "An error occurred: cannot display the colorbar"
            error_occurred(self.colorbar_plot.show_colorbar, 'show_colorbar', err, error_msg)

    def open_color_by_length_dialog(self):

        try:
            dlg = md.ColorByLengthDialog()

            if dlg.exec_():
                cfg.short_color, cfg.long_color, cfg.run_params['min_seq_length'], cfg.run_params['max_seq_length'] = \
                    dlg.get_colors()

                self.color_by_seq_length()

        except Exception as err:
            error_msg = "An error occurred: cannot color the data by sequence-length"
            error_occurred(self.open_color_by_length_dialog, 'open_color_by_length_dialog', err, error_msg)

    def change_coloring(self):

        # Color the data by groups (if none - color all in black)
        if self.color_by_combo.currentIndex() == 0:
            self.color_by = "groups"

            if self.is_init == 0:

                # Enable all the group-related controls (if there are groups)
                if len(cfg.groups_by_categories[self.group_by]['groups']) > 0:
                    self.edit_groups_button.setEnabled(True)
                    self.show_group_names_button.setEnabled(True)

                    if self.mode_combo.currentIndex() == 1:
                        self.selection_type_combo.setEnabled(True)

                # Enable add + remove from group if there is at least one selected point
                if len(self.network_plot.selected_points) > 0:
                    self.add_to_group_button.setEnabled(True)
                    self.remove_selected_button.setEnabled(True)

                if self.dim_num == 2 and len(cfg.groups_by_categories[self.group_by]['groups']) > 0:
                    self.z_index_mode_combo.setEnabled(True)
                    self.z_index_mode_label.setStyleSheet("color: black;")

                # Enable the 'group-by' combo box if is more than one grouping option
                if self.group_by_combo.count() > 1:
                    self.group_by_combo.setEnabled(True)
                    self.manage_categories_action.setEnabled(True)

                self.color_by_groups()

        # Color the data by some numeric parameter
        elif self.color_by_combo.currentIndex() > 0:
            self.color_by = "param"

            # Disable all the group-related controls and hide the group names
            self.edit_groups_button.setEnabled(False)
            self.add_to_group_button.setEnabled(False)
            self.remove_selected_button.setEnabled(False)
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
                self.z_index_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")

    def color_by_user_param(self, param):

        min_param_color = cfg.sequences_numeric_params[param]['min_color']
        max_param_color = cfg.sequences_numeric_params[param]['max_color']

        # Produce the real colormap
        try:
            gradient_colormap = colors.generate_colormap_gradient_2_colors(min_param_color, max_param_color)
        except Exception as err:
            error_msg = "An error occurred: cannot generate colormap"
            error_occurred(colors.generate_colormap_gradient_2_colors, 'generate_colormap_gradient_2_colors', err,
                           error_msg)
            return

        # Produce an opposite colormap just for the colorbar presentation (workaround a bug in the colorbar visual)
        try:
            opposite_gradient_colormap = colors.generate_colormap_gradient_2_colors(max_param_color, min_param_color)
        except Exception as err:
            error_msg = "An error occurred: cannot generate colormap"
            error_occurred(colors.generate_colormap_gradient_2_colors, 'generate_colormap_gradient_2_colors', err,
                           error_msg)
            return

        try:
            seq.normalize_numeric_param(param)
        except Exception as err:
            error_msg = "An error occurred: cannot normalize the new range of values"
            error_occurred(seq.normalize_numeric_param, 'normalize_numeric_param', err, error_msg)
            return

        try:
            self.network_plot.color_by_param(gradient_colormap, cfg.sequences_numeric_params[param]['norm'],
                                             self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
        except Exception as err:
            error_msg = "An error occurred: cannot color the data by the custom parameter"
            error_occurred(self.network_plot.color_by_param, 'color_by_param', err, error_msg)
            return

        try:
            self.colorbar_plot.show_colorbar(opposite_gradient_colormap, param, cfg.sequences_numeric_params[param]['min_val'],
                                             cfg.sequences_numeric_params[param]['max_val'])
        except Exception as err:
            error_msg = "An error occurred: cannot display the colorbar"
            error_occurred(self.colorbar_plot.show_colorbar, 'show_colorbar', err, error_msg)

    def open_color_by_param_dialog(self):

        try:
            dlg = md.ColorByParamDialog()

            if dlg.exec_():
                selected_param, added_params_list, min_param_color, max_param_color, min_val, max_val = dlg.get_param()

                if selected_param:

                    # At least one new parameter was added
                    if len(added_params_list) > 0:

                        for param_name in added_params_list:
                            self.color_by_combo.addItem(param_name)

                    self.color_by_combo.setCurrentText(selected_param)
                    self.color_by_combo.setEnabled(True)
                    self.manage_params_action.setEnabled(True)

                    # Update the colors of the selected parameter
                    cfg.sequences_numeric_params[selected_param]['min_color'] = min_param_color
                    cfg.sequences_numeric_params[selected_param]['max_color'] = max_param_color

                    # Update the values range of the selected parameter
                    cfg.sequences_numeric_params[selected_param]['min_val'] = min_val
                    cfg.sequences_numeric_params[selected_param]['max_val'] = max_val

                    self.color_by_user_param(selected_param)

        except Exception as err:
            error_msg = "An error occurred: cannot color the data by custom parameter"
            error_occurred(self.open_color_by_param_dialog, 'open_color_by_param_dialog', err, error_msg)

    def change_grouping(self):

        self.group_by = self.group_by_combo.currentIndex()

        if not self.is_init:

            if self.dim_num == 2:
                if not self.is_subset_mode and len(cfg.groups_by_categories[self.group_by]['groups']) > 0:
                    self.z_index_mode_combo.setEnabled(True)
                    self.z_index_mode_label.setStyleSheet("color: black;")
                else:
                    self.z_index_mode_combo.setEnabled(False)
                    self.z_index_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")

                if self.z_indexing_mode == 'groups':
                    try:
                        self.network_plot.hide_scatter_by_groups()
                    except Exception as err:
                        error_msg = "An error occurred: cannot remove scatter by groups"
                        error_occurred(self.network_plot.hide_scatter_by_groups, 'hide_scatter_by_groups', err, error_msg)

            try:
                self.network_plot.hide_group_names()
            except Exception as err:
                error_msg = "An error occurred: cannot hide the group names"
                error_occurred(self.network_plot.hide_group_names, 'hide_group_names', err, error_msg)

            # Clear the groups-selection
            if len(self.network_plot.selected_groups) > 0:
                self.network_plot.selected_groups_text_visual = {}
                self.network_plot.selected_groups = {}

            try:
                self.network_plot.update_group_by(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
            except Exception as err:
                error_msg = "An error occurred: cannot change grouping category"
                error_occurred(self.network_plot.update_group_by, 'update_group_by', err, error_msg)

            # Enable all groups-related controls (in case there are groups)
            if len(cfg.groups_by_categories[self.group_by]['groups']) > 0:
                self.edit_groups_button.setEnabled(True)
                self.show_group_names_button.setEnabled(True)

                if self.mode_combo.currentIndex() == 1:
                    self.selection_type_combo.setEnabled(True)

                # The group names are displayed -> update them including the new group
                if self.is_show_group_names:
                    self.show_groups_combo.setCurrentIndex(0)
                    self.show_groups_combo.setEnabled(False)

                    try:
                        self.network_plot.show_group_names('all')
                    except Exception as err:
                        error_msg = "An error occurred: cannot display the group names"
                        error_occurred(self.network_plot.show_group_names, 'show_group_names', err, error_msg)

            # If there are no group (in 'Manual definition' group-by, for example)
            else:
                self.edit_groups_button.setEnabled(False)
                self.show_group_names_button.setChecked(False)
                self.reset_group_names_button.setEnabled(False)
                self.is_show_group_names = 0
                self.show_group_names_button.setEnabled(False)
                self.selection_type_combo.setCurrentIndex(0)
                self.selection_type_combo.setEnabled(False)

    def change_selection_type(self):

        # Sequences selection
        if self.selection_type_combo.currentIndex() == 0:
            self.selection_type = "sequences"

        # Groups selection
        else:
            self.selection_type = "groups"

    def select_all(self):

        try:
            self.network_plot.select_all(self.selection_type, self.dim_num, self.z_indexing_mode, self.color_by,
                                         self.group_by, self.is_show_group_names, self.group_names_display)
        except Exception as err:
            error_msg = "An error occurred: cannot perform the selection"
            error_occurred(self.network_plot.select_all, 'select_all', err, error_msg)
            return

        # Update the selected sequences window
        try:
            self.selected_seq_window.update_sequences()
        except Exception as err:
            error_msg = "An error occurred: cannot update the selected sequences window"
            error_occurred(self.selected_seq_window.update_sequences, 'update_sequences', err, error_msg)
            return

        # Enable the selection-related buttons
        self.show_selected_names_button.setEnabled(True)
        self.open_selected_button.setEnabled(True)
        self.clear_selection_button.setEnabled(True)
        self.add_to_group_button.setEnabled(True)
        self.remove_selected_button.setEnabled(True)

        # Disable the 'Show selected only' option (make no sense if selecting all)
        self.data_mode_combo.setEnabled(False)

    def inverse_selection(self):

        try:
            self.network_plot.inverse_selection(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by,
                                                self.is_show_group_names, self.group_names_display)
        except Exception as err:
            error_msg = "An error occurred: cannot perform the selection"
            error_occurred(self.network_plot.inverse_selection, 'inverse_selection', err, error_msg)
            return

        # Update the selected sequences window
        try:
            self.selected_seq_window.update_sequences()
        except Exception as err:
            error_msg = "An error occurred: cannot update the selected sequences window"
            error_occurred(self.selected_seq_window.update_sequences, 'update_sequences', err, error_msg)
            return

        # Disable the show all/selected group names combo
        if self.is_show_group_names:
            self.show_groups_combo.setCurrentIndex(0)
            self.show_groups_combo.setEnabled(False)

    def clear_selection(self):

        try:
            self.network_plot.reset_selection(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by,
                                              self.is_show_group_names, self.group_names_display)
        except Exception as err:
            error_msg = "An error occurred: cannot clear the selection"
            error_occurred(self.network_plot.reset_selection, 'reset_selection', err, error_msg)
            return

        # Update the selected sequences window
        try:
            self.selected_seq_window.update_sequences()
        except Exception as err:
            error_msg = "An error occurred: cannot update the selected sequences window"
            error_occurred(self.selected_seq_window.update_sequences, 'update_sequences', err, error_msg)
            return

        # Hide the sequences names and release the button (if was checked)
        self.show_selected_names_button.setChecked(False)
        self.show_selected_names_button.setEnabled(False)
        self.open_selected_button.setEnabled(False)
        self.clear_selection_button.setEnabled(False)
        self.inverse_selection_button.setEnabled(False)
        self.data_mode_combo.setCurrentIndex(0)
        self.data_mode_combo.setEnabled(False)
        self.add_to_group_button.setEnabled(False)
        self.remove_selected_button.setEnabled(False)
        self.is_show_selected_names = 0

        try:
            self.network_plot.hide_sequences_names()
        except Exception as err:
            error_msg = "An error occurred: cannot hide the sequences names"
            error_occurred(self.network_plot.hide_sequences_names, 'hide_sequences_names', err, error_msg)

        # Disable the show all/selected group names combo
        if self.is_show_group_names:
            self.show_groups_combo.setCurrentIndex(0)
            self.show_groups_combo.setEnabled(False)

    def show_selected_names(self):
        if self.show_selected_names_button.isChecked():
            self.is_show_selected_names = 1

            # Display the names
            try:
                self.network_plot.show_sequences_names()
            except Exception as err:
                error_msg = "An error occurred: cannot display the sequences names"
                error_occurred(self.network_plot.show_sequences_names, 'show_sequences_names', err, error_msg)

        else:
            self.is_show_selected_names = 0

            try:
                self.network_plot.hide_sequences_names()
            except Exception as err:
                error_msg = "An error occurred: cannot hide the sequences names"
                error_occurred(self.network_plot.hide_sequences_names, 'hide_sequences_names', err, error_msg)

    def open_selected_window(self):

        try:
            self.selected_seq_window.update_sequences()

            if self.selected_seq_window.is_visible == 0:
                self.selected_seq_window.open_window()

        except Exception as err:
            error_msg = "An error occurred: cannot open the selected sequences window"
            error_occurred(self.open_selected_window, 'open_selected_window', err, error_msg)

    def select_by_text(self):
        try:
            self.search_window.open_window()

        except Exception as err:
            error_msg = "An error occurred: cannot open the 'Select by text' window"
            error_occurred(self.select_by_text, 'select_by_text', err, error_msg)

    def select_by_groups(self):
        try:
            self.select_by_groups_window.open_window()

        except Exception as err:
            error_msg = "An error occurred: cannot open the 'Select by groups' window"
            error_occurred(self.select_by_groups, 'select_by_groups', err, error_msg)

    def manage_subset_presentation(self):

        # Subset mode
        if self.data_mode_combo.currentIndex() == 1:
            self.is_subset_mode = 1

            print("Displaying selected subset")

            self.start_button.setText("Start clustering")
            self.round_num_label.setText("0")
            self.rounds_done_subset = 0

            # Disable all selection-related buttons
            self.mode_combo.setEnabled(False)
            self.mode_combo.setCurrentIndex(0)
            self.select_all_button.setEnabled(False)
            self.clear_selection_button.setEnabled(False)
            self.inverse_selection_button.setEnabled(False)
            self.z_index_mode_combo.setCurrentIndex(0)
            self.z_index_mode_combo.setEnabled(False)
            self.z_index_mode_label.setStyleSheet("color: " + cfg.inactive_color + ";")

            # Disable save as stereo
            self.save_stereo_image_action.setEnabled(False)

            try:
                self.network_plot.set_subset_view(self.dim_num, self.color_by, self.group_by,
                                                  self.z_indexing_mode)
            except Exception as err:
                error_msg = "An error occurred: cannot set the subset view"
                error_occurred(self.network_plot.set_subset_view, 'set_subset_view', err, error_msg)
                return

            if self.is_show_group_names:
                try:
                    self.network_plot.show_group_names('selected')
                except Exception as err:
                    error_msg = "An error occurred: cannot display the group names"
                    error_occurred(self.network_plot.show_group_names, 'show_group_names', err, error_msg)

        # Full data mode
        else:
            self.is_subset_mode = 0

            print("Back to full-data view")

            if self.rounds_done > 0:
                self.start_button.setText("Resume clustering")
            else:
                self.start_button.setText("Start clustering")
            self.round_num_label.setText(str(self.rounds_done))

            # Enable all selection-related buttons
            self.mode_combo.setEnabled(True)
            self.select_all_button.setEnabled(True)
            self.clear_selection_button.setEnabled(True)
            self.inverse_selection_button.setEnabled(True)
            self.select_by_text_button.setEnabled(True)
            self.select_by_groups_button.setEnabled(True)

            # Enable save as stereo
            if cfg.run_params['dimensions_num_for_clustering'] == 3:
                self.save_stereo_image_action.setEnabled(True)

            if self.dim_num == 2 and len(cfg.groups_by_categories[self.group_by]['groups']) > 0:
                self.z_index_mode_combo.setEnabled(True)
                self.z_index_mode_label.setStyleSheet("color: black;")

            # Update the coordinates in the fruchterman-reingold object
            try:
                self.fr_object.init_coordinates(cfg.sequences_array['x_coor'],
                                                cfg.sequences_array['y_coor'],
                                                cfg.sequences_array['z_coor'])
            except Exception as err:
                error_msg = "An error occurred: cannot initialize the coordinates"
                error_occurred(self.fr_object.init_coordinates, 'init_coordinates', err, error_msg)
                return

            try:
                self.network_plot.set_full_view(self.dim_num, self.color_by, self.group_by,
                                                self.z_indexing_mode)
            except Exception as err:
                error_msg = "An error occurred: cannot set the full-data view"
                error_occurred(self.network_plot.set_full_view, 'set_full_view', err, error_msg)
                return

            if self.is_show_group_names:
                try:
                    self.network_plot.show_group_names('all')
                except Exception as err:
                    error_msg = "An error occurred: cannot display the group names"
                    error_occurred(self.network_plot.show_group_names, 'show_group_names', err, error_msg)

    def change_group_names_display(self):

        # Show all the group names
        if self.show_groups_combo.currentIndex() == 0:
            self.group_names_display = 'all'

        # Show the selected group names only
        else:
            self.group_names_display = 'selected'

        try:
            self.network_plot.hide_group_names()
        except Exception as err:
            error_msg = "An error occurred: cannot hide the group names"
            error_occurred(self.network_plot.hide_group_names, 'hide_group_names', err, error_msg)

        try:
            self.network_plot.show_group_names(self.group_names_display)
        except Exception as err:
            error_msg = "An error occurred: cannot display the group names"
            error_occurred(self.network_plot.show_group_names, 'show_group_names', err, error_msg)

    def reset_group_names_positions(self):

        try:
            self.network_plot.reset_group_names_positions(self.group_by)
        except Exception as err:
            error_msg = "An error occurred: cannot initialize the group names positions"
            error_occurred(self.network_plot.reset_group_names_positions, 'reset_group_names_positions', err, error_msg)

    def manage_group_names(self):

        # The 'show group names' button is checked
        if self.show_group_names_button.isChecked():
            self.is_show_group_names = 1
            self.reset_group_names_button.setEnabled(True)

            if len(self.network_plot.selected_groups) > 0:
                self.show_groups_combo.setEnabled(True)
            else:
                self.show_groups_combo.setCurrentIndex(0)
                self.show_groups_combo.setEnabled(False)

            self.change_group_names_display()

        # The 'show group names' button is not checked
        else:
            self.is_show_group_names = 0
            self.show_groups_combo.setEnabled(False)
            self.reset_group_names_button.setEnabled(False)

            try:
                self.network_plot.hide_group_names()
            except Exception as err:
                error_msg = "An error occurred: cannot hide the group names"
                error_occurred(self.network_plot.hide_group_names, 'hide_group_names', err, error_msg)

    #def add_text(self):

        # Open the 'Enter new text element' dialog
        #dlg = td.NewTextDialog(self.network_plot)

        # The user has entered text
        #if dlg.exec_():
            ## Get all the text definitions entered by the user
            #text, size, color_array = dlg.get_text_info()

    def edit_params(self):

        try:
            dlg = md.EditParamsDialog(self, self.network_plot)

            if dlg.exec_():

                selected_feature = dlg.get_current_feature()
                deleted_features = dlg.get_deleted_features()

                self.color_by_combo.clear()

                self.color_by_combo.addItem("Groups/Default")

                index = 0
                current_index = 0

                # No selected feature -> all features were removed
                if selected_feature is None:
                    self.done_color_by_length = 0
                    self.color_by_combo.setCurrentIndex(0)
                    self.color_by_combo.setEnabled(False)
                    self.manage_params_action.setEnabled(False)

                # There is still at least one numeric feature
                else:
                    if self.done_color_by_length:

                        # Seq. length feature was deleted
                        if 'Seq. length' in deleted_features:
                            self.done_color_by_length = 0

                        # Add Seq. length to the list
                        else:
                            self.color_by_combo.addItem('Seq. length')
                            index = 1

                            if selected_feature == 'Seq. length':
                                current_index = 1

                    # Add the other numerical features
                    for feature in cfg.sequences_numeric_params:
                        self.color_by_combo.addItem(str(feature))
                        index += 1

                        # Find the selected feature's index
                        if str(feature) == selected_feature:
                            current_index = index

                    # Change the view to the edited feature
                    self.color_by_combo.setCurrentIndex(current_index)

        except Exception as err:
            error_msg = "An error occurred: cannot edit the numerical feature"
            error_occurred(self.edit_params, 'edit_params', err, error_msg)

    def edit_categories(self):

        try:
            dlg = gd.EditCategoriesDialog(self.network_plot, self.dim_num, self.z_indexing_mode, self.color_by,
                                          self.group_by)

            if dlg.exec_():

                selected_category_index = dlg.get_current_category()

                self.group_by_combo.clear()

                for category_index in range(len(cfg.groups_by_categories)):
                    self.group_by_combo.addItem(cfg.groups_by_categories[category_index]['name'])

                self.group_by_combo.setCurrentIndex(selected_category_index)

                # No categories left except from 'Manual definition'
                if len(cfg.groups_by_categories) == 1:
                    self.manage_categories_action.setEnabled(False)

        except Exception as err:
            error_msg = "An error occurred: cannot edit the grouping-categories"
            error_occurred(self.edit_categories, 'edit_categories', err, error_msg)

    def edit_groups(self):

        try:
            dlg = gd.ManageGroupsDialog(self.network_plot, self.view, self.dim_num, self.z_indexing_mode, self.color_by,
                                        self.group_by)

            if dlg.exec_():

                # The order of the groups has changed
                if dlg.changed_order_flag:

                    try:
                        self.network_plot.update_groups_order(self.dim_num, self.z_indexing_mode, self.color_by,
                                                              self.group_by)
                    except Exception as err:
                        error_msg = "An error occurred: cannot update the groups order"
                        error_occurred(self.network_plot.update_groups_order, 'update_groups_order', err, error_msg)

        except Exception as err:
            error_msg = "An error occurred: cannot edit the groups"
            error_occurred(self.edit_groups, 'edit_groups', err, error_msg)

    def open_add_to_group_dialog(self):

        try:
            dlg = gd.AddToGroupDialog(self.group_by)

            if dlg.exec_():
                choice, group_ID = dlg.get_choice()

                if choice == 'new':

                    print("Creating a new group")
                    self.create_group_from_selected()

                # The user chose to add the selected sequences to an existing group
                else:
                    print("Adding the sequences to group " + cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name'])
                    self.add_sequences_to_group(group_ID)

        except Exception as err:
            error_msg = "An error occurred: cannot add the sequences to group"
            error_occurred(self.open_add_to_group_dialog, 'open_add_to_group_dialog', err, error_msg)

    def add_sequences_to_group(self, group_ID):

        # Add the sequences to the main group_list array
        try:
            groups.add_to_group(self.group_by, self.network_plot.selected_points, group_ID)
        except Exception as err:
            error_msg = "An error occurred: cannot add the sequences to group"
            error_occurred(groups.add_to_group, 'add_to_group', err, error_msg)
            return

        # Update the look of the selected data-points according to the new group definitions
        try:
            self.network_plot.add_to_group(self.network_plot.selected_points, group_ID, self.dim_num,
                                           self.z_indexing_mode, self.color_by, self.group_by)
        except Exception as err:
            error_msg = "An error occurred: cannot add the sequences to group"
            error_occurred(self.network_plot.add_to_group, 'add_to_group', err, error_msg)

    def create_group_from_selected(self):

        # Open the 'Create group from selected' dialog
        dlg = gd.CreateGroupDialog(self.group_by)

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
            group_dict['order'] = len(cfg.groups_by_categories[self.group_by]['groups']) - 1
            group_dict['outline_color'] = outline_color

            try:
                group_ID = groups.add_group_with_sequences(self.group_by, self.network_plot.selected_points.copy(),
                                                           group_dict)
            except Exception as err:
                error_msg = "An error occurred: cannot add a group"
                error_occurred(groups.add_group_with_sequences, 'add_group_with_sequences', err, error_msg)
                return

            # Add the new group to the graph
            try:
                self.network_plot.add_group(self.group_by, group_ID)
            except Exception as err:
                error_msg = "An error occurred: cannot add a group"
                error_occurred(self.network_plot.add_group, 'add_group', err, error_msg)
                return

            # Update the look of the selected data-points according to the new group definitions
            if self.dim_num == 2 and len(cfg.groups_by_categories[self.group_by]['groups']) > 0:
                self.z_index_mode_combo.setEnabled(True)
                self.z_index_mode_label.setStyleSheet("color: black;")

            try:
                self.network_plot.add_to_group(self.network_plot.selected_points, group_ID, self.dim_num,
                                               self.z_indexing_mode, self.color_by, self.group_by)
            except Exception as err:
                error_msg = "An error occurred: cannot add sequences to the group"
                error_occurred(self.network_plot.add_to_group, 'add_to_group', err, error_msg)
                return

            self.edit_groups_button.setEnabled(True)
            self.show_group_names_button.setEnabled(True)
            self.select_by_groups_button.setEnabled(True)

            if self.mode_combo.currentIndex() == 1:
                self.selection_type_combo.setEnabled(True)

            # The group names are displayed -> update them including the new group
            if self.is_show_group_names:
                try:
                    self.network_plot.show_group_names('all')
                except Exception as err:
                    error_msg = "An error occurred: cannot display the group names"
                    error_occurred(self.network_plot.show_group_names, 'show_group_names', err, error_msg)

    def remove_selected_from_group(self):

        # Remove the selected sequences group-assignment in the main group_list array
        try:
            groups_with_deleted_members = groups.remove_from_group(self.group_by, self.network_plot.selected_points.copy())
        except Exception as err:
            error_msg = "An error occurred: cannot remove the sequences from the group"
            error_occurred(groups.remove_from_group, 'remove_from_group', err, error_msg)
            return

        # Update the look of the selected data-points to the default look (without group assignment)
        try:
            self.network_plot.remove_from_group(self.network_plot.selected_points, self.dim_num, self.z_indexing_mode,
                                                self.color_by, self.group_by)
        except Exception as err:
            error_msg = "An error occurred: cannot remove the sequences from the group"
            error_occurred(self.network_plot.remove_from_group, 'remove_from_group', err, error_msg)
            return

        # Check if there is an empty group among the groups with removed members
        for group_ID in groups_with_deleted_members:
            if len(cfg.groups_by_categories[self.group_by]['groups'][group_ID]['seqIDs']) == 0:

                # 1. Delete it from the group_names visual and other graph-related data-structures
                try:
                    self.network_plot.delete_empty_group(group_ID, self.dim_num, self.z_indexing_mode, self.color_by,
                                                         self.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot delete the empty group"
                    error_occurred(self.network_plot.delete_empty_group, 'delete_empty_group', err, error_msg)
                    return

                # 2. Delete the group
                try:
                    groups.delete_group(self.group_by, group_ID)
                except Exception as err:
                    error_msg = "An error occurred: cannot delete the group"
                    error_occurred(groups.delete_group, 'delete_group', err, error_msg)

        # Check if there are groups left. If not, disable the related groups controls
        if len(cfg.groups_by_categories[self.group_by]['groups']) == 0:
            self.show_group_names_button.setChecked(False)
            self.show_group_names_button.setEnabled(False)
            self.show_groups_combo.setEnabled(False)
            self.reset_group_names_button.setEnabled(False)
            self.selection_type_combo.setCurrentIndex(0)
            self.selection_type_combo.setEnabled(False)
            self.edit_groups_button.setEnabled(False)

        if len(cfg.groups_by_categories) == 1 and len(cfg.groups_by_categories[0]['groups']) == 0:
            self.select_by_groups_button.setEnabled(False)

    def group_by_taxonomy(self):

        # Open the 'Group by taxonomy' dialog
        dlg = md.GroupByTaxDialog()

        # Create and execute the taxonomy worker to get the organism names and their taxonomy hierarchy
        # (only the first time)
        if not cfg.run_params['finished_taxonomy_search']:
            taxonomy_worker = io.TaxonomyWorker()
            self.threadpool.start(taxonomy_worker)
            taxonomy_worker.signals.finished.connect(dlg.finished_tax_search)

        if dlg.exec_():
            tax_level, points_size, outline_color, outline_width, group_names_size, is_bold, is_italic = \
                dlg.get_tax_level()

            category_name = "Taxonomy - " + tax_level

            found_tax_level = 0
            for category_index in range(len(cfg.groups_by_categories)):
                if category_name == cfg.groups_by_categories[category_index]['name']:
                    found_tax_level = 1

            # First time for this taxonomic level
            if not found_tax_level:
                cfg.groups_by_categories.append(dict())
                self.group_by = len(cfg.groups_by_categories) - 1  # The current category index
                cfg.groups_by_categories[self.group_by]['name'] = category_name
                cfg.groups_by_categories[self.group_by]['nodes_size'] = points_size
                cfg.groups_by_categories[self.group_by]['text_size'] = group_names_size
                cfg.groups_by_categories[self.group_by]['nodes_outline_color'] = outline_color
                cfg.groups_by_categories[self.group_by]['nodes_outline_width'] = outline_width
                cfg.groups_by_categories[self.group_by]['is_bold'] = is_bold
                cfg.groups_by_categories[self.group_by]['is_italic'] = is_italic
                cfg.groups_by_categories[self.group_by]['groups'] = dict()
                cfg.groups_by_categories[self.group_by]['sequences'] = np.full(cfg.run_params['total_sequences_num'], -1)

                # Generate distinct colors according to the number of groups in the chosen level
                try:
                    color_map = colors.generate_distinct_colors(len(cfg.seq_by_tax_level_dict[tax_level]) - 1)
                except Exception as err:
                    error_msg = "An error occurred: cannot generate colormap"
                    error_occurred(colors.generate_distinct_colors, 'generate_distinct_colors', err, error_msg)

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
                    group_dict['outline_color'] = outline_color
                    group_dict['is_bold'] = is_bold
                    group_dict['is_italic'] = is_italic
                    group_dict['order'] = len(cfg.groups_by_categories[self.group_by]['groups']) - 1
                    seq_dict = cfg.seq_by_tax_level_dict[tax_level][tax_group].copy()

                    try:
                        group_ID = groups.add_group_with_sequences(self.group_by, seq_dict, group_dict)
                    except Exception as err:
                        error_msg = "An error occurred: cannot add group " + tax_group
                        error_occurred(groups.add_group_with_sequences, 'add_group_with_sequences', err, error_msg)
                        return

                # Add the new group-type to the group-by combo-box, enable it and update the grouping
                self.group_by_combo.addItem(category_name)

            self.group_by_combo.setCurrentText(category_name)
            self.group_by_combo.setEnabled(True)
            self.manage_categories_action.setEnabled(True)

    def add_groups_from_metadata(self):

        # Open the 'Add custom grouping category' dialog
        dlg = md.GroupByParamDialog()

        if dlg.exec_():
            groups_dict, points_size, outline_color, outline_width, group_names_size, is_bold, is_italic, is_error = \
                dlg.get_categories()

            if not is_error:

                for category in groups_dict:

                    cfg.groups_by_categories.append(dict())
                    category_index = len(cfg.groups_by_categories) - 1
                    cfg.groups_by_categories[category_index]['name'] = category
                    cfg.groups_by_categories[category_index]['nodes_size'] = points_size
                    cfg.groups_by_categories[category_index]['text_size'] = group_names_size
                    cfg.groups_by_categories[category_index]['nodes_outline_color'] = outline_color
                    cfg.groups_by_categories[category_index]['nodes_outline_width'] = outline_width
                    cfg.groups_by_categories[category_index]['is_bold'] = is_bold
                    cfg.groups_by_categories[category_index]['is_italic'] = is_italic
                    cfg.groups_by_categories[category_index]['groups'] = dict()
                    cfg.groups_by_categories[category_index]['sequences'] = \
                        np.full(cfg.run_params['total_sequences_num'], -1)

                    # Generate distinct colors according to the number of groups in the chosen level
                    if "Not assigned" in groups_dict[category]:
                        colors_num = len(groups_dict[category]) - 1
                    else:
                        colors_num = len(groups_dict[category])

                    try:
                        color_map = colors.generate_distinct_colors(colors_num)
                    except Exception as err:
                        error_msg = "An error occurred: cannot generate colormap"
                        error_occurred(colors.generate_distinct_colors, 'generate_distinct_colors', err, error_msg)

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
                        group_dict['outline_color'] = outline_color
                        group_dict['is_bold'] = is_bold
                        group_dict['is_italic'] = is_italic
                        group_dict['order'] = len(cfg.groups_by_categories[category_index]['groups']) - 1
                        seq_dict = groups_dict[category][group].copy()

                        try:
                            group_ID = groups.add_group_with_sequences(category_index, seq_dict, group_dict)
                        except Exception as err:
                            error_msg = "An error occurred: cannot add group " + group_dict['name']
                            error_occurred(groups.add_group_with_sequences, 'add_group_with_sequences', err, error_msg)
                            return

                    # Add the new group-type to the group-by combo-box, enable it and update the grouping
                    self.group_by_combo.addItem(category)
                    self.group_by_combo.setCurrentText(category)
                    self.group_by_combo.setEnabled(True)
                    self.manage_categories_action.setEnabled(True)

                #self.group_by = category_index
                # If the coloring is by groups - move to the newly added category
                if self.color_by == 'groups':
                    self.change_grouping()

                # If the coloring was by parameter - move to coloring by groups and present the new category
                else:
                    self.group_by = category_index
                    self.color_by_combo.setCurrentIndex(0)

    def add_empty_category(self):

        # Append a new empty category to the main categories list
        cfg.groups_by_categories.append(dict())
        category_index = len(cfg.groups_by_categories) - 1
        cfg.groups_by_categories[category_index]['name'] = "Category_" + str(category_index)
        cfg.groups_by_categories[category_index]['nodes_size'] = cfg.run_params['nodes_size']
        cfg.groups_by_categories[category_index]['text_size'] = cfg.run_params['text_size']
        cfg.groups_by_categories[category_index]['nodes_outline_color'] = cfg.run_params['nodes_outline_color']
        cfg.groups_by_categories[category_index]['nodes_outline_width'] = cfg.run_params['nodes_outline_width']
        cfg.groups_by_categories[category_index]['is_bold'] = True
        cfg.groups_by_categories[category_index]['is_italic'] = False
        cfg.groups_by_categories[category_index]['groups'] = dict()
        cfg.groups_by_categories[category_index]['sequences'] = np.full(cfg.run_params['total_sequences_num'], -1)

        # Open the Edit Category dialog to let the user configure the new category
        try:
            edit_category_dlg = gd.EditCategoryDialog(category_index)
        except Exception as err:
            error_msg = "An error occurred: cannot create EditCategoryDialog object"
            error_occurred(self.add_empty_category, 'add_empty_category', err, error_msg)
            return

        if edit_category_dlg.exec_():

            try:
                category_name, points_size, outline_color, outline_width, names_size, is_bold, is_italic = \
                    edit_category_dlg.get_info()
            except Exception as err:
                error_msg = "An error occurred: cannot get category parameters"
                error_occurred(edit_category_dlg.get_info, 'get_info', err, error_msg)
                return

            if category_name != "":
                # Update the category name in the main list
                cfg.groups_by_categories[category_index]['name'] = category_name

            is_changed_points_size = 0
            is_changed_names_size = 0
            is_changed_outline_color = 0
            is_changed_bold = 0
            is_changed_italic = 0

            if points_size != cfg.groups_by_categories[category_index]['nodes_size']:
                is_changed_points_size = 1
            cfg.groups_by_categories[category_index]['nodes_size'] = points_size

            if names_size != cfg.groups_by_categories[category_index]['text_size']:
                is_changed_names_size = 1
            cfg.groups_by_categories[category_index]['text_size'] = names_size

            if ColorArray(outline_color).hex != \
                    ColorArray(cfg.groups_by_categories[category_index]['nodes_outline_color']).hex:
                is_changed_outline_color = 1
            cfg.groups_by_categories[category_index]['nodes_outline_color'] = outline_color

            if is_bold != cfg.groups_by_categories[category_index]['is_bold']:
                is_changed_bold = 1
            cfg.groups_by_categories[category_index]['is_bold'] = is_bold

            if is_italic != cfg.groups_by_categories[category_index]['is_italic']:
                is_changed_italic = 1
            cfg.groups_by_categories[category_index]['is_italic'] = is_italic

            cfg.groups_by_categories[category_index]['nodes_outline_width'] = outline_width

            # Add the new category to the group-by combo-box, enable it and update the grouping
            self.group_by_combo.addItem(cfg.groups_by_categories[category_index]['name'])
            self.group_by_combo.setCurrentText(cfg.groups_by_categories[category_index]['name'])
            self.group_by_combo.setEnabled(True)
            self.manage_categories_action.setEnabled(True)

            self.group_by = category_index

    def open_about_window(self):
        try:
            self.about_window.open_window()

        except Exception as err:
            error_msg = "An error occurred: cannot open the 'About CLANS' window"
            error_occurred(self.open_about_window, 'open_about_window', err, error_msg)

    def open_manual(self):
        try:
            manual_path = os.path.abspath(cfg.manual_path)
            url = QUrl.fromLocalFile(manual_path)

            if not QDesktopServices.openUrl(url):
                warn_message = "Cannot open " + manual_path
                QMessageBox.warning(self, 'Open Url', warn_message)

        except Exception as err:
            error_msg = "An error occurred: cannot open the manual"
            error_occurred(self.open_manual, 'open_manual', err, error_msg)

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

                try:
                    self.network_plot.find_selected_point(self.selection_type, event.pos, self.z_indexing_mode,
                                                          self.color_by, self.group_by, self.is_show_group_names,
                                                          self.group_names_display)
                except Exception as err:
                    error_msg = "An error occurred: cannot select point"
                    error_occurred(self.network_plot.find_selected_point, 'find_selected_point', err, error_msg)
                    return

            # Drag event
            elif self.is_selection_drag_event:

                self.is_selection_drag_event = 0

                try:
                    self.network_plot.remove_dragging_rectangle()
                except Exception as err:
                    error_msg = "An error occurred"
                    error_occurred(self.network_plot.remove_dragging_rectangle, 'remove_dragging_rectangle', err, error_msg)

                try:
                    self.network_plot.find_selected_area(self.selection_type, pos_array[0], event.pos, self.z_indexing_mode,
                                                         self.color_by, self.group_by, self.is_show_group_names,
                                                         self.group_names_display)
                except Exception as err:
                    error_msg = "An error occurred: cannot select area"
                    error_occurred(self.network_plot.find_selected_area, 'find_selected_area', err, error_msg)
                    return

            # If at least one point is selected -> enable all buttons related to actions on selected points
            if self.network_plot.selected_points != {}:
                self.show_selected_names_button.setEnabled(True)
                self.open_selected_button.setEnabled(True)
                self.clear_selection_button.setEnabled(True)
                self.inverse_selection_button.setEnabled(True)
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
            try:
                self.selected_seq_window.update_sequences()
            except Exception as err:
                error_msg = "An error occurred: cannot update the selected sequences window"
                error_occurred(self.selected_seq_window.update_sequences, 'update_sequences', err, error_msg)

        # The event is done in the 'Move visuals' mode
        elif self.mode == 'text':

            # Finish the move of a group name
            try:
                self.network_plot.finish_group_name_move()
            except Exception as err:
                error_msg = "An error occurred: cannot move the group name"
                error_occurred(self.network_plot.finish_group_name_move, 'finish_group_name_move', err, error_msg)

            self.visual_to_move = None

    def canvas_mouse_drag(self, event):

        pos_array = event.trail()

        if self.mode == "selection":

            # CTRL key is pressed - move the selected data points
            if self.ctrl_key_pressed:
                if len(pos_array) >= 2:

                    # Update points location if the mouse position was changed above a certain distance
                    distance = np.linalg.norm(pos_array[-1] - pos_array[-2])
                    if distance >= 1:
                        try:
                            self.network_plot.move_selected_points(self.dim_num, pos_array[-2],
                                                                   pos_array[-1], self.z_indexing_mode, self.color_by,
                                                                   self.group_by)
                        except Exception as err:
                            error_msg = "An error occurred: cannot move the selected points"
                            error_occurred(self.network_plot.move_selected_points, 'move_selected_points', err, error_msg)

            # Regular dragging event for selection
            else:
                self.is_selection_drag_event = 1

                # Initiation of dragging -> create a rectangle visual
                if len(pos_array) == 3:
                    try:
                        self.network_plot.start_dragging_rectangle(pos_array[0])
                    except Exception as err:
                        error_msg = "An error occurred: cannot start drag event"
                        error_occurred(self.network_plot.start_dragging_rectangle, 'start_dragging_rectangle', err,
                                       error_msg)

                # Mouse dragging continues -> update the rectangle
                elif len(pos_array) > 3:
                    # Update the rectangle if the mouse position was actually changed
                    if pos_array[-1][0] != pos_array[-2][0] and pos_array[-1][1] != pos_array[-2][1]:
                        try:
                            self.network_plot.update_dragging_rectangle(pos_array[0], pos_array[-1])
                        except Exception as err:
                            error_msg = "An error occurred: cannot mark drag event"
                            error_occurred(self.network_plot.update_dragging_rectangle, 'update_dragging_rectangle', err,
                                           error_msg)

        # Interactive mode
        elif self.mode == "interactive":

            # CTRL key is pressed - move the selected data points
            if self.ctrl_key_pressed and len(pos_array) >= 2:

                # Update points location if the mouse position was changed above a certain distance
                distance = np.linalg.norm(pos_array[-1] - pos_array[-2])
                if distance >= 1:
                    try:
                        self.network_plot.move_selected_points(self.dim_num, pos_array[-2],
                                                               pos_array[-1], self.z_indexing_mode, self.color_by,
                                                               self.group_by)
                    except Exception as err:
                        error_msg = "An error occurred: cannot move the selected points"
                        error_occurred(self.network_plot.move_selected_points, 'move_selected_points', err, error_msg)

        # Move visuals mode
        else:

            # Initiation of dragging -> find the visual to move
            if len(pos_array) == 3:
                try:
                    self.visual_to_move = self.network_plot.find_visual(self.canvas, pos_array[0])
                except Exception as err:
                    error_msg = "An error occurred: cannot find a visual to move"
                    error_occurred(self.network_plot.find_visual, 'find_visual', err, error_msg)
                    return

                # The visual to move is a group name
                if self.visual_to_move == "text":
                    try:
                        self.network_plot.find_group_name_to_move(pos_array[0], self.group_by, self.group_names_display)
                    except Exception as err:
                        error_msg = "An error occurred: cannot find a group name to move"
                        error_occurred(self.network_plot.find_group_name_to_move, 'find_group_name_to_move', err,
                                       error_msg)

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
                        try:
                            self.network_plot.move_group_name(pos_array[-1], self.group_names_display)
                        except Exception as err:
                            error_msg = "An error occurred: cannot move group name"
                            error_occurred(self.network_plot.move_group_name, 'move_group_name', err, error_msg)

                    ## Disabled currently
                    # Move data-point(s)
                    #elif self.visual_to_move == "data":
                        #self.network_plot.move_points(pos_array[-2], pos_array[-1], self.z_indexing_mode,
                                                    # self.color_by, self.group_by)

    def canvas_mouse_double_click(self, event):

        pos_array = event.pos
        #print(pos_array)
        #print(pos_array[0])

        if self.mode == 'text':
            try:
                visual_to_edit = self.network_plot.find_visual(self.canvas, pos_array)
            except Exception as err:
                error_msg = "An error occurred: cannot find a visual to move"
                error_occurred(self.network_plot.find_visual, 'find_visual', err, error_msg)
                return

            # The visual to move is a group name
            if visual_to_edit == "text":
                try:
                    group_ID = self.network_plot.find_group_name_to_edit(pos_array, self.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot find group name to edit"
                    error_occurred(self.network_plot.find_group_name_to_edit, 'find_group_name_to_edit', err, error_msg)
                    return

                edit_group_name_dlg = gd.EditGroupNameDialog(self.group_by, group_ID)

                if edit_group_name_dlg.exec_():
                    group_name, group_name_size, clans_color, color_array, is_bold, is_italic = \
                        edit_group_name_dlg.get_group_info()

                    # Update the group information in the main dict
                    cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name'] = group_name
                    cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name_size'] = group_name_size
                    cfg.groups_by_categories[self.group_by]['groups'][group_ID]['color'] = clans_color
                    cfg.groups_by_categories[self.group_by]['groups'][group_ID]['color_array'] = color_array
                    cfg.groups_by_categories[self.group_by]['groups'][group_ID]['is_bold'] = is_bold
                    cfg.groups_by_categories[self.group_by]['groups'][group_ID]['is_italic'] = is_italic

                    # Update the plot with the new group parameters
                    try:
                        self.network_plot.edit_group_parameters(group_ID, 2, self.z_indexing_mode, self.color_by,
                                                                self.group_by)
                    except Exception as err:
                        error_msg = "An error occurred: cannot edit the group parameters"
                        error_occurred(self.network_plot.edit_group_parameters, 'edit_group_parameters', err,
                                       error_msg)

    def canvas_CTRL_release(self, event):
        self.ctrl_key_pressed = 0

        if self.mode == "interactive" or self.mode == "selection":
            try:
                self.network_plot.update_moved_positions(self.network_plot.selected_points, self.dim_num)
            except Exception as err:
                error_msg = "An error occurred: cannot update the positions of the data-points"
                error_occurred(self.network_plot.update_moved_positions, 'update_moved_positions', err, error_msg)
                return

            # Update the coordinates in the fruchterman-reingold object
            try:
                self.fr_object.init_coordinates(cfg.sequences_array['x_coor'],
                                                cfg.sequences_array['y_coor'],
                                                cfg.sequences_array['z_coor'])
            except Exception as err:
                error_msg = "An error occurred: cannot initialize the coordinates"
                error_occurred(self.fr_object.init_coordinates, 'init_coordinates', err, error_msg)














