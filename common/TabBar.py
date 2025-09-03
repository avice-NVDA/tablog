"""
TabBar.py - Custom Tab Bar with Colored Backgrounds

Main Functions:
- TabBar: Custom QTabBar that displays tabs with individual background colors
- paintEvent(): Custom painting that applies per-tab background colors from LogViewer
- Each tab gets its color from the associated LogViewer's Colorizer-generated background
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import QTabBar


class TabBar(QTabBar):
    def __init__(self, parent):
        super(TabBar, self).__init__()
        self.parent = parent

    def paintEvent(self, event):
        painter = QPainter(self)
        border_color = QColor(Qt.GlobalColor.lightGray)
        border_width = 1

        for index in range(self.count()):
            tab_rect = self.tabRect(index)
            tab_text = self.tabText(index)
            bg = self.parent.widget(index).get_background()

            # Adjust tab_rect for border drawing
            tab_rect_adjusted = tab_rect.adjusted(border_width, border_width, -border_width, -border_width)

            # Customize background color per tab
            painter.fillRect(tab_rect_adjusted, QBrush(QColor(bg)))

            # Draw border
            painter.setPen(QPen(border_color, border_width))  # Apply border settings
            painter.drawRect(tab_rect_adjusted)
            # Customize background color per tab
            painter.setPen(QPen(QColor(Qt.black), 1))
            painter.drawText(tab_rect, Qt.AlignCenter, tab_text + " " * 6)
            if self.currentIndex() != index:
                painter.fillRect(tab_rect_adjusted, QBrush(QColor(200, 200, 200, 150)))
