from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import clans.config as cfg
import clans.data.groups as gr


class AddToGroupDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add selected sequences")

        self.layout = QVBoxLayout()

        self.title = QLabel("Add the selected sequences to:")

        self.new_group_button = QRadioButton("Create a new group")
        self.new_group_button.setChecked(True)

        self.existing_group_button = QRadioButton("Choose an existing group")
        if len(cfg.groups_dict) == 0:
            self.existing_group_button.setEnabled(False)

        self.groups_combo = QComboBox()
        self.groups_combo.addItem("Select group")
        self.group_IDs_list = sorted(cfg.groups_dict.keys(), key=lambda k: cfg.groups_dict[k]['order'])

        for i in range(len(self.group_IDs_list)):
            group_ID = self.group_IDs_list[i]
            self.groups_combo.addItem(cfg.groups_dict[group_ID]['name'])
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

        # Set the size of the group names
        self.group_name_size_label = QLabel("Group name text size:")
        default_size = net_plot_object.text_size
        self.group_name_size = QComboBox()

        i = 0
        for size in range(5, 21):
            self.group_name_size.addItem(str(size))
            if size == int(default_size):
                default_index = i
            i += 1
        self.group_name_size.setCurrentIndex(default_index)

        self.layout.addWidget(self.group_name_size_label, 1, 0)
        self.layout.addWidget(self.group_name_size, 1, 1)

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

        self.layout.addLayout(self.bold_layout, 2, 0)
        self.layout.addLayout(self.italic_layout, 2, 1)

        # Set the color of the group's nodes
        self.color_label = QLabel("Color:")
        self.selected_color_label = QLabel(" ")
        self.selected_color = "black"
        self.rgb_color = "0,0,0,255"
        self.clans_color = "0;0;0;255"
        self.color_array = [0.0, 0.0, 0.0, 1.0]
        self.selected_color_label.setStyleSheet("background-color: " + self.selected_color)

        self.change_color_button = QPushButton("Change color")
        self.change_color_button.pressed.connect(self.change_color)

        self.layout.addWidget(self.color_label, 3, 0)
        self.layout.addWidget(self.selected_color_label, 3, 1)
        self.layout.addWidget(self.change_color_button, 3, 2)

        # Set the size of the group nodes
        self.size_label = QLabel("Data-points size:")
        default_size = net_plot_object.nodes_size
        self.group_size = QComboBox()

        i = 0
        for size in range(5, 21):
            self.group_size.addItem(str(size))
            if size == default_size:
                default_index = i
            i += 1
        self.group_size.setCurrentIndex(default_index)

        self.layout.addWidget(self.size_label, 4, 0)
        self.layout.addWidget(self.group_size, 4, 1)

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
            self.clans_color = str(red) + ";" + str(green) + ";" + str(blue) + ";255"
            self.rgb_color = color.rgb()
            self.color_array = [red/255, green/255, blue/255, 1.0]
            self.selected_color = hex
            self.selected_color_label.setStyleSheet("background-color: " + self.selected_color)

    def get_group_info(self):

        # Get the group name
        if self.name_widget.text() == "":
            group_name = self.default_group_name
        else:
            group_name = self.name_widget.text()

        # Get the selected size
        size = self.group_size.currentText()

        # Get the group name size
        group_name_size = self.group_name_size.currentText()

        return group_name, group_name_size, size, self.clans_color, self.rgb_color, self.color_array


