from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import clans.config as cfg


class NewTextDialog(QDialog):

    def __init__(self, net_plot_object):
        super().__init__()

        self.setWindowTitle("Enter new text element")

        self.main_layout = QVBoxLayout()
        self.layout = QGridLayout()

        # Enter the text
        self.text_label = QLabel("Enter text:")
        self.text_widget = QLineEdit()

        self.layout.addWidget(self.text_label, 0, 0)
        self.layout.addWidget(self.text_widget, 0, 1, 1, 2)

        # Set the size of the text
        self.text_size_label = QLabel("Text size:")
        default_size = net_plot_object.text_size
        self.text_size = QComboBox()

        i = 0
        for size in range(5, 21):
            self.text_size.addItem(str(size))
            if size == int(default_size):
                default_index = i
            i += 1
        self.text_size.setCurrentIndex(default_index)

        self.layout.addWidget(self.text_size_label, 1, 0)
        self.layout.addWidget(self.text_size, 1, 1)

        # Set the color of the text
        self.color_label = QLabel("Color:")
        self.selected_color_label = QLabel(" ")
        self.selected_color = "black"
        self.rgb_color = "0,0,0,255"
        self.color_array = [0.0, 0.0, 0.0, 1.0]
        self.selected_color_label.setStyleSheet("background-color: " + self.selected_color)

        self.change_color_button = QPushButton("Change color")
        self.change_color_button.pressed.connect(self.change_color)

        self.layout.addWidget(self.color_label, 3, 0)
        self.layout.addWidget(self.selected_color_label, 3, 1)
        self.layout.addWidget(self.change_color_button, 3, 2)

        # Add bold and italic check-boxes

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
            self.rgb_color = color.rgb()
            self.color_array = [red/255, green/255, blue/255, 1.0]
            self.selected_color = hex
            self.selected_color_label.setStyleSheet("background-color: " + self.selected_color)

    def get_text_info(self):

        # Get the text
        text = self.text_widget.text()

        # Get the selected size
        size = self.text_size.currentText()

        return text, size, self.rgb_color, self.color_array


class EditTextDialog(QDialog):

    def __init__(self, net_plot_object):
        super().__init__()

        self.setWindowTitle("Edit text element")

        self.main_layout = QVBoxLayout()
        self.layout = QGridLayout()

        # Enter the text
        self.text_label = QLabel("Enter text:")
        self.text_widget = QLineEdit()

        self.layout.addWidget(self.text_label, 0, 0)
        self.layout.addWidget(self.text_widget, 0, 1, 1, 2)

        # Set the size of the text
        self.text_size_label = QLabel("Text size:")
        default_size = net_plot_object.text_size
        self.text_size = QComboBox()

        i = 0
        for size in range(5, 21):
            self.text_size.addItem(str(size))
            if size == int(default_size):
                default_index = i
            i += 1
        self.text_size.setCurrentIndex(default_index)

        self.layout.addWidget(self.text_size_label, 1, 0)
        self.layout.addWidget(self.text_size, 1, 1)

        # Set the color of the text
        self.color_label = QLabel("Color:")
        self.selected_color_label = QLabel(" ")
        self.selected_color = "black"
        self.rgb_color = "0,0,0,255"
        self.color_array = [0.0, 0.0, 0.0, 1.0]
        self.selected_color_label.setStyleSheet("background-color: " + self.selected_color)

        self.change_color_button = QPushButton("Change color")
        self.change_color_button.pressed.connect(self.change_color)

        self.layout.addWidget(self.color_label, 3, 0)
        self.layout.addWidget(self.selected_color_label, 3, 1)
        self.layout.addWidget(self.change_color_button, 3, 2)

        # Add bold and italic check-boxes

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
            self.rgb_color = color.rgb()
            self.color_array = [red / 255, green / 255, blue / 255, 1.0]
            self.selected_color = hex
            self.selected_color_label.setStyleSheet("background-color: " + self.selected_color)

    def get_text_info(self):

        # Get the text
        text = self.text_widget.text()

        # Get the selected size
        size = self.text_size.currentText()

        return text, size, self.rgb_color, self.color_array
