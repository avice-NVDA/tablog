# 🎨 Avice Logo Integration Plan for TabLog

## Overview
Add the Avice logo (`avice_logo.png`) to TabLog's GUI to personalize the application.

---

## 📋 Implementation Plan

### **Phase 1: Prepare Logo Assets** ✅

#### 1.1 Copy Original Logo
- **Source:** `/home/scratch.avice_vlsi/cursor/avice_wa_review/assets/images/avice_logo.png`
- **Destination:** `/home/scratch.avice_vlsi/tablog/icons/avice_logo.png`
- **Size:** 1024x1024 PNG (815 KB)

#### 1.2 Create Scaled Versions
The logo is currently 1024x1024, which is very large. We should create optimized versions:

**Recommended sizes:**
- `avice_logo_64.png` - 64x64 - For toolbar/title bar icons
- `avice_logo_128.png` - 128x128 - For help dialog header
- `avice_logo_256.png` - 256x256 - For about dialog

**Tools to use:**
- ImageMagick (convert)
- Python PIL (Pillow) in virtual environment
- Qt's QPixmap scaling (runtime)

---

### **Phase 2: Update Qt Resource System** 🔧

#### 2.1 Add Logo to icons.qrc
File: `/home/scratch.avice_vlsi/tablog/icons/icons.qrc`

Add new entries:
```xml
<file>avice_logo.png</file>
<file>avice_logo_64.png</file>
<file>avice_logo_128.png</file>
<file>avice_logo_256.png</file>
```

#### 2.2 Regenerate icons_rc.py
```bash
cd /home/scratch.avice_vlsi/tablog
pyrcc5 icons/icons.qrc -o icons_rc.py
```

This makes the logo accessible via Qt's resource system: `:icons/avice_logo.png`

---

### **Phase 3: Add Logo to Main Window** 🪟

#### 3.1 Update LogViewTab.py
File: `/home/scratch.avice_vlsi/tablog/LogViewTab.py`

**Location:** Line ~79 (in `if __name__ == '__main__':` block)

**Current code:**
```python
main_window.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'logo.png')))
```

**Updated code:**
```python
# Use Avice logo as window icon
main_window.setWindowIcon(QIcon(':/icons/avice_logo_64.png'))
```

**Impact:** 
- Logo appears in window title bar
- Logo appears in taskbar
- Logo appears in Alt+Tab switcher

---

### **Phase 4: Add Logo to Help Dialog** 📚

#### 4.1 Update show_help_dialog() in LogViewer.py
File: `/home/scratch.avice_vlsi/tablog/LogViewer.py`

**Location:** Line ~446 (`show_help_dialog()` method)

**Enhancement 1: Dialog Icon**
```python
dialog = QDialog(self)
dialog.setWindowTitle("TabLog Help")
dialog.setWindowIcon(QIcon(':/icons/avice_logo_64.png'))  # Add this
dialog.setModal(True)
dialog.resize(750, 550)
```

**Enhancement 2: Header with Logo**
Add before the tab widget:
```python
# Create header with logo
header_widget = QWidget()
header_layout = QHBoxLayout()
header_layout.setContentsMargins(10, 10, 10, 10)
header_widget.setLayout(header_layout)

# Add logo
logo_label = QLabel()
logo_pixmap = QIcon(':/icons/avice_logo_128.png').pixmap(96, 96)
logo_label.setPixmap(logo_pixmap)
logo_label.setAlignment(Qt.AlignCenter)
header_layout.addWidget(logo_label)

# Add title text
title_layout = QVBoxLayout()
title_label = QLabel("<h1>TabLog</h1>")
title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
subtitle_label = QLabel("<i>Advanced Log Viewer by Avice</i>")
subtitle_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
title_layout.addWidget(title_label)
title_layout.addWidget(subtitle_label)
header_layout.addLayout(title_layout)
header_layout.addStretch()

layout.addWidget(header_widget)
```

#### 4.2 Update _get_about_help_text()
File: `/home/scratch.avice_vlsi/tablog/LogViewer.py`

**Location:** Line ~651 (`_get_about_help_text()` method)

