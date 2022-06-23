from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from vispy.color import ColorArray
import numpy as np
import clans.config as cfg
import clans.clans.data.groups as gr


def error_occurred(method, method_name, exception_err, error_msg):

    if cfg.run_params['is_debug_mode']:
        print("\nError in " + method.__globals__['__file__'] + " (" + method_name + "):")
        print(exception_err)

    msg_box = QMessageBox()
    msg_box.setText(error_msg)
    if msg_box.exec_():
        return


class AddToGroupDialog(QDialog):

    def __init__(self, group_by):
        super().__init__()

        try:

            self.setWindowTitle("Add selected sequences")

            self.layout = QVBoxLayout()

            self.title = QLabel("Add the selected sequences to:")

            self.new_group_button = QRadioButton("Create a new group")
            self.new_group_button.setChecked(True)

            self.existing_group_button = QRadioButton("Choose an existing group")
            if len(cfg.groups_by_categories[group_by]['groups']) == 0:
                self.existing_group_button.setEnabled(False)

            self.groups_combo = QComboBox()
            self.groups_combo.addItem("Select group")
            self.group_IDs_list = sorted(cfg.groups_by_categories[group_by]['groups'].keys(),
                                        key=lambda k: cfg.groups_by_categories[group_by]['groups'][k]['order'])

            for i in range(len(self.group_IDs_list)):
                group_ID = self.group_IDs_list[i]
                self.groups_combo.addItem(cfg.groups_by_categories[group_by]['groups'][group_ID]['name'])
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

        except Exception as err:
            error_msg = "An error occurred: cannot init AddToGroupDialog"
            error_occurred(self.__init__, 'init', err, error_msg)

    def on_radio_button_change(self):
        try:
            if self.existing_group_button.isChecked():
                self.groups_combo.setEnabled(True)
            else:
                self.groups_combo.setEnabled(False)

        except Exception as err:
            error_msg = "An error occurred: cannot change selection"
            error_occurred(self.on_radio_button_change, 'on_radio_button_change', err, error_msg)

    def get_choice(self):
        try:
            if self.new_group_button.isChecked():
                return 'new', ''
            else:
                index = int(self.groups_combo.currentIndex() - 1)
                group_ID = self.group_IDs_list[index]
                return 'existing', group_ID
        except Exception as err:
            error_msg = "An error occurred: cannot get user selection"
            error_occurred(self.get_choice, 'get_choice', err, error_msg)


