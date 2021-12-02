from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import clans.config as cfg
import clans.io.file_formats.clans_format as clans
import clans.io.file_formats.clans_minimal_format as clans_mini
import clans.io.file_formats.tab_delimited_format as tab
import clans.data.sequence_pairs as sp
import time


class ReadInputSignals(QObject):
    finished = pyqtSignal(int, str)


class ReadInputWorker(QRunnable):
    def __init__(self, format):
        super().__init__()

        self.signals = ReadInputSignals()

        if format == 'clans':
            self.format_object = clans.ClansFormat()
        elif format == 'mini_clans':
            self.format_object = clans_mini.ClansMinimalFormat()
        else:
            self.format_object = tab.DelimitedFormat()

        self.before = None
        self.after = None

    def load_complete(self):

        file_name = self.format_object.file_name

        # If the file is valid without errors, fill the sequences information in the related global variables
        if self.format_object.file_is_valid == 1:

            self.before = time.time()
            self.format_object.fill_values()

            if cfg.run_params['is_debug_mode']:
                self.after = time.time()
                duration = (self.after - self.before)
                print("Filling connections and groups took " + str(duration) + " seconds")

            # Build the list of connected pairs (non-redundant, [indexi][indexj]) for the edges display
            self.before = time.time()
            sp.define_connected_sequences_list()

            if cfg.run_params['is_debug_mode']:
                self.after = time.time()
                duration = (self.after - self.before)
                print("Building the list of connected pairs took " + str(duration) + " seconds")

            self.signals.finished.emit(0, file_name)

        # The file has an error
        else:
            cfg.run_params['is_problem'] = True
            cfg.run_params['error'] = self.format_object.error
            self.signals.finished.emit(1, file_name)

    @pyqtSlot()
    def run(self):

        self.before = time.time()
        self.format_object.read_file(cfg.run_params['input_file'])

        if cfg.run_params['is_debug_mode']:
            self.after = time.time()
            duration = (self.after - self.before)
            print("Reading the file took " + str(duration) + " seconds")

        self.load_complete()


class FileHandler:
    def __init__(self, file_format):
        self.file_format = file_format
        self.file_path = ""
        self.format_object = ""

        if self.file_format == 'clans':
            self.format_object = clans.ClansFormat()
        elif self.file_format == 'mini_clans':
            self.format_object = clans_mini.ClansMinimalFormat()
        else:
            self.format_object = tab.DelimitedFormat()

    def write_file(self, file_path, is_param):
        self.file_path = file_path
        self.format_object.write_file(file_path, is_param)

        if self.format_object.error == "":
            print("Successfully saved to: " + str(self.file_path))




