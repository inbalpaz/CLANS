from PyQt5.QtWidgets import *


class MessageDialog(QDialog):

    def __init__(self, message):
        super().__init__()

        self.setGeometry(200, 200, 300, 150)

        self.main_layout = QVBoxLayout()

        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("color: red")

        # Add the OK  standard button
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)

        self.main_layout.addWidget(self.message_label)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)