"""
FilterTableModel.py - Filtered Log Table Model

Main Functions:
- FilterTableModel: QAbstractTableModel that displays filtered log data from LogTableModel
- set_filter(): Applies log level and text filters, highlighting matched text
- data(): Returns formatted data with HTML highlighting for search terms
- row_to_origin(): Maps filtered row indices back to original log data
"""

from PyQt5.QtCore import QVariant, QAbstractTableModel, Qt

from LogLevel import LogLevel
from LogLevelColor import LogLevelColor


class FilterTableModel(QAbstractTableModel):
    # noinspection PyUnresolvedReferences
    def __init__(self, parent: 'LogViewer', log_model: 'LogTableModel'):
        self.parent = parent
        self.logModel: 'LogTableModel' = log_model
        self.logData: list[tuple[int, LogLevel, str]] = []
        super().__init__()
        self.filterText: str = ""

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return "Text"
        if orientation == Qt.Vertical:
            return self.logData[section][0] + 1
        return QVariant()

    def set_filter(self, levels: list[LogLevel], filter_text: str):
        self.beginResetModel()
        if not levels:
            levels = list(LogLevel)
        self.filterText = filter_text.lower()
        self.logData = []
        if self.filterText or len(levels) not in [0, len(LogLevel)]:
            self.logData = [
                (row, classification, line) for row, (classification, line) in enumerate(self.logModel.logData)
                if self.filterText in line.lower() and classification in levels
            ]
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.logData)

    def columnCount(self, parent=None):
        return 1  # Assuming one column: Log Line

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row, level, log_line = self.logData[index.row()]
        log_line = log_line.replace('<', '&lt;').replace('>', '&gt;')
        if role == Qt.UserRole:
            return level
        if self.filterText:
            log_line_lower = log_line.lower()
            result = ""
            line_parts = log_line_lower.split(self.filterText)
            if len(line_parts) >= 1:
                start, end, filter_len = 0, -1, len(self.filterText)
                for part in line_parts:
                    end = start + len(part)
                    result += log_line[start:end]
                    result += '<span style="background-color:#FF9632;font-weight:bold">'
                    start, end = end, end + filter_len
                    result += log_line[start:end]
                    result += '</span>'
                    start = end
                log_line = result
        if role == Qt.DisplayRole:
            return log_line
        if role == Qt.ToolTipRole:
            fg, bg = LogLevelColor(level).colors()
            return F'<div style="color:{fg};">{log_line}</div>'
        return QVariant()

    def row_to_origin(self, row: int):
        return self.logData[row][0]
