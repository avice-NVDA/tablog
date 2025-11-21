#!/home/utils/Python/builds/3.11.9-20250715/bin/python3

"""
LogViewer.py - Main Log Viewer Widget

Main Functions:
- LogViewer: Primary widget for viewing and filtering log files with dual-pane interface
- load_file(): Loads log files (plain text, gzipped, ANSI colored) and classifies log levels
- search_logs(): Applies filters by log level and search text with live highlighting
- init_shortcuts(): Sets up keyboard shortcuts for navigation (arrows, page up/down, search)
- Standalone mode: Can be run directly as a complete log viewing application
"""

import os
import sys
import traceback
from ansi2html import Ansi2HTMLConverter as a2h
from PyQt5.QtCore import Qt, QModelIndex, QPoint, QEventLoop, QObject
from PyQt5.QtGui import QFont, QColor, QCursor, QIcon, QKeySequence, QClipboard
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit, QPushButton, QWidget, QVBoxLayout, QSplitter, QHBoxLayout, QTableView,
    QMenu, QWidgetAction, QTextEdit, QLabel, QShortcut, QAction, QSizePolicy
)
from pip._internal import self_outdated_check

from common.Colorizer import Colorizer
from FilterTableModel import FilterTableModel
from LogLevel import LogLevel
from LogLevelColor import LogLevelColor
from LogLevelKeywords import LogLevelKeywords
from LogLineDelegate import LogLineDelegate
from LogTableModel import LogTableModel
# noinspection PyUnresolvedReferences
from icons_rc import *