class CreateGroupDialog(QDialog):

    def __init__(self, group_by):
        super().__init__()

        try:
            self.setWindowTitle("Create group from selected")

            self.main_layout = QVBoxLayout()
            self.layout = QGridLayout()

            # Set the group name
            self.name_label = QLabel("Group name:")
            self.name_widget = QLineEdit()

            if len(cfg.groups_by_categories[group_by]['groups']) == 0:
                group_num = 1
            else:
                group_num = max(cfg.groups_by_categories[group_by]['groups'].keys()) + 1
            self.default_group_name = "Group_" + str(group_num)
            self.name_widget.setPlaceholderText(self.default_group_name)

            self.layout.addWidget(self.name_label, 0, 0)
            self.layout.addWidget(self.name_widget, 0, 1, 1, 2)

            # Set the size of the group names
            self.group_name_size_label = QLabel("Group name text size:")
            default_size = cfg.groups_by_categories[group_by]['text_size']
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
            default_size = cfg.groups_by_categories[group_by]['nodes_size']
            self.group_size = QComboBox()

            i = 0
            for size in range(4, 21):
                self.group_size.addItem(str(size))
                if size == default_size:
                    default_index = i
                i += 1
            self.group_size.setCurrentIndex(default_index)

            self.layout.addWidget(self.size_label, 4, 0)
            self.layout.addWidget(self.group_size, 4, 1)

            # Set the outline color of the group's nodes
            self.outline_color_label = QLabel("Data-points outline color:")
            self.outline_color_box = QLabel(" ")
            self.outline_color = ColorArray('black')
            self.outline_color_box.setStyleSheet("background-color: " + self.outline_color.hex[0])

            self.change_outline_color_button = QPushButton("Change color")
            self.change_outline_color_button.pressed.connect(self.change_outline_color)

            self.layout.addWidget(self.outline_color_label, 5, 0)
            self.layout.addWidget(self.outline_color_box, 5, 1)
            self.layout.addWidget(self.change_outline_color_button, 5, 2)

            # Add the OK/Cancel standard buttons
            self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.connect(self.reject)

            self.main_layout.addLayout(self.layout)
            self.main_layout.addWidget(self.button_box)
            self.setLayout(self.main_layout)

        except Exception as err:
            error_msg = "An error occurred: cannot init CreateGroupDialog"
            error_occurred(self.__init__, 'init', err, error_msg)

    def change_color(self):
        try:
            dialog = QColorDialog()
            if dialog.exec_():
                color = dialog.currentColor()
                red = color.red()
                green = color.green()
                blue = color.blue()
                hex = color.name()
                self.clans_color = str(red) + ";" + str(green) + ";" + str(blue) + ";255"
                self.color_array = [red/255, green/255, blue/255, 1.0]
                self.selected_color = hex
                self.selected_color_label.setStyleSheet("background-color: " + self.selected_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change color"
            error_occurred(self.change_color, 'change_color', err, error_msg)

    def change_outline_color(self):
        try:
            dialog = QColorDialog()

            if dialog.exec_():
                color = dialog.currentColor()
                hex_color = color.name()

                self.outline_color = ColorArray(hex_color)
                self.outline_color_box.setStyleSheet("background-color: " + hex_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change color"
            error_occurred(self.change_outline_color, 'change_outline_color', err, error_msg)

    def get_group_info(self):

        try:

            # Get the group name
            if self.name_widget.text() == "":
                group_name = self.default_group_name
            else:
                group_name = self.name_widget.text()

            # Get the selected size
            size = int(self.group_size.currentText())

            # Get the group name size
            group_name_size = int(self.group_name_size.currentText())

            is_bold = self.bold_checkbox.isChecked()
            is_italic = self.italic_checkbox.isChecked()

            return group_name, group_name_size, size, self.clans_color, self.color_array, is_bold, is_italic, \
                   self.outline_color.rgba[0]

        except Exception as err:
            error_msg = "An error occurred: cannot get the group's parameters"
            error_occurred(self.get_group_info, 'get_group_info', err, error_msg)


class ManageGroupsDialog(QDialog):

    def __init__(self, net_plot_object, view, dim_num, z_index_mode, color_by, group_by):
        super().__init__()

        self.network_plot = net_plot_object
        self.view = view
        self.dim_num = dim_num
        self.z_index_mode = z_index_mode
        self.color_by = color_by
        self.group_by = group_by
        self.changed_order_flag = 0

        self.setWindowTitle("Manage groups")

        self.main_layout = QVBoxLayout()

        # Add a list widget of all the groups
        self.groups_list = QListWidget()

        try:
            self.group_IDs_list = sorted(cfg.groups_by_categories[self.group_by]['groups'].keys(),
                                         key=lambda k: cfg.groups_by_categories[self.group_by]['groups'][k]['order'])

            for i in range(len(self.group_IDs_list)):
                group_ID = self.group_IDs_list[i]
                name_str = cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name'] + " (" + \
                           str(len(cfg.groups_by_categories[self.group_by]['groups'][group_ID]['seqIDs'])) + ")"
                item = QListWidgetItem(name_str)
                group_color = ColorArray(cfg.groups_by_categories[self.group_by]['groups'][group_ID]['color_array'])
                item_color = QColor(group_color.hex[0])
                item.setForeground(item_color)
                self.groups_list.insertItem(i, item)

        except Exception as err:
            error_msg = "An error occurred: cannot init ManageGroupsDialog"
            error_occurred(self.__init__, 'init', err, error_msg)
            return

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

        try:
            edit_group_dlg = EditGroupDialog(self.group_by, group_ID)
        except Exception as err:
            error_msg = "An error occurred: cannot create EditGroupDialog object"
            error_occurred(self.edit_group, 'edit_group', err, error_msg)
            return

        if edit_group_dlg.exec_():

            try:
                group_name, group_size, group_name_size, clans_color, color_array, outline_color, is_bold, is_italic, \
                removed_dict = self.get_group_info(edit_group_dlg, group_ID)
            except Exception as err:
                error_msg = "An error occurred: cannot get group's parameters"
                error_occurred(self.get_group_info, 'get_group_info', err, error_msg)
                return

            try:
                # Update the group information in the main dict
                cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name'] = group_name
                cfg.groups_by_categories[self.group_by]['groups'][group_ID]['size'] = group_size
                cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name_size'] = group_name_size
                cfg.groups_by_categories[self.group_by]['groups'][group_ID]['color'] = clans_color
                cfg.groups_by_categories[self.group_by]['groups'][group_ID]['color_array'] = color_array
                cfg.groups_by_categories[self.group_by]['groups'][group_ID]['outline_color'] = outline_color
                cfg.groups_by_categories[self.group_by]['groups'][group_ID]['is_bold'] = is_bold
                cfg.groups_by_categories[self.group_by]['groups'][group_ID]['is_italic'] = is_italic

                # Update the removed sequences in the main dict
                for seq_index in removed_dict:
                    if seq_index in cfg.groups_by_categories[self.group_by]['groups'][group_ID]['seqIDs']:
                        del cfg.groups_by_categories[self.group_by]['groups'][group_ID]['seqIDs'][seq_index]

                # Update the name and color of the list-item
                name_str = cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name'] + " (" + \
                        str(len(cfg.groups_by_categories[self.group_by]['groups'][group_ID]['seqIDs'])) + ")"
                item = self.groups_list.currentItem()
                item.setText(name_str)
                item.setForeground(QColor(edit_group_dlg.color.hex[0]))

            except Exception as err:
                error_msg = "An error occurred while updating the group's parameters"
                error_occurred(self.edit_group, 'edit_group', err, error_msg)
                return

            # Update the plot with the removed sequences
            if len(removed_dict) > 0:
                try:
                    self.network_plot.remove_from_group(removed_dict, self.dim_num, self.z_index_mode, self.color_by,
                                                        self.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot remove sequences from group"
                    error_occurred(self.network_plot.remove_from_group, 'remove_from_group', err, error_msg)

            # Update the plot with the new group parameters
            try:
                self.network_plot.edit_group_parameters(group_ID, self.dim_num, self.z_index_mode, self.color_by,
                                                        self.group_by)
            except Exception as err:
                error_msg = "An error occurred: cannot update group parameters"
                error_occurred(self.network_plot.edit_group_parameters, 'edit_group_parameters', err, error_msg)

    def get_group_info(self, edit_group_dlg, group_ID):

        # Get the group name
        if edit_group_dlg.name_widget.text() == "":
            # Add an error popup
            group_name = cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name']
        else:
            group_name = edit_group_dlg.name_widget.text()

        # Get the selected size
        group_size = int(edit_group_dlg.group_size.currentText())

        # Get the group color
        group_color = edit_group_dlg.color
        clans_color = str(group_color.RGBA[0][0]) + ";" + str(group_color.RGBA[0][1]) + ";" + \
                      str(group_color.RGBA[0][2]) + ";255"
        color_array = group_color.rgba[0]
        outline_color = edit_group_dlg.outline_color.rgba[0]

        # Get the selected group-name size
        group_name_size = int(edit_group_dlg.group_name_size.currentText())

        # Get the bold and italic states
        is_bold = edit_group_dlg.bold_checkbox.isChecked()
        is_italic = edit_group_dlg.italic_checkbox.isChecked()

        # Get a dictionary of the sequences that were removed from the group
        removed_dict = edit_group_dlg.removed_seq_dict

        return group_name, group_size, group_name_size, clans_color, color_array, outline_color, is_bold, is_italic, \
               removed_dict

    def delete_group(self):

        group_index = self.groups_list.currentRow()
        group_ID = self.group_IDs_list[group_index]
        seq_dict = cfg.groups_by_categories[self.group_by]['groups'][group_ID]['seqIDs'].copy()

        # 1. Remove the sequences assigned to this group (they get '-1' assignment)
        try:
            gr.remove_from_group(seq_dict)
        except Exception as err:
            error_msg = "An error occurred: cannot remove sequences from group"
            error_occurred(gr.remove_from_group, 'remove_from_group', err, error_msg)
            return

        # 2. Remove the group from the plot
        try:
            self.network_plot.delete_group(group_ID, seq_dict, self.dim_num, self.z_index_mode, self.color_by,
                                           self.group_by)
        except Exception as err:
            error_msg = "An error occurred: cannot delete the group from the graph"
            error_occurred(self.network_plot.delete_group, 'delete_group', err, error_msg)
            return

        # 3. Delete the group from the main groups dictionary
        try:
            gr.delete_group(self.group_by, group_ID)
        except Exception as err:
            error_msg = "An error occurred: cannot delete the group"
            error_occurred(gr.delete_group, 'delete_group', err, error_msg)
            return

        try:
            # Remove the group from the presented list
            self.groups_list.takeItem(group_index)

            # Update the group_IDs list after the deletion
            self.group_IDs_list = sorted(cfg.groups_by_categories[self.group_by]['groups'].keys(),
                                         key=lambda k: cfg.groups_by_categories[self.group_by]['groups'][k]['order'])
        except Exception as err:
            error_msg = "An error occurred: cannot delete the group"
            error_occurred(self.delete_group, 'delete_group', err, error_msg)

    def move_up_group(self):

        try:
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
            cfg.groups_by_categories[self.group_by]['groups'][group_ID]['order'] -= 1
            cfg.groups_by_categories[self.group_by]['groups'][second_group_ID]['order'] += 1

            self.changed_order_flag = 1

        except Exception as err:
            error_msg = "An error occurred: cannot move the group up"
            error_occurred(self.move_up_group, 'move_up_group', err, error_msg)

    def move_down_group(self):

        try:
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
            cfg.groups_by_categories[self.group_by]['groups'][group_ID]['order'] += 1
            cfg.groups_by_categories[self.group_by]['groups'][second_group_ID]['order'] -= 1

            self.changed_order_flag = 1

        except Exception as err:
            error_msg = "An error occurred: cannot move the group down"
            error_occurred(self.move_down_group, 'move_down_group', err, error_msg)


class EditGroupDialog(QDialog):

    def __init__(self, group_by, group_ID):
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
        self.name_widget.setPlaceholderText(cfg.groups_by_categories[group_by]['groups'][group_ID]['name'])

        self.grid_layout.addWidget(self.name_label, 0, 0)
        self.grid_layout.addWidget(self.name_widget, 0, 1, 1, 2)

        # Set the size of the group names
        self.group_name_size_label = QLabel("Group name text size:")
        if cfg.groups_by_categories[group_by]['groups'][group_ID]['name_size'] != "":
            default_size = cfg.groups_by_categories[group_by]['groups'][group_ID]['name_size']
        else:
            default_size = cfg.groups_by_categories[group_by]['text_size']
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
        if cfg.groups_by_categories[group_by]['groups'][group_ID]['is_bold'] is True:
            self.bold_checkbox.setChecked(True)
        self.bold_layout = QHBoxLayout()
        self.bold_layout.addWidget(self.bold_checkbox)
        self.bold_layout.addWidget(self.bold_label)
        self.bold_layout.addStretch()

        self.italic_label = QLabel("Italic")
        self.italic_checkbox = QCheckBox()
        if cfg.groups_by_categories[group_by]['groups'][group_ID]['is_italic'] is True:
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
        self.color = ColorArray(cfg.groups_by_categories[group_by]['groups'][group_ID]['color_array'])
        self.color_box.setStyleSheet("background-color: " + self.color.hex[0])

        self.change_color_button = QPushButton("Change color")
        self.change_color_button.pressed.connect(self.change_color)

        self.grid_layout.addWidget(self.color_label, 3, 0)
        self.grid_layout.addWidget(self.color_box, 3, 1)
        self.grid_layout.addWidget(self.change_color_button, 3, 2)

        # Set the size of the group nodes
        self.size_label = QLabel("Data points size:")
        default_size = cfg.groups_by_categories[group_by]['groups'][group_ID]['size']
        self.group_size = QComboBox()

        i = 0
        for size in range(4, 21):
            self.group_size.addItem(str(size))
            if size == int(default_size):
                default_index = i
            i += 1
        self.group_size.setCurrentIndex(default_index)

        self.grid_layout.addWidget(self.size_label, 4, 0)
        self.grid_layout.addWidget(self.group_size, 4, 1)

        # Set the outline color of the group's nodes
        self.outline_color_label = QLabel("Data-points outline color:")
        self.outline_color_box = QLabel(" ")
        self.outline_color = ColorArray(cfg.groups_by_categories[group_by]['groups'][group_ID]['outline_color'])
        self.outline_color_box.setStyleSheet("background-color: " + self.outline_color.hex[0])

        self.change_outline_color_button = QPushButton("Change color")
        self.change_outline_color_button.pressed.connect(self.change_outline_color)

        self.grid_layout.addWidget(self.outline_color_label, 5, 0)
        self.grid_layout.addWidget(self.outline_color_box, 5, 1)
        self.grid_layout.addWidget(self.change_outline_color_button, 5, 2)

        self.parameters_layout.addLayout(self.grid_layout)
        self.parameters_layout.addStretch()

        # Create the group members layout

        self.removed_seq_dict = {}

        # Add a list widget of all the members of the group
        self.members_label = QLabel("Group members:")
        self.members_list = QListWidget()

        self.sorted_seq_list = sorted(cfg.groups_by_categories[group_by]['groups'][group_ID]['seqIDs'])

        for i in range(len(self.sorted_seq_list)):
            name_str = str(self.sorted_seq_list[i]) + "  " + \
                       cfg.sequences_array['seq_title'][self.sorted_seq_list[i]][1:]
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
        try:
            dialog = QColorDialog()
            if dialog.exec_():
                color = dialog.currentColor()
                hex_color = color.name()
                self.color = ColorArray(hex_color)
                self.color_box.setStyleSheet("background-color: " + hex_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change color"
            error_occurred(self.change_color, 'change_color', err, error_msg)

    def change_outline_color(self):
        try:
            dialog = QColorDialog()
            if dialog.exec_():
                color = dialog.currentColor()
                hex_color = color.name()
                self.outline_color = ColorArray(hex_color)
                self.outline_color_box.setStyleSheet("background-color: " + hex_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change outline color"
            error_occurred(self.change_outline_color, 'change_outline_color', err, error_msg)

    def remove_from_group(self):
        try:
            row_index = self.members_list.currentRow()
            seq_index = self.sorted_seq_list[row_index]

            # Add the seq index to the removed dict
            self.removed_seq_dict[seq_index] = 1

            self.sorted_seq_list.remove(seq_index)
            self.members_list.takeItem(row_index)

        except Exception as err:
            error_msg = "An error occurred: cannot remove sequence from group"
            error_occurred(self.remove_from_group, 'remove_from_group', err, error_msg)


class EditGroupNameDialog(QDialog):

    def __init__(self, group_by, group_ID):
        super().__init__()

        self.group_ID = group_ID
        self.group_by = group_by

        self.setWindowTitle("Edit group name")

        self.main_layout = QVBoxLayout()
        self.grid_layout = QGridLayout()

        # Create the group parameters layout

        # Edit the group name
        self.name_label = QLabel("Group name:")
        self.name_widget = QLineEdit()
        self.name_widget.setPlaceholderText(cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name'])

        self.grid_layout.addWidget(self.name_label, 0, 0)
        self.grid_layout.addWidget(self.name_widget, 0, 1, 1, 2)

        # Set the size of the group names
        self.group_name_size_label = QLabel("Text size:")
        if cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name_size'] != "":
            default_size = cfg.groups_by_categories[self.group_by]['groups'][group_ID]['name_size']
        else:
            default_size = cfg.groups_by_categories[self.group_by]['text_size']
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
        self.color = QColor(cfg.groups_by_categories[self.group_by]['groups'][group_ID]['color_array'][0] * 255,
                            cfg.groups_by_categories[self.group_by]['groups'][group_ID]['color_array'][1] * 255,
                            cfg.groups_by_categories[self.group_by]['groups'][group_ID]['color_array'][2] * 255)

        self.color_box.setStyleSheet("background-color: " + self.color.name())

        self.change_color_button = QPushButton("Change color")
        self.change_color_button.pressed.connect(self.change_color)

        self.grid_layout.addWidget(self.color_label, 2, 0)
        self.grid_layout.addWidget(self.color_box, 2, 1)
        self.grid_layout.addWidget(self.change_color_button, 2, 2)

        # Add Bold and Italic options
        self.bold_label = QLabel("Bold")
        self.bold_checkbox = QCheckBox()
        if cfg.groups_by_categories[self.group_by]['groups'][group_ID]['is_bold']:
            self.bold_checkbox.setChecked(True)
        self.bold_layout = QHBoxLayout()
        self.bold_layout.addWidget(self.bold_checkbox)
        self.bold_layout.addWidget(self.bold_label)
        self.bold_layout.addStretch()

        self.italic_label = QLabel("Italic")
        self.italic_checkbox = QCheckBox()
        if cfg.groups_by_categories[self.group_by]['groups'][group_ID]['is_italic']:
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
            group_name = cfg.groups_by_categories[self.group_by]['groups'][self.group_ID]['name']
        else:
            group_name = self.name_widget.text()

        # Get the selected group-name size
        group_name_size = int(self.group_name_size.currentText())

        # Get the group color
        group_color = self.color
        clans_color = str(group_color.red()) + ";" + str(group_color.green()) + ";" + str(group_color.blue()) + ";255"
        color_array = [group_color.red() / 255, group_color.green() / 255, group_color.blue() / 255, 1.0]

        # Get the bold and italic states
        is_bold = self.bold_checkbox.isChecked()
        is_italic = self.italic_checkbox.isChecked()

        return group_name, group_name_size, clans_color, color_array, is_bold, is_italic


class EditCategoriesDialog(QDialog):

    def __init__(self, net_plot_object, dim_num, z_index_mode, color_by, group_by):
        super().__init__()

        self.net_plot_object = net_plot_object
        self.dim_num = dim_num
        self.z_index_mode = z_index_mode
        self.color_by = color_by
        self.group_by = group_by

        self.setWindowTitle("Edit grouping categories")

        self.main_layout = QVBoxLayout()

        # Add a list widget of all the groups
        self.categories_list = QListWidget()

        for category_index in range(1, len(cfg.groups_by_categories)):
            item = QListWidgetItem(cfg.groups_by_categories[category_index]['name'])
            self.categories_list.insertItem(category_index, item)

        self.main_layout.addWidget(self.categories_list)

        # Add a layout for buttons
        self.buttons_layout = QHBoxLayout()

        self.edit_button = QPushButton("Edit category")
        self.edit_button.released.connect(self.edit_category)

        self.move_up_button = QPushButton("Move up")
        self.move_up_button.released.connect(self.move_up_category)

        self.move_down_button = QPushButton("Move down")
        self.move_down_button.released.connect(self.move_down_category)

        self.delete_category_button = QPushButton("Delete category")
        self.delete_category_button.released.connect(self.delete_category)

        self.buttons_layout.addWidget(self.edit_button)
        self.buttons_layout.addWidget(self.move_up_button)
        self.buttons_layout.addWidget(self.move_down_button)
        self.buttons_layout.addWidget(self.delete_category_button)
        self.buttons_layout.addStretch()

        self.main_layout.addLayout(self.buttons_layout)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def edit_category(self):
        category_in_list_index = self.categories_list.currentRow()  # The index of the category in the list
        category_index = category_in_list_index + 1  # The list doesn't include the default entry ('Manual definition')

        try:
            edit_category_dlg = EditCategoryDialog(category_index)
        except Exception as err:
            error_msg = "An error occurred: cannot create EditCategoryDialog object"
            error_occurred(self.edit_category, 'edit_category', err, error_msg)
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

                # Update the category name in the QListWidget
                item = self.categories_list.currentItem()
                item.setText(category_name)

                # Update the category name in the main list
                cfg.groups_by_categories[category_index]['name'] = category_name

            is_changed_points_size = 0
            is_changed_names_size = 0
            is_changed_outline_color = 0
            is_changed_bold = 0
            is_changed_italic= 0

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

            # Update only the changed parameters in the group definitions
            for group_ID in cfg.groups_by_categories[category_index]['groups']:

                if is_changed_points_size:
                    cfg.groups_by_categories[category_index]['groups'][group_ID]['size'] = points_size

                if is_changed_names_size:
                    cfg.groups_by_categories[category_index]['groups'][group_ID]['name_size'] = names_size

                if is_changed_outline_color:
                    cfg.groups_by_categories[category_index]['groups'][group_ID]['outline_color'] = outline_color

                if is_changed_bold:
                    cfg.groups_by_categories[category_index]['groups'][group_ID]['is_bold'] = is_bold

                if is_changed_italic:
                    cfg.groups_by_categories[category_index]['groups'][group_ID]['is_italic'] = is_italic

            # If the edited category is currently presented -> update the graph
            if category_index == self.group_by:
                try:
                    self.net_plot_object.hide_group_names()
                except Exception as err:
                    error_msg = "An error occurred: cannot hide the group names"
                    error_occurred(self.net_plot_object.hide_group_names, 'hide_group_names', err, error_msg)
                    return

                try:
                    self.net_plot_object.update_group_by(self.dim_num, self.z_index_mode, self.color_by, self.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot update the grouping-category"
                    error_occurred(self.net_plot_object.update_group_by, 'update_group_by', err, error_msg)

    def delete_category(self):

        category_in_list_index = self.categories_list.currentRow()  # The index of the category in the list
        category_index = category_in_list_index + 1  # The list doesn't include the default entry ('Manual definition')

        try:
            gr.delete_grouping_category(category_index)
        except Exception as err:
            error_msg = "An error occurred: cannot delete the grouping-category"
            error_occurred(gr.delete_grouping_category, 'delete_grouping_category', err, error_msg)
            return

        # Remove the group from the presented list
        self.categories_list.takeItem(category_in_list_index)

    def move_up_category(self):

        try:
            category_in_list_index = self.categories_list.currentRow()  # The index of the category in the list
            category_index = category_in_list_index + 1  # The list doesn't include the default entry ('Manual definition')

            # The category is already the first -> nothing to do
            if category_in_list_index == 0:
                return

            # Swap the lines in the ListWidget
            current_item = self.categories_list.takeItem(category_in_list_index)
            self.categories_list.insertItem(category_in_list_index-1, current_item)
            self.categories_list.setCurrentItem(current_item)

            # Swap the categories in the main list
            popped_dict = cfg.groups_by_categories.pop(category_index)
            cfg.groups_by_categories.insert(category_index-1, popped_dict)

        except Exception as err:
            error_msg = "An error occurred: cannot move the category up"
            error_occurred(self.move_up_category, 'move_up_category', err, error_msg)

    def move_down_category(self):

        try:
            category_in_list_index = self.categories_list.currentRow()  # The index of the category in the list
            category_index = category_in_list_index + 1  # The list doesn't include the default entry ('Manual definition')

            # The category is already the last -> nothing to do
            if category_index == len(cfg.groups_by_categories) - 1:
                return

            # Swap the lines in the ListWidget
            current_item = self.categories_list.takeItem(category_in_list_index)
            self.categories_list.insertItem(category_in_list_index+1, current_item)
            self.categories_list.setCurrentItem(current_item)

            # Swap the categories in the main list
            popped_dict = cfg.groups_by_categories.pop(category_index)
            cfg.groups_by_categories.insert(category_index+1, popped_dict)

        except Exception as err:
            error_msg = "An error occurred: cannot move the category down"
            error_occurred(self.move_down_category, 'move_down_category', err, error_msg)

    def get_current_category(self):

        category_index = self.categories_list.currentRow() + 1
        return category_index


class EditCategoryDialog(QDialog):

    def __init__(self, category_index):
        super().__init__()

        self.setWindowTitle("Edit category name")

        self.main_layout = QVBoxLayout()
        self.grid_layout = QGridLayout()

        # Edit the group name
        self.name_label = QLabel("Grouping category name:")
        self.name_widget = QLineEdit()
        self.name_widget.setPlaceholderText(cfg.groups_by_categories[category_index]['name'])

        self.grid_layout.addWidget(self.name_label, 0, 0)
        self.grid_layout.addWidget(self.name_widget, 0, 1)

        self.group_params_label = QLabel("General parameters for the groups:")
        self.grid_layout.addWidget(self.group_params_label, 1, 0, 1, 3)

        # Set the data points size
        self.points_size_label = QLabel("Data-points size:")
        default_size = cfg.groups_by_categories[category_index]['nodes_size']
        self.points_size_combo = QComboBox()

        i = 0
        for size in range(4, 21):
            self.points_size_combo.addItem(str(size))
            if size == default_size:
                default_index = i
            i += 1
        self.points_size_combo.setCurrentIndex(default_index)

        self.grid_layout.addWidget(self.points_size_label, 2, 0)
        self.grid_layout.addWidget(self.points_size_combo, 2, 1)

        self.outline_color_label = QLabel("Outline color:")
        self.outline_color = ColorArray(cfg.groups_by_categories[category_index]['nodes_outline_color'])
        self.outline_color_box = QLabel(" ")
        self.outline_color_box.setStyleSheet("background-color: " + self.outline_color.hex[0])
        self.outline_color_button = QPushButton("Change color")
        self.outline_color_button.pressed.connect(self.change_outline_color)

        self.grid_layout.addWidget(self.outline_color_label, 3, 0)
        self.grid_layout.addWidget(self.outline_color_box, 3, 1)
        self.grid_layout.addWidget(self.outline_color_button, 3, 2)

        self.outline_width_label = QLabel("Outline width:")
        self.outline_width_combo = QComboBox()

        i = 0
        width_options = np.arange(0, 3.5, 0.5)
        for size in width_options:
            self.outline_width_combo.addItem(str(size))
            if size == cfg.groups_by_categories[category_index]['nodes_outline_width']:
                default_index = i
            i += 1
        self.outline_width_combo.setCurrentIndex(default_index)

        self.grid_layout.addWidget(self.outline_width_label, 4, 0)
        self.grid_layout.addWidget(self.outline_width_combo, 4, 1)

        # Set the size of the group names
        self.group_name_size_label = QLabel("Group names text size:")
        default_size = cfg.groups_by_categories[category_index]['text_size']
        self.group_name_size = QComboBox()

        i = 0
        for size in range(5, 21):
            self.group_name_size.addItem(str(size))
            if size == int(default_size):
                default_index = i
            i += 1
        self.group_name_size.setCurrentIndex(default_index)

        self.grid_layout.addWidget(self.group_name_size_label, 5, 0)
        self.grid_layout.addWidget(self.group_name_size, 5, 1)

        # Add Bold and Italic options
        self.bold_label = QLabel("Bold")
        self.bold_checkbox = QCheckBox()
        self.bold_checkbox.setChecked(cfg.groups_by_categories[category_index]['is_bold'])
        self.bold_layout = QHBoxLayout()
        self.bold_layout.addWidget(self.bold_checkbox)
        self.bold_layout.addWidget(self.bold_label)
        self.bold_layout.addStretch()

        self.italic_label = QLabel("Italic")
        self.italic_checkbox = QCheckBox()
        self.italic_checkbox.setChecked(cfg.groups_by_categories[category_index]['is_italic'])
        self.italic_layout = QHBoxLayout()
        self.italic_layout.addWidget(self.italic_checkbox)
        self.italic_layout.addWidget(self.italic_label)
        self.italic_layout.addStretch()

        self.grid_layout.addLayout(self.bold_layout, 6, 0)
        self.grid_layout.addLayout(self.italic_layout, 6, 1)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def change_outline_color(self):

        try:
            dialog = QColorDialog()

            if dialog.exec_():
                color = dialog.currentColor()
                hex_color = color.name()

                self.outline_color = ColorArray(hex_color)
                self.outline_color_box.setStyleSheet("background-color: " + hex_color)

        except Exception as err:
            error_msg = "An error occurred: cannot change the outline color"
            error_occurred(self.change_outline_color, 'change_outline_color', err, error_msg)

    def get_info(self):

        name = self.name_widget.text()
        points_size = int(self.points_size_combo.currentText())
        outline_color = self.outline_color.rgba[0]
        outline_width = float(self.outline_width_combo.currentText())
        group_names_size = int(self.group_name_size.currentText())
        is_bold = self.bold_checkbox.isChecked()
        is_italic = self.italic_checkbox.isChecked()

        return name, points_size, outline_color, outline_width, group_names_size, is_bold, is_italic





