# TabLog Quick Start Guide

## Installation (Already Done ✓)
```bash
cd /home/scratch.avice_vlsi/tablog
chmod +x tablog
```

## Basic Usage

### Open a Single Log File
```bash
./tablog /path/to/your/logfile.log
```

### Open Multiple Log Files
```bash
./tablog file1.log file2.log.gz file3.txt
```

### Open from Current Directory
```bash
./tablog *.log
```

## Common Issues & Solutions

### Issue: "Cannot connect to X server"

**Quick Fix:**
```bash
# Check your DISPLAY
echo $DISPLAY

# Should show something like: :0 or :3 or localhost:10.0
# If it shows something else or nothing, reconnect with:
exit  # exit current session
ssh -X avice@tlv02-container-xterm-031.prd.it
```

### Issue: Wrong DISPLAY after login

**Quick Fix for csh:**
```csh
setenv DISPLAY :0
./tablog your_file.log
```

## Keyboard Shortcuts (In TabLog)

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open new file |
| `Ctrl+W` | Close current tab |
| `Ctrl+R` or `F5` | Reload current file |
| `Ctrl+F` or `F3` | Focus search box |
| `Ctrl+C` | Copy selected rows |
| `Ctrl+A` | Select all (if < 1000 rows) |
| `↑` `↓` | Navigate log lines |
| `PgUp` `PgDn` | Page through log |
| `Ctrl+Home/End` | Jump to top/bottom |

## Filtering Logs

1. **By Level:** Click level buttons (Debug, Info, Warning, Error)
2. **By Text:** Type in search box, press Enter
3. **Clear Filters:** Click "Clear" button

## File Support

✅ Plain text (`.log`, `.txt`)  
✅ Gzipped logs (`.log.gz`)  
✅ ANSI colored logs  
✅ Clickable file paths (`.log`, `.tcl`, `.yaml`, `.cfg`, `.txt`, `.py`)  

## Tips & Tricks

### Tip 1: Open Linked Files
- Click on file paths in logs to open them in a new tab

### Tip 2: Quick Reload
- Press `F5` to reload the current log (useful for monitoring)

### Tip 3: Large File Selection
- `Ctrl+A` is disabled for files > 1000 lines (performance)
- Use mouse selection or filters instead

### Tip 4: Copy Multiple Lines
- Select rows (Shift+Click for range)
- Press `Ctrl+C` to copy
- Paste into any text editor

## Examples

### Monitor a Growing Log
```bash
./tablog /path/to/active.log
# Press F5 periodically to reload
```

### Filter for Errors Only
```bash
./tablog error.log
# Click "Error" button to show only error lines
```

### Search for Specific Text
```bash
./tablog large.log
# Type search term in search box
# Press Enter
# Use Ctrl+Up/Down to navigate matches
```

## Getting Help

### Check TabLog is Working
```bash
./tablog example1.log
# Should open with no errors
```

### Test X Server
```bash
xset q
# Should show keyboard/mouse settings
# If error, X server not accessible
```

### View Diagnostics
```bash
# Intentionally use bad DISPLAY to see diagnostic output
DISPLAY=invalid:0 ./tablog example1.log
```

## Advanced Usage

### Custom Python Installation
Edit `tablog`, line 50:
```python
self.python_exe = "/your/custom/python3"
```

### Enable Qt Debug Output
Edit `tablog`, line 36:
```python
# Comment out this line:
# os.environ.setdefault('QT_LOGGING_RULES', '*=false')
```

### Run Without Launcher
```bash
export QT_PLUGIN_PATH=/home/utils/qt-5.15.16/plugins
export XDG_RUNTIME_DIR=/tmp/runtime-${USER}
/home/utils/Python/builds/3.11.9-20250715/bin/python3 LogViewTab.py file.log
```

## Support Files

- `README.md` - Full documentation
- `IMPROVEMENTS.md` - Recent changes and fixes
- `example1.log` - Sample log for testing
- `tablog.bash.backup` - Original bash launcher (backup)

## Quick Diagnostics

Run this command to check your setup:
```bash
echo "DISPLAY: $DISPLAY"
echo "USER: $USER"
echo "HOST: $(hostname)"
xset q > /dev/null 2>&1 && echo "X Server: OK" || echo "X Server: NOT ACCESSIBLE"
```

Expected output:
```
DISPLAY: :3
USER: avice
HOST: tlv02-container-xterm-031.prd.it.nvidia.com
X Server: OK
```

If "X Server: NOT ACCESSIBLE", reconnect with `ssh -X` or `ssh -Y`.

