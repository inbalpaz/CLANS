import sys
import os
import shutil
from PyQt5.QtWidgets import QApplication
from clans.clans.io.parser import parse_arguments
from clans.clans.GUI.main_window import MainWindow
import clans.config as cfg
from clans.clans_cmd import run_cmd


def copy_dir(root_src_dir, root_dst_dir):

    os.makedirs(root_dst_dir)
    if cfg.run_params['is_debug_mode']:
        print("Copy files to directory " + root_dst_dir)

    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if not os.path.exists(dst_file):
                shutil.copy(src_file, dst_dir)


def main():

    cfg.run_params['working_dir'] = os.getcwd()

    # Parse the command-line arguments
    try:
        error = parse_arguments()

        if error is not None:
            print(error)
            exit()

    except Exception as error:
        print(error)
        print("Cannot parse the command-line arguments")

    # Check if 'input_example' directory exists in working directory. If not, copy it
    input_example_local_dir = cfg.run_params['working_dir'] + '/clans/input_example/'
    if not os.path.exists(input_example_local_dir):
        try:
            copy_dir(cfg.input_example_dir, input_example_local_dir)

        except Exception as error:
            print(error)
            print("Cannot copy the 'input_example' directory to the working directory. Continue without...")

    # Run the application in command-line mode (no GUI)
    if cfg.run_params['no_gui']:
        try:
            run_cmd()

        except Exception as error:
            print(error)
            print("CLANS application cannot be executed in command-line mode")
            exit()

    # Open the GUI
    else:
        try:
            app = QApplication([])
            window = MainWindow()
            window.show()
            sys.exit(app.exec_())

        except Exception as error:
            print(error)
            print("CLANS application cannot be executed")


if __name__ == '__main__':
    sys.exit(main())
