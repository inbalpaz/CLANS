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
        for size in range(4, 21):
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

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addLayout(self.layout)
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

        self.color_title = QLabel("Set the edges color(s):")

        self.uniform_color_button = QRadioButton("Uniform color for all edges")

        self.bins_color_button = QRadioButton("Color edges by ")
        self.bins_color_button.setChecked(True)