class ManageGroupsDialog(QDialog):

    def __init__(self, net_plot_object, view, dim_num, z_index_mode):
        super().__init__()

        self.network_plot = net_plot_object
        self.view = view
        self.dim_num = dim_num
        self.z_index_mode = z_index_mode
        self.changed_order_flag = 0

        self.setWindowTitle("Manage groups")

        self.main_layout = QVBoxLayout()

        # Add a list widget of all the groups
        self.groups_list = QListWidget()

        self.group_IDs_list = sorted(cfg.groups_dict.keys(), key=lambda k: cfg.groups_dict[k]['order'])

        for i in range(len(self.group_IDs_list)):
            group_ID = self.group_IDs_list[i]
            name_str = cfg.groups_dict[group_ID]['name'] + " (" + str(len(cfg.groups_dict[group_ID]['seqIDs'])) + ")"
            item = QListWidgetItem(name_str)
            item_color = QColor(cfg.groups_dict[group_ID]['color_array'][0]*255,
                                cfg.groups_dict[group_ID]['color_array'][1]*255,
                                cfg.groups_dict[group_ID]['color_array'][2]*255)
            item.setForeground(item_color)
            self.groups_list.insertItem(i, item)

        self.main_layout.addWidget(self.groups_list)

        # Add a layout for buttons
        self.buttons_layout = QHBoxLayout()
        self.edit_group_button = QPushButton("Edit group")
        self.edit_group_button.released.connect(self.edit_group)

        self.delete_group_button = QPushButton("Delete group")
        self.delete_group_button.released.connect(self.delete_group)

        self.move_up_button = QPushButton("Move up")
        self.move_up_button.released.connect(self.move_up_group)

        self.move_down_button = QPushButton("Move down")
        self.move_down_button.released.connect(self.move_down_group)

        self.buttons_layout.addWidget(self.edit_group_button)
        self.buttons_layout.addWidget(self.delete_group_button)
        self.buttons_layout.addWidget(self.move_up_button)
        self.buttons_layout.addWidget(self.move_down_button)
        self.buttons_layout.addStretch()

        self.main_layout.addLayout(self.buttons_layout)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def edit_group(self):

        group_index = self.groups_list.currentRow()
        group_ID = self.group_IDs_list[group_index]

        edit_group_dlg = EditGroupDialog(group_ID, self.network_plot)

        if edit_group_dlg.exec_():
            group_name, group_size, group_name_size, clans_color, rgb_color, color_array, is_bold, is_italic, \
            removed_dict = self.get_group_info(edit_group_dlg, group_ID)

            # Update the group information in the main dict
            cfg.groups_dict[group_ID]['name'] = group_name
            cfg.groups_dict[group_ID]['size'] = group_size
            cfg.groups_dict[group_ID]['name_size'] = group_name_size
            cfg.groups_dict[group_ID]['color'] = clans_color
            cfg.groups_dict[group_ID]['color_rgb'] = rgb_color
            cfg.groups_dict[group_ID]['color_array'] = color_array
            cfg.groups_dict[group_ID]['is_bold'] = is_bold
            cfg.groups_dict[group_ID]['is_italic'] = is_italic

            # Update the removed sequences in the main dict
            for seq_index in removed_dict:
                if seq_index in cfg.groups_dict[group_ID]['seqIDs']:
                    del cfg.groups_dict[group_ID]['seqIDs'][seq_index]

            # Update the name and color of the list-item
            name_str = cfg.groups_dict[group_ID]['name'] + " (" + str(len(cfg.groups_dict[group_ID]['seqIDs'])) + ")"
            item = self.groups_list.currentItem()
            item.setText(name_str)
            item.setForeground(edit_group_dlg.color)

            # Update the plot with the removed sequences
            if len(removed_dict) > 0:
                self.network_plot.remove_from_group(removed_dict, self.dim_num, self.view, self.z_index_mode)

            # Update the plot with the new group parameters
            self.network_plot.edit_group_parameters(group_ID, self.view, self.dim_num, self.z_index_mode)

    def get_group_info(self, edit_group_dlg, group_ID):

        # Get the group name
        if edit_group_dlg.name_widget.text() == "":
            # Add an error popup
            group_name = cfg.groups_dict[group_ID]['name']
        else:
            group_name = edit_group_dlg.name_widget.text()

        # Get the selected size
        group_size = edit_group_dlg.group_size.currentText()

        # Get the group color
        group_color = edit_group_dlg.color
        rgb_color = group_color.rgb()
        clans_color = str(group_color.red()) + ";" + str(group_color.green()) + ";" + str(group_color.blue()) + ";255"
        color_array = [group_color.red() / 255, group_color.green() / 255, group_color.blue() / 255, 1.0]

        # Get the selected group-name size
        group_name_size = edit_group_dlg.group_name_size.currentText()

        # Get the bold and italic states
        is_bold = edit_group_dlg.bold_checkbox.isChecked()
        is_italic = edit_group_dlg.italic_checkbox.isChecked()

        # Get a dictionary of the sequences that were removed from the group
        removed_dict = edit_group_dlg.removed_seq_dict

        return group_name, group_size, group_name_size, clans_color, rgb_color, color_array, is_bold, is_italic, \
               removed_dict

    def delete_group(self):

        group_index = self.groups_list.currentRow()
        group_ID = self.group_IDs_list[group_index]
        seq_dict = cfg.groups_dict[group_ID]['seqIDs'].copy()

        # 1. Remove the sequences assigned to this group (they get '-1' assignment)
        gr.remove_from_group(seq_dict)

        # 2. Remove the group from the plot
        self.network_plot.delete_group(group_ID, seq_dict, self.view, self.dim_num, self.z_index_mode)

        # 3. Delete the group from the main groups dictionary
        gr.delete_group(group_ID)

        # Remove the group from the presented list
        self.groups_list.takeItem(group_index)

        # Update the group_IDs list after the deletion
        self.group_IDs_list = sorted(cfg.groups_dict.keys(), key=lambda k: cfg.groups_dict[k]['order'])

    def move_up_group(self):

        group_index = self.groups_list.currentRow()
        group_ID = self.group_IDs_list[group_index]

        # The group is already the first ->nothing to do
        if group_index == 0:
            return

        second_group_ID = self.group_IDs_list[group_index - 1]

        # Swap the groups in the groups list
        self.group_IDs_list[group_index - 1] = group_ID
        self.group_IDs_list[group_index] = second_group_ID

        # Swap the lines in the ListWidget
        current_item = self.groups_list.takeItem(group_index)
        self.groups_list.insertItem(group_index - 1, current_item)
        self.groups_list.setCurrentItem(current_item)

        # Update the order of the groups in the main groups dict
        cfg.groups_dict[group_ID]['order'] -= 1
        cfg.groups_dict[second_group_ID]['order'] += 1

        self.changed_order_flag = 1

    def move_down_group(self):
        group_index = self.groups_list.currentRow()
        group_ID = self.group_IDs_list[group_index]

        # The group is already the first ->nothing to do
        if group_index == len(self.group_IDs_list)-1:
            return

        second_group_ID = self.group_IDs_list[group_index + 1]

        # Swap the groups in the groups list
        self.group_IDs_list[group_index + 1] = group_ID
        self.group_IDs_list[group_index] = second_group_ID

        # Swap the lines in the ListWidget
        current_item = self.groups_list.takeItem(group_index)
        self.groups_list.insertItem(group_index + 1, current_item)
        self.groups_list.setCurrentItem(current_item)

        # Update the order of the groups in the main groups dict
        cfg.groups_dict[group_ID]['order'] += 1
        cfg.groups_dict[second_group_ID]['order'] -= 1

        self.changed_order_flag = 1


