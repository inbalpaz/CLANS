from PyQt5.QtWidgets import *
import re
import numpy as np
from vispy.color import ColorArray
import clans.config as cfg


def error_occurred(method, method_name, exception_err, error_msg):

    if cfg.run_params['is_debug_mode']:
        print("\nError in " + method.__globals__['__file__'] + " (" + method_name + "):")
        print(exception_err)

    msg_box = QMessageBox()
    msg_box.setText(error_msg)
    if msg_box.exec_():
        return


class FruchtermanReingoldConfig(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Configure Fruchterman-Reingold layout")

        self.main_layout = QVBoxLayout()
        self.layout = QGridLayout()

        self.att_val_label = QLabel("Attraction factor")
        self.att_val = QLineEdit(str(cfg.run_params['att_val']))

        self.att_exp_label = QLabel("Attraction exponent (int)")
        self.att_exp = QLineEdit(str(cfg.run_params['att_exp']))

        self.rep_val_label = QLabel("Repulsion factor")
        self.rep_val = QLineEdit(str(cfg.run_params['rep_val']))

        self.rep_exp_label = QLabel("Repulsion exponent (int)")
        self.rep_exp = QLineEdit(str(cfg.run_params['rep_exp']))

        self.gravity_label = QLabel("Gravity")
        self.gravity = QLineEdit(str(cfg.run_params['gravity']))

        self.dampening_label = QLabel("Dampening")
        self.dampening = QLineEdit(str(cfg.run_params['dampening']))

        self.maxmove_label = QLabel("Max. move")
        self.maxmove = QLineEdit(str(cfg.run_params['maxmove']))

        self.cooling_label = QLabel("Cooling")
        self.cooling = QLineEdit(str(cfg.run_params['cooling']))

        self.layout.addWidget(self.att_val_label, 0, 0)
        self.layout.addWidget(self.att_val, 0, 1)

        self.layout.addWidget(self.att_exp_label, 1, 0)
        self.layout.addWidget(self.att_exp, 1, 1)

        self.layout.addWidget(self.rep_val_label, 2, 0)
        self.layout.addWidget(self.rep_val, 2, 1)

        self.layout.addWidget(self.rep_exp_label, 3, 0)
        self.layout.addWidget(self.rep_exp, 3, 1)

        self.layout.addWidget(self.gravity_label, 4, 0)
        self.layout.addWidget(self.gravity, 4, 1)

        self.layout.addWidget(self.dampening_label, 5, 0)
        self.layout.addWidget(self.dampening, 5, 1)

        self.layout.addWidget(self.maxmove_label, 6, 0)
        self.layout.addWidget(self.maxmove, 6, 1)

        self.layout.addWidget(self.cooling_label, 7, 0)
        self.layout.addWidget(self.cooling, 7, 1)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addLayout(self.layout)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def get_parameters(self):

        if re.search("^\d+(\.\d+)?$", self.att_val.text()):
            att_val = float(self.att_val.text())
        else:
            att_val = cfg.run_params['att_val']

        if re.search("^\d$", self.att_exp.text()):
            att_exp = int(self.att_exp.text())
        else:
            att_exp = cfg.run_params['att_exp']

        if re.search("^\d+(\.\d+)?$", self.rep_val.text()):
            rep_val = float(self.rep_val.text())
        else:
            rep_val = cfg.run_params['rep_val']

        if re.search("^\d$", self.rep_exp.text()):
            rep_exp = int(self.rep_exp.text())
        else:
            rep_exp = cfg.run_params['rep_exp']

        if re.search("^\d+(\.\d+)?$", self.gravity.text()):
            gravity = float(self.gravity.text())
        else:
            gravity = cfg.run_params['gravity']

        if re.search("^\d+(\.\d+)?$", self.dampening.text()):
            if 0 <= float(self.dampening.text()) <= 1:
                dampening = float(self.dampening.text())
            else:
                dampening = cfg.run_params['dampening']
        else:
            dampening = cfg.run_params['dampening']

        if re.search("^\d+(\.\d+)?$", self.maxmove.text()):
            if float(self.maxmove.text()) > 0:
                maxmove = float(self.maxmove.text())
            else:
                maxmove = cfg.run_params['maxmove']
        else:
            maxmove = cfg.run_params['maxmove']

        if re.search("^\d+(\.\d+)?$", self.cooling.text()):
            if 0 < float(self.cooling.text()) <= 1:
                cooling = float(self.cooling.text())
            else:
                cooling = cfg.run_params['cooling']
        else:
            cooling = cfg.run_params['cooling']

        return att_val, att_exp, rep_val, rep_exp, gravity, dampening, maxmove, cooling


class NodesConfig(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Configure data-points visual parameters")

        self.main_layout = QVBoxLayout()
        self.layout = QGridLayout()

        self.nodes_sizes_label = QLabel("Size:")
        self.nodes_size_combo = QComboBox()

        i = 0
        for size in range(1, 21):
            self.nodes_size_combo.addItem(str(size))
            if size == cfg.run_params['nodes_size']:
                default_index = i
            i += 1
        self.nodes_size_combo.setCurrentIndex(default_index)

        self.layout.addWidget(self.nodes_sizes_label, 0, 0)
        self.layout.addWidget(self.nodes_size_combo, 0, 1)

        self.nodes_color_label = QLabel("Color:")

        self.nodes_color = ColorArray(cfg.run_params['nodes_color'])
        self.nodes_color_box = QLabel(" ")
        self.nodes_color_box.setStyleSheet("background-color: " + self.nodes_color.hex[0])
        self.nodes_color_button = QPushButton("Change color")
        self.nodes_color_button.pressed.connect(self.change_nodes_color)

        self.layout.addWidget(self.nodes_color_label, 1, 0)
        self.layout.addWidget(self.nodes_color_box, 1, 1)
        self.layout.addWidget(self.nodes_color_button, 1, 2)

        self.outline_color_label = QLabel("Outline color:")

        self.outline_color = ColorArray(cfg.run_params['nodes_outline_color'])
        self.outline_color_box = QLabel(" ")
        self.outline_color_box.setStyleSheet("background-color: " + self.outline_color.hex[0])
        self.outline_color_button = QPushButton("Change color")
        self.outline_color_button.pressed.connect(self.change_outline_color)

        self.layout.addWidget(self.outline_color_label, 2, 0)
        self.layout.addWidget(self.outline_color_box, 2, 1)
        self.layout.addWidget(self.outline_color_button, 2, 2)

        self.outline_width_label = QLabel("Outline width:")
        self.outline_width_combo = QComboBox()

        i = 0
        width_options = np.arange(0, 3.5, 0.5)
        for size in width_options:
            self.outline_width_combo.addItem(str(size))
            if size == cfg.run_params['nodes_outline_width']:
                default_index = i
            i += 1
        self.outline_width_combo.setCurrentIndex(default_index)

        self.layout.addWidget(self.outline_width_label, 3, 0)
        self.layout.addWidget(self.outline_width_combo, 3, 1)

        self.reset_button = QPushButton("Reset to defaults")
        self.reset_button.pressed.connect(self.reset)

        self.layout.addWidget(self.reset_button, 4, 0, 1, 1)

        self.note = QLabel("Note: changes to data-points color only apply if they are not assigned to any group.\n"
                           "The color of the groups can be changed using the 'Edit groups' dialog.")
        self.note.setStyleSheet("color: " + cfg.title_color + ";")

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addLayout(self.layout)
        self.main_layout.addWidget(self.note)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def change_nodes_color(self):

        dialog = QColorDialog()

        if dialog.exec_():
            color = dialog.currentColor()
            hex_color = color.name()

            self.nodes_color = ColorArray(hex_color)
            self.nodes_color_box.setStyleSheet("background-color: " + hex_color)

    def change_outline_color(self):

        dialog = QColorDialog()

        if dialog.exec_():
            color = dialog.currentColor()
            hex_color = color.name()

            self.outline_color = ColorArray(hex_color)
            self.outline_color_box.setStyleSheet("background-color: " + hex_color)

    def reset(self):

        # Set the default nodes size according to the dataset size
        if cfg.run_params['total_sequences_num'] <= 1000:
            cfg.run_params['nodes_size'] = cfg.nodes_size_large
        elif 1000 < cfg.run_params['total_sequences_num'] <= 4000:
            cfg.run_params['nodes_size'] = cfg.nodes_size_medium
        elif 4000 < cfg.run_params['total_sequences_num'] <= 10000:
            cfg.run_params['nodes_size'] = cfg.nodes_size_small
        else:
            cfg.run_params['nodes_size'] = cfg.nodes_size_tiny

        i = 0
        for size in range(4, 21):
            if size == cfg.run_params['nodes_size']:
                default_index = i
            i += 1
        self.nodes_size_combo.setCurrentIndex(default_index)

        # Set the default nodes color
        cfg.run_params['nodes_color'] = cfg.nodes_color
        self.nodes_color = ColorArray(cfg.run_params['nodes_color'])
        self.nodes_color_box.setStyleSheet("background-color: " + self.nodes_color.hex[0])

        # Set the default nodes outline color
        cfg.run_params['nodes_outline_color'] = cfg.nodes_outline_color
        self.outline_color = ColorArray(cfg.run_params['nodes_outline_color'])
        self.outline_color_box.setStyleSheet("background-color: " + self.outline_color.hex[0])

        # Set the default nodes outline width
        cfg.run_params['nodes_outline_width'] = cfg.nodes_outline_width
        i = 0
        width_options = np.arange(0, 3.5, 0.5)
        for size in width_options:
            if size == cfg.run_params['nodes_outline_width']:
                default_index = i
            i += 1
        self.outline_width_combo.setCurrentIndex(default_index)

    def get_parameters(self):

        size = int(self.nodes_size_combo.currentText())
        color = self.nodes_color.rgba[0]
        outline_color = self.outline_color.rgba[0]
        outline_width = float(self.outline_width_combo.currentText())

        return size, color, outline_color, outline_width


class EdgesConfig(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Configure edges visual parameters")

        self.main_layout = QVBoxLayout()
        self.layout = QGridLayout()
        self.colors_layout = QGridLayout()
        self.width_layout = QGridLayout()

        self.color_title = QLabel("Set the color(s) of the edges:")

        self.layout.addWidget(self.color_title, 0, 0, 1, 6)

        self.color_group = QButtonGroup()
        self.width_group = QButtonGroup()

        self.bins_color_button = QRadioButton("Color edges by score bins (normalized values)")
        if not cfg.run_params['is_uniform_edges_color']:
            self.bins_color_button.setChecked(True)
        self.bins_color_button.toggled.connect(self.on_color_button_change)
        self.color_group.addButton(self.bins_color_button)

        self.layout.addWidget(self.bins_color_button, 1, 0, 1, 6)

        self.color_range_label = QLabel("Define the color for each bin:")
        self.colors_layout.addWidget(self.color_range_label, 0, 0, 1, 5)

        self.bin1_label = QLabel("0.2")
        self.bin2_label = QLabel("0.4")
        self.bin3_label = QLabel("0.6")
        self.bin4_label = QLabel("0.8")
        self.bin5_label = QLabel("1.0")

        self.colors_layout.addWidget(self.bin1_label, 1, 0)
        self.colors_layout.addWidget(self.bin2_label, 1, 1)
        self.colors_layout.addWidget(self.bin3_label, 1, 2)
        self.colors_layout.addWidget(self.bin4_label, 1, 3)
        self.colors_layout.addWidget(self.bin5_label, 1, 4)

        self.bin1_color = ColorArray(cfg.run_params['edges_color_scale'][0])
        self.bin1_color_button = QPushButton("Change")
        self.bin1_color_button.setFixedSize(60, 28)
        self.bin1_color_button.setStyleSheet("background-color: " + self.bin1_color.hex[0])
        self.bin1_color_button.pressed.connect(self.change_bin1_color)

        self.bin2_color = ColorArray(cfg.run_params['edges_color_scale'][1])
        self.bin2_color_button = QPushButton("Change")
        self.bin2_color_button.setFixedSize(60, 28)
        self.bin2_color_button.setStyleSheet("background-color: " + self.bin2_color.hex[0])
        self.bin2_color_button.pressed.connect(self.change_bin2_color)

        self.bin3_color = ColorArray(cfg.run_params['edges_color_scale'][2])
        self.bin3_color_button = QPushButton("Change")
        self.bin3_color_button.setFixedSize(60, 28)
        self.bin3_color_button.setStyleSheet("background-color: " + self.bin3_color.hex[0])
        self.bin3_color_button.pressed.connect(self.change_bin3_color)

        self.bin4_color = ColorArray(cfg.run_params['edges_color_scale'][3])
        self.bin4_color_button = QPushButton("Change")
        self.bin4_color_button.setFixedSize(60, 28)
        self.bin4_color_button.setStyleSheet("background-color: " + self.bin3_color.hex[0])
        self.bin4_color_button.pressed.connect(self.change_bin4_color)

        self.bin5_color = ColorArray(cfg.run_params['edges_color_scale'][4])
        self.bin5_color_button = QPushButton("Change")
        self.bin5_color_button.setFixedSize(60, 28)
        self.bin5_color_button.setStyleSheet("background-color: " + self.bin5_color.hex[0])
        self.bin5_color_button.pressed.connect(self.change_bin5_color)

        self.colors_layout.addWidget(self.bin1_color_button, 2, 0)
        self.colors_layout.addWidget(self.bin2_color_button, 2, 1)
        self.colors_layout.addWidget(self.bin3_color_button, 2, 2)
        self.colors_layout.addWidget(self.bin4_color_button, 2, 3)
        self.colors_layout.addWidget(self.bin5_color_button, 2, 4)

        self.layout.addLayout(self.colors_layout, 2, 0, 1, 6)

        self.uniform_color_radio_button = QRadioButton("Uniform color for all edges")
        if cfg.run_params['is_uniform_edges_color']:
            self.uniform_color_radio_button.setChecked(True)
        self.uniform_color_radio_button.toggled.connect(self.on_color_button_change)
        self.color_group.addButton(self.uniform_color_radio_button)

        self.layout.addWidget(self.uniform_color_radio_button, 3, 0, 1, 6)

        self.uniform_color_label = QLabel("Color:")

        self.edges_color = ColorArray(cfg.run_params['edges_color'])
        self.edges_color_box = QLabel(" ")
        self.edges_color_box.setStyleSheet("background-color: " + self.edges_color.hex[0])
        self.edges_color_button = QPushButton("Change color")
        self.edges_color_button.setEnabled(False)
        self.edges_color_button.pressed.connect(self.change_edges_color)

        self.layout.addWidget(self.uniform_color_label, 4, 1, 1, 1)
        self.layout.addWidget(self.edges_color_box, 4, 2, 1, 1)
        self.layout.addWidget(self.edges_color_button, 4, 3, 1, 2)

        self.space_label = QLabel("  ")
        self.layout.addWidget(self.space_label, 5, 0, 1, 6)

        self.width_title = QLabel("Set the width of the edges:")
        self.layout.addWidget(self.width_title, 6, 0, 1, 6)

        self.uniform_width_radio_button = QRadioButton("Uniform width for all edges:")
        if cfg.run_params['is_uniform_edges_width']:
            self.uniform_width_radio_button.setChecked(True)
        self.uniform_width_radio_button.toggled.connect(self.on_width_button_change)
        self.width_group.addButton(self.uniform_width_radio_button)

        self.bins_width_radio_button = QRadioButton("Set different width according score bins (normalized values)")
        if not cfg.run_params['is_uniform_edges_width']:
            self.bins_width_radio_button.setChecked(True)
        self.bins_width_radio_button.toggled.connect(self.on_width_button_change)
        self.width_group.addButton(self.bins_width_radio_button)

        self.layout.addWidget(self.uniform_width_radio_button, 7, 0, 1, 3)

        self.uniform_width_combo = QComboBox()
        i = 0
        width_options = np.arange(1, 5.5, 0.5)
        for size in width_options:
            self.uniform_width_combo.addItem(str(size))
            if size == cfg.run_params['edges_width']:
                default_index = i
            i += 1
        self.uniform_width_combo.setCurrentIndex(default_index)

        self.layout.addWidget(self.uniform_width_combo, 7, 3, 1, 1)

        self.layout.addWidget(self.bins_width_radio_button, 8, 0, 1, 6)

        self.width_range_label = QLabel("Define the width for each bin:")
        self.width_layout.addWidget(self.width_range_label, 0, 0, 1, 5)

        self.bin1_width_label = QLabel("0.2")
        self.bin2_width_label = QLabel("0.4")
        self.bin3_width_label = QLabel("0.6")
        self.bin4_width_label = QLabel("0.8")
        self.bin5_width_label = QLabel("1.0")

        self.width_layout.addWidget(self.bin1_width_label, 1, 0)
        self.width_layout.addWidget(self.bin2_width_label, 1, 1)
        self.width_layout.addWidget(self.bin3_width_label, 1, 2)
        self.width_layout.addWidget(self.bin4_width_label, 1, 3)
        self.width_layout.addWidget(self.bin5_width_label, 1, 4)

        self.bin1_width_combo = QComboBox()
        i = 0
        for size in width_options:
            self.bin1_width_combo.addItem(str(size))
            if size == cfg.run_params['edges_width_scale'][0]:
                default_index = i
            i += 1
        self.bin1_width_combo.setCurrentIndex(default_index)
        self.bin1_width_combo.setEnabled(False)

        self.bin2_width_combo = QComboBox()
        i = 0
        for size in width_options:
            self.bin2_width_combo.addItem(str(size))
            if size == cfg.run_params['edges_width_scale'][1]:
                default_index = i
            i += 1
        self.bin2_width_combo.setCurrentIndex(default_index)
        self.bin2_width_combo.setEnabled(False)

        self.bin3_width_combo = QComboBox()
        i = 0
        for size in width_options:
            self.bin3_width_combo.addItem(str(size))
            if size == cfg.run_params['edges_width_scale'][2]:
                default_index = i
            i += 1
        self.bin3_width_combo.setCurrentIndex(default_index)
        self.bin3_width_combo.setEnabled(False)

        self.bin4_width_combo = QComboBox()
        i = 0
        for size in width_options:
            self.bin4_width_combo.addItem(str(size))
            if size == cfg.run_params['edges_width_scale'][3]:
                default_index = i
            i += 1
        self.bin4_width_combo.setCurrentIndex(default_index)
        self.bin4_width_combo.setEnabled(False)

        self.bin5_width_combo = QComboBox()
        i = 0
        for size in width_options:
            self.bin5_width_combo.addItem(str(size))
            if size == cfg.run_params['edges_width_scale'][4]:
                default_index = i
            i += 1
        self.bin5_width_combo.setCurrentIndex(default_index)
        self.bin5_width_combo.setEnabled(False)

        self.width_layout.addWidget(self.bin1_width_combo, 2, 0)
        self.width_layout.addWidget(self.bin2_width_combo, 2, 1)
        self.width_layout.addWidget(self.bin3_width_combo, 2, 2)
        self.width_layout.addWidget(self.bin4_width_combo, 2, 3)
        self.width_layout.addWidget(self.bin5_width_combo, 2, 4)

        self.layout.addLayout(self.width_layout, 9, 0, 1, 6)

        self.main_layout.addLayout(self.layout)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

        self.on_color_button_change()
        self.on_width_button_change()

    def on_color_button_change(self):
        try:
            if self.uniform_color_radio_button.isChecked():
                self.edges_color_button.setEnabled(True)
                self.bin1_color_button.setEnabled(False)
                self.bin2_color_button.setEnabled(False)
                self.bin3_color_button.setEnabled(False)
                self.bin4_color_button.setEnabled(False)
                self.bin5_color_button.setEnabled(False)
            else:
                self.edges_color_button.setEnabled(False)
                self.bin1_color_button.setEnabled(True)
                self.bin2_color_button.setEnabled(True)
                self.bin3_color_button.setEnabled(True)
                self.bin4_color_button.setEnabled(True)
                self.bin5_color_button.setEnabled(True)

        except Exception as err:
            error_msg = "An error occurred: cannot change selection"
            error_occurred(self.on_color_button_change, 'on_color_button_change', err, error_msg)

    def change_edges_color(self):

        dialog = QColorDialog()

        if dialog.exec_():
            color = dialog.currentColor()
            hex_color = color.name()

            self.edges_color = ColorArray(hex_color)
            self.edges_color_box.setStyleSheet("background-color: " + hex_color)

    def change_bin1_color(self):
        try:
            dialog = QColorDialog()
            if dialog.exec_():
                color = dialog.currentColor()
                hex_color = color.name()

                self.bin1_color = ColorArray(hex_color)
                self.bin1_color_button.setStyleSheet("background-color: " + hex_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change color"
            error_occurred(self.change_bin1_color, 'change_bin1_color', err, error_msg)

    def change_bin2_color(self):
        try:
            dialog = QColorDialog()
            if dialog.exec_():
                color = dialog.currentColor()
                hex_color = color.name()

                self.bin2_color = ColorArray(hex_color)
                self.bin2_color_button.setStyleSheet("background-color: " + hex_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change color"
            error_occurred(self.change_bin2_color, 'change_bin2_color', err, error_msg)

    def change_bin3_color(self):
        try:
            dialog = QColorDialog()
            if dialog.exec_():
                color = dialog.currentColor()
                hex_color = color.name()

                self.bin3_color = ColorArray(hex_color)
                self.bin3_color_button.setStyleSheet("background-color: " + hex_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change color"
            error_occurred(self.change_bin3_color, 'change_bin3_color', err, error_msg)

    def change_bin4_color(self):
        try:
            dialog = QColorDialog()
            if dialog.exec_():
                color = dialog.currentColor()
                hex_color = color.name()

                self.bin4_color = ColorArray(hex_color)
                self.bin4_color_button.setStyleSheet("background-color: " + hex_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change color"
            error_occurred(self.change_bin4_color, 'change_bin4_color', err, error_msg)

    def change_bin5_color(self):
        try:
            dialog = QColorDialog()
            if dialog.exec_():
                color = dialog.currentColor()
                hex_color = color.name()

                self.bin5_color = ColorArray(hex_color)
                self.bin5_color_button.setStyleSheet("background-color: " + hex_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change color"
            error_occurred(self.change_bin5_color, 'change_bin5_color', err, error_msg)

    def on_width_button_change(self):

        try:
            if self.bins_width_radio_button.isChecked():
                self.uniform_width_combo.setEnabled(False)
                self.bin1_width_combo.setEnabled(True)
                self.bin2_width_combo.setEnabled(True)
                self.bin3_width_combo.setEnabled(True)
                self.bin4_width_combo.setEnabled(True)
                self.bin5_width_combo.setEnabled(True)
            else:
                self.uniform_width_combo.setEnabled(True)
                self.bin1_width_combo.setEnabled(False)
                self.bin2_width_combo.setEnabled(False)
                self.bin3_width_combo.setEnabled(False)
                self.bin4_width_combo.setEnabled(False)
                self.bin5_width_combo.setEnabled(False)

        except Exception as err:
            error_msg = "An error occurred: cannot change selection"
            error_occurred(self.on_width_button_change, 'on_width_button_change', err, error_msg)

    def get_parameters(self):

        color = self.edges_color.rgba[0]

        color_scale = list()
        color_scale.append(self.bin1_color.rgba[0])
        color_scale.append(self.bin2_color.rgba[0])
        color_scale.append(self.bin3_color.rgba[0])
        color_scale.append(self.bin4_color.rgba[0])
        color_scale.append(self.bin5_color.rgba[0])

        width = float(self.uniform_width_combo.currentText())

        width_scale = list()
        width_scale.append(float(self.bin1_width_combo.currentText()))
        width_scale.append(float(self.bin2_width_combo.currentText()))
        width_scale.append(float(self.bin3_width_combo.currentText()))
        width_scale.append(float(self.bin4_width_combo.currentText()))
        width_scale.append(float(self.bin5_width_combo.currentText()))

        if self.uniform_color_radio_button.isChecked():
            is_uniform_color = True
        else:
            is_uniform_color = False

        if self.uniform_width_radio_button.isChecked():
            is_uniform_width = True
        else:
            is_uniform_width = False

        return is_uniform_color, color, color_scale, is_uniform_width, width, width_scale






