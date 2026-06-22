from PyQt6.QtCore import QThread, pyqtSignal


class ApiWorker(QThread):
    done  = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self._func   = func
        self._args   = args
        self._kwargs = kwargs

    def run(self):
        try:
            self.done.emit(self._func(*self._args, **self._kwargs))
        except Exception as e:
            self.error.emit(str(e))