class EditGroupDialog(QDialog):

    def __init__(self, group_ID, net_plot_object):
        super().__init__()

        self.setWindowTitle("Edit group")

        self.main_layout = QVBoxLayout()
        self.parameters_layout = QHBoxLayout()
        self.grid_layout = QGridLayout()
        self.members_layout = QVBoxLayout()
        self.buttons_layout = QHBoxLayout()

        # Create the group parameters layout

        # Edit the group name
        self.name_label = QLabel("Group name:")
        self.name_widget = QLineEdit()
        self.name_widget.setPlaceholderText(cfg.groups_dict[group_ID]['name'])

        self.grid_layout.addWidget(self.name_label, 0, 0)
        self.grid_layout.addWidget(self.name_widget, 0, 1, 1, 2)

        # Set the size of the group names
        self.group_name_size_label = QLabel("Group name text size:")
        if cfg.groups_dict[group_ID]['name_size'] != "":
            default_size = cfg.groups_dict[group_ID]['name_size']
        else:
            default_size = net_plot_object.text_size
        self.group_name_size = QComboBox()

        i = 0
        for size in range(5, 21):
            self.group_name_size.addItem(str(size))
            if size == int(default_size):
                default_index = i
            i += 1
        self.group_name_size.setCurrentIndex(default_index)

        self.grid_layout.addWidget(self.group_name_size_label, 1, 0)
        self.grid_layout.addWidget(self.group_name_size, 1, 1)

        # Add Bold and Italic options
        self.bold_label = QLabel("Bold")
        self.bold_checkbox = QCheckBox()
        if net_plot_object.groups_text_visual[group_ID].bold is True:
            self.bold_checkbox.setChecked(True)
        self.bold_layout = QHBoxLayout()
        self.bold_layout.addWidget(self.bold_checkbox)
        self.bold_layout.addWidget(self.bold_label)
        self.bold_layout.addStretch()

        self.italic_label = QLabel("Italic")
        self.italic_checkbox = QCheckBox()
        if net_plot_object.groups_text_visual[group_ID].italic is True:
            self.italic_checkbox.setChecked(True)
        self.italic_layout = QHBoxLayout()
        self.italic_layout.addWidget(self.italic_checkbox)
        self.italic_layout.addWidget(self.italic_label)
        self.italic_layout.addStretch()

        self.grid_layout.addLayout(self.bold_layout, 2, 0)
        self.grid_layout.addLayout(self.italic_layout, 2, 1)

        # Set the color of the group's nodes and names
        self.color_label = QLabel("Group color:")
        self.color_box = QLabel(" ")
        self.color = QColor(cfg.groups_dict[group_ID]['color_array'][0] * 255,
                            cfg.groups_dict[group_ID]['color_array'][1] * 255,
                            cfg.groups_dict[group_ID]['color_array'][2] * 255)

        self.color_box.setStyleSheet("background-color: " + self.color.name())

        self.change_color_button = QPushButton("Change color")
        self.change_color_button.pressed.connect(self.change_color)

        self.grid_layout.addWidget(self.color_label, 3, 0)
        self.grid_layout.addWidget(self.color_box, 3, 1)
        self.grid_layout.addWidget(self.change_color_button, 3, 2)

        # Set the size of the group nodes
        self.size_label = QLabel("Data points size:")
        default_size = cfg.groups_dict[group_ID]['size']
        self.group_size = QComboBox()

        i = 0
        for size in range(5, 21):
            self.group_size.addItem(str(size))
            if size == int(default_size):
                default_index = i
            i += 1
        self.group_size.setCurrentIndex(default_index)

        self.grid_layout.addWidget(self.size_label, 4, 0)
        self.grid_layout.addWidget(self.group_size, 4, 1)

        self.parameters_layout.addLayout(self.grid_layout)
        self.parameters_layout.addStretch()

        # Create the group members layout

        self.removed_seq_dict = {}

        # Add a list widget of all the members of the group
        self.members_label = QLabel("Group members:")
        self.members_list = QListWidget()

        self.sorted_seq_list = sorted(cfg.groups_dict[group_ID]['seqIDs'])

        for i in range(len(self.sorted_seq_list)):
            name_str = str(self.sorted_seq_list[i]) + "  " + cfg.sequences_array['seq_title'][self.sorted_seq_list[i]][1:]
            item = QListWidgetItem(name_str)
            self.members_list.insertItem(i, item)

        self.remove_seq_button = QPushButton("Remove from group")
        self.remove_seq_button.released.connect(self.remove_from_group)

        self.members_layout.addWidget(self.members_label)
        self.members_layout.addWidget(self.members_list)

        self.buttons_layout.addWidget(self.remove_seq_button)
        self.buttons_layout.addStretch()
        self.members_layout.addLayout(self.buttons_layout)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addLayout(self.parameters_layout)
        self.main_layout.addLayout(self.members_layout)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def change_color(self):
        dialog = QColorDialog()
        if dialog.exec_():
            self.color = dialog.currentColor()
            self.color_box.setStyleSheet("background-color: " + self.color.name())

    def remove_from_group(self):
        row_index = self.members_list.currentRow()
        seq_index = self.sorted_seq_list[row_index]

        # Add the seq index to the removed dict
        self.removed_seq_dict[seq_index] = 1

        self.sorted_seq_list.remove(seq_index)
        self.members_list.takeItem(row_index)


