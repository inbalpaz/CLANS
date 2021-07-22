from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import time


class LayoutCalculationSignals(QObject):
    finished_iteration = pyqtSignal()
    stopped = pyqtSignal()


class LayoutCalculationWorker(QRunnable):
    def __init__(self, layout_object, is_subset_mode):
        super().__init__()

        self.layout_object = layout_object
        self.is_subset_mode = is_subset_mode

        self.signals = LayoutCalculationSignals()

        self.is_stopped = False

    @pyqtSlot()
    def run(self):
        while self.is_stopped is False:
            self.layout_object.calculate_new_positions(self.is_subset_mode)
            self.signals.finished_iteration.emit()
            time.sleep(0.01)

        if self.is_stopped is True:
            self.signals.stopped.emit()

    def stop(self):
        self.is_stopped = True