**Add Avice branding:**
```python
def _get_about_help_text(self):
    return """
TabLog - Advanced Log Viewer
Version: 1.2.0+

Created by: Avice
Email: avice@nvidia.com
Repository: github.com:avice-NVDA/tablog.git

Features:
• Multi-level log filtering (TEXT, DEBUG, INFO, WARNING, ERROR)
• Real-time search with regex support
• ANSI color support
• Gzip file support
• Level count badges
• Comprehensive keyboard shortcuts
• LSF shell compatibility

Built with:
• Python 3.11.9
• PyQt5 5.15.6
• Qt 5.15.2

License: Internal NVIDIA Tool
© 2025 NVIDIA Corporation
    """.strip()
```

---

### **Phase 5: Optional Enhancements** 🌟

#### 5.1 Splash Screen (Future)
Show logo while loading large files:
```python
from PyQt5.QtWidgets import QSplashScreen

splash = QSplashScreen(QPixmap(':/icons/avice_logo_256.png'))
splash.show()
# ... load file ...
splash.close()
```

#### 5.2 About Dialog (Future)
Create a dedicated "About TabLog" dialog:
- Large logo (256x256)
- Version information
- Credits
- System information

#### 5.3 Toolbar Button (Optional)
Add a toolbar with logo:
```python
toolbar = QToolBar()
logo_action = QAction(QIcon(':/icons/avice_logo_64.png'), 'About', self)
toolbar.addAction(logo_action)
```

---

## 🔍 Testing Checklist

After implementation:

- [ ] Logo appears in main window title bar
- [ ] Logo appears in help dialog window icon
- [ ] Logo displays in help dialog header (96x96)
- [ ] Logo scales properly at different DPI settings
- [ ] Logo works in both regular and LSF shells
- [ ] No performance impact when opening help dialog
- [ ] Icons resource file regenerates correctly
- [ ] Git repository size increase is acceptable (<1 MB)

---

## 📦 Files to Modify

1. **Copy logo:**
   - `/home/scratch.avice_vlsi/tablog/icons/avice_logo.png`
   - `/home/scratch.avice_vlsi/tablog/icons/avice_logo_64.png`
   - `/home/scratch.avice_vlsi/tablog/icons/avice_logo_128.png`

2. **Update resource file:**
   - `/home/scratch.avice_vlsi/tablog/icons/icons.qrc`
   - Regenerate: `/home/scratch.avice_vlsi/tablog/icons_rc.py`

3. **Update Python files:**
   - `/home/scratch.avice_vlsi/tablog/LogViewTab.py` (line ~79)
   - `/home/scratch.avice_vlsi/tablog/LogViewer.py` (lines ~446-520, ~651)

---

## 🎯 Implementation Strategy

### **Recommended Approach: Incremental**

**Step 1:** Copy logo and create scaled versions
**Step 2:** Update icons.qrc and regenerate icons_rc.py
**Step 3:** Add logo to main window (simple, low risk)
**Step 4:** Test main window logo
**Step 5:** Add logo to help dialog (more complex)
**Step 6:** Test help dialog
**Step 7:** Update About text with Avice branding
**Step 8:** Commit and push to GitHub

### **Alternative Approach: Runtime Loading**

If we don't want to regenerate `icons_rc.py`, we can load the logo directly:

```python
logo_path = os.path.join(os.path.dirname(__file__), 'icons', 'avice_logo_64.png')
main_window.setWindowIcon(QIcon(logo_path))
```

**Pros:** 
- No need to regenerate resource file
- Easier to update logo in future

**Cons:**
- Slightly slower (file I/O vs embedded resource)
- Need to ensure file exists

---

## 🚀 Next Steps

**Ready to proceed?**

1. I can create the scaled logo versions
2. Update the resource file
3. Modify the Python code
4. Test in both shells
5. Commit and push

**Or would you prefer:**
- See mockups first?
- Start with just the window icon?
- Add more features (splash screen, about dialog)?
- Use runtime loading instead of Qt resources?

---

## 📝 Notes

- The original logo is 815 KB - scaled versions will be much smaller
- Qt resources embed images in the Python file (icons_rc.py)
- Git will track the logo images (consider using Git LFS for large images)
- Logo should work seamlessly in both regular and LSF shells
- No additional dependencies needed (QIcon/QPixmap are in PyQt5)

---

**Ready to implement?** Let me know which approach you prefer! 🎨

