"""
LogLineDelegate.py - Custom Log Line Renderer

Main Functions:
- LogLineDelegate: QStyledItemDelegate for rendering log lines with custom styling
- paint(): Renders log lines with level-based colors and clickable file links
- wrap_log_file(): Converts file paths in log lines to clickable HTML links
- editorEvent(): Handles mouse clicks on file links to load referenced files
"""

import os
import re

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QTextDocument, QColor
from PyQt5.QtWidgets import QStyledItemDelegate, QTableView, QStyle

from LogLevelColor import LogLevelColor


class LogLineDelegate(QStyledItemDelegate):
    def __init__(self, parent: QTableView, filter: bool = False):
        self.parent: QTableView = parent
        self.is_filter: bool = filter
        self.docText: QTextDocument = QTextDocument()
        self.docText.setDocumentMargin(0)
        self.docText.setDefaultFont(parent.font())
        self.nfs_pattern = r'(/home/[\w/._-]+\.log)'
        self.linkCallback = None
        super().__init__(parent)

    def wrap_log_file(self, text: str) -> str:
        # no wrappping for filter
        if self.is_filter:
            return text
        # Regular expression to match NFS file paths
        nfs_pattern = r'((\/home\/)[\w\/._:-]+\.(log|tcl|yaml|cfg|txt|py))'

        # Function to wrap the matched NFS file path with <a> tag
        def wrap_with_a_tag(re_match: re.Match) -> str:
            nfs_path = re_match.group(1)
            if os.path.exists(nfs_path):
                if os.path.isfile(nfs_path):
                    return f'<a href="{nfs_path}">{nfs_path}</a>'
                elif os.path.isdir(nfs_path):
                    return nfs_path
            return f'<u style="color:#BF5B16">{nfs_path}</u>'

        # Use re.sub() to replace the NFS file path with the wrapped version
        wrapped_line = re.sub(nfs_pattern, wrap_with_a_tag, text)
        return wrapped_line

    def paint(self, painter, option, index):
        if not index.isValid():
            return super().paint(painter, option, index)
        painter.save()
        fg, bg = "black", "white"
        text = index.model().data(index)
        if level := index.data(Qt.UserRole):
            fg, bg = LogLevelColor(level).colors()
            painter.fillRect(option.rect, QColor(bg))
        text = self.wrap_log_file(text)
        text = F"<pre style='color:{fg};'>{text}</pre>"
        self.docText.setTextWidth(option.rect.width())
        self.docText.setHtml(text)
        painter.translate(option.rect.topLeft())
        self.docText.drawContents(painter)
        painter.restore()
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(0, 100, 255, 50))

    def set_link_callback(self, callback):
        self.linkCallback = callback

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonDblClick:
            return super().editorEvent(event, model, option, index)
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            text = index.model().data(index)
            self.docText.setHtml(self.wrap_log_file(text))
            pos = event.pos() - option.rect.topLeft()

            anchor = self.docText.documentLayout().anchorAt(pos)
            if anchor:  # If the click is on a file link
                if self.linkCallback:
                    self.linkCallback(anchor)
                else:
                    # noinspection PyUnresolvedReferences
                    index.model().parent.load_file(anchor)
                return False
        return super().editorEvent(event, model, option, index)

    def helpEvent(self, event, view, option, index):
        if not index.isValid() or not index.model() or not index.model().data(index):
            return super().helpEvent(event, view, option, index)
        text = index.model().data(index)
        self.docText.setHtml(self.wrap_log_file(text))
        pos = event.pos() - option.rect.topLeft()
        anchor = self.docText.documentLayout().anchorAt(pos)
        if anchor:
            option.widget.setCursor(Qt.PointingHandCursor)
        else:
            option.widget.setCursor(Qt.ArrowCursor)
        return super().helpEvent(event, view, option, index)

    def sizeHint(self, option, index):
        return super().sizeHint(option, index)
