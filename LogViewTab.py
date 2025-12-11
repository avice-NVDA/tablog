#!/home/utils/Python/builds/3.11.9-20250715/bin/python3
import os.path
from functools import partial

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QShortcut

from LogViewer import LogViewer
from common.TabBar import TabBar

"""
LogViewTab.py - Tabbed Log Viewer Application

Main Functions:
- LogViewTab: A QTabWidget subclass that manages multiple log viewer tabs
- add_log(): Adds new log files as tabs, reusing existing tabs for the same file
- rename_tab(): Renames log viewer tabs and updates their tooltips
- Standalone application: When run directly, creates a GUI window with file menu
  and keyboard shortcuts (Ctrl+O to open, Ctrl+W to close tabs, Ctrl+R/F5 to reload)
"""


class LogViewTab(QtWidgets.QTabWidget):
    def __init__(self, parent):
        self.parent = parent
        super(LogViewTab, self).__init__(parent)
        self.setTabBar(TabBar(self))
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(lambda index: self.removeTab(index))
        self.setContentsMargins(0, 0, 0, 0)
        self.init_shortcuts()

    def init_shortcuts(self):
        shortcut_ctrl_w = QtWidgets.QShortcut("Ctrl+W", self)
        shortcut_ctrl_w.activated.connect(lambda: self.removeTab(self.currentIndex()))

    def add_log(self, title: str, name: str, file: str):
        """Add a log file to the tab view, or switch to it if already open.
        
        Returns:
            bool: True if the tab already existed, False if newly created
        """
        tabs = [(t, self.widget(t)) for t in range(self.count())
                if self.widget(t).title == title]
        insert_index = tabs[-1][0] + 1 if tabs else self.count()
        tabs = [(t, w) for t, w in tabs if w.logFile == file]
        if tabs:
            # Tab already exists
            index, log_viewer = tabs[0]
            was_existing = True
        else:
            # Create new tab
            log_viewer = LogViewer(title, name, file, self)
            log_viewer.set_link_callback(partial(self.add_log, title, name))
            index = self.insertTab(insert_index, log_viewer, log_viewer.name)
            self.setTabToolTip(index, F"<h4>{title}</h4><h5>{name}</h5><h5>{file}</h5>")
            was_existing = False
        
        # Switch to the tab (existing or new)
        self.setCurrentWidget(log_viewer)
        
        # If tab already existed, provide visual feedback
        if was_existing:
            self.flash_tab(index)
        
        return was_existing

    def flash_tab(self, index: int):
        """Flash the tab at the given index to provide visual feedback.
        
        Briefly changes the tab background color to indicate it's already open.
        Uses a timer to create a flash effect (2 flashes over 400ms).
        """
        from PyQt5.QtCore import QTimer
        
        # Get the tab bar
        tab_bar = self.tabBar()
        
        # Store original stylesheet
        original_style = tab_bar.tabTextColor(index)
        flash_count = [0]  # Use list to allow modification in nested function
        
        def toggle_flash():
            if flash_count[0] < 4:  # 4 toggles = 2 complete flashes
                if flash_count[0] % 2 == 0:
                    # Flash ON - highlight background
                    tab_bar.setTabTextColor(index, QtGui.QColor(255, 140, 0))  # Orange text
                else:
                    # Flash OFF - restore original
                    tab_bar.setTabTextColor(index, original_style)
                flash_count[0] += 1
                QTimer.singleShot(100, toggle_flash)  # Next toggle in 100ms
            else:
                # Ensure we end with original color
                tab_bar.setTabTextColor(index, original_style)
        
        # Start the flash animation
        toggle_flash()

    def rename_tab(self, old_title: str, new_title: str):
        viewers: list[(int, LogViewer)] = [
            (t, self.widget(t)) for t in range(self.count())
            if self.widget(t).title == old_title]
        for index, log_viewer in viewers:
            log_viewer.rename(new_title)
            log_viewer.set_link_callback(partial(self.add_log, new_title, log_viewer.name))
            self.setTabToolTip(
                index, F"<h4>{new_title}</h4><h5>{log_viewer.name}</h5><h5>{log_viewer.logFile}</h5>")
            self.setTabText(index, log_viewer.name)  # Force color update on the tab bar


