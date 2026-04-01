from PyQt6.QtCore import QObject, pyqtSignal

class DataEmitter(QObject):
    data_changed = pyqtSignal()  # Signal emitted when data is modified