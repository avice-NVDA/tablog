"""
LogTableModel.py - Log Data Table Model

Main Functions:
- LogTableModel: QAbstractTableModel that holds and displays log data with levels
- update_data(): Updates the model with new log data (level, text) tuples
- data(): Provides formatted data for display, including HTML escaping and tooltips
- raw_data(): Returns unformatted log line text for copying
"""

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant

from LogLevel import LogLevel
from LogLevelColor import LogLevelColor


class LogTableModel(QAbstractTableModel):
    # noinspection PyUnresolvedReferences
    def __init__(self, parent: 'LogViewer'):
        self.parent = parent
        super().__init__()
        self.logData: list[tuple[LogLevel, str]] = []

    def rowCount(self, parent=None):
        return len(self.logData)

    def columnCount(self, parent=None):
        return 1  # Assuming one column: Log Line

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        level, log_line = self.logData[index.row()]
        log_line = log_line.replace('<', '&lt;').replace('>', '&gt;')
        if role == Qt.UserRole:
            return level
        if role == Qt.DisplayRole:
            return log_line
        if role == Qt.ToolTipRole:
            fg, bg = LogLevelColor(level).colors()
            return F'<div style="color:{fg};">{log_line}</div>'
        return QVariant()

    def raw_data(self, row: int) -> str:
        return self.logData[row][1]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return "Text"
        if orientation == Qt.Vertical:
            return section + 1
        return QVariant()

    def update_data(self, new_data: list[tuple[LogLevel, str]]):
        self.beginResetModel()
        self.logData = new_data
        self.endResetModel()
