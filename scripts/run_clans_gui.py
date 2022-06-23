# The main script for running clans as a graphical application #
################################################################
from PyQt5.QtWidgets import QApplication
from clans.clans.io.parser import parse_arguments
from clans.clans.GUI.main_window import MainWindow

# Parse the command-line arguments
parse_arguments()

try:
    app = QApplication([])
    window = MainWindow()
    window.app.run()

except Exception as error:
    print(error)
    print("CLANS application cannot be executed")


