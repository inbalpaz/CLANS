# The main script for running clans as a graphical application #
################################################################
import clans.config as cfg
import clans.io.parser as parser
from PyQt5.QtWidgets import QApplication
import clans.graphics.gui as gui

# Parse the command-line arguments
parser.parse_arguments()

app = QApplication([])
window = gui.MainWindow()
window.app.run()
