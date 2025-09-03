"""
Colorizer.py - Text-Based Color Generator

Main Functions:
- Colorizer: Generates consistent RGB colors from text using SHA-1 hash
- rgb(): Returns RGB tuple based on text hash with normalized brightness
- hex(): Returns hex color string for Qt/CSS usage
- predefinedColors: Special color mappings for specific text values
"""

import hashlib

from PyQt5.QtGui import QColor


class Colorizer:
    """
    Colorizer class is responsible for generating an RGB color based on the original text.
    """

    predefinedColors: dict[str, tuple[int, int, int]] = {
        "tablog": (255, 243, 0),  # HEX #FFF300
        # "sonic": (68, 167, 194),  # HEX #44A7C2
    }

    def __init__(self, text: str):
        self._text = text
        self._defaultColor = (239, 239, 239)  # RGB color for the default text
        self._hexValue: str = self.hex()

    @staticmethod
    def normalize_value(value: int, original_min: int, original_max: int, new_min: int, new_max: int) -> int:
        normalized_value = (
                ((value - original_min) / (original_max - original_min)) * (new_max - new_min) + new_min)
        return int(normalized_value)

    def rgb(self) -> tuple[int, int, int]:
        """
        Returns the Red, Green, and Blue int values based on the original text.
        """
        if not self._text:
            return self._defaultColor
        if self._text.lower() in self.predefinedColors:
            return self.predefinedColors[self._text.lower()]
        hash_value = hashlib.sha1(self._text.encode('utf-8')).hexdigest()
        r, g, b = [int('0x' + hash_value[i:i + 2], 16) for i in range(0, 6, 2)]
        r, g, b = [Colorizer.normalize_value(v, 0, 255, 200, 255)
                   for v in [r, g, b]]
        return r, g, b

    def hex(self) -> str:
        """
        Returns the HEX color string based on the RGB color.
        """
        r, g, b = self.rgb()
        return '#{:02X}{:02X}{:02X}'.format(r, g, b)

    def __str__(self) -> str:
        return self._hexValue

    def color(self) -> QColor:
        """
        Returns the QColor object based on the RGB color.
        """
        return QColor(self._hexValue)
