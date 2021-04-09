# The main script for running clans as a graphical application #
################################################################
import clans.io.parser as parser
from PyQt5.QtWidgets import QApplication
import clans.GUI.main_window as gui

# Parse the command-line arguments
parser.parse_arguments()

app = QApplication([])
window = gui.MainWindow()
window.app.run()
