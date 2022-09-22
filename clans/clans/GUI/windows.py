from PyQt5.QtWidgets import *
from vispy import scene, util
import re
import numpy as np
from PIL import Image
import clans.config as cfg
import clans.clans.graphics.network3d as net
import clans.clans.graphics.colors as colors


def error_occurred(method, method_name, exception_err, error_msg):

    if cfg.run_params['is_debug_mode']:
        print("\nError in " + method.__globals__['__file__'] + " (" + method_name + "):")
        print(exception_err)

    msg_box = QMessageBox()
    msg_box.setText(error_msg)
    if msg_box.exec_():
        return


class AboutWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.is_visible = 0

        self.layout = QVBoxLayout()

        self.setWindowTitle("About CLANS")
        self.setGeometry(400, 100, 300, 150)

        self.version_label = QLabel("Version: " + cfg.version)
        self.version_label.setStyleSheet("color: maroon")

        self.overview_label = QLabel("CLANS 2.0 is a Python-based program for clustering sequences in the 2D or 3D "
                                     "space,\nbased on their sequence similarities.\n"
                                     "CLANS visualizes the dynamic clustering process and enables the user\n"
                                     "to interactively control it and explore the cluster map in various ways.")

        self.layout.addWidget(self.version_label)
        self.layout.addWidget(self.overview_label)

        self.setLayout(self.layout)

    def open_window(self):
        try:
            self.is_visible = 1
            self.show()
        except Exception as err:
            error_msg = "An error occurred: cannot open the 'About CLANS' window"
            error_occurred(self.open_window, 'open_window', err, error_msg)

    def close_window(self):
        try:
            self.is_visible = 0
            self.close()

        except Exception as err:
            error_msg = "An error occurred: cannot close the 'About CLANS' window"
            error_occurred(self.close_window, 'close_window', err, error_msg)


