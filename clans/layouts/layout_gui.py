from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import clans.layouts.fruchterman_reingold as fr
import time


class LayoutCalculationSignals(QObject):
    finished_iteration = pyqtSignal()
    stopped = pyqtSignal()


class LayoutCalculationWorker(QRunnable):
    def __init__(self):
        super().__init__()

        self.signals = LayoutCalculationSignals()

        self.is_stopped = False

    @pyqtSlot()
    def run(self):
        while self.is_stopped is False:
            fr.calculate_new_positions()
            self.signals.finished_iteration.emit()
            time.sleep(0.01)

        if self.is_stopped is True:
            self.signals.stopped.emit()

    def stop(self):
        self.is_stopped = True