if __name__ == '__main__':
    import sys
    import argparse
    from PyQt5.QtGui import QIcon, QKeySequence

    # Set XDG_RUNTIME_DIR to prevent Qt warning
    if 'XDG_RUNTIME_DIR' not in os.environ:
        os.environ['XDG_RUNTIME_DIR'] = f'/tmp/runtime-{os.getenv("USER", "user")}'

    parser = argparse.ArgumentParser(description='Tablog log viewer')
    parser.add_argument('log_files', nargs='*', type=str, help='Log files to open')
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    # Use Avice logo as window icon
    avice_logo_path = os.path.join(os.path.dirname(__file__), 'icons', 'avice_logo_64.png')
    main_window.setWindowIcon(QIcon(avice_logo_path))
    main_window.setWindowTitle("TabLog")
    main_window.setGeometry(400, 200, 1200, 800)
    log_tabs = LogViewTab(None)
    main_window.setCentralWidget(log_tabs)
    menu = main_window.menuBar().addMenu("File")
    open_action = QAction('Open', main_window)
    open_action.setShortcut('Ctrl+O')


    def open_file():
        file, _ = QtWidgets.QFileDialog.getOpenFileName(
            main_window, "Open log file", "",
            "Log files (*.log);;Zipped logs (*.log.gz);;All files (*)")
        if file:
            file_name = os.path.basename(file)
            log_tabs.add_log(file_name, file_name, file)


    open_action.triggered.connect(open_file)
    menu.addAction(open_action)
    menu.addSeparator()
    exit_action = QAction('Exit', main_window)
    exit_action.setShortcut('Ctrl+Q')
    exit_action.triggered.connect(main_window.close)
    menu.addAction(exit_action)
    
    # View menu
    view_menu = main_window.menuBar().addMenu("View")
    
    # Note: Actual shortcuts are registered in LogViewer.init_font_shortcuts() with ApplicationShortcut context
    # Menu items just display the shortcut hint and trigger the same methods when clicked
    zoom_in_action = QAction('Zoom In\tCtrl++', main_window)  # \t adds shortcut hint without registering
    zoom_in_action.triggered.connect(
        lambda: log_tabs.currentWidget().increase_font_size() if log_tabs.currentWidget() else None)
    view_menu.addAction(zoom_in_action)
    
    zoom_out_action = QAction('Zoom Out\tCtrl+-', main_window)  # \t adds shortcut hint without registering
    zoom_out_action.triggered.connect(
        lambda: log_tabs.currentWidget().decrease_font_size() if log_tabs.currentWidget() else None)
    view_menu.addAction(zoom_out_action)
    
    reset_zoom_action = QAction('Reset Zoom\tCtrl+0', main_window)  # \t adds shortcut hint without registering
    reset_zoom_action.triggered.connect(
        lambda: log_tabs.currentWidget().reset_font_size() if log_tabs.currentWidget() else None)
    view_menu.addAction(reset_zoom_action)
    
    # Help menu
    help_menu = main_window.menuBar().addMenu("Help")
    help_action = QAction('Show Help', main_window)
    help_action.setShortcut('F1')
    help_action.triggered.connect(lambda: log_tabs.currentWidget().show_help_dialog() if log_tabs.currentWidget() else None)
    help_menu.addAction(help_action)
    
    shortcuts_action = QAction('Keyboard Shortcuts', main_window)
    shortcuts_action.setShortcut('Ctrl+H')
    shortcuts_action.triggered.connect(lambda: log_tabs.currentWidget().show_help_dialog() if log_tabs.currentWidget() else None)
    help_menu.addAction(shortcuts_action)
    
    for log_file in args.log_files:
        log_tabs.add_log(os.path.basename(log_file), "", log_file)

    # reload file on Ctrl-R
    QShortcut(QKeySequence(Qt.CTRL + Qt.Key_R), main_window).activated.connect(log_tabs.currentWidget().reload_file)
    # reload file on F5
    QShortcut(QKeySequence(Qt.Key_F5), main_window).activated.connect(log_tabs.currentWidget().reload_file)

    main_window.show()
    sys.exit(app.exec_())