class SelectedSeqWindow(QWidget):

    def __init__(self, main_window, net_plot):
        super().__init__()

        self.main_window_object = main_window
        self.net_plot_object = net_plot

        self.sorted_seq_indices = []
        self.items = []

        self.is_visible = 0

        self.main_layout = QVBoxLayout()

        self.setWindowTitle("Selected Subset")
        self.setGeometry(600, 150, 600, 400)

        # Add a message for the number of selected sequences on top
        self.message = QLabel("")
        self.message.setStyleSheet("color: maroon;")

        self.main_layout.addWidget(self.message)

        # Add a list widget to display the sequences
        self.seq_list = QListWidget()
        self.seq_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.main_layout.addWidget(self.seq_list)

        # Add a layout for buttons
        self.buttons_layout = QHBoxLayout()

        self.highlight_button = QPushButton("Highlight in graph")
        self.highlight_button.setCheckable(True)
        self.highlight_button.released.connect(self.highlight_points)

        self.remove_button = QPushButton("Remove from subset")
        self.remove_button.released.connect(self.remove_from_selected)

        self.keep_selected_button = QPushButton("Set as selected subset")
        self.keep_selected_button.released.connect(self.keep_selected)

        self.find_button = QPushButton("Find in subset")
        self.find_button.released.connect(self.find_in_subset)

        self.close_button = QPushButton("Close")
        self.close_button.released.connect(self.close_window)

        self.buttons_layout.addWidget(self.highlight_button)
        self.buttons_layout.addWidget(self.keep_selected_button)
        self.buttons_layout.addWidget(self.remove_button)
        self.buttons_layout.addWidget(self.find_button)
        self.buttons_layout.addWidget(self.close_button)
        self.buttons_layout.addStretch()

        self.main_layout.addLayout(self.buttons_layout)

        self.setLayout(self.main_layout)

        self.seq_list.itemSelectionChanged.connect(self.highlight_points)

    def open_window(self):
        try:
            self.is_visible = 1
            self.show()
        except Exception as err:
            error_msg = "An error occurred: cannot open the selected sequences window"
            error_occurred(self.open_window, 'open_window', err, error_msg)

    def close_window(self):
        try:
            self.highlight_button.setChecked(False)

            try:
                self.highlight_points()
            except Exception as err:
                error_msg = "An error occurred: cannot turn off points highlighting"
                error_occurred(self.highlight_points, 'highlight_points', err, error_msg)

            self.is_visible = 0
            self.close()

        except Exception as err:
            error_msg = "An error occurred: cannot close the selected sequences window"
            error_occurred(self.close_window, 'close_window', err, error_msg)

    def update_window_title(self, file_name):

        self.setWindowTitle("Selected Subset from " + file_name)

    def update_sequences(self):

        self.highlight_button.setChecked(False)

        try:
            self.highlight_points()
        except Exception as err:
            error_msg = "An error occurred: cannot highlight data-points"
            error_occurred(self.highlight_points, 'highlight_points', err, error_msg)
            return

        self.seq_list.clear()
        self.items = []

        self.sorted_seq_indices = sorted(self.net_plot_object.selected_points)

        # There is at least one selected sequence
        if len(self.sorted_seq_indices) > 0:
            for i in range(len(self.sorted_seq_indices)):
                seq_index = self.sorted_seq_indices[i]
                seq_title = cfg.sequences_array[seq_index]['seq_ID'][0:]

                # The sequence header is the same as the index -> display only once
                if str(seq_index) == seq_title:
                    line_str = str(seq_index)
                else:
                    line_str = str(seq_index) + "  " + seq_title

                self.items.append(QListWidgetItem(line_str))
                self.seq_list.insertItem(i, self.items[i])

                self.message.setText("Displaying " + str(len(self.sorted_seq_indices)) + " selected sequences")

        else:
            self.message.setText("No selected sequences")

    def clear_list(self):

        try:
            self.seq_list.clear()
            self.sorted_seq_indices = []
            self.items = []
            self.highlight_button.setChecked(False)
            self.message.setText("")

        except Exception as err:
            error_msg = "An error occurred: cannot clear the sequences list"
            error_occurred(self.clear_list, 'clear_list', err, error_msg)

    def highlight_points(self):

        try:
            selected_indices = {}
            not_selected_indices = {}

            for item in self.seq_list.selectedIndexes():
                row_index = item.row()
                selected_indices[self.sorted_seq_indices[row_index]] = 1

            for seq_index in self.sorted_seq_indices:
                if seq_index not in selected_indices:
                    not_selected_indices[seq_index] = 1

            if len(selected_indices) > 0:

                # Highlight button is checked
                if self.highlight_button.isChecked():

                    # Highlight the selected points
                    try:
                        self.net_plot_object.highlight_selected_points(selected_indices, self.main_window_object.dim_num,
                                                                       self.main_window_object.z_indexing_mode,
                                                                       self.main_window_object.color_by,
                                                                       self.main_window_object.group_by)
                    except Exception as err:
                        error_msg = "An error occurred: cannot highlight the selected points"
                        error_occurred(self.net_plot_object.highlight_selected_points, 'highlight_selected_points', err,
                                       error_msg)
                        return

                    # Turn off all the rest (not selected)
                    try:
                        self.net_plot_object.unhighlight_selected_points(not_selected_indices,
                                                                         self.main_window_object.dim_num,
                                                                         self.main_window_object.z_indexing_mode,
                                                                         self.main_window_object.color_by,
                                                                         self.main_window_object.group_by)
                    except Exception as err:
                        error_msg = "An error occurred: cannot turn off highlighting"
                        error_occurred(self.net_plot_object.unhighlight_selected_points, 'unhighlight_selected_points', err,
                                       error_msg)

                # Turn off highlighting of all selected sequences (back to normal selected presentation)
                else:
                    try:
                        self.net_plot_object.unhighlight_selected_points(self.sorted_seq_indices,
                                                                         self.main_window_object.dim_num,
                                                                         self.main_window_object.z_indexing_mode,
                                                                         self.main_window_object.color_by,
                                                                         self.main_window_object.group_by)
                    except Exception as err:
                        error_msg = "An error occurred: cannot turn off highlighting"
                        error_occurred(self.net_plot_object.unhighlight_selected_points, 'unhighlight_selected_points',
                                       err, error_msg)

        except Exception as err:
            error_msg = "An error occurred: cannot turn highlight points"
            error_occurred(self.highlight_points, 'highlight_points', err, error_msg)

    def keep_selected(self):

        try:
            selected_indices = {}
            not_selected_indices = {}

            for item in self.seq_list.selectedIndexes():
                row_index = item.row()
                selected_indices[self.sorted_seq_indices[row_index]] = 1

            for seq_index in self.sorted_seq_indices:
                if seq_index not in selected_indices:
                    not_selected_indices[seq_index] = 1

            if len(not_selected_indices) > 0:

                try:
                    self.net_plot_object.remove_from_selected(not_selected_indices, self.main_window_object.dim_num,
                                                            self.main_window_object.z_indexing_mode,
                                                            self.main_window_object.color_by,
                                                            self.main_window_object.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot remove sequences from the selected-subset"
                    error_occurred(self.net_plot_object.remove_from_selected, 'remove_from_selected', err, error_msg)
                    return

                try:
                    self.update_sequences()
                except Exception as err:
                    error_msg = "An error occurred: cannot update the sequences list in the selected sequences window"
                    error_occurred(self.update_sequences, 'update_sequences', err, error_msg)

        except Exception as err:
            error_msg = "An error occurred: cannot keep the sequences as selected"
            error_occurred(self.keep_selected, 'keep_selected', err, error_msg)

    def remove_from_selected(self):

        try:
            # Turn off highlighting
            self.highlight_button.setChecked(False)

            try:
                self.highlight_points()
            except Exception as err:
                error_msg = "An error occurred: cannot highlight data-points"
                error_occurred(self.highlight_points, 'highlight_points', err, error_msg)
                return

            selected_rows = []
            selected_indices = {}

            for item in self.seq_list.selectedIndexes():
                row_index = item.row()
                selected_rows.append(row_index)
                selected_indices[self.sorted_seq_indices[row_index]] = 1

            if len(selected_indices) > 0:

                try:
                    self.net_plot_object.remove_from_selected(selected_indices, self.main_window_object.dim_num,
                                                              self.main_window_object.z_indexing_mode,
                                                              self.main_window_object.color_by,
                                                              self.main_window_object.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot remove sequences from the selected-subset"
                    error_occurred(self.net_plot_object.remove_from_selected, 'remove_from_selected', err, error_msg)
                    return

                # Delete the selected rows from the list (in reverse order, to prevent problems with the row-indices)
                for row_index in reversed(selected_rows):
                    self.seq_list.takeItem(row_index)
                    self.sorted_seq_indices.pop(row_index)

                # Update the selected sequences list
                self.sorted_seq_indices = sorted(self.net_plot_object.selected_points)

                # Update the number of sequences message
                if len(self.sorted_seq_indices) > 0:
                    self.message.setText("Displaying " + str(len(self.sorted_seq_indices)) + " selected sequences")
                else:
                    self.message.setText("No selected sequences")

        except Exception as err:
            error_msg = "An error occurred: cannot remove sequences from the selected-subset"
            error_occurred(self.remove_from_selected, 'remove_from_selected', err, error_msg)

    def find_in_subset(self):

        try:
            find_dlg = FindDialog("Find in subset")

            if find_dlg.exec_():
                text, is_case_sensitive = find_dlg.get_input()

                # The user entered some text
                if text != "":

                    self.seq_list.clearSelection()
                    # Turn off highlighting
                    self.highlight_button.setChecked(False)

                    try:
                        self.highlight_points()
                    except Exception as err:
                        error_msg = "An error occurred: cannot highlight data-points"
                        error_occurred(self.highlight_points, 'highlight_points', err, error_msg)
                        return

                    i = 0
                    for seq_index in self.sorted_seq_indices:
                        seq_title = cfg.sequences_array[seq_index]['seq_ID']

                        if is_case_sensitive:
                            m = re.search(text, seq_title)
                        else:
                            m = re.search(text, seq_title, re.IGNORECASE)
                        # Search term was found in sequence title
                        if m:
                            self.items[i].setSelected(True)
                        i += 1

        except Exception as err:
            error_msg = "An error occurred while searching the subset"
            error_occurred(self.find_in_subset, 'find_in_subset', err, error_msg)


class FindDialog(QDialog):

    def __init__(self, win_title):
        super().__init__()

        self.setWindowTitle(win_title)
        self.setGeometry(650, 600, 300, 100)

        self.layout = QVBoxLayout()

        self.title = QLabel("Enter a search term:")
        self.find_area = QLineEdit()
        self.case_checkbox = QCheckBox("Case sensitive")

        self.text = ""
        self.is_case_sensitive = False

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.find_area)
        self.layout.addWidget(self.case_checkbox)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def get_input(self):

        self.text = self.find_area.text()
        self.is_case_sensitive = self.case_checkbox.isChecked()

        return self.text, self.is_case_sensitive


class SearchResultsWindow(QWidget):

    def __init__(self, main_window, net_plot):
        super().__init__()

        self.main_window_object = main_window
        self.net_plot_object = net_plot

        self.sorted_seq_indices = []
        self.items = []
        self.is_visible = 0

        self.setWindowTitle("Select by text results")
        self.setGeometry(650, 280, 600, 400)

        self.main_layout = QVBoxLayout()

        # Add a message on top
        self.message = QLabel("")
        self.message.setStyleSheet("color: maroon;")

        self.main_layout.addWidget(self.message)

        # Add a list widget to display the sequences
        self.seq_list = QListWidget()
        self.seq_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.main_layout.addWidget(self.seq_list)

        # Add a layout for buttons
        self.buttons_layout = QHBoxLayout()

        self.highlight_button = QPushButton("Highlight all")
        self.highlight_button.setCheckable(True)
        self.highlight_button.released.connect(self.highlight_all)

        self.add_to_selected_button = QPushButton("Add to selected subset")
        self.add_to_selected_button.released.connect(self.add_to_selected)

        self.set_as_selected_button = QPushButton("Set as selected subset")
        self.set_as_selected_button.released.connect(self.set_as_selected)

        self.new_search_button = QPushButton("New search")
        self.new_search_button.released.connect(self.new_search)

        self.close_button = QPushButton("Close")
        self.close_button.released.connect(self.close_window)

        self.buttons_layout.addWidget(self.highlight_button)
        self.buttons_layout.addWidget(self.add_to_selected_button)
        self.buttons_layout.addWidget(self.set_as_selected_button)
        self.buttons_layout.addWidget(self.new_search_button)
        self.buttons_layout.addWidget(self.close_button)
        self.buttons_layout.addStretch()

        self.main_layout.addLayout(self.buttons_layout)
        self.setLayout(self.main_layout)

    def open_window(self):

        try:
            self.is_visible = 1
            self.show()

            # Open the 'find' dialog when this window opens
            self.open_find_dialog()

        except Exception as err:
            error_msg = "An error occurred: cannot open the Search Results Window"
            error_occurred(self.open_window, 'open_window', err, error_msg)

    def close_window(self):
        try:
            self.clear_seq_list()
            self.is_visible = 0
            self.close()

        except Exception as err:
            error_msg = "An error occurred: cannot close the Search Results Window"
            error_occurred(self.close_window, 'close_window', err, error_msg)

    def highlight_all(self):
        try:
            # Select all items
            if self.highlight_button.isChecked():
                for i in range(len(self.items)):
                    self.items[i].setSelected(True)

            # De-select all items
            else:
                for i in range(len(self.items)):
                    self.items[i].setSelected(False)

        except Exception as err:
            error_msg = "An error occurred: cannot mark all sequences as selected"
            error_occurred(self.highlight_all, 'highlight_all', err, error_msg)

    def open_find_dialog(self):

        find_dlg = FindDialog("Search in sequence headers")
        find_dlg.setGeometry(750, 350, 300, 100)

        if find_dlg.exec_():
            text, is_case_sensitive = find_dlg.get_input()

            try:
                self.clear_seq_list()
            except Exception as err:
                error_msg = "An error occurred: cannot clear the sequences list"
                error_occurred(self.clear_seq_list, 'clear_seq_list', err, error_msg)

            # The user entered some text
            if text != "":
                self.update_message("Searching data...")

                try:
                    self.find_in_data(text, is_case_sensitive)
                except Exception as err:
                    error_msg = "An error occurred while searching the data"
                    error_occurred(self.find_in_data, 'find_in_data', err, error_msg)

            else:
                self.update_message("No results found")

    def find_in_data(self, text, is_case_sensitive):

        i = 0
        for seq_index in range(cfg.run_params['total_sequences_num']):
            seq_title = cfg.sequences_array[seq_index]['seq_ID']

            if is_case_sensitive:
                m = re.search(text, seq_title)
            else:
                m = re.search(text, seq_title, re.IGNORECASE)

            # Search term was found in sequence title - add this sequence to the list
            if m:
                self.sorted_seq_indices.append(seq_index)

                # The sequence header is the same as the index -> display only once
                if str(seq_index) == seq_title:
                    line_str = str(seq_index)
                else:
                    line_str = str(seq_index) + "  " + seq_title

                self.items.append(QListWidgetItem(line_str))
                self.seq_list.insertItem(i, self.items[i])

                i += 1

        # No results found
        if i == 0:
            self.update_message("No results found")
        else:
            self.update_message("Found " + str(i) + " matching sequences")

    def clear_seq_list(self):
        self.seq_list.clear()
        self.highlight_button.setChecked(False)
        self.sorted_seq_indices = []
        self.items = []

    def update_message(self, message):
        self.message.setText(message)

    def new_search(self):
        try:
            self.open_find_dialog()
        except Exception as err:
            error_msg = "An error occurred: cannot open the 'Find' dialog"
            error_occurred(self.open_find_dialog, 'open_find_dialog', err, error_msg)

    def add_to_selected(self):

        try:
            selected_indices = {}

            for item in self.seq_list.selectedIndexes():
                row_index = item.row()
                selected_indices[self.sorted_seq_indices[row_index]] = 1

            if len(selected_indices) > 0:

                # Set the selected sequences as the selected subset
                try:
                    self.net_plot_object.select_subset(selected_indices, self.main_window_object.dim_num,
                                                       self.main_window_object.z_indexing_mode,
                                                       self.main_window_object.color_by,
                                                       self.main_window_object.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot add to the selected subset"
                    error_occurred(self.net_plot_object.select_subset, 'select_subset', err, error_msg)
                    return

                # Update the selected sequences window
                try:
                    self.main_window_object.selected_seq_window.update_sequences()
                except Exception as err:
                    error_msg = "An error occurred: cannot update the sequences list in the selected sequences window"
                    error_occurred(self.main_window_object.selected_seq_window.update_sequences, 'update_sequences',
                                   err, error_msg)

                # Enable all the controls that are related to selected items in the Main Window
                self.main_window_object.open_selected_button.setEnabled(True)
                self.main_window_object.clear_selection_button.setEnabled(True)
                self.main_window_object.inverse_selection_button.setEnabled(True)
                self.main_window_object.show_selected_names_button.setEnabled(True)
                self.main_window_object.add_to_group_button.setEnabled(True)
                self.main_window_object.remove_selected_button.setEnabled(True)
                if len(self.net_plot_object.selected_points) >= 4:
                    self.main_window_object.data_mode_combo.setEnabled(True)

        except Exception as err:
            error_msg = "An error occurred: cannot add to the selected subset"
            error_occurred(self.add_to_selected, 'add_to_selected', err, error_msg)

    def set_as_selected(self):

        try:
            selected_indices = {}

            for item in self.seq_list.selectedIndexes():
                row_index = item.row()
                selected_indices[self.sorted_seq_indices[row_index]] = 1

            if len(selected_indices) > 0:

                # Clear the current selection
                try:
                    self.net_plot_object.reset_selection(self.main_window_object.dim_num,
                                                         self.main_window_object.z_indexing_mode,
                                                         self.main_window_object.color_by,
                                                         self.main_window_object.group_by,
                                                         self.main_window_object.is_show_group_names,
                                                         self.main_window_object.group_names_display)
                except Exception as err:
                    error_msg = "An error occurred: cannot clear the selected subset"
                    error_occurred(self.net_plot_object.reset_selection, 'reset_selection', err, error_msg)
                    return

                # Set the selected sequences as the selected subset
                try:
                    self.net_plot_object.select_subset(selected_indices, self.main_window_object.dim_num,
                                                       self.main_window_object.z_indexing_mode,
                                                       self.main_window_object.color_by,
                                                       self.main_window_object.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot set the sequences as the selected-subset"
                    error_occurred(self.net_plot_object.select_subset, 'select_subset', err, error_msg)
                    return

                # Update the selected sequences window
                try:
                    self.main_window_object.selected_seq_window.update_sequences()
                except Exception as err:
                    error_msg = "An error occurred: cannot update the sequences list in the selected sequences window"
                    error_occurred(self.main_window_object.selected_seq_window.update_sequences, 'update_sequences',
                                   err, error_msg)

                # Enable all the controls that are related to selected items in the Main Window
                self.main_window_object.open_selected_button.setEnabled(True)
                self.main_window_object.clear_selection_button.setEnabled(True)
                self.main_window_object.inverse_selection_button.setEnabled(True)
                self.main_window_object.show_selected_names_button.setEnabled(True)
                self.main_window_object.add_to_group_button.setEnabled(True)
                self.main_window_object.remove_selected_button.setEnabled(True)
                if len(self.net_plot_object.selected_points) >= 4:
                    self.main_window_object.data_mode_combo.setEnabled(True)

        except Exception as err:
            error_msg = "An error occurred: cannot set the sequences as the selected-subset"
            error_occurred(self.set_as_selected, 'set_as_selected', err, error_msg)


class GroupsIntersectionResults(QWidget):

    def __init__(self, main_window, net_plot):
        super().__init__()

        self.main_window_object = main_window
        self.net_plot_object = net_plot

        self.sorted_seq_indices = []
        self.items = []
        self.is_visible = 0

        self.setWindowTitle("Select by groups results")
        self.setGeometry(830, 310, 600, 400)

        self.main_layout = QVBoxLayout()

        # Add a message on top
        self.message = QLabel("")
        self.message.setStyleSheet("color: maroon;")

        self.main_layout.addWidget(self.message)

        # Add a list widget to display the sequences
        self.seq_list = QListWidget()
        self.seq_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.main_layout.addWidget(self.seq_list)

        # Add a layout for buttons
        self.buttons_layout = QHBoxLayout()

        self.highlight_button = QPushButton("Highlight all")
        self.highlight_button.setCheckable(True)
        self.highlight_button.released.connect(self.highlight_all)

        self.add_to_selected_button = QPushButton("Add to selected subset")
        self.add_to_selected_button.released.connect(self.add_to_selected)

        self.set_as_selected_button = QPushButton("Set as selected subset")
        self.set_as_selected_button.released.connect(self.set_as_selected)

        self.close_button = QPushButton("Close")
        self.close_button.released.connect(self.close_window)

        self.buttons_layout.addWidget(self.highlight_button)
        self.buttons_layout.addWidget(self.add_to_selected_button)
        self.buttons_layout.addWidget(self.set_as_selected_button)
        self.buttons_layout.addWidget(self.close_button)
        self.buttons_layout.addStretch()

        self.main_layout.addLayout(self.buttons_layout)
        self.setLayout(self.main_layout)

    def open_window(self, sorted_seq_indices):
        try:
            self.is_visible = 1

            # Create/update the sequences list
            self.build_seq_list(sorted_seq_indices)

            self.show()

        except Exception as err:
            error_msg = "An error occurred: cannot open the 'Select by groups' Window"
            error_occurred(self.open_window, 'open_window', err, error_msg)

    def close_window(self):
        try:
            self.clear_seq_list()
            self.is_visible = 0
            self.close()

        except Exception as err:
            error_msg = "An error occurred: cannot close the Search Results Window"
            error_occurred(self.close_window, 'close_window', err, error_msg)

    def highlight_all(self):
        try:
            # Select all items
            if self.highlight_button.isChecked():
                for i in range(len(self.items)):
                    self.items[i].setSelected(True)

            # De-select all items
            else:
                for i in range(len(self.items)):
                    self.items[i].setSelected(False)

        except Exception as err:
            error_msg = "An error occurred: cannot mark all sequences as selected"
            error_occurred(self.highlight_all, 'highlight_all', err, error_msg)

    def clear_seq_list(self):
        self.seq_list.clear()
        self.highlight_button.setChecked(False)
        self.sorted_seq_indices = []
        self.items = []

    def build_seq_list(self, sorted_seq_indices):

        # Clear the previous list (if any)
        self.clear_seq_list()

        self.sorted_seq_indices = sorted_seq_indices
        seq_num = len(self.sorted_seq_indices)

        # Update the message
        if seq_num == 0:
            self.update_message("No sequences found")
        else:
            self.update_message("Found " + str(seq_num) + " matching sequences")

        # Update the list
        for i in range(seq_num):
            seq_index = self.sorted_seq_indices[i]
            seq_title = cfg.sequences_array[seq_index]['seq_ID']

            # The sequence header is the same as the index -> display only once
            if str(seq_index) == seq_title:
                line_str = str(seq_index)
            else:
                line_str = str(seq_index) + "  " + seq_title

            self.items.append(QListWidgetItem(line_str))
            self.seq_list.insertItem(i, self.items[i])

    def update_message(self, message):
        self.message.setText(message)

    def add_to_selected(self):

        try:
            selected_indices = {}

            for item in self.seq_list.selectedIndexes():
                row_index = item.row()
                selected_indices[self.sorted_seq_indices[row_index]] = 1

            if len(selected_indices) > 0:

                # Set the selected sequences as the selected subset
                try:
                    self.net_plot_object.select_subset(selected_indices, self.main_window_object.dim_num,
                                                       self.main_window_object.z_indexing_mode,
                                                       self.main_window_object.color_by,
                                                       self.main_window_object.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot add to the selected subset"
                    error_occurred(self.net_plot_object.select_subset, 'select_subset', err, error_msg)
                    return

                # Update the selected sequences window
                try:
                    self.main_window_object.selected_seq_window.update_sequences()
                except Exception as err:
                    error_msg = "An error occurred: cannot update the sequences list in the selected sequences window"
                    error_occurred(self.main_window_object.selected_seq_window.update_sequences, 'update_sequences',
                                   err, error_msg)

                # Enable all the controls that are related to selected items in the Main Window
                self.main_window_object.open_selected_button.setEnabled(True)
                self.main_window_object.clear_selection_button.setEnabled(True)
                self.main_window_object.inverse_selection_button.setEnabled(True)
                self.main_window_object.show_selected_names_button.setEnabled(True)
                self.main_window_object.add_to_group_button.setEnabled(True)
                self.main_window_object.remove_selected_button.setEnabled(True)
                if len(self.net_plot_object.selected_points) >= 4:
                    self.main_window_object.data_mode_combo.setEnabled(True)

        except Exception as err:
            error_msg = "An error occurred: cannot add to the selected subset"
            error_occurred(self.add_to_selected, 'add_to_selected', err, error_msg)

    def set_as_selected(self):

        try:
            selected_indices = {}

            for item in self.seq_list.selectedIndexes():
                row_index = item.row()
                selected_indices[self.sorted_seq_indices[row_index]] = 1

            if len(selected_indices) > 0:

                # Clear the current selection
                try:
                    self.net_plot_object.reset_selection(self.main_window_object.dim_num,
                                                         self.main_window_object.z_indexing_mode,
                                                         self.main_window_object.color_by,
                                                         self.main_window_object.group_by,
                                                         self.main_window_object.is_show_group_names,
                                                         self.main_window_object.group_names_display)
                except Exception as err:
                    error_msg = "An error occurred: cannot clear the selected subset"
                    error_occurred(self.net_plot_object.reset_selection, 'reset_selection', err, error_msg)
                    return

                # Set the selected sequences as the selected subset
                try:
                    self.net_plot_object.select_subset(selected_indices, self.main_window_object.dim_num,
                                                       self.main_window_object.z_indexing_mode,
                                                       self.main_window_object.color_by,
                                                       self.main_window_object.group_by)
                except Exception as err:
                    error_msg = "An error occurred: cannot set the sequences as the selected-subset"
                    error_occurred(self.net_plot_object.select_subset, 'select_subset', err, error_msg)
                    return

                # Update the selected sequences window
                try:
                    self.main_window_object.selected_seq_window.update_sequences()
                except Exception as err:
                    error_msg = "An error occurred: cannot update the sequences list in the selected sequences window"
                    error_occurred(self.main_window_object.selected_seq_window.update_sequences, 'update_sequences',
                                   err, error_msg)

                # Enable all the controls that are related to selected items in the Main Window
                self.main_window_object.open_selected_button.setEnabled(True)
                self.main_window_object.clear_selection_button.setEnabled(True)
                self.main_window_object.inverse_selection_button.setEnabled(True)
                self.main_window_object.show_selected_names_button.setEnabled(True)
                self.main_window_object.add_to_group_button.setEnabled(True)
                self.main_window_object.remove_selected_button.setEnabled(True)
                if len(self.net_plot_object.selected_points) >= 4:
                    self.main_window_object.data_mode_combo.setEnabled(True)

        except Exception as err:
            error_msg = "An error occurred: cannot set the sequences as the selected-subset"
            error_occurred(self.set_as_selected, 'set_as_selected', err, error_msg)


class SelectByGroupsWindow(QWidget):

    def __init__(self, main_window, net_plot):
        super().__init__()

        self.main_window_object = main_window
        self.net_plot_object = net_plot

        # Build the results window, for later use
        self.results_window = GroupsIntersectionResults(self.main_window_object, self.net_plot_object)

        self.list_widgets_dict = {}
        self.list_titles_dict = {}
        self.name_to_group_ID = {}
        self.is_visible = 0

        self.setWindowTitle("Select by groups")
        self.setGeometry(750, 350, 400, 700)

        self.main_layout = QVBoxLayout()

        self.space_line = QLabel("  ")
        self.space_line.setFixedSize(60, 5)

        # Add a message on top
        self.message = QLabel("Select sequences which belong to the following group(s):\n"
                              "(Multi-selection of groups is possible)\n\n"
                              "Selecting groups from different grouping-categories is treated as intersection\n"
                              "(AND logic operation)")
        self.message.setStyleSheet("font-size: 14px")
        self.main_layout.addWidget(self.message)
        self.main_layout.addWidget(self.space_line)

        # Create the lists widget inside a scrollable area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.lists_widget = QWidget()
        self.lists_widget.setGeometry(750, 350, 400, 800)

        self.lists_layout = QVBoxLayout()
        self.lists_widget.setLayout(self.lists_layout)

        self.scroll_area.setWidget(self.lists_widget)

        self.main_layout.addWidget(self.scroll_area)

        # Add a layout for buttons
        self.buttons_layout = QHBoxLayout()

        self.get_sequences_button = QPushButton("Get sequences by groups intersection")
        self.get_sequences_button.released.connect(self.get_selected_sequences)

        self.clear_button = QPushButton("Clear selection")
        self.clear_button.released.connect(self.clear_selection)

        self.close_button = QPushButton("Close")
        self.close_button.released.connect(self.close_window)

        self.buttons_layout.addWidget(self.get_sequences_button)
        self.buttons_layout.addWidget(self.clear_button)
        self.buttons_layout.addWidget(self.close_button)
        self.buttons_layout.addStretch()

        self.main_layout.addLayout(self.buttons_layout)

        self.setLayout(self.main_layout)

    def build_lists(self):

        list_index = 0
        for category_index in range(len(cfg.groups_by_categories)):
            if len(cfg.groups_by_categories[category_index]['groups']) > 0:

                # Add a list widget to display the groups of the grouping-category
                self.list_widgets_dict[category_index] = QListWidget()
                self.list_widgets_dict[category_index].setSelectionMode(QAbstractItemView.ExtendedSelection)

                self.list_titles_dict[category_index] = QLabel()
                self.list_titles_dict[category_index].setStyleSheet("color: maroon;")
                self.list_titles_dict[category_index].setText(cfg.groups_by_categories[category_index]['name'])

                # A loop over the groups to add them to the list
                self.list_widgets_dict[category_index].addItem("---")

                for group_ID in cfg.groups_by_categories[category_index]['groups']:
                    group_name = cfg.groups_by_categories[category_index]['groups'][group_ID]['name']

                    # Add the group name to the list widget
                    self.list_widgets_dict[category_index].addItem(group_name)

                    # Save mapping of the grouo_ID to group_name for later use
                    self.name_to_group_ID[group_name] = group_ID

                self.lists_layout.addWidget(self.list_titles_dict[category_index])
                self.lists_layout.addWidget(self.list_widgets_dict[category_index])

                list_index += 1

    def open_window(self):

        try:
            self.is_visible = 1

            # Clear the previous lists layout
            for i in reversed(range(self.lists_layout.count())):
                self.lists_layout.itemAt(i).widget().setParent(None)

            # Build the updates lists
            self.build_lists()

            # Open the window
            self.show()

        except Exception as err:
            error_msg = "An error occurred: cannot open the 'Select by groups' Window"
            error_occurred(self.open_window, 'open_window', err, error_msg)

    def close_window(self):
        try:
            self.is_visible = 0

            # Close the results window
            self.results_window.close_window()

            self.close()

        except Exception as err:
            error_msg = "An error occurred: cannot close the 'Select by groups' Window"
            error_occurred(self.close_window, 'close_window', err, error_msg)

    def clear_selection(self):

        for category_index in self.list_widgets_dict:
            self.list_widgets_dict[category_index].setCurrentRow(0)

        self.results_window.clear_seq_list()

    def get_selected_sequences(self):

        selected_indices_by_category = []
        selected_indices_intersection = {}

        selected_category_index = 0
        for category_index in range(len(cfg.groups_by_categories)):
            # Go over all the presented categories
            if len(cfg.groups_by_categories[category_index]['groups']) > 0:
                found_selected_group = 0

                # Get the selected groups from this category list widget
                for item in self.list_widgets_dict[category_index].selectedItems():
                    group_name = item.text()
                    if group_name != "---":
                        group_ID = self.name_to_group_ID[group_name]

                        # First selected group in the category
                        if found_selected_group == 0:
                            selected_indices_by_category.append(dict())

                        found_selected_group = 1

                        # Add the sequences that belong to the selected group to the by-category dictionary
                        for seq_index in cfg.groups_by_categories[category_index]['groups'][group_ID]['seqIDs']:
                            selected_indices_by_category[selected_category_index][seq_index] = 1

                if found_selected_group:
                    selected_category_index += 1

        # Perform the intersection between the categories
        selected_categories_num = len(selected_indices_by_category)
        if selected_categories_num > 0:
            for seq_index in selected_indices_by_category[0]:

                # There are selected groups from more than one category -> check intersection
                if selected_categories_num > 1:
                    found_seq_in_category = 1

                    # A loop over the rest of the categories
                    for selected_category_index in range(1, selected_categories_num):
                        if seq_index in selected_indices_by_category[selected_category_index]:
                            found_seq_in_category += 1

                    # Add the sequence to the selected set only if it appears in all selected categories
                    if found_seq_in_category == selected_categories_num:
                        selected_indices_intersection[seq_index] = 1

                # There are groups only from one category -> add all the sequences to the selected set
                else:
                    selected_indices_intersection[seq_index] = 1

        # Open / Update the results window, presenting the sequences
        if self.results_window.is_visible:
            self.results_window.build_seq_list(sorted(selected_indices_intersection))
        else:
            self.results_window.open_window(sorted(selected_indices_intersection))


class SetAngleDialog(QDialog):

    def __init__(self, current_angle):
        super().__init__()

        try:
            self.current_angle = current_angle

            self.setWindowTitle("Set the offset angle")

            self.main_layout = QVBoxLayout()
            self.angle_layout = QHBoxLayout()

            self.title_label = QLabel("Set the offset angle between the left and right images")

            self.main_layout.addWidget(self.title_label)

            # Set the group name
            self.angle_label = QLabel("Angle (in degrees):")
            self.angle_widget = QLineEdit()
            self.angle_widget.setText(str(self.current_angle))

            self.angle_layout.addWidget(self.angle_label)
            self.angle_layout.addWidget(self.angle_widget)

            self.main_layout.addLayout(self.angle_layout)

            # Add the OK/Cancel standard buttons
            self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.connect(self.reject)

            self.main_layout.addWidget(self.button_box)
            self.setLayout(self.main_layout)

        except Exception as err:
            error_msg = "An error occurred: cannot init SetAngleDialog"
            error_occurred(self.__init__, 'init', err, error_msg)

    def get_angle(self):

        if self.angle_widget.text() != "":
            entered_angle = self.angle_widget.text()
        else:
            entered_angle = self.current_angle

        return entered_angle


class StereoImageWindow(QWidget):

    def __init__(self, main_window):
        super().__init__()

        self.main_window_object = main_window

        self.is_visible = 0
        self.offset_angle = 10
        self.is_show_connections = 0
        self.dim_num = self.main_window_object.dim_num
        #self.z_indexing_mode = self.main_window_object.z_indexing_mode
        self.z_indexing_mode = 'groups'
        self.group_by = self.main_window_object.group_by
        self.color_by = self.main_window_object.color_by

        self.setGeometry(150, 150, 1000, 750)

        self.main_layout = QVBoxLayout()

        # Create the canvas (the graph area)
        self.canvas = scene.SceneCanvas(size=(1000, 700), keys='interactive', show=False, bgcolor='w')
        self.main_layout.addWidget(self.canvas.native)

        # Add a grid for two view-boxes
        self.grid = self.canvas.central_widget.add_grid()
        self.left_view = self.grid.add_view(0, 0)
        self.right_view = self.grid.add_view(0, 1)

        # Add a layout for buttons
        self.buttons_layout = QHBoxLayout()

        self.horizontal_spacer_tiny = QSpacerItem(6, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.set_offset_button = QPushButton("Set offset angle")
        self.set_offset_button.released.connect(self.set_offset_angle)

        self.connections_button = QPushButton("Display connections")
        self.connections_button.setCheckable(True)
        self.connections_button.released.connect(self.manage_connections)

        self.update_image_button = QPushButton("Update image")
        self.update_image_button.released.connect(self.update_image)

        self.save_image_button = QPushButton("Save image")
        self.save_image_button.released.connect(self.save_image)

        self.close_button = QPushButton("Close")
        self.close_button.released.connect(self.close_window)

        self.buttons_layout.addWidget(self.set_offset_button)
        self.buttons_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.buttons_layout.addWidget(self.update_image_button)
        self.buttons_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.buttons_layout.addWidget(self.connections_button)
        self.buttons_layout.addSpacerItem(self.horizontal_spacer_tiny)
        self.buttons_layout.addWidget(self.save_image_button)
        self.buttons_layout.addWidget(self.close_button)
        self.buttons_layout.addStretch()

        self.main_layout.addLayout(self.buttons_layout)

        self.setLayout(self.main_layout)

        # Create the graph object
        self.left_plot = net.Network3D(self.left_view)
        self.right_plot = net.Network3D(self.right_view)

        self.left_view.camera._viewbox.events.mouse_move.disconnect(self.left_view.camera.viewbox_mouse_event)
        self.left_view.camera._viewbox.events.mouse_press.disconnect(self.left_view.camera.viewbox_mouse_event)
        self.right_view.camera._viewbox.events.mouse_move.disconnect(self.right_view.camera.viewbox_mouse_event)
        self.right_view.camera._viewbox.events.mouse_press.disconnect(self.right_view.camera.viewbox_mouse_event)

        # For debugging purposes
        #self.left_plot.xyz.parent = self.left_view.scene
        #self.right_plot.xyz.parent = self.right_view.scene

        # Link the two cameras
        self.left_view.camera.link(self.right_view.camera)

    def init_plot(self):

        self.left_plot.init_data(self.main_window_object.fr_object, self.main_window_object.group_by)
        self.right_plot.init_data(self.main_window_object.fr_object, self.main_window_object.group_by)

        self.is_show_connections = self.main_window_object.is_show_connections
        if self.is_show_connections:
            self.connections_button.setChecked(True)
        else:
            self.connections_button.setChecked(False)
        self.manage_connections()

    def reset_plot(self):
        self.left_plot.reset_data()
        self.right_plot.reset_data()

    def update_plot_with_rotation(self, plot_obj):

        plot_obj.update_data(self.dim_num, self.main_window_object.fr_object, 1,
                             self.main_window_object.color_by)

        # Calculate the rotation of the main graph
        self.main_window_object.network_plot.calculate_rotation()

        # Save the coordinated in the rotated state
        plot_obj.pos_array = self.main_window_object.network_plot.rotated_pos_array.copy()
        plot_obj.rotated_pos_array = plot_obj.pos_array.copy()

        plot_obj.update_view(self.dim_num, self.main_window_object.color_by,
                             self.main_window_object.group_by, self.main_window_object.z_indexing_mode)

    def manage_connections(self):

        # Show the connections
        if self.connections_button.isChecked():
            self.is_show_connections = 1

            # Display the connecting lines
            try:
                self.left_plot.show_connections()
            except Exception as err:
                error_msg = "An error occurred: cannot display the connecting lines"
                error_occurred(self.left_plot.show_connections, 'show_connections', err, error_msg)

            try:
                self.right_plot.show_connections()
            except Exception as err:
                error_msg = "An error occurred: cannot display the connecting lines"
                error_occurred(self.right_plot.show_connections, 'show_connections', err, error_msg)

        # Hide the connections
        else:
            self.is_show_connections = 0

            try:
                self.left_plot.hide_connections()
            except Exception as err:
                error_msg = "An error occurred: cannot hide the connecting lines"
                error_occurred(self.left_plot.hide_connections, 'hide_connections', err, error_msg)

            try:
                self.right_plot.hide_connections()
            except Exception as err:
                error_msg = "An error occurred: cannot hide the connecting lines"
                error_occurred(self.right_plot.hide_connections, 'hide_connections', err, error_msg)

    def update_image(self):

        self.reset_plot()
        self.init_plot()

        self.dim_num = self.main_window_object.dim_num
        #self.z_indexing_mode = self.main_window_object.z_indexing_mode

        # Update the color-by parameter
        if self.color_by != self.main_window_object.color_by:
            self.color_by = self.main_window_object.color_by

            # Color by groups
            if self.color_by == 'groups':
                # Update the group-by parameter
                if self.group_by != self.main_window_object.group_by:
                    self.group_by = self.main_window_object.group_by
                    self.left_plot.update_group_by(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
                    self.right_plot.update_group_by(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)

            # Color by param
            else:
                param = self.main_window_object.color_by_combo.currentText()
                # Color by seq. length
                if param == 'Seq. length':
                    gradient_colormap = colors.generate_colormap_gradient_2_colors(cfg.short_color, cfg.long_color)
                    self.left_plot.color_by_param(gradient_colormap, cfg.sequences_array['norm_seq_length'],
                                                  self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
                    self.right_plot.color_by_param(gradient_colormap, cfg.sequences_array['norm_seq_length'],
                                                  self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
                # Color by custom parameter
                else:
                    min_param_color = cfg.sequences_numeric_params[param]['min_color']
                    max_param_color = cfg.sequences_numeric_params[param]['max_color']
                    gradient_colormap = colors.generate_colormap_gradient_2_colors(min_param_color, max_param_color)
                    self.left_plot.color_by_param(gradient_colormap, cfg.sequences_numeric_params[param]['norm'],
                                                  self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
                    self.right_plot.color_by_param(gradient_colormap, cfg.sequences_numeric_params[param]['norm'],
                                                  self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)

        # Color by has not changed
        else:
            # Color by groups
            if self.color_by == 'groups':
                # Update the group-by parameter
                if self.group_by != self.main_window_object.group_by:
                    self.group_by = self.main_window_object.group_by
                    self.left_plot.update_group_by(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
                    self.right_plot.update_group_by(self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)

            # Color by param
            else:
                param = self.main_window_object.color_by_combo.currentText()
                # Color by seq. length
                if param == 'Seq. length':
                    gradient_colormap = colors.generate_colormap_gradient_2_colors(cfg.short_color, cfg.long_color)
                    self.left_plot.color_by_param(gradient_colormap, cfg.sequences_array['norm_seq_length'],
                                                  self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
                    self.right_plot.color_by_param(gradient_colormap, cfg.sequences_array['norm_seq_length'],
                                                   self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
                # Color by custom parameter
                else:
                    min_param_color = cfg.sequences_numeric_params[param]['min_color']
                    max_param_color = cfg.sequences_numeric_params[param]['max_color']
                    gradient_colormap = colors.generate_colormap_gradient_2_colors(min_param_color, max_param_color)
                    self.left_plot.color_by_param(gradient_colormap, cfg.sequences_numeric_params[param]['norm'],
                                                  self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)
                    self.right_plot.color_by_param(gradient_colormap, cfg.sequences_numeric_params[param]['norm'],
                                                   self.dim_num, self.z_indexing_mode, self.color_by, self.group_by)

        self.update_plot_with_rotation(self.left_plot)
        self.update_plot_with_rotation(self.right_plot)

        # Create offset coordinates in the right plot
        rotation_mtx = util.transforms.rotate(self.offset_angle, [0, 1, 0])
        pos_array_4 = np.append(self.right_plot.pos_array, np.full((cfg.run_params['total_sequences_num'], 1), 1.0),
                                axis=1)
        offset_pos_array_4 = np.dot(pos_array_4, rotation_mtx)
        self.left_plot.pos_array = offset_pos_array_4[:, :3]
        self.left_plot.rotated_pos_array = self.left_plot.pos_array.copy()

        self.left_plot.update_view(2, self.main_window_object.color_by,
                                   self.main_window_object.group_by, self.z_indexing_mode)
        self.right_plot.update_view(2, self.main_window_object.color_by,
                                    self.main_window_object.group_by, self.z_indexing_mode)

        self.is_show_connections = self.main_window_object.is_show_connections
        if self.is_show_connections:
            self.connections_button.setChecked(True)
        else:
            self.connections_button.setChecked(False)
        self.manage_connections()

    def open_window(self):

        try:
            self.is_visible = 1

            self.setWindowTitle("Stereo presentation of " + self.main_window_object.file_name)

            self.update_image()

            # Show the canvas
            self.canvas.show = True

            # Open the window
            self.show()

        except Exception as err:
            error_msg = "An error occurred: cannot open the 'Stereo presentation' Window"
            error_occurred(self.open_window, 'open_window', err, error_msg)

    def close_window(self):
        try:
            self.is_visible = 0

            self.close()

        except Exception as err:
            error_msg = "An error occurred: cannot close the 'Stereo presentation' Window"
            error_occurred(self.close_window, 'close_window', err, error_msg)

    def set_offset_angle(self):

        dlg = SetAngleDialog(self.offset_angle)

        if dlg.exec_():
            angle = dlg.get_angle()

            # The value is a number
            if re.search("^\d+$", angle):
                if 0 <= int(angle) <= 360:
                    self.offset_angle = int(angle)

                    self.update_image()

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

                print("Stereo Image was saved in file " + str(saved_file))

        except Exception as err:
            error_msg = "An error occurred: cannot save the stereo presentation as an image."
            error_occurred(self.save_image, 'save_image', err, error_msg)


