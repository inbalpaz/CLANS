import sys
from PyQt5.QtWidgets import QApplication
from clans.clans.io.parser import parse_arguments
from clans.clans.GUI.main_window import MainWindow
import clans.config as cfg
from clans.clans_cmd import run_cmd


def main():

    # Parse the command-line arguments
    error = parse_arguments()

    if error is not None:
        print(error)
        exit()

    # Run the application in command-line mode (no GUI)
    if cfg.run_params['no_gui']:
        try:
            run_cmd()

        except Exception as error:
            print(error)
            print("CLANS application cannot be executed")

    # Open the GUI
    else:
        try:
            app = QApplication([])
            window = MainWindow()
            window.app.run()

        except Exception as error:
            print(error)
            print("CLANS application cannot be executed")


if __name__ == '__main__':
    sys.exit(main())