class EditGroupNameDialog(QDialog):

    def __init__(self, group_ID, net_plot_object):
        super().__init__()

        self.group_ID = group_ID

        self.setWindowTitle("Edit group name")

        self.main_layout = QVBoxLayout()
        self.grid_layout = QGridLayout()

        # Create the group parameters layout

        # Edit the group name
        self.name_label = QLabel("Group name:")
        self.name_widget = QLineEdit()
        self.name_widget.setPlaceholderText(cfg.groups_dict[group_ID]['name'])

        self.grid_layout.addWidget(self.name_label, 0, 0)
        self.grid_layout.addWidget(self.name_widget, 0, 1, 1, 2)

        # Set the size of the group names
        self.group_name_size_label = QLabel("Text size:")
        if cfg.groups_dict[group_ID]['name_size'] != "":
            default_size = cfg.groups_dict[group_ID]['name_size']
        else:
            default_size = net_plot_object.text_size
        self.group_name_size = QComboBox()

        i = 0
        for size in range(5, 21):
            self.group_name_size.addItem(str(size))
            if size == int(default_size):
                default_index = i
            i += 1
        self.group_name_size.setCurrentIndex(default_index)

        self.grid_layout.addWidget(self.group_name_size_label, 1, 0)
        self.grid_layout.addWidget(self.group_name_size, 1, 1)

        # Set the color of the group's nodes
        self.color_label = QLabel("Color:")
        self.color_box = QLabel(" ")
        self.color = QColor(cfg.groups_dict[group_ID]['color_array'][0]*255,
                            cfg.groups_dict[group_ID]['color_array'][1]*255,
                            cfg.groups_dict[group_ID]['color_array'][2]*255)

        self.color_box.setStyleSheet("background-color: " + self.color.name())

        self.change_color_button = QPushButton("Change color")
        self.change_color_button.pressed.connect(self.change_color)

        self.grid_layout.addWidget(self.color_label, 2, 0)
        self.grid_layout.addWidget(self.color_box, 2, 1)
        self.grid_layout.addWidget(self.change_color_button, 2, 2)

        # Add Bold and Italic options
        self.bold_label = QLabel("Bold")
        self.bold_checkbox = QCheckBox()
        if net_plot_object.groups_text_visual[group_ID].bold is True:
            self.bold_checkbox.setChecked(True)
        self.bold_layout = QHBoxLayout()
        self.bold_layout.addWidget(self.bold_checkbox)
        self.bold_layout.addWidget(self.bold_label)
        self.bold_layout.addStretch()

        self.italic_label = QLabel("Italic")
        self.italic_checkbox = QCheckBox()
        if net_plot_object.groups_text_visual[group_ID].italic is True:
            self.italic_checkbox.setChecked(True)
        self.italic_layout = QHBoxLayout()
        self.italic_layout.addWidget(self.italic_checkbox)
        self.italic_layout.addWidget(self.italic_label)
        self.italic_layout.addStretch()

        self.grid_layout.addLayout(self.bold_layout, 3, 0)
        self.grid_layout.addLayout(self.italic_layout, 3, 1)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def change_color(self):
        dialog = QColorDialog()
        if dialog.exec_():
            self.color = dialog.currentColor()
            self.color_box.setStyleSheet("background-color: " + self.color.name())

    def get_group_info(self):

        # Get the group name
        if self.name_widget.text() == "":
            # Add an error popup
            group_name = cfg.groups_dict[self.group_ID]['name']
        else:
            group_name = self.name_widget.text()

        # Get the selected group-name size
        group_name_size = self.group_name_size.currentText()

        # Get the group color
        group_color = self.color
        rgb_color = group_color.rgb()
        clans_color = str(group_color.red()) + ";" + str(group_color.green()) + ";" + str(group_color.blue()) + ";255"
        color_array = [group_color.red() / 255, group_color.green() / 255, group_color.blue() / 255, 1.0]

        # Get the bold and italic states
        is_bold = self.bold_checkbox.isChecked()
        is_italic = self.italic_checkbox.isChecked()

        return group_name, group_name_size, clans_color, rgb_color, color_array, is_bold, is_italic





