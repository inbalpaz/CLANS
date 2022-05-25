from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import time
import clans.config as cfg


class LayoutCalculationSignals(QObject):
    finished_iteration = pyqtSignal()
    stopped = pyqtSignal(str)


class LayoutCalculationWorker(QRunnable):
    def __init__(self, layout_object, is_subset_mode):
        super().__init__()

        self.layout_object = layout_object
        self.is_subset_mode = is_subset_mode

        self.signals = LayoutCalculationSignals()

        self.is_stopped = False

    @pyqtSlot()
    def run(self):
        error = ""

        while self.is_stopped is False:

            try:
                self.layout_object.calculate_new_positions(self.is_subset_mode)
            except Exception as error:
                if cfg.run_params['is_debug_mode']:
                    print("\nError in " + self.layout_object.calculate_new_positions.__globals__['__file__'] +
                          " (calculate_new_positions):")
                    print(error)
                cfg.run_params['is_problem'] = True
                cfg.run_params['error'] = "An error has occurred during clustering"
                self.is_stopped = True
                self.signals.stopped.emit(cfg.run_params['error'])
                return

            self.signals.finished_iteration.emit()
            time.sleep(0.01)

        if self.is_stopped is True:
            self.signals.stopped.emit(error)

    def stop(self):
        self.is_stopped = True
