from PyQt5.QtWidgets import *
import re
import clans.config as cfg


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
        #self.remove_button.isEnabled(False)

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
        self.is_visible = 1
        self.show()

    def close_window(self):
        self.highlight_button.setChecked(False)
        self.highlight_points()

        self.is_visible = 0
        self.close()

    def update_window_title(self, file_name):

        self.setWindowTitle("Selected Subset from " + file_name)

    def update_sequences(self):

        self.highlight_button.setChecked(False)
        self.highlight_points()
        self.seq_list.clear()
        self.items = []

        self.sorted_seq_indices = sorted(self.net_plot_object.selected_points)

        # There is at least one selected sequence
        if len(self.sorted_seq_indices) > 0:
            for i in range(len(self.sorted_seq_indices)):
                seq_index = self.sorted_seq_indices[i]
                seq_title = cfg.sequences_array[seq_index]['seq_title'][0:]

                # The sequence header is the same as the index -> display only once
                if str(seq_index) == seq_title:
                    line_str = str(seq_index)
                else:
                    line_str = str(seq_index) + "  " + seq_title

                self.items.append(QListWidgetItem(line_str))
                self.seq_list.insertItem(i, self.items[i])


                #self.message.setText("The selected subset consists of " + str(i) + " sequences")
                self.message.setText("Displaying " + str(len(self.sorted_seq_indices)) + " selected sequences")

        else:
            self.message.setText("No selected sequences")

    def clear_list(self):
        self.seq_list.clear()
        self.sorted_seq_indices = []
        self.items = []
        self.highlight_button.setChecked(False)

        self.message.setText("")

    def highlight_points(self):

        selected_indices = {}
        not_selected_indices = {}

        for item in self.seq_list.selectedIndexes():
            row_index = item.row()
            selected_indices[self.sorted_seq_indices[row_index]] = 1

        for seq_index in self.sorted_seq_indices:
            if seq_index not in selected_indices:
                not_selected_indices[seq_index] = 1

        if len(selected_indices) > 0:

            if self.main_window_object.view_in_dimensions_num == 2 or self.main_window_object.mode == "selection":
                dim_num = 2
            else:
                dim_num = 3

            # Highlight button is checked
            if self.highlight_button.isChecked():

                # Highlight the selected points
                self.net_plot_object.highlight_selected_points(selected_indices, self.main_window_object.view, dim_num,
                                                               self.main_window_object.z_indexing_mode)

                # Turn off all the rest (not selected)
                self.net_plot_object.unhighlight_selected_points(not_selected_indices,
                                                                 self.main_window_object.view, dim_num,
                                                                 self.main_window_object.z_indexing_mode)

            # Turn off highlighting of all selected sequences (back to normal selected presentation)
            else:
                self.net_plot_object.unhighlight_selected_points(self.sorted_seq_indices, self.main_window_object.view,
                                                                 dim_num, self.main_window_object.z_indexing_mode)

    def keep_selected(self):

        selected_indices = {}
        not_selected_indices = {}

        for item in self.seq_list.selectedIndexes():
            row_index = item.row()
            selected_indices[self.sorted_seq_indices[row_index]] = 1

        for seq_index in self.sorted_seq_indices:
            if seq_index not in selected_indices:
                not_selected_indices[seq_index] = 1

        if len(not_selected_indices) > 0:

            if self.main_window_object.view_in_dimensions_num == 2 or self.main_window_object.mode == "selection":
                dim_num = 2
            else:
                dim_num = 3

            self.net_plot_object.remove_from_selected(not_selected_indices, self.main_window_object.view, dim_num,
                                                      self.main_window_object.z_indexing_mode)

            self.update_sequences()

    def remove_from_selected(self):

        # Turn off highlighting
        self.highlight_button.setChecked(False)
        self.highlight_points()

        selected_rows = []
        selected_indices = {}

        for item in self.seq_list.selectedIndexes():
            row_index = item.row()
            selected_rows.append(row_index)
            selected_indices[self.sorted_seq_indices[row_index]] = 1

        if len(selected_indices) > 0:

            if self.main_window_object.view_in_dimensions_num == 2 or self.main_window_object.mode == "selection":
                dim_num = 2
            else:
                dim_num = 3

            self.net_plot_object.remove_from_selected(selected_indices, self.main_window_object.view, dim_num,
                                                      self.main_window_object.z_indexing_mode)

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

    def find_in_subset(self):

        find_dlg = FindDialog("Find in subset")

        if find_dlg.exec_():
            text, is_case_sensitive = find_dlg.get_input()

            # The user entered some text
            if text != "":

                self.seq_list.clearSelection()
                # Turn off highlighting
                self.highlight_button.setChecked(False)
                self.highlight_points()

                i = 0
                for seq_index in self.sorted_seq_indices:
                    seq_title = cfg.sequences_array[seq_index]['seq_title']

                    if is_case_sensitive:
                        m = re.search(text, seq_title)
                    else:
                        m = re.search(text, seq_title, re.IGNORECASE)
                    # Search term was found in sequence title
                    if m:
                        self.items[i].setSelected(True)
                    i += 1


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

        self.setWindowTitle("Search results")
        self.setGeometry(650, 400, 600, 400)

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
        self.is_visible = 1
        self.show()

        self.setGeometry(650, 400, 600, 400)

        # Open the 'find' dialog when this window opens
        self.open_find_dialog()

    def close_window(self):
        self.clear_seq_list()
        self.is_visible = 0
        self.close()

    def highlight_all(self):

        # Select all items
        if self.highlight_button.isChecked():
            for i in range(len(self.items)):
                self.items[i].setSelected(True)

        # De-select all items
        else:
            for i in range(len(self.items)):
                self.items[i].setSelected(False)

    def open_find_dialog(self):
        find_dlg = FindDialog("Find in data")
        find_dlg.setGeometry(750, 500, 300, 100)

        if find_dlg.exec_():
            text, is_case_sensitive = find_dlg.get_input()
            self.clear_seq_list()

            # The user entered some text
            if text != "":
                self.update_message("Searching data...")
                self.find_in_data(text, is_case_sensitive)
            else:
                self.update_message("No results found")

    def find_in_data(self, text, is_case_sensitive):

        i = 0
        for seq_index in range(cfg.run_params['total_sequences_num']):
            seq_title = cfg.sequences_array[seq_index]['seq_title']

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
        self.open_find_dialog()

    def add_to_selected(self):

        selected_indices = {}

        for item in self.seq_list.selectedIndexes():
            row_index = item.row()
            selected_indices[self.sorted_seq_indices[row_index]] = 1

        if len(selected_indices) > 0:

            if self.main_window_object.view_in_dimensions_num == 2 or self.main_window_object.mode == "selection":
                dim_num = 2
            else:
                dim_num = 3

            # Set the selected sequences as the selected subset
            self.net_plot_object.select_subset(selected_indices, self.main_window_object.view, dim_num,
                                               self.main_window_object.z_indexing_mode)

            # Update the selected sequences window
            self.main_window_object.selected_seq_window.update_sequences()

            # Enable all the controls that are related to selected items in the Main Window
            self.main_window_object.open_selected_button.setEnabled(True)
            self.main_window_object.show_selected_names_button.setEnabled(True)
            self.main_window_object.add_to_group_button.setEnabled(True)
            self.main_window_object.remove_selected_button.setEnabled(True)
            if len(self.net_plot_object.selected_points) >= 4:
                self.main_window_object.data_mode_combo.setEnabled(True)

    def set_as_selected(self):

        selected_indices = {}

        for item in self.seq_list.selectedIndexes():
            row_index = item.row()
            selected_indices[self.sorted_seq_indices[row_index]] = 1

        if len(selected_indices) > 0:

            if self.main_window_object.view_in_dimensions_num == 2 or self.main_window_object.mode == "selection":
                dim_num = 2
            else:
                dim_num = 3

            # Clear the current selection
            self.net_plot_object.reset_selection(self.main_window_object.view, dim_num,
                                                 self.main_window_object.z_indexing_mode)

            # Set the selected sequences as the selected subset
            self.net_plot_object.select_subset(selected_indices, self.main_window_object.view, dim_num,
                                               self.main_window_object.z_indexing_mode)

            # Update the selected sequences window
            self.main_window_object.selected_seq_window.update_sequences()

            # Enable all the controls that are related to selected items in the Main Window
            self.main_window_object.open_selected_button.setEnabled(True)
            self.main_window_object.show_selected_names_button.setEnabled(True)
            self.main_window_object.add_to_group_button.setEnabled(True)
            self.main_window_object.remove_selected_button.setEnabled(True)
            if len(self.net_plot_object.selected_points) >= 4:
                self.main_window_object.data_mode_combo.setEnabled(True)


