from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import clans.config as cfg
import clans.clans.io.file_formats.clans_format as clans
import clans.clans.io.file_formats.tab_delimited_format as tab
import clans.clans.data.sequence_pairs as sp
import clans.clans.taxonomy.taxonomy as tax
import time


class ReadInputSignals(QObject):
    finished = pyqtSignal(int)


class ReadInputWorker(QRunnable):
    def __init__(self, format):
        super().__init__()

        self.signals = ReadInputSignals()

        if format == 'clans':
            self.format_object = clans.ClansFormat()
        else:
            self.format_object = tab.DelimitedFormat()

        self.file_name = cfg.run_params['input_file']

        self.before = None
        self.after = None

    def load_complete(self):

        # If the file is valid without errors, fill the sequences information in the related global variables
        if self.format_object.file_is_valid == 1:

            self.before = time.time()

            try:
                self.format_object.fill_values()
            except Exception as error:
                if cfg.run_params['is_debug_mode']:
                    print("\nError in " + self.format_object.fill_values.__globals__['__file__'] + " (fill_values):")
                    print(error)
                cfg.run_params['is_problem'] = True
                cfg.run_params['error'] = "An error has occurred: the input file has some problem or inconsistency.\n" \
                                          #"Please correct the file and try to reload."
                self.signals.finished.emit(1)
                return

            if cfg.run_params['is_debug_mode']:
                self.after = time.time()
                duration = (self.after - self.before)
                print("Filling connections and groups took " + str(duration) + " seconds")

            # Build the list of connected pairs (non-redundant, [indexi][indexj]) for the edges display
            self.before = time.time()

            try:
                sp.define_connected_sequences_list()

            except Exception as error:
                if cfg.run_params['is_debug_mode']:
                    print("\nError in " + sp.define_connected_sequences_list.__globals__['__file__'] +
                          " (define_connected_sequences_list):")
                    print(error)
                cfg.run_params['is_problem'] = True
                cfg.run_params['error'] = "An error has occurred: the input file has some problem or inconsistency.\n" \
                                          "Please correct the file and try to reload."
                self.signals.finished.emit(1)
                return

            if cfg.run_params['is_debug_mode']:
                self.after = time.time()
                duration = (self.after - self.before)
                print("Building the list of connected pairs took " + str(duration) + " seconds")

            self.signals.finished.emit(0)

        # The file has an error
        else:
            cfg.run_params['is_problem'] = True
            cfg.run_params['error'] = self.format_object.error
            self.signals.finished.emit(1)

    @pyqtSlot()
    def run(self):

        self.before = time.time()

        # Read the input file
        try:
            self.format_object.read_file(cfg.run_params['input_file'])

        except Exception as error:
            if cfg.run_params['is_debug_mode']:
                print("\nError in " + self.format_object.read_file.__globals__['__file__'] + " (read_file):")
                print(error)
            cfg.run_params['is_problem'] = True
            cfg.run_params['error'] = "An error has occurred: the input file has some problem or inconsistency.\n" \
                                      "Please correct the file and try to reload."
            self.signals.finished.emit(1)
            return

        if cfg.run_params['is_debug_mode']:
            self.after = time.time()
            duration = (self.after - self.before)
            print("Reading the file took " + str(duration) + " seconds")

        # Create and fill the main data-structures
        self.load_complete()


class ReadMetadataSignals(QObject):
    finished = pyqtSignal(dict, str)


class ReadMetadataWorker(QRunnable):
    def __init__(self, file):
        super().__init__()

        self.signals = ReadMetadataSignals()
        self.file = file

    def get_metadata(self):

        format_obj = tab.DelimitedFormat()
        params_dict = dict()

        # Read the metadata file
        try:
            params_dict, error = format_obj.read_metadata(self.file)

        except Exception as err:
            if cfg.run_params['is_debug_mode']:
                print("\nError in " + format_obj.read_metadata.__globals__['__file__'] + " (read_metadata):")
                print(err)
            error = "An error has occurred: the uploaded metadata file has some problem or inconsistency.\n" \
                    "Please correct the file and try to reload."

        self.signals.finished.emit(params_dict, error)

    @pyqtSlot()
    def run(self):
        self.get_metadata()


