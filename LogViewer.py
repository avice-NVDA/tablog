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
from PyQt5.QtCore import Qt, QModelIndex, QPoint, QEventLoop, QObject, QSettings
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
        
        # Font size settings
        self.default_font_size = 10
        self.min_font_size = 6
        self.max_font_size = 24
        # Load saved font size preference or use default
        settings = QSettings("Avice", "TabLog")
        self.current_font_size = settings.value("font_size", self.default_font_size, type=int)
        # Ensure loaded value is within valid range
        self.current_font_size = max(self.min_font_size, min(self.max_font_size, self.current_font_size))
        
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
        self.init_font_shortcuts()
        
        # Install event filter to intercept Ctrl+Wheel events before tables consume them
        self.logTable.viewport().installEventFilter(self)
        self.filterTable.viewport().installEventFilter(self)
        
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

        monospaced_font = QFont("Courier New", self.current_font_size)

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
            # Detect file type using 'file' command (content-based, not extension-based)
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
            
            # Treat ALL successfully loaded text files as logs for classification
            # This enables filters/classification for .txt, .prc, .yaml, .status, etc.
            self.isLog = True
            
            # Always classify lines by log level patterns (ERROR, WARNING, INFO, DEBUG, TEXT)
            # If no patterns match, lines are classified as TEXT with count shown
            self.logModel.update_data(self.logLevelKeywords.classify_lines(lines))
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

    def init_font_shortcuts(self):
        """Setup keyboard shortcuts for font size adjustment.
        
        Note: These shortcuts have Qt.ApplicationShortcut context so they work
        regardless of which widget has focus. This ensures Ctrl+0, Ctrl+-, etc.
        work consistently throughout the application.
        """
        # Increase font size: Ctrl++ or Ctrl+=
        # Note: + key is Shift+= on most keyboards, so we bind to both Plus and Equal
        shortcut_plus = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Plus), self)
        shortcut_plus.setContext(Qt.ApplicationShortcut)
        shortcut_plus.activated.connect(self.increase_font_size)
        
        shortcut_equal = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Equal), self)
        shortcut_equal.setContext(Qt.ApplicationShortcut)
        shortcut_equal.activated.connect(self.increase_font_size)
        
        # Decrease font size: Ctrl+-
        shortcut_minus = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Minus), self)
        shortcut_minus.setContext(Qt.ApplicationShortcut)
        shortcut_minus.activated.connect(self.decrease_font_size)
        
        # Reset font size: Ctrl+0
        shortcut_zero = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_0), self)
        shortcut_zero.setContext(Qt.ApplicationShortcut)
        shortcut_zero.activated.connect(self.reset_font_size)

    def increase_font_size(self):
        """Increase font size by 1pt."""
        if self.current_font_size < self.max_font_size:
            self.current_font_size += 1
            self.update_font_sizes()
            self.save_font_size()

    def decrease_font_size(self):
        """Decrease font size by 1pt."""
        if self.current_font_size > self.min_font_size:
            self.current_font_size -= 1
            self.update_font_sizes()
            self.save_font_size()

    def reset_font_size(self):
        """Reset font size to default (10pt)."""
        self.current_font_size = self.default_font_size
        self.update_font_sizes()
        self.save_font_size()

    def update_font_sizes(self):
        """Apply current font size to all widgets."""
        font = QFont("Courier New", self.current_font_size)
        
        # Update tables
        self.logTable.setFont(font)
        self.filterTable.setFont(font)
        
        # Update search and title
        self.searchEntry.setFont(font)
        self.fileTitle.setFont(font)
        
        # Update buttons
        for button in self.levelButtons.values():
            button.setFont(font)
        self.cleanLevels.setFont(font)
        self.reloadButton.setFont(font)
        self.helpButton.setFont(font)
        
        # Update delegate fonts (for proper text rendering)
        self.logTable.itemDelegate().docText.setDefaultFont(font)
        self.filterTable.itemDelegate().docText.setDefaultFont(font)
        
        # Force viewport repaint
        self.logTable.viewport().update()
        self.filterTable.viewport().update()

    def save_font_size(self):
        """Save font size preference using QSettings."""
        settings = QSettings("Avice", "TabLog")
        settings.setValue("font_size", self.current_font_size)

    def eventFilter(self, obj, event):
        """Event filter to intercept Ctrl+Wheel events before child widgets process them.
        
        This is necessary because tables consume wheel events for scrolling.
        By filtering events at the viewport level, we can intercept Ctrl+Wheel
        BEFORE the table scrolls, allowing immediate font size adjustment.
        """
        from PyQt5.QtCore import QEvent
        
        if event.type() == QEvent.Wheel:
            # Check if Ctrl key is held down
            if event.modifiers() & Qt.ControlModifier:
                # Get wheel delta (positive = scroll up/away, negative = scroll down/toward)
                delta = event.angleDelta().y()
                
                if delta > 0:
                    # Wheel up → Increase font size
                    self.increase_font_size()
                elif delta < 0:
                    # Wheel down → Decrease font size
                    self.decrease_font_size()
                
                # Return True to indicate event was handled (prevents further processing)
                return True
        
        # For all other events, use default behavior
        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        """Handle mouse wheel events for font size adjustment.
        
        This handles wheel events on the LogViewer widget itself (non-table areas).
        Table wheel events are handled by eventFilter() above.
        
        When Ctrl is held down, mouse wheel adjusts font size:
        - Wheel up (away from user) → Increase font size
        - Wheel down (toward user) → Decrease font size
        
        Without Ctrl, normal scrolling behavior is preserved.
        """
        # Check if Ctrl key is held down
        if event.modifiers() & Qt.ControlModifier:
            # Get wheel delta (positive = scroll up/away, negative = scroll down/toward)
            delta = event.angleDelta().y()
            
            if delta > 0:
                # Wheel up → Increase font size
                self.increase_font_size()
            elif delta < 0:
                # Wheel down → Decrease font size
                self.decrease_font_size()
            
            # Accept the event to prevent default scrolling
            event.accept()
        else:
            # No Ctrl key, use default behavior (scroll)
            super().wheelEvent(event)

    def show_help_dialog(self):
        """Show the help dialog with tabs.
        
        Solution A (PyQt5 5.15.6 venv): This version uses PyQt5 from pip with
        bundled Qt 5.15.2 that has minimal GLIBCXX requirements (3.4 base),
        compatible with system GLIBCXX 3.4.25. In-app help should work without crashes.
        
        Features compact inline header with clickable logo.
        """
        from PyQt5.QtWidgets import (QDialog, QTabWidget, QPlainTextEdit,
                                      QVBoxLayout, QPushButton, QHBoxLayout)
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QPixmap, QCursor

        
        dialog = QDialog(self)
        dialog.setWindowTitle("TabLog Help")
        dialog.setModal(True)
        dialog.resize(750, 600)
        
        # Set dialog icon
        avice_logo_path = os.path.join(os.path.dirname(__file__), 'icons', 'avice_logo_64.png')
        if os.path.exists(avice_logo_path):
            dialog.setWindowIcon(QIcon(avice_logo_path))
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # Create tab widget first (needed for logo click handler)
        tabs = QTabWidget()
        
        # OPTION 1: Compact inline header with clickable logo
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(8)
        header_widget.setLayout(header_layout)
        
        # Clickable Avice logo (32x32)
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), 'icons', 'avice_logo_64.png')
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setCursor(QCursor(Qt.PointingHandCursor))  # Hand cursor on hover
            logo_label.setToolTip("Click to enlarge logo")
            
            # Make logo clickable - shows enlarged version in popup
            def show_enlarged_logo(event):
                # Check if large logo file exists FIRST (before creating dialog)
                logo_path_large = os.path.join(os.path.dirname(__file__), 'icons', 'avice_logo_256.png')
                if not os.path.exists(logo_path_large):
                    # Don't show dialog if logo file doesn't exist
                    return
                
                # Create popup dialog to show enlarged logo
                logo_dialog = QDialog(dialog)
                logo_dialog.setWindowTitle("Avice Logo")
                logo_dialog.setModal(True)
                
                logo_layout = QVBoxLayout()
                logo_dialog.setLayout(logo_layout)
                
                # Show large logo (256x256) - file existence already verified
                large_logo_label = QLabel()
                large_pixmap = QPixmap(logo_path_large)
                large_logo_label.setPixmap(large_pixmap)
                large_logo_label.setAlignment(Qt.AlignCenter)
                logo_layout.addWidget(large_logo_label)
                
                # Add logo info
                info_label = QLabel("<center><b>Avice Logo</b><br>256 × 256 pixels</center>")
                info_label.setStyleSheet("margin: 10px; color: #666;")
                logo_layout.addWidget(info_label)
                
                # Resize dialog to fit logo
                logo_dialog.resize(300, 320)
                
                # Close button
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(logo_dialog.accept)
                logo_layout.addWidget(close_btn)
                
                logo_dialog.exec_()
            
            logo_label.mousePressEvent = show_enlarged_logo
        header_layout.addWidget(logo_label)
        
        # Title and subtitle inline
        title_label = QLabel("<b>TabLog</b> - <i>Advanced Log Viewer by Avice</i>")
        title_label.setStyleSheet("font-size: 11pt;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addWidget(header_widget)
        
        # Add thin separator line
        separator = QLabel()
        separator.setFrameStyle(QLabel.HLine | QLabel.Sunken)
        layout.addWidget(separator)
        
        # Add tab widget
        layout.addWidget(tabs)
        
        # Create help tabs with QPlainTextEdit (lightweight and stable)
        def create_help_tab(text):
            widget = QPlainTextEdit()
            widget.setReadOnly(True)
            widget.setLineWrapMode(QPlainTextEdit.WidgetWidth)
            widget.setPlainText(text)
            return widget
        
        # Add all help tabs
        tabs.addTab(create_help_tab(self._get_filters_help_text()), "Filters")
        tabs.addTab(create_help_tab(self._get_search_help_text()), "Search")
        tabs.addTab(create_help_tab(self._get_shortcuts_help_text()), "Shortcuts")
        tabs.addTab(create_help_tab(self._get_about_help_text()), "About")
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def _get_filters_help_text(self) -> str:
        """Generate plain text for filters help tab."""
        return """FILTER BUTTONS
================================

TabLog automatically classifies log lines into different levels.
Use the filter buttons to show only specific log levels.

🔵 TEXT (Level 1)
------------------
Purpose: Regular text lines without specific log level markers
Patterns: Any line that doesn't match other levels
Example: Processing started...

🔍 DEBUG (Level 2)
-------------------
Purpose: Detailed diagnostic information for debugging
Patterns matched:
  • DEBUG, D:, Debug:
  • -D-, -Debug-
  • [DEBUG], DEBUG]
Example: DEBUG Initializing module

ℹ️ INFO (Level 3)
------------------
Purpose: Informational messages about normal program flow
Patterns matched:
  • INFO, I:, Information:
  • -I-, -Info-
  • [INFO], INFO]
Example: INFO Process completed successfully

⚠️ WARNING (Level 4)
---------------------
Purpose: Potential issues that aren't critical but need attention
Patterns matched:
  • WARNING, W:, Warning:
  • -W-, -Warning-
  • [WARNING], [WARN], WARN]
Example: WARNING Slow network detected

❌ ERROR (Level 5)
-------------------
Purpose: Serious errors, fatal issues, or critical problems
Patterns matched:
  • ERROR, E:, Error:
  • FATAL, F:, Fatal:
  • CRITICAL, C:, Critical:
  • Segmentation fault encountered
  • [ERROR], [FATAL], [CRITICAL]
Example: ERROR Connection failed

USING FILTERS
================================

💡 Tip: Click multiple filter buttons to combine them (OR logic)
Example: Click Warning + Error to see all warnings and errors

FILTER COUNTS
-------------
Each button shows the count of matching lines:
  • Normal view: "Error (12)" = 12 error lines total
  • When filtering: "Error (5/12)" = 5 matching search, 12 total

CLEAR BUTTON
------------
Click the "Clear" button (🧹) to uncheck all filters and show all lines.
"""
    
    def _get_search_help_text(self) -> str:
        """Generate plain text for search help tab."""
        return """SEARCH FEATURES
================================

BASIC SEARCH
------------
Type text in the search box and press Enter or click the search icon (🔍).
  • Search is case-insensitive
  • Matches are highlighted in orange
  • Filtered results appear in the bottom pane

SEARCH NAVIGATION
-----------------
Button/Key          Action
------------------  ------------------------
🔍 or Enter         Execute search
⬆ or Ctrl+Up       Go to previous match
⬇ or Ctrl+Down     Go to next match
✖ (Clear icon)     Clear search text
Ctrl+F or F3        Focus search box
Esc                 Clear search and unfocus

COMBINING SEARCH WITH FILTERS
------------------------------
You can combine text search with log level filters:
  1. Click one or more filter buttons (e.g., Warning + Error)
  2. Type search text (e.g., "timeout")
  3. See only warnings/errors containing "timeout"

💡 Pro Tip: Use search to find specific patterns, then use filter 
   buttons to focus on important log levels!

SEARCH RESULTS
--------------
  • Results show in the bottom pane
  • Click a result to see it in context in the top pane
  • The top pane auto-scrolls and highlights the selected line
"""
    
    def _get_shortcuts_help_text(self) -> str:
        """Generate plain text for keyboard shortcuts help tab."""
        return """KEYBOARD SHORTCUTS
================================

📁 FILE OPERATIONS
------------------
Shortcut               Action
---------------------  -----------------------
Ctrl+O                 Open file
Ctrl+W                 Close current tab
Ctrl+R or F5           Reload current file
Ctrl+Q                 Quit application

🔍 SEARCH
---------
Shortcut               Action
---------------------  -----------------------
Ctrl+F or F3           Focus search box
Enter                  Execute search
Ctrl+Up                Previous search result
Ctrl+Down              Next search result
Esc                    Clear search and unfocus

🧭 NAVIGATION
-------------
Shortcut               Action
---------------------  -----------------------
↑ / ↓                  Scroll up/down one line
← / →                  Scroll left/right (fast)
Ctrl+← / Ctrl+→        Scroll left/right (slow)
Page Up / Page Down    Page up/down in main view
Ctrl+PgUp / Ctrl+PgDn  Page up/down in filter view
Ctrl+Home              Jump to top of log
Ctrl+End               Jump to bottom of log
Ctrl+Shift+Home        Jump to top of filtered view
Ctrl+Shift+End         Jump to bottom of filtered view

📋 CLIPBOARD
------------
Shortcut               Action
---------------------  -----------------------
Ctrl+C                 Copy selected rows
Ctrl+A                 Select all (if < 1000 rows)
Right-click            Context menu with Copy

🔍 VIEW / ZOOM
--------------
Shortcut               Action
---------------------  -----------------------
Ctrl++ or Ctrl+=       Increase font size
Ctrl+-                 Decrease font size
Ctrl+0                 Reset font to default (10pt)
Ctrl+Mouse Wheel       Zoom in/out (wheel up/down)

💡 TIPS
-------
  • Double-click a log line to view it in a popup
  • Click file paths in logs to open them in a new tab
  • Font size preference is saved across sessions
  • Ctrl+Mouse Wheel works anywhere in the window
  • Use Shift+Click to select multiple rows
  • Right-click selected rows and choose "Copy"
"""
    
    def _get_about_help_text(self) -> str:
        """Generate plain text for about help tab."""
        return """
════════════════════════════════════════════════════════════════
                          TABLOG
        Advanced Log Viewer with Smart Classification
════════════════════════════════════════════════════════════════

Version:        1.2.0+
Created by:     Avice
Email:          avice@nvidia.com
Organization:   NVIDIA Corporation
Repository:     github.com:avice-NVDA/tablog.git

════════════════════════════════════════════════════════════════
                         FEATURES
════════════════════════════════════════════════════════════════

✅ Multi-tab Interface
   Open multiple log files in separate tabs with easy navigation

✅ Smart Log Classification
   Automatically detects TEXT, DEBUG, INFO, WARNING, ERROR levels

✅ Level Count Badges
   See real-time counts of lines per level (e.g., "Error (5/12)")

✅ Advanced Filtering
   Filter by log level and search text with live highlighting

✅ Regex Search Support
   Use regular expressions for powerful pattern matching

✅ Clickable File Links
   File paths in logs become clickable links to open in new tabs

✅ Comprehensive Help System
   In-app help with detailed documentation and shortcuts

✅ Multiple File Format Support
   Plain text, gzipped logs (.log.gz), ANSI colored logs

✅ Dual-Pane View
   See full log and filtered results simultaneously

✅ LSF Shell Compatibility
   Works in both regular shells and LSF interactive shells

✅ Keyboard Shortcuts
   Full keyboard navigation for power users

✅ Copy Support
   Copy selected lines to clipboard with one click

════════════════════════════════════════════════════════════════
                      FILE FORMATS
════════════════════════════════════════════════════════════════

Supported file types:
  • Plain text (.log, .txt)
  • Gzipped logs (.log.gz)
  • ANSI colored logs
  • Clickable paths (.log, .tcl, .yaml, .cfg, .txt, .py, .rpt)

════════════════════════════════════════════════════════════════
                    TECHNICAL DETAILS
════════════════════════════════════════════════════════════════

Python Version:     3.11.9
PyQt5 Version:      5.15.6
Qt Version:         5.15.2 (bundled)
GLIBCXX Support:    3.4 (compatible with RHEL 8)
Platform:           Linux x86_64

Key Libraries:
  • PyQt5 5.15.6 (with bundled Qt 5.15.2)
  • ansi2html (for ANSI color conversion)
  • Virtual environment (portable, self-contained)

════════════════════════════════════════════════════════════════
                         SUPPORT
════════════════════════════════════════════════════════════════

📦 GitHub:          github.com:avice-NVDA/tablog.git
📄 Documentation:   README.md, QUICK_START.md, FEATURES_v1.1.md
🛠️ Troubleshooting: LSF_SHELL_GUIDE.md, IMPROVEMENTS.md
📝 Changelog:       CHANGELOG_v1.2.md

════════════════════════════════════════════════════════════════

© 2025 NVIDIA Corporation. Internal Tool.
Developed with ❤️ by Avice for the NVIDIA VLSI team.

════════════════════════════════════════════════════════════════
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