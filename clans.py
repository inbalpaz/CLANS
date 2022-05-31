# The main script for running clans as a graphical application #
################################################################
from PyQt5.QtWidgets import QApplication
import clans.io.parser as parser
import clans.GUI.main_window as gui

# Parse the command-line arguments
parser.parse_arguments()

try:
    app = QApplication([])
    window = gui.MainWindow()
    window.app.run()

except Exception as error:
    print(error)
    print("CLANS application cannot be executed")