class ReadMetadataGroupsSignals(QObject):
    finished = pyqtSignal(dict, str)


class ReadMetadataGroupsWorker(QRunnable):
    def __init__(self, file):
        super().__init__()

        self.signals = ReadMetadataGroupsSignals()
        self.file = file

    def get_metadata(self):

        format_obj = tab.DelimitedFormat()
        groups_dict = dict()

        # Read the groups file
        try:
            groups_dict, error = format_obj.read_metadata_groups(self.file)

        except Exception as err:
            if cfg.run_params['is_debug_mode']:
                print("\nError in " + format_obj.read_metadata_groups.__globals__['__file__'] + " (read_metadata_groups):")
                print(err)
            error = "An error has occurred: the uploaded groups file has some problem or inconsistency.\n" \
                    "Please correct the file and try to reload."

        self.signals.finished.emit(groups_dict, error)

    @pyqtSlot()
    def run(self):
        self.get_metadata()


class TaxonomySignals(QObject):
    finished = pyqtSignal(str)


class TaxonomyWorker(QRunnable):
    def __init__(self):
        super().__init__()

        self.signals = TaxonomySignals()

        self.before = None
        self.after = None

    def get_hierarchy(self):

        # Search for organisms in the sequence headers and init the taxonomy dict
        try:
            error = tax.init_taxonomy_dict()
        except Exception as err:
            if cfg.run_params['is_debug_mode']:
                print("\nError in " + tax.init_taxonomy_dict.__globals__['__file__'] + " (init_taxonomy_dict):")
                print(err)
            error = "An error has occurred while searching for taxonomic information.\n" \
                    "This feature cannot be applied on the current dataset."
            cfg.run_params['finished_taxonomy_search'] = True
            time.sleep(0.01)
            self.signals.finished.emit(error)
            return

        if not cfg.run_params['is_taxonomy_available']:
            cfg.run_params['finished_taxonomy_search'] = True
            time.sleep(0.01)
            self.signals.finished.emit(error)
            return

        # Get the taxonomic hierarchy for all the organism names that were found in the input file
        self.before = time.time()

        try:
            error = tax.get_taxonomy_hierarchy()
        except Exception as err:
            if cfg.run_params['is_debug_mode']:
                print("\nError in " + tax.get_taxonomy_hierarchy.__globals__['__file__'] + " (get_taxonomy_hierarchy):")
                print(err)
            error = "An error has occurred while searching for taxonomic information.\n" \
                    "This feature cannot be applied on the current dataset."
            cfg.run_params['finished_taxonomy_search'] = True
            time.sleep(0.01)
            self.signals.finished.emit(error)
            return

        if not cfg.run_params['is_taxonomy_available']:
            cfg.run_params['finished_taxonomy_search'] = True
            time.sleep(0.01)
            self.signals.finished.emit(error)
            return

        if cfg.run_params['is_debug_mode']:
            self.after = time.time()
            duration = (self.after - self.before)
            print("Getting the taxonomy hierarchy took " + str(duration) + " seconds")
            if cfg.run_params['is_taxonomy_available']:
                print("Successfully found hierarchy for " + str(len(cfg.taxonomy_dict)) + " taxa")
            else:
                print("No organism was found in the taxonomy file - feature is not available")

        self.before = time.time()
        try:
            tax.assign_sequences_to_tax_level()
        except Exception as err:
            if cfg.run_params['is_debug_mode']:
                print("\nError in " + tax.assign_sequences_to_tax_level.__globals__['__file__']
                      + " (assign_sequences_to_tax_level):")
                print(err)
            error = "An error has occurred while searching for taxonomic information.\n" \
                    "This feature cannot be applied on the current dataset."
            cfg.run_params['finished_taxonomy_search'] = True
            time.sleep(0.01)
            self.signals.finished.emit(error)
            return

        if cfg.run_params['is_debug_mode']:
            self.after = time.time()
            duration = (self.after - self.before)
            print("Assigning sequences to taxonomic ranks took " + str(duration) + " seconds")

        cfg.run_params['finished_taxonomy_search'] = True
        self.signals.finished.emit(error)

    @pyqtSlot()
    def run(self):
        self.get_hierarchy()




