from PyQt5.QtWidgets import *
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
        for group_index in range(len(cfg.groups_list)):
            self.groups_combo.addItem(cfg.groups_list[group_index]['name'])
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
            group_index = self.groups_combo.currentIndex() - 1
            return 'existing', group_index


class CreateGroupDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Create group from selected")