class LogViewer(QWidget):
    def __init__(self, title: str, name: str, log_file: str, parent=None):
        self.title = title if title else ""
        self.name = name if name else os.path.basename(log_file)
        self.logFile = log_file
        self.isLog = True
        self.isZipped = False
        self.parent = parent
        self.background = Colorizer(title).hex()
        self.logLevelKeywords = LogLevelKeywords()
        super().__init__(parent)
        self.setWindowTitle(title)
        self.fileTitle = QLineEdit()
        self.splitter = QSplitter(Qt.Vertical, self)
        self.reloadButton = QPushButton()
        self.cleanLevels = QPushButton("Clear")
        self.levelButtons: dict[LogLevel, QPushButton] = {}
        self.levelCounts: dict[LogLevel, int] = {level: 0 for level in LogLevel}
        self.filteredCounts: dict[LogLevel, int] = {level: 0 for level in LogLevel}
        self.logTable = QTableView(self)
        self.logModel = LogTableModel(self)
        self.filterTable = QTableView(self)
        self.filterModel = FilterTableModel(self, self.logModel)
        self.searchEntry = QLineEdit()
        self.helpButton = QPushButton("❓ Help")
        self.init_ui()
        self.load_file(self.logFile)

    def get_background(self) -> str:
        return self.background

    def rename(self, title: str):
        self.title = title if title else self.title
        self.background = Colorizer(title).hex()
        palette = self.palette()
        palette.setColor(palette.ColorRole.Background, QColor(self.background))
        self.setPalette(palette)

    def set_link_callback(self, callback):
        self.logTable.itemDelegate().set_link_callback(callback)

    def init_ui(self):
        self.rename(self.title)
        self.setAutoFillBackground(True)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(2, 2, 2, 2)

        # File name label
        self.fileTitle.setFocusPolicy(Qt.NoFocus)
        self.fileTitle.setReadOnly(True)
        font = self.fileTitle.font()
        font.setPointSize(10), font.setBold(True)
        self.fileTitle.setFont(font), self.fileTitle.setStyleSheet("background-color: #DDDDDD;")
        self.layout().addWidget(self.fileTitle)

        splitter_img = os.path.join(os.path.dirname(__file__), "icons", "splitter5h.png")
        self.layout().addWidget(self.splitter)
        self.splitter.setStyleSheet(
            "QSplitter::handle {\n"
            "    border: 1px solid #D4D4D4;\n"
            "    background-color: #EFEFEF;\n"
            "    height: 5px;\n"
            F"    image: url('{splitter_img}');\n"
            "}"
        )

        # Table view
        self.logTable.setObjectName("logTable")
        self.logTable.setModel(self.logModel)
        self.filterTable.setObjectName("filterTable")
        self.filterTable.setModel(self.filterModel)
        for table in [self.logTable, self.filterTable]:
            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(self.show_context_menu)
        self.splitter.addWidget(self.logTable)
        bottom_section = QWidget(self)
        bottom_section.setLayout(QVBoxLayout())
        bottom_section.setContentsMargins(0, 0, 0, 0)
        bottom_section.layout().setContentsMargins(0, 0, 0, 0)
        bottom_section.layout().setSpacing(0)
        bottom_section.layout().addWidget(self.filterTable)
        self.splitter.addWidget(bottom_section)

        monospaced_font = QFont("Courier New", 10)

        for ind, table in enumerate([self.logTable, self.filterTable]):
            table.horizontalHeader().setStretchLastSection(True)
            table.setHorizontalScrollMode(QTableView.ScrollPerPixel)
            table.setAutoScroll(False)
            table.setStyleSheet(
                "QTableView {"
                "   gridline-color: transparent;"
                "   border: none;"
                "   background-color: #F8F8F8;"
                "}"
            )
            table.setFont(monospaced_font)
            delegate = LogLineDelegate(table, table == self.filterTable)
            table.setItemDelegate(delegate)

            # Set the horizontal header properties
            table.horizontalHeader().setVisible(False)

            # Set the vertical header properties
            table.verticalHeader().setDefaultSectionSize(12)  # Set the default row height (adjust as needed)
            table.verticalHeader().setVisible(True)
            table.verticalHeader().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.verticalHeader().setStyleSheet("background-color: #DDDDDD;")

            table.doubleClicked.connect(self.on_double_click)
        # allow only single selected row
        self.filterTable.setSelectionMode(QTableView.SingleSelection)
        self.filterTable.setSelectionBehavior(QTableView.SelectRows)
        self.filterTable.selectionModel().selectionChanged.connect(
            lambda selection: (
                row := self.filterModel.row_to_origin(selection.indexes()[0].row()),
                self.logTable.selectRow(row),
                self.logTable.scrollTo(self.logModel.index(row, 0), QTableView.PositionAtCenter),
                self.logTable.horizontalScrollBar().setValue(0),
            ) if selection.indexes() else self.logTable.clearSelection()
        )
        self.splitter.setSizes([400, 200])

        # Filter toolbar
        toolbar_layout = QHBoxLayout()
        self.reloadButton.setIcon(QIcon(":/reload"))
        self.reloadButton.setToolTip("Reload log file")
        self.reloadButton.clicked.connect(self.reload_file)
        toolbar_layout.addWidget(self.reloadButton)
        toolbar_layout.addWidget(QLabel(" "))
        level: LogLevel
        for level in list(LogLevel):
            level_btn = QPushButton(level.name.capitalize(), self)
            fg, bg = LogLevelColor(level).colors()
            level_btn.setToolTip(F'Show <b style="color:{fg};background-color:{bg}">{level.name}</b> log lines')
            level_btn.setCheckable(True)
            self.levelButtons[level] = level_btn
            level_btn.setChecked(False)
            level_btn.clicked.connect(self.search_logs)
            level_btn.setIcon(QIcon(F":/{level.name.lower()}"))
            toolbar_layout.addWidget(level_btn)
        toolbar_layout.addWidget(self.cleanLevels)
        toolbar_layout.addWidget(QLabel(" "))
        self.cleanLevels.setToolTip("Clear level filters")
        self.cleanLevels.setIcon(QIcon(":/clear"))
        self.cleanLevels.clicked.connect(
            lambda state: [cb.setChecked(False) for cb in self.levelButtons.values()] and self.search_logs()
        )

        self.init_search_actions()
        toolbar_layout.addWidget(self.searchEntry)
        toolbar_layout.addWidget(QLabel(" "))
        self.helpButton.setToolTip("Show help and keyboard shortcuts")
        self.helpButton.clicked.connect(self.show_help_dialog)
        toolbar_layout.addWidget(self.helpButton)
        bottom_section.layout().addLayout(toolbar_layout)

        self.init_shortcuts()

    def show_context_menu(self, position):
        table = self.sender()
        menu = QMenu(table)
        copy_action = QAction('Copy', table)
        copy_action.triggered.connect(lambda: self.copy_rows(self.logTable))
        menu.addAction(copy_action)
        menu.exec_(table.viewport().mapToGlobal(position))

    def copy_rows(self, table: QTableView):
        # get numbers of selected rows
        selection: list[int] = [ind.row() for ind in table.selectionModel().selectedRows() if ind and ind.isValid()]
        if not selection or len(selection) > 1000:
            return
        sorted_rows: list[int] = sorted(selection)
        copied_text = "\n".join(self.logModel.raw_data(row) for row in sorted_rows)
        clipboard = QApplication.clipboard()
        clipboard.setText(copied_text, QClipboard.Clipboard)
        clipboard.setText(copied_text, QClipboard.Selection)

    def init_search_actions(self):
        self.searchEntry.setPlaceholderText("Search...")
        self.searchEntry.returnPressed.connect(self.search_logs)
        action = QAction(QIcon(":/find"), "Search\tEnter", self)
        action.triggered.connect(self.search_logs)
        self.searchEntry.addAction(action, QLineEdit.TrailingPosition)
        action = QAction(QIcon(":/up"), "Next\tCtrl+Up", self)
        action.triggered.connect(lambda: self.select_finding())
        self.searchEntry.addAction(action, QLineEdit.TrailingPosition)
        action = QAction(QIcon(":/down"), "Prev\tCtrl+Down", self)
        action.triggered.connect(lambda: self.select_finding(prev=True))
        self.searchEntry.addAction(action, QLineEdit.TrailingPosition)
        action = QAction(QIcon(":/clear"), "Clear", self)
        action.triggered.connect(lambda: (self.searchEntry.setText(""), self.search_logs()))
        self.searchEntry.addAction(action, QLineEdit.TrailingPosition)

    @staticmethod
    def scroll_page(table: QTableView, up: bool):
        table.verticalScrollBar().setValue(
            table.verticalScrollBar().value() - table.verticalScrollBar().pageStep() if up
            else table.verticalScrollBar().value() + table.verticalScrollBar().pageStep()
        )

    @staticmethod
    def scroll_horizontal(table: QTableView, left: bool, step: int = 1):
        current_value = table.horizontalScrollBar().value()
        page_step = table.horizontalScrollBar().pageStep() // step
        table.horizontalScrollBar().setValue(current_value - page_step if left else current_value + page_step)

    @staticmethod
    def scroll_line(table: QTableView, up: bool):
        current_value = table.verticalScrollBar().value()
        single_step = table.verticalScrollBar().singleStep()
        table.verticalScrollBar().setValue(current_value - single_step if up else current_value + single_step)

    def init_shortcuts(self):
        QShortcut(QKeySequence("F3"), self).activated.connect(self.searchEntry.setFocus)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.searchEntry.setFocus)

        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(
            lambda: (self.searchEntry.clearFocus(), self.searchEntry.setText(""))
        )

        QShortcut(QKeySequence(Qt.Key_Left), self).activated.connect(
            lambda: self.scroll_horizontal(self.logTable, left=True, step=10)
        )
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(
            lambda: self.scroll_horizontal(self.logTable, left=False, step=10)
        )
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Left), self).activated.connect(
            lambda: self.scroll_horizontal(self.logTable, left=True, step=1)
        )
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Right), self).activated.connect(
            lambda: self.scroll_horizontal(self.logTable, left=False, step=1)
        )
        # allow select all only if the number of rows is less than 1000
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_A), self).activated.connect(
            lambda: self.logTable.selectAll() if self.logTable.model().rowCount() < 1000 else None)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_C), self).activated.connect(lambda: self.copy_rows(self.logTable))

        QShortcut(QKeySequence(Qt.Key_Up), self).activated.connect(lambda: self.scroll_line(self.logTable, up=True))
        QShortcut(QKeySequence(Qt.Key_Down), self).activated.connect(lambda: self.scroll_line(self.logTable, up=False))

        QShortcut(QKeySequence("Ctrl+Up"), self).activated.connect(lambda: self.select_finding())
        QShortcut(QKeySequence("Ctrl+Down"), self).activated.connect(lambda: self.select_finding(prev=True))

        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Home), self).activated.connect(self.logTable.scrollToTop)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_End), self).activated.connect(self.logTable.scrollToBottom)
        QShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_Home), self).activated.connect(
            self.filterTable.scrollToTop)
        QShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_End), self).activated.connect(
            self.filterTable.scrollToBottom)
        QShortcut(QKeySequence(Qt.Key_PageUp), self).activated.connect(
            lambda: self.scroll_page(self.logTable, up=True)
        )
        QShortcut(QKeySequence(Qt.Key_PageDown), self).activated.connect(
            lambda: self.scroll_page(self.logTable, up=False)
        )
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_PageUp), self).activated.connect(
            lambda: self.scroll_page(self.filterTable, up=True)
        )
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_PageDown), self).activated.connect(
            lambda: self.scroll_page(self.filterTable, up=False)
        )

    def on_double_click(self, index: QModelIndex):
        row = index.row()
        line = index.data(Qt.DisplayRole)
        if line:
            line = F'<pre style="white-space:pre-wrap;word-wrap:break-word;">{line}</pre>'
        level: LogLevel
        *orig_row, level, _ = index.model().logData[row]
        fg, bg = LogLevelColor(level).colors()
        bg = QColor(bg).darker(120).name()
        menu = QMenu(self.logTable)
        action = QWidgetAction(menu)
        text_widget = QTextEdit(menu)
        text_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        text_widget.setHtml(line)
        text_widget.setFixedWidth(int(self.logTable.width() * 0.8))
        text_widget.setReadOnly(True)
        text_widget.setStyleSheet(F"QTextEdit {{ color: {fg}; }}")
        action.setDefaultWidget(text_widget)
        menu.setStyleSheet(F"QMenu {{ border: 5px solid {bg}; }}")
        menu.addAction(action)
        mouse_pos = QCursor.pos()
        menu_size = menu.sizeHint()
        centered_pos = mouse_pos - QPoint(menu_size.width() // 2, menu_size.height() // 2)
        menu.show()
        menu.move(centered_pos)

    def select_finding(self, prev=False):
        selection = self.filterTable.selectionModel().selectedRows()
        max_row = self.filterTable.model().rowCount() - 1
        row_now = selection[0].row() if selection else max_row
        row_next = max(0, row_now + 1) if prev else min(row_now - 1, max_row)
        self.logTable.clearSelection()
        self.filterTable.selectRow(row_next)
        hor_scroll_val = self.filterTable.horizontalScrollBar().value()
        self.filterTable.scrollTo(self.filterModel.index(row_next, 0), QTableView.PositionAtCenter)
        self.filterTable.horizontalScrollBar().setValue(hor_scroll_val)

    def count_levels(self) -> None:
        """Count the number of lines for each log level."""
        self.levelCounts = {level: 0 for level in LogLevel}
        for level, _ in self.logModel.logData:
            self.levelCounts[level] = self.levelCounts.get(level, 0) + 1
    
    def count_filtered_levels(self) -> None:
        """Count the number of filtered lines for each log level."""
        self.filteredCounts = {level: 0 for level in LogLevel}
        for _, level, _ in self.filterModel.logData:
            self.filteredCounts[level] = self.filteredCounts.get(level, 0) + 1
    
    def update_level_button_text(self) -> None:
        """Update filter button text with counts."""
        search_text = self.searchEntry.text().lower()
        has_filter = bool(search_text) or any(btn.isChecked() for btn in self.levelButtons.values())
        
        for level, button in self.levelButtons.items():
            total_count = self.levelCounts.get(level, 0)
            
            if has_filter:
                filtered_count = self.filteredCounts.get(level, 0)
                button.setText(f"{level.name.capitalize()} ({filtered_count}/{total_count})")
            else:
                button.setText(f"{level.name.capitalize()} ({total_count})")

    def load_file(self, log_file: str) -> None:
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.logFile = log_file
            self.fileTitle.setText(self.logFile)
            if not self.logFile or not os.path.exists(self.logFile):
                self.logModel.update_data([
                    (LogLevel.ERROR, F"File not found: '{self.logFile}'")
                ])
                return
            self.isLog = self.logFile.endswith(".log") or self.logFile.endswith(".log.gz")
            file_type = "ASCII text"
            with os.popen(F"/usr/bin/file -bL {log_file}") as fd:
                lines = fd.read().splitlines(keepends=False)
                if lines:
                    file_type = lines[0].strip()
            if "ASCII text" in file_type:
                if "with escape sequences" in file_type:
                    html_content=a2h(inline=True).convert(open(self.logFile).read(), full=False)
                    lines = html_content.splitlines(keepends=False)
                else:
                    with open(self.logFile, 'r') as fd:
                        lines = fd.read().splitlines(keepends=False)
            elif "gzip compressed data" in file_type:
                with os.popen(F"/usr/bin/zcat -vq {self.logFile}") as fd:
                    lines = fd.read().splitlines(keepends=False)
            else:
                self.logModel.update_data([
                    (LogLevel.ERROR, F"Unsupported file type: '{file_type}'")
                ])
                return
            if self.isLog:
                self.logModel.update_data(self.logLevelKeywords.classify_lines(lines))
            else:
                self.logModel.update_data([(LogLevel.TEXT, line) for line in lines])
                for b in self.levelButtons.values():
                    b.setChecked(False)
                    b.setEnabled(False)
                self.cleanLevels.setEnabled(False)
            self.logTable.resizeColumnToContents(0)

            self.count_levels()
            self.search_logs()
            for table in [self.logTable, self.filterTable]:
                table.scrollTo(self.logModel.index(0, 0), QTableView.PositionAtTop)
        except Exception as e:
            error_message = F"-ERROR- loading file: '{self.logFile}': {e}\n{traceback.format_exc()}"
            print(error_message)
            self.logModel.update_data([
                (LogLevel.ERROR, F"Error loading file: '{self.logFile}':"),
                (LogLevel.ERROR, error_message)
            ])
        finally:
            QApplication.restoreOverrideCursor()

    def reload_file(self):
        self.load_file(self.logFile)
        self.search_logs()
        self.logTable.scrollToBottom()

    def search_logs(self):
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.filterModel.beginResetModel()
            levels = [level for level in list(LogLevel) if self.levelButtons[level].isChecked()]
            search_text = self.searchEntry.text().lower()
            self.filterModel.set_filter(levels, search_text)
            self.filterTable.resizeColumnToContents(0)
        finally:
            self.filterModel.endResetModel()
            QApplication.restoreOverrideCursor()
        
        # Update counts after filtering
        self.count_filtered_levels()
        self.update_level_button_text()
        
        row_count = self.filterModel.rowCount()
        if row_count > 0:
            QApplication.processEvents(flags=QEventLoop.ExcludeUserInputEvents)
            self.filterTable.scrollTo(self.filterModel.index(row_count - 1, 0), QTableView.PositionAtTop)
            self.filterTable.selectRow(row_count - 1)

    def show_help_dialog(self):
        """Show the help dialog with tabs."""
        from PyQt5.QtWidgets import QDialog, QTabWidget, QTextBrowser, QVBoxLayout, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("TabLog Help")
        dialog.setModal(True)
        dialog.resize(700, 500)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Filters Tab
        filters_tab = QTextBrowser()
        filters_tab.setOpenExternalLinks(False)
        filters_tab.setHtml(self._get_filters_help_html())
        tabs.addTab(filters_tab, "Filters")
        
        # Search Tab
        search_tab = QTextBrowser()
        search_tab.setHtml(self._get_search_help_html())
        tabs.addTab(search_tab, "Search")
        
        # Shortcuts Tab
        shortcuts_tab = QTextBrowser()
        shortcuts_tab.setHtml(self._get_shortcuts_help_html())
        tabs.addTab(shortcuts_tab, "Shortcuts")
        
        # About Tab
        about_tab = QTextBrowser()
        about_tab.setOpenExternalLinks(True)
        about_tab.setHtml(self._get_about_help_html())
        tabs.addTab(about_tab, "About")
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def _get_filters_help_html(self) -> str:
        """Generate HTML for filters help tab."""
        return """
        <html>
        <head><style>
            body { font-family: Arial, sans-serif; padding: 15px; }
            h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            h3 { color: #34495e; margin-top: 20px; }
            .level { padding: 10px; margin: 10px 0; border-left: 4px solid; }
            .text { background: #f2f2f2; border-color: #95a5a6; }
            .debug { background: #f8f8f8; border-color: #808080; color: #808080; }
            .info { background: #ebf5fb; border-color: #3498db; color: #232B99; }
            .warning { background: #fffacd; border-color: #f39c12; }
            .error { background: #fadbd8; border-color: #e74c3c; }
            code { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; }
            .tip { background: #d5f4e6; padding: 10px; margin: 10px 0; border-left: 4px solid #27ae60; }
        </style></head>
        <body>
            <h2>Filter Buttons</h2>
            <p>TabLog automatically classifies log lines into different levels. Use the filter buttons to show only specific log levels.</p>
            
            <div class="level text">
                <h3>🔵 Text (Level 1)</h3>
                <p><b>Purpose:</b> Regular text lines without specific log level markers</p>
                <p><b>Patterns matched:</b> Any line that doesn't match other levels</p>
                <p><b>Example:</b> <code>Processing started...</code></p>
            </div>
            
            <div class="level debug">
                <h3>🔍 Debug (Level 2)</h3>
                <p><b>Purpose:</b> Detailed diagnostic information for debugging</p>
                <p><b>Patterns matched:</b> Lines starting with or containing:</p>
                <ul>
                    <li><code>DEBUG</code>, <code>D:</code>, <code>Debug:</code></li>
                    <li><code>-D-</code>, <code>-Debug-</code></li>
                    <li><code>[DEBUG]</code>, <code>DEBUG]</code></li>
                </ul>
                <p><b>Example:</b> <code>DEBUG Initializing module</code></p>
            </div>
            
            <div class="level info">
                <h3>ℹ️ Info (Level 3)</h3>
                <p><b>Purpose:</b> Informational messages about normal program flow</p>
                <p><b>Patterns matched:</b> Lines starting with or containing:</p>
                <ul>
                    <li><code>INFO</code>, <code>I:</code>, <code>Information:</code></li>
                    <li><code>-I-</code>, <code>-Info-</code></li>
                    <li><code>[INFO]</code>, <code>INFO]</code></li>
                </ul>
                <p><b>Example:</b> <code>INFO Process completed successfully</code></p>
            </div>
            
            <div class="level warning">
                <h3>⚠️ Warning (Level 4)</h3>
                <p><b>Purpose:</b> Potential issues that aren't critical but need attention</p>
                <p><b>Patterns matched:</b> Lines starting with or containing:</p>
                <ul>
                    <li><code>WARNING</code>, <code>W:</code>, <code>Warning:</code></li>
                    <li><code>-W-</code>, <code>-Warning-</code></li>
                    <li><code>[WARNING]</code>, <code>[WARN]</code>, <code>WARN]</code></li>
                </ul>
                <p><b>Example:</b> <code>WARNING Slow network detected</code></p>
            </div>
            
            <div class="level error">
                <h3>❌ Error (Level 5)</h3>
                <p><b>Purpose:</b> Serious errors, fatal issues, or critical problems</p>
                <p><b>Patterns matched:</b> Lines starting with or containing:</p>
                <ul>
                    <li><code>ERROR</code>, <code>E:</code>, <code>Error:</code></li>
                    <li><code>FATAL</code>, <code>F:</code>, <code>Fatal:</code></li>
                    <li><code>CRITICAL</code>, <code>C:</code>, <code>Critical:</code></li>
                    <li><code>Segmentation fault encountered</code></li>
                    <li><code>[ERROR]</code>, <code>[FATAL]</code>, <code>[CRITICAL]</code></li>
                </ul>
                <p><b>Example:</b> <code>ERROR Connection failed</code></p>
            </div>
            
            <h2>Using Filters</h2>
            <div class="tip">
                <p><b>💡 Tip:</b> Click multiple filter buttons to combine them (OR logic)</p>
                <p><b>Example:</b> Click Warning + Error to see all warnings and errors</p>
            </div>
            
            <h3>Filter Counts</h3>
            <p>Each button shows the count of matching lines:</p>
            <ul>
                <li><b>Normal view:</b> <code>Error (12)</code> = 12 error lines total</li>
                <li><b>When filtering:</b> <code>Error (5/12)</code> = 5 matching your search, 12 total</li>
            </ul>
            
            <h3>Clear Button</h3>
            <p>Click the <b>Clear</b> button (🧹) to uncheck all filters and show all lines.</p>
        </body>
        </html>
        """
    
    def _get_search_help_html(self) -> str:
        """Generate HTML for search help tab."""
        return """
        <html>
        <head><style>
            body { font-family: Arial, sans-serif; padding: 15px; }
            h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            h3 { color: #34495e; margin-top: 20px; }
            code { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; }
            .highlight { background: #FF9632; font-weight: bold; padding: 2px 4px; }
            .tip { background: #d5f4e6; padding: 10px; margin: 10px 0; border-left: 4px solid #27ae60; }
            ul { line-height: 1.8; }
        </style></head>
        <body>
            <h2>Search Features</h2>
            
            <h3>Basic Search</h3>
            <p>Type text in the search box and press <code>Enter</code> or click the search icon (🔍).</p>
            <ul>
                <li>Search is <b>case-insensitive</b></li>
                <li>Matches are <span class="highlight">highlighted in orange</span></li>
                <li>Filtered results appear in the bottom pane</li>
            </ul>
            
            <h3>Search Navigation</h3>
            <table border="1" cellpadding="8" style="border-collapse: collapse; margin: 10px 0;">
                <tr style="background: #3498db; color: white;">
                    <th>Button/Key</th>
                    <th>Action</th>
                </tr>
                <tr>
                    <td><code>🔍</code> or <code>Enter</code></td>
                    <td>Execute search</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td><code>⬆</code> or <code>Ctrl+Up</code></td>
                    <td>Go to previous match</td>
                </tr>
                <tr>
                    <td><code>⬇</code> or <code>Ctrl+Down</code></td>
                    <td>Go to next match</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td><code>✖</code> (Clear icon)</td>
                    <td>Clear search text</td>
                </tr>
                <tr>
                    <td><code>Ctrl+F</code> or <code>F3</code></td>
                    <td>Focus search box</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td><code>Esc</code></td>
                    <td>Clear search and unfocus</td>
                </tr>
            </table>
            
            <h3>Combining Search with Filters</h3>
            <p>You can combine text search with log level filters:</p>
            <ol>
                <li>Click one or more filter buttons (e.g., <b>Warning</b> + <b>Error</b>)</li>
                <li>Type search text (e.g., "timeout")</li>
                <li>See only warnings/errors containing "timeout"</li>
            </ol>
            
            <div class="tip">
                <p><b>💡 Pro Tip:</b> Use search to find specific patterns, then use filter buttons to focus on important log levels!</p>
            </div>
            
            <h3>Search Results</h3>
            <ul>
                <li>Results show in the <b>bottom pane</b></li>
                <li>Click a result to see it in context in the <b>top pane</b></li>
                <li>The top pane auto-scrolls and highlights the selected line</li>
            </ul>
        </body>
        </html>
        """
    
    def _get_shortcuts_help_html(self) -> str:
        """Generate HTML for keyboard shortcuts help tab."""
        return """
        <html>
        <head><style>
            body { font-family: Arial, sans-serif; padding: 15px; }
            h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            h3 { color: #34495e; margin-top: 20px; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th { background: #3498db; color: white; padding: 10px; text-align: left; }
            td { padding: 8px; border-bottom: 1px solid #ddd; }
            tr:nth-child(even) { background: #f8f9fa; }
            .key { background: #ecf0f1; padding: 3px 8px; border-radius: 3px; font-family: monospace; white-space: nowrap; }
        </style></head>
        <body>
            <h2>Keyboard Shortcuts</h2>
            
            <h3>📁 File Operations</h3>
            <table>
                <tr><th>Shortcut</th><th>Action</th></tr>
                <tr><td><span class="key">Ctrl+O</span></td><td>Open file</td></tr>
                <tr><td><span class="key">Ctrl+W</span></td><td>Close current tab</td></tr>
                <tr><td><span class="key">Ctrl+R</span> or <span class="key">F5</span></td><td>Reload current file</td></tr>
                <tr><td><span class="key">Ctrl+Q</span></td><td>Quit application</td></tr>
            </table>
            
            <h3>🔍 Search</h3>
            <table>
                <tr><th>Shortcut</th><th>Action</th></tr>
                <tr><td><span class="key">Ctrl+F</span> or <span class="key">F3</span></td><td>Focus search box</td></tr>
                <tr><td><span class="key">Enter</span></td><td>Execute search</td></tr>
                <tr><td><span class="key">Ctrl+Up</span></td><td>Previous search result</td></tr>
                <tr><td><span class="key">Ctrl+Down</span></td><td>Next search result</td></tr>
                <tr><td><span class="key">Esc</span></td><td>Clear search and unfocus</td></tr>
            </table>
            
            <h3>🧭 Navigation</h3>
            <table>
                <tr><th>Shortcut</th><th>Action</th></tr>
                <tr><td><span class="key">↑</span> / <span class="key">↓</span></td><td>Scroll up/down one line</td></tr>
                <tr><td><span class="key">←</span> / <span class="key">→</span></td><td>Scroll left/right (fast)</td></tr>
                <tr><td><span class="key">Ctrl+←</span> / <span class="key">Ctrl+→</span></td><td>Scroll left/right (slow)</td></tr>
                <tr><td><span class="key">Page Up</span> / <span class="key">Page Down</span></td><td>Page up/down in main view</td></tr>
                <tr><td><span class="key">Ctrl+Page Up</span> / <span class="key">Ctrl+Page Down</span></td><td>Page up/down in filter view</td></tr>
                <tr><td><span class="key">Ctrl+Home</span></td><td>Jump to top of log</td></tr>
                <tr><td><span class="key">Ctrl+End</span></td><td>Jump to bottom of log</td></tr>
                <tr><td><span class="key">Ctrl+Shift+Home</span></td><td>Jump to top of filtered view</td></tr>
                <tr><td><span class="key">Ctrl+Shift+End</span></td><td>Jump to bottom of filtered view</td></tr>
            </table>
            
            <h3>📋 Clipboard</h3>
            <table>
                <tr><th>Shortcut</th><th>Action</th></tr>
                <tr><td><span class="key">Ctrl+C</span></td><td>Copy selected rows</td></tr>
                <tr><td><span class="key">Ctrl+A</span></td><td>Select all (if less than 1000 rows)</td></tr>
                <tr><td><span class="key">Right-click</span></td><td>Context menu with Copy option</td></tr>
            </table>
            
            <h3>💡 Tips</h3>
            <ul style="line-height: 1.8;">
                <li>Double-click a log line to view it in a popup</li>
                <li>Click file paths in logs to open them in a new tab</li>
                <li>Use <span class="key">Shift+Click</span> to select multiple rows</li>
                <li>Right-click selected rows and choose "Copy" to copy to clipboard</li>
            </ul>
        </body>
        </html>
        """
    
    def _get_about_help_html(self) -> str:
        """Generate HTML for about help tab."""
        return """
        <html>
        <head><style>
            body { font-family: Arial, sans-serif; padding: 15px; }
            h1 { color: #2c3e50; text-align: center; }
            h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }
            .logo { text-align: center; font-size: 48px; margin: 20px 0; }
            .version { text-align: center; color: #7f8c8d; font-size: 14px; }
            ul { line-height: 1.8; }
            .feature { margin: 10px 0; }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style></head>
        <body>
            <div class="logo">📋</div>
            <h1>TabLog</h1>
            <p class="version">Version 1.1.0</p>
            <p style="text-align: center;">A powerful PyQt5-based log viewing application</p>
            
            <h2>Features</h2>
            <ul>
                <li class="feature">✅ <b>Multi-tab Interface</b> - Open multiple log files in separate tabs</li>
                <li class="feature">✅ <b>Smart Log Classification</b> - Automatically detects DEBUG, INFO, WARNING, ERROR levels</li>
                <li class="feature">✅ <b>Advanced Filtering</b> - Filter by log level and search text with live highlighting</li>
                <li class="feature">✅ <b>Level Counts</b> - See how many lines of each level exist</li>
                <li class="feature">✅ <b>Clickable File Links</b> - File paths in logs become clickable links</li>
                <li class="feature">✅ <b>Keyboard Shortcuts</b> - Full keyboard navigation support</li>
                <li class="feature">✅ <b>Multiple Formats</b> - Supports plain text, gzipped, and ANSI-colored logs</li>
                <li class="feature">✅ <b>Dual-Pane View</b> - See full log and filtered results simultaneously</li>
                <li class="feature">✅ <b>Copy Support</b> - Copy selected lines to clipboard</li>
            </ul>
            
            <h2>File Support</h2>
            <ul>
                <li>Plain text (.log, .txt)</li>
                <li>Gzipped logs (.log.gz)</li>
                <li>ANSI colored logs</li>
                <li>Clickable file paths (.log, .tcl, .yaml, .cfg, .txt, .py)</li>
            </ul>
            
            <h2>Links</h2>
            <ul>
                <li>📦 GitHub: <a href="https://github.com/avice-NVDA/tablog">https://github.com/avice-NVDA/tablog</a></li>
                <li>📄 Documentation: See README.md and QUICK_START.md</li>
            </ul>
            
            <h2>Requirements</h2>
            <ul>
                <li>Python 3.11+</li>
                <li>PyQt5</li>
                <li>ansi2html (for ANSI color support)</li>
            </ul>
            
            <h2>Credits</h2>
            <p>Developed by avice @ NVIDIA</p>
            <p style="margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 12px;">
                © 2025 TabLog. All rights reserved.
            </p>
        </body>
        </html>
        """


if __name__ == '__main__':
    # Set XDG_RUNTIME_DIR to prevent Qt warning
    if 'XDG_RUNTIME_DIR' not in os.environ:
        os.environ['XDG_RUNTIME_DIR'] = f'/tmp/runtime-{os.getenv("USER", "user")}'
    
    app = QApplication(sys.argv)
    file = "/home/scratch.avice_vlsi/tablog/example.log"
    viewer = LogViewer("test_exp4", os.path.basename(file), file)
    viewer.show()
    viewer.setGeometry(400, 200, 1000, 800)
    sys.exit(app.exec_())
