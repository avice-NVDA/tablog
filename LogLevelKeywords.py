"""
LogLevelKeywords.py - Log Level Classification System

Main Functions:
- LogLevelKeywords: Maintains keyword patterns for classifying log lines by severity
- classify_lines(): Analyzes log lines and assigns appropriate LogLevel based on content
- Keywords include regex patterns for DEBUG, INFO, WARNING, ERROR detection
"""

import re

from LogLevel import LogLevel


class LogLevelKeywords:
    def __init__(self):
        self._level_to_keywords: dict[LogLevel, list[str]] = {
            LogLevel.TEXT: [""],
            LogLevel.DEBUG: ["^DEBUG", "^D:", "^Debug:", "^-D-", "^-Debug-",
                             r"\[DEBUG\s*\]", r"DEBUG\]"],
            LogLevel.INFO: ["^INFO", "^I:", "^Information:", "^-I-", "^-Info-",
                            r"\[INFO\s*\]", r"INFO\]"],
            LogLevel.WARNING: ["^WARNING", "^W:", "^Warning:", "^-W-", "^-Warning-",
                               "^Warning",  # Lines starting with Warning (without colon)
                               r"^\[main\] Warning",  # Lines starting with [main] Warning
                               "^#WARNING",  # Lines starting with #WARNING
                               r"^\*\*WARN",  # Lines starting with **WARN
                               r"^\[NV\]\[.*?\]Warning",  # Lines like [NV][09/Dec/2025 17:09:35 IST]Warning
                               r"\[WARNING\]", r"WARN\]", r"\[WARN\s*\]"],
            LogLevel.ERROR: ["^ERROR", "^E:", "^Error:", "^-E-", "^-Error-",
                             "^FATAL", "^F:", "^Fatal:", "^-F-", "^-Fatal-",
                             "^CRITICAL", "^C:", "^-C-", "^-Critical-",
                             "^Segmentation fault encountered", "^Error:", "^Fatal:", "^Critical:",
                             r"^\*\*ERROR",  # Lines starting with **ERROR
                             r"^\[NV\]\[.*?\]Error",  # Lines like [NV][28/Nov/2025 19:17:55 IST]Error
                             r"^\[main\] Error",  # Lines starting with [main] Error
                             r"^\[ErrorParser\]",  # Lines starting with [ErrorParser]
                             "^ERR",  # Lines starting with ERR
                             "^TOTAL ERRORS",  # Lines starting with TOTAL ERRORS
                             r"\[ERROR\s*\]", r"ERROR\]",
                             r"\[FATAL\s*\]", r"\[CRITICAL\s*\]",
                             r"FATAL",  # FATAL anywhere in line
                             r"(?i)Extended\s+Error\s+Info"],  # Case insensitive Extended Error Info
        }
        self._compiled_patterns = {}
        for keywords in self._level_to_keywords.values():
            for keyword in [k for k in keywords if k]:
                # Compile all regex patterns (both ^ and non-^ patterns with regex chars)
                if not keyword.startswith('^') or any(c in keyword for c in r'[]().*+?{}|\\'):
                    try:
                        self._compiled_patterns[keyword] = re.compile(RF"{keyword}")
                    except re.error:
                        pass  # Skip invalid patterns

    def __getitem__(self, level: LogLevel) -> list[str]:
        return self._level_to_keywords[level]

    def __setitem__(self, level: LogLevel, keywords: list[str]):
        self._level_to_keywords[level] = keywords

    def __iter__(self) -> iter:
        return iter(self._level_to_keywords)

    def __len__(self) -> int:
        return len(self._level_to_keywords)

    def __contains__(self, level: LogLevel) -> bool:
        return level in self._level_to_keywords

    def keywords(self, level: LogLevel) -> list[str]:
        return self._level_to_keywords[level]

    def classify_lines(self, lines: list[str]) -> list[tuple[LogLevel, str]]:
        classified_data: list[tuple[LogLevel, str]] = []
        default_level = LogLevel.TEXT
        for line in lines:
            classification, level_assigned = default_level, False
            for level in self:
                if level_assigned:
                    break
                if level == default_level:
                    continue
                # Check all patterns (both ^ and non-^ patterns)
                for keyword in self.keywords(level):
                    if not keyword:  # Skip empty patterns
                        continue
                    
                    # If it's a simple ^ pattern (no regex chars), use fast string startswith
                    if keyword.startswith('^') and not any(c in keyword for c in r'[]().*+?{}|\\'):
                        if line.startswith(keyword[1:]):
                            classification, level_assigned = level, True
                            break
                    # Otherwise, use compiled regex pattern
                    elif keyword in self._compiled_patterns:
                        if self._compiled_patterns[keyword].search(line):
                            classification, level_assigned = level, True
                            break
                    
                if level_assigned:
                    break
            classified_data.append((classification, line))
        return classified_data
