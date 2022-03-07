from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QThreadPool
from vispy.color import ColorArray
import clans.config as cfg
import clans.io.io_gui as io
import clans.data.sequences as seq


class GroupByTaxDialog(QDialog):

    def __init__(self, net_plot_object):
        super().__init__()

        self.setWindowTitle("Group data by taxonomy")

        self.main_layout = QVBoxLayout()
        self.grid_layout = QGridLayout()

        # Add a 'message' label
        self.message_label = QLabel()
        self.grid_layout.addWidget(self.message_label, 0, 0, 1, 2)

        # Add a taxonomic-level selection combo-box
        self.tax_level_label = QLabel("Taxonomic level to group by:")
        self.tax_level_combo = QComboBox()
        self.tax_level_combo.addItem("Family")
        self.tax_level_combo.addItem("Order")
        self.tax_level_combo.addItem("Class")
        self.tax_level_combo.addItem("Phylum")
        self.tax_level_combo.addItem("Kingdom")
        self.tax_level_combo.addItem("Domain")

        self.grid_layout.addWidget(self.tax_level_label, 2, 0)
        self.grid_layout.addWidget(self.tax_level_combo, 2, 1)

        # Add general parameters for groups presentation (hided at first)
        self.space_label = QLabel(" ")
        self.grid_layout.addWidget(self.space_label, 3, 0, 1, 2)
        self.group_params_label = QLabel("General parameters for the groups:")
        self.grid_layout.addWidget(self.group_params_label, 4, 0, 1, 2)

        # Set the data points size
        self.points_size_label = QLabel("Data-points size:")
        default_size = net_plot_object.nodes_size
        self.points_size_combo = QComboBox()

        i = 0
        for size in range(4, 21):
            self.points_size_combo.addItem(str(size))
            if size == default_size:
                default_index = i
            i += 1
        self.points_size_combo.setCurrentIndex(default_index)

        self.grid_layout.addWidget(self.points_size_label, 5, 0)
        self.grid_layout.addWidget(self.points_size_combo, 5, 1)

        # Set the size of the group names
        self.group_name_size_label = QLabel("Group names text size:")
        default_size = net_plot_object.text_size
        self.group_name_size = QComboBox()

        i = 0
        for size in range(5, 21):
            self.group_name_size.addItem(str(size))
            if size == int(default_size):
                default_index = i
            i += 1
        self.group_name_size.setCurrentIndex(default_index)

        self.grid_layout.addWidget(self.group_name_size_label, 6, 0)
        self.grid_layout.addWidget(self.group_name_size, 6, 1)

        # Add Bold and Italic options
        self.bold_label = QLabel("Bold")
        self.bold_checkbox = QCheckBox()
        self.bold_checkbox.setChecked(True)
        self.bold_layout = QHBoxLayout()
        self.bold_layout.addWidget(self.bold_checkbox)
        self.bold_layout.addWidget(self.bold_label)
        self.bold_layout.addStretch()

        self.italic_label = QLabel("Italic")
        self.italic_checkbox = QCheckBox()
        self.italic_checkbox.setChecked(False)
        self.italic_layout = QHBoxLayout()
        self.italic_layout.addWidget(self.italic_checkbox)
        self.italic_layout.addWidget(self.italic_label)
        self.italic_layout.addStretch()

        self.grid_layout.addLayout(self.bold_layout, 7, 0)
        self.grid_layout.addLayout(self.italic_layout, 7, 1)

        self.main_layout.addLayout(self.grid_layout)

        # First time - no taxonomy search was done yet
        if not cfg.run_params['finished_taxonomy_search']:

            # Write a "searching" message
            self.message_label.setText("Extracting taxonomic information...")

            # Add a 'loading' gif
            self.loading_label = QLabel()
            self.loading_gif = QMovie("clans/GUI/icons/loading_bar_blue_small.gif")
            self.loading_label.setMovie(self.loading_gif)
            self.loading_gif.start()

            self.grid_layout.addWidget(self.loading_label, 1, 0, 1, 2)

            # Hide all the further widgets until the search finishes
            self.tax_level_label.hide()
            self.tax_level_combo.hide()
            self.space_label.hide()
            self.group_params_label.hide()
            self.points_size_label.hide()
            self.points_size_combo.hide()
            self.group_name_size_label.hide()
            self.group_name_size.hide()
            self.bold_label.hide()
            self.bold_checkbox.hide()
            self.italic_label.hide()
            self.italic_checkbox.hide()

        # The taxonomic search was already done
        else:

            # Taxonomic information exists
            if cfg.run_params['is_taxonomy_available']:
                text = "Taxonomic hierarchy for " + str(len(cfg.taxonomy_dict)) + " taxa is available"
                self.message_label.setText(text)
                self.message_label.setStyleSheet("color: maroon; font-size: 14px;")

                # Add the OK/Cancel standard buttons
                self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                self.button_box.accepted.connect(self.accept)
                self.button_box.rejected.connect(self.reject)
                self.main_layout.addWidget(self.button_box)

            # The taxonomy search was done but no information was found
            else:
                text = "Cannot group by taxonomy, as taxonomic information could not be extracted"
                self.message_label.setText(text)
                self.message_label.setStyleSheet("color: maroon; font-size: 14px;")

                # Hide all the widgets
                self.tax_level_label.hide()
                self.tax_level_combo.hide()
                self.space_label.hide()
                self.group_params_label.hide()
                self.points_size_label.hide()
                self.points_size_combo.hide()
                self.group_name_size_label.hide()
                self.group_name_size.hide()
                self.bold_label.hide()
                self.bold_checkbox.hide()
                self.italic_label.hide()
                self.italic_checkbox.hide()

        self.setLayout(self.main_layout)

    def finished_tax_search(self, error):

        if cfg.run_params['is_taxonomy_available']:
            text_message = "Found taxonomic hierarchy for " + str(len(cfg.taxonomy_dict)) + " taxa"
            self.message_label.setText(text_message)
            self.message_label.setStyleSheet("color: maroon; font-size: 14px;")

            self.loading_gif.stop()
            self.loading_label.hide()

            self.tax_level_label.show()
            self.tax_level_combo.show()
            self.space_label.show()
            self.group_params_label.show()
            self.points_size_label.show()
            self.points_size_combo.show()
            self.group_name_size_label.show()
            self.group_name_size.show()
            self.bold_label.show()
            self.bold_checkbox.show()
            self.italic_label.show()
            self.italic_checkbox.show()

            # Add the OK/Cancel standard buttons
            self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.connect(self.reject)
            self.main_layout.addWidget(self.button_box)

        else:
            self.message_label.setText(error)
            self.message_label.setStyleSheet("color: maroon; font-size: 12px")

            self.loading_gif.stop()
            self.loading_label.hide()

    def get_tax_level(self):

        tax_level = self.tax_level_combo.currentText()
        points_size = self.points_size_combo.currentText()
        group_names_size = self.group_name_size.currentText()
        is_bold = self.bold_checkbox.isChecked()
        is_italic = self.italic_checkbox.isChecked()

        return tax_level, points_size, group_names_size, is_bold, is_italic


class ColorByLengthDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Configure color by seq. length")

        self.main_layout = QVBoxLayout()
        self.layout = QGridLayout()

        self.title = QLabel("Define the color range:")
        self.layout.addWidget(self.title, 0, 0, 1, 3)

        self.row_space = QLabel(" ")
        self.row_space.setFixedSize(150, 15)
        self.layout.addWidget(self.row_space, 1, 0, 1, 2)

        self.short_label = QLabel("Short")
        self.long_label = QLabel("Long")

        self.layout.addWidget(self.short_label, 2, 0)
        self.layout.addWidget(self.long_label, 2, 2)

        self.short_color = cfg.short_color
        self.short_color_button = QPushButton("Change")
        self.short_color_button.setFixedSize(65, 28)
        self.short_color_button.setStyleSheet("background-color: " + self.short_color.hex[0])
        self.short_color_button.pressed.connect(self.change_short_color)

        self.long_color = cfg.long_color
        self.long_color_button = QPushButton("Change")
        self.long_color_button.setFixedSize(65, 28)
        self.long_color_button.setStyleSheet("background-color: " + self.long_color.hex[0])
        self.long_color_button.pressed.connect(self.change_long_color)

        self.switch_button = QPushButton()
        self.switch_button.setIcon(QIcon("clans/GUI/icons/switch_icon_trans.png"))
        self.switch_button.pressed.connect(self.switch_colors)

        self.layout.addWidget(self.short_color_button, 3, 0)
        self.layout.addWidget(self.switch_button, 3, 1)
        self.layout.addWidget(self.long_color_button, 3, 2)

        self.main_layout.addLayout(self.layout)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def change_short_color(self):
        dialog = QColorDialog()
        if dialog.exec_():
            color = dialog.currentColor()
            hex_color = color.name()

            self.short_color = ColorArray(hex_color)
            self.short_color_button.setStyleSheet("background-color: " + hex_color)

    def change_long_color(self):
        dialog = QColorDialog()
        if dialog.exec_():
            color = dialog.currentColor()
            hex_color = color.name()

            self.long_color = ColorArray(hex_color)
            self.long_color_button.setStyleSheet("background-color: " + hex_color)

    def switch_colors(self):
        short_color = self.short_color
        long_color = self.long_color

        self.short_color = long_color
        self.long_color = short_color

        self.short_color_button.setStyleSheet("background-color: " + self.short_color.hex[0])
        self.long_color_button.setStyleSheet("background-color: " + self.long_color.hex[0])

    def get_colors(self):
        return self.short_color, self.long_color


class ColorByParamDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.added_params = []

        self.threadpool = QThreadPool()

        self.setWindowTitle("Color-by custom parameter")

        self.main_layout = QVBoxLayout()
        self.layout = QGridLayout()
        self.colors_layout = QGridLayout()

        self.title = QLabel("Define a parameter by which to color the data")
        self.title.setStyleSheet("font-size: 14px")
        self.layout.addWidget(self.title, 0, 0, 1, 3)

        self.row_space = QLabel(" ")
        self.row_space.setFixedSize(150, 10)
        self.layout.addWidget(self.row_space, 1, 0, 1, 3)

        self.message_label = QLabel("No user-defined parameters")
        self.message_label.setStyleSheet("color: red;font-size: 14px")

        self.layout.addWidget(self.message_label, 2, 0, 1, 3)

        self.param_label = QLabel("Select a parameter from the list:")
        self.param_combo = QComboBox()
        self.param_combo.currentIndexChanged.connect(self.change_param)
        self.file_label = QLabel()

        self.upload_file_button = QPushButton("Upload file")
        self.upload_file_button.pressed.connect(self.upload_file)

        self.layout.addWidget(self.param_label, 3, 0)
        self.layout.addWidget(self.param_combo, 3, 1)

        self.layout.addWidget(self.file_label, 4, 0, 1, 2)
        self.layout.addWidget(self.upload_file_button, 4, 2)

        self.layout.addWidget(self.row_space, 5, 0, 1, 3)

        self.color_range_label = QLabel("Define the color range:")
        self.colors_layout.addWidget(self.color_range_label, 0, 0, 1, 2)

        self.min_label = QLabel("Min. value")
        self.max_label = QLabel("Max. value")

        self.colors_layout.addWidget(self.min_label, 1, 0)
        self.colors_layout.addWidget(self.max_label, 1, 2)

        self.min_color = cfg.min_param_color
        self.min_color_button = QPushButton("Change")
        self.min_color_button.setFixedSize(65, 28)
        self.min_color_button.setStyleSheet("background-color: " + self.min_color.hex[0])
        self.min_color_button.pressed.connect(self.change_min_color)

        self.max_color = cfg.max_param_color
        self.max_color_button = QPushButton("Change")
        self.max_color_button.setFixedSize(65, 28)
        self.max_color_button.setStyleSheet("background-color: " + self.max_color.hex[0])
        self.max_color_button.pressed.connect(self.change_max_color)

        self.switch_button = QPushButton()
        self.switch_button.setIcon(QIcon("clans/GUI/icons/switch_icon_trans.png"))
        self.switch_button.pressed.connect(self.switch_colors)

        self.colors_layout.addWidget(self.min_color_button, 2, 0)
        self.colors_layout.addWidget(self.switch_button, 2, 1)
        self.colors_layout.addWidget(self.max_color_button, 2, 2)

        self.layout.addLayout(self.colors_layout, 6, 0, 1, 2)

        self.main_layout.addLayout(self.layout)
        #self.main_layout.addLayout(self.colors_layout)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

        # There is at least one user-defined parameter
        if len(cfg.sequences_numeric_params) > 0:

            param_index = 0
            for param in cfg.sequences_numeric_params:
                self.param_combo.addItem(param)

                # Set the colors of the first parameter in the list
                if param_index == 0:
                    self.min_color = cfg.sequences_numeric_params[param]['min_color']
                    self.min_color_button.setStyleSheet("background-color: " + self.min_color.hex[0])
                    self.max_color = cfg.sequences_numeric_params[param]['max_color']
                    self.max_color_button.setStyleSheet("background-color: " + self.max_color.hex[0])

                param_index += 1

            self.message_label.hide()
            self.param_label.setText("Select a parameter from the list:")
            self.file_label.setText("Or upload a metadata file with additional(s) parameter(s)")

        else:
            self.param_label.hide()
            self.param_combo.hide()

            self.file_label.setText("Upload a metadata file with user-defined numeric parameter(s)")

            self.color_range_label.hide()
            self.min_label.hide()
            self.max_label.hide()
            self.min_color_button.hide()
            self.switch_button.hide()
            self.max_color_button.hide()

    def upload_file(self):
        opened_file, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All files (*.*)")

        if opened_file:
            file_worker = io.ReadMetadataWorker(opened_file)
            file_worker.signals.finished.connect(self.update_metadata)

            # Execute worker
            self.threadpool.start(file_worker)

    def update_metadata(self, sequences_params_dict, error):

        # The parameter's values was added correctly - add the parameter to the list
        if error == "":

            self.added_params = seq.add_numeric_params(sequences_params_dict)

            self.param_label.setText("Select a parameter from the list:")
            self.param_label.setStyleSheet("color: black;font-size: 12px")

            self.param_combo.clear()
            for param_name in cfg.sequences_numeric_params:
                self.param_combo.addItem(param_name)

            self.message_label.hide()
            self.param_label.show()
            self.param_combo.show()
            self.file_label.setText("Or upload a metadata file with additional(s) parameter(s)")

            self.color_range_label.show()
            self.min_label.show()
            self.max_label.show()
            self.min_color_button.show()
            self.switch_button.show()
            self.max_color_button.show()

        else:
            print(error)
            self.message_label.setText(error)
            self.message_label.show()

    def change_min_color(self):
        dialog = QColorDialog()
        if dialog.exec_():
            color = dialog.currentColor()
            hex_color = color.name()

            self.min_color = ColorArray(hex_color)
            self.min_color_button.setStyleSheet("background-color: " + hex_color)

    def change_max_color(self):
        dialog = QColorDialog()
        if dialog.exec_():
            color = dialog.currentColor()
            hex_color = color.name()

            self.max_color = ColorArray(hex_color)
            self.max_color_button.setStyleSheet("background-color: " + hex_color)

    def switch_colors(self):
        min_color = self.min_color
        max_color = self.max_color

        self.min_color = max_color
        self.max_color = min_color

        self.min_color_button.setStyleSheet("background-color: " + self.min_color.hex[0])
        self.max_color_button.setStyleSheet("background-color: " + self.max_color.hex[0])

    def change_param(self):
        selected_param = self.param_combo.currentText()

        if selected_param in cfg.sequences_numeric_params:
            self.min_color = cfg.sequences_numeric_params[selected_param]['min_color']
            self.min_color_button.setStyleSheet("background-color: " + self.min_color.hex[0])
            self.max_color = cfg.sequences_numeric_params[selected_param]['max_color']
            self.max_color_button.setStyleSheet("background-color: " + self.max_color.hex[0])

    def get_param(self):

        selected_param_name = self.param_combo.currentText()
        return selected_param_name, self.added_params, self.min_color, self.max_color






