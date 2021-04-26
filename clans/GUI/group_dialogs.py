from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import clans.config as cfg


class AddToGroupDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add selected sequences")

        self.layout = QVBoxLayout()

        self.title = QLabel("Add the selected sequences to:")

        self.new_group_button = QRadioButton("Create a new group")
        self.new_group_button.setChecked(True)

        self.existing_group_button = QRadioButton("Choose an existing group")

        self.groups_combo = QComboBox()
        self.groups_combo.addItem("Select group")
        self.group_IDs_list = []
        for group_ID in cfg.groups_dict:
            self.groups_combo.addItem(cfg.groups_dict[group_ID]['name'])
            self.group_IDs_list.append(group_ID)
        self.groups_combo.setEnabled(False)

        self.new_group_button.toggled.connect(self.on_radio_button_change)
        self.existing_group_button.toggled.connect(self.on_radio_button_change)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.new_group_button)
        self.layout.addWidget(self.existing_group_button)
        self.layout.addWidget(self.groups_combo)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

    def on_radio_button_change(self):
        if self.existing_group_button.isChecked():
            self.groups_combo.setEnabled(True)
        else:
            self.groups_combo.setEnabled(False)

    def get_choice(self):
        if self.new_group_button.isChecked():
            return 'new', ''
        else:
            index = int(self.groups_combo.currentIndex() - 1)
            group_ID = self.group_IDs_list[index]
            return 'existing', group_ID


class CreateGroupDialog(QDialog):

    def __init__(self, net_plot_object):
        super().__init__()

        self.setWindowTitle("Create group from selected")

        self.main_layout = QVBoxLayout()
        self.layout = QGridLayout()

        # Set the group name
        self.name_label = QLabel("Group name:")
        self.name_widget = QLineEdit()

        if len(cfg.groups_dict) == 0:
            group_num = 1
        else:
            group_num = max(cfg.groups_dict.keys()) + 1
        self.default_group_name = "Group_" + str(group_num)
        self.name_widget.setPlaceholderText(self.default_group_name)

        self.layout.addWidget(self.name_label, 0, 0)
        self.layout.addWidget(self.name_widget, 0, 1, 1, 2)

        self.sep = QFrame()
        #self.sep.setFrameShape(QFrame.HLine)
        self.sep.setFrameShape(QFrame.Box)
        self.layout.addWidget(self.sep, 1, 1)

        self.label = QLabel("Display settings for the group's data-points:")
        self.label.setStyleSheet("font-size:14px;")
        self.layout.addWidget(self.label, 2, 0, 1, 3)

        # Set the shape of the group nodes
        #self.shape_label = QLabel("Shape:")
        #self.group_shape = QComboBox()
        #self.shapes_array = ["circle", "triangle_up", "triangle_down", "clover", "star", "square", "diamond", "cross",
        #                     "x"]
        #self.group_shape.addItems(self.shapes_array)
        #disc_icon = QIcon('clans/GUI/icons/circle.png')
        #triangle_up_icon = QIcon('clans/GUI/icons/triangle_up.png')
        #triangle_down_icon = QIcon('clans/GUI/icons/triangle_down.png')
        #clover_icon = QIcon('clans/GUI/icons/clover.png')
        #star_icon = QIcon('clans/GUI/icons/star.png')
        #square_icon = QIcon('clans/GUI/icons/square.png')
        #diamond_icon = QIcon('clans/GUI/icons/diamond.png')
        #cross_icon = QIcon('clans/GUI/icons/cross.png')
        #x_icon = QIcon('clans/GUI/icons/x.png')
        #self.group_shape.setItemIcon(0, disc_icon)
        #self.group_shape.setItemIcon(1, triangle_up_icon)
        #self.group_shape.setItemIcon(2, triangle_down_icon)
        #self.group_shape.setItemIcon(3, clover_icon)
        #self.group_shape.setItemIcon(4, star_icon)
        #self.group_shape.setItemIcon(5, square_icon)
        #self.group_shape.setItemIcon(6, diamond_icon)
        #self.group_shape.setItemIcon(7, cross_icon)
        #self.group_shape.setItemIcon(8, x_icon)

        #self.layout.addWidget(self.shape_label, 3, 0)
        #self.layout.addWidget(self.group_shape, 3, 1)

        # Set the size of the group nodes
        self.size_label = QLabel("Size:")
        default_size = net_plot_object.nodes_size
        self.group_size = QComboBox()

        i = 0
        for size in range(5, 16):
            self.group_size.addItem(str(size))
            if size == default_size:
                default_index = i
            i += 1
        self.group_size.setCurrentIndex(default_index)

        self.layout.addWidget(self.size_label, 4, 0)
        self.layout.addWidget(self.group_size, 4, 1)

        # Set the color of the group's nodes
        self.color_label = QLabel("Color:")
        self.selected_color_label = QLabel(" ")
        self.selected_color = "black"
        self.rgb_color = "0;0;0;255"
        self.color_array = [0.0, 0.0, 0.0, 1.0]
        self.selected_color_label.setStyleSheet("background-color: " + self.selected_color)

        self.change_color_button = QPushButton("Change color")
        self.change_color_button.pressed.connect(self.change_color)

        self.layout.addWidget(self.color_label, 5, 0)
        self.layout.addWidget(self.selected_color_label, 5, 1)
        self.layout.addWidget(self.change_color_button, 5, 2)

        # Add a checkbox to show/hide the group
        self.show_group_checkbox = QCheckBox("Show group")
        self.show_group_checkbox.setChecked(True)

        self.layout.addWidget(self.show_group_checkbox, 6, 0)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addLayout(self.layout)
        self.main_layout.addWidget(self.button_box)
        self.setLayout(self.main_layout)

    def change_color(self):
        dialog = QColorDialog()
        if dialog.exec_():
            color = dialog.currentColor()
            red = color.red()
            green = color.green()
            blue = color.blue()
            hex = color.name()
            self.rgb_color = str(red) + ";" + str(green) + ";" + str(blue) + ";255"
            self.color_array = [red/255, green/255, blue/255, 1.0]
            self.selected_color = hex
            self.selected_color_label.setStyleSheet("background-color: " + self.selected_color)

    def get_group_info(self):

        # Get the group name
        if self.name_widget.text() == "":
            group_name = self.default_group_name
        else:
            group_name = self.name_widget.text()

        # Get the selected shape
        #shape_index = self.group_shape.currentIndex()
        #shape_name = self.shapes_array[shape_index]
        #if shape_name == "circle":
            #shape_name = "disc"
        #elif shape_name == "clover":
            #shape_name = "clobber"

        # Get the selected size
        size = self.group_size.currentText()

        # Get the show/hide state
        if self.show_group_checkbox.isChecked():
            hide = 0
        else:
            hide = 1

        return group_name, size, self.rgb_color, self.color_array, hide
