# TabLog - Tabbed Log Viewer

A powerful PyQt5-based log viewing application with advanced filtering, search, and multi-tab support.

## Features

- **Multi-tab Interface**: Open multiple log files in separate tabs
- **Smart Log Classification**: Automatically detects DEBUG, INFO, WARNING, ERROR levels
- **Advanced Filtering**: Filter by log level and search text with live highlighting
- **Level Count Badges**: See how many lines of each level exist (e.g., "Error (12)")
- **Comprehensive Help System**: Built-in help with keyboard shortcuts and feature explanations
- **Clickable File Links**: File paths in logs become clickable links
- **Keyboard Shortcuts**: Full keyboard navigation support
- **Multiple Formats**: Supports plain text, gzipped, and ANSI-colored logs

## Installation

### Requirements
- Python 3.11+
- PyQt5
- ansi2html (for ANSI color support)

### Setup
```bash
# Make the launcher executable
chmod +x tablog

# Run the application
./tablog [log_files...]
```

## Usage

### Opening Files
- **From command line**: `./tablog file1.log file2.log`
- **From GUI**: Ctrl+O or File → Open menu
- **Drag and drop**: (if supported by your window manager)

### Keyboard Shortcuts
- **F1 / Ctrl+H**: Show help dialog
- **Ctrl+O**: Open file
- **Ctrl+W**: Close current tab
- **Ctrl+R / F5**: Reload current file
- **Ctrl+F / F3**: Focus search box
- **Ctrl+C**: Copy selected rows
- **Ctrl+A**: Select all (if less than 1000 rows)
- **Arrow keys**: Navigate log
- **Page Up/Down**: Page through log
- **Ctrl+Home/End**: Jump to top/bottom

For complete keyboard shortcuts, press **F1** in the application.

### Log Level Filtering
Click the level buttons (Text, Debug, Info, Warning, Error) to filter by log severity.

### Search
Enter text in the search box to highlight and filter matching lines.

## File Support

### Supported Log Types
- Plain text (.log, .txt)
- Gzipped logs (.log.gz)
- ANSI colored logs

### Clickable File Extensions
Paths starting with `/home` and ending with:
- `.log`, `.tcl`, `.yaml`, `.cfg`, `.txt`, `.py`

## Troubleshooting

### X Server Connection Issues

If you get an error about Qt platform plugin initialization:

**Solution 1: Use SSH X11 Forwarding (Recommended)**
```bash
ssh -X user@host
# or for trusted forwarding
ssh -Y user@host
```

**Solution 2: Set DISPLAY to Local X Server**
```csh
# For csh/tcsh
setenv DISPLAY :0
```

**Solution 3: Check X Server Accessibility**
```bash
xset q  # Test X server connection
```

The Python launcher (`tablog.py`) provides detailed diagnostics when connection issues occur.

## Development

### Project Structure
```
tablog/
├── LogViewTab.py      # Main tabbed interface
├── LogViewer.py       # Core log viewing widget
├── LogLevel.py        # Log level enumeration
├── LogLevelColor.py   # Color mapping for levels
├── LogLevelKeywords.py # Log classification patterns
├── LogTableModel.py   # Qt table model for logs
├── FilterTableModel.py # Filtered/search table model
├── LogLineDelegate.py # Custom line renderer
├── icons_rc.py        # Embedded UI icons
├── common/
│   ├── Colorizer.py   # Text-based color generator
│   └── TabBar.py      # Custom colored tab bar
├── icons/             # Icon resources
├── example.log        # Sample log file
├── tablog             # Python launcher with diagnostics
└── tablog.bash.backup # Original bash launcher (backup)
```

## License

[Add your license here]

## Version

Current version: 1.1.0

### What's New in v1.1
- ✨ Level count badges on filter buttons (e.g., "Error (12)")
- ✨ Comprehensive help system (press F1)
- ✨ Help button in toolbar
- 📝 Detailed documentation for all features

See [FEATURES_v1.1.md](FEATURES_v1.1.md) for complete details.
