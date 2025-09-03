"""
LogLevelColor.py - Log Level Color Mapping

Main Functions:
- LogLevelColor: Maps log levels to foreground and background colors
- colors(): Returns the (foreground, background) color tuple for display
- ColorMap: Predefined color scheme for each log level
"""

from LogLevel import LogLevel


class LogLevelColor:

    ColorMap = {
            LogLevel.TEXT: ("#000000", "#F2F2F2"),
            LogLevel.DEBUG: ("#808080", "#F2F2F2"),
            LogLevel.INFO: ("#232B99", "#F2F2F2"),
            LogLevel.WARNING: ("#000000", "#FFFA99"),
            LogLevel.ERROR: ("#000000", "#F8A1A4"),
        }

    def __init__(self, level: LogLevel):
        self.level = level
        self.fg, self.bg = LogLevelColor.ColorMap[LogLevel.TEXT]
        if level in LogLevelColor.ColorMap:
            self.fg, self.bg = LogLevelColor.ColorMap[level]

    def colors(self):
        return self.fg, self.bg

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return F"{self.level}: {self.fg}, {self.bg}"
