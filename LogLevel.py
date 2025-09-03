"""
LogLevel.py - Log Level Enumeration

Main Functions:
- LogLevel: Enum class defining different log severity levels (TEXT, DEBUG, INFO, WARNING, ERROR)
- from_string(): Static method to create LogLevel from string representation
- from_int(): Static method to create LogLevel from integer value
"""

import re
from enum import Enum, auto


class LogLevel(Enum):
    TEXT = 1
    DEBUG = 2
    INFO = 3
    WARNING = 4
    ERROR = 5

    @staticmethod
    def from_string(level: str) -> 'LogLevel':
        return LogLevel[level.upper()]

    @staticmethod
    def from_int(level: int) -> 'LogLevel':
        return LogLevel(level)

    def __str__(self) -> str:
        return self.name

