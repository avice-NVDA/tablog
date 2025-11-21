# TabLog v1.1 - New Features

## Overview
Version 1.1 adds enhanced filtering with level counts and a comprehensive help system.

---

## Feature 1: Level Count Badges

### What's New
Filter buttons now show the count of matching lines for each log level.

### Display Format
- **Normal view:** `Error (12)` - Shows total count
- **When filtering:** `Error (5/12)` - Shows filtered count / total count
- **Zero counts:** `Debug (0)` - Still clickable, shows there are no debug lines

### Benefits
- **Quick Overview:** See at a glance how many errors, warnings, etc. exist
- **Filtering Feedback:** Understand how many lines match your current filter
- **Better Navigation:** Know what to expect before clicking a filter

### Examples
```
[Text (5000)]  [Debug (2500)]  [Info (2455)]  [Warning (33)]  [Error (12)]
```

After searching for "timeout":
```
[Text (0/5000)]  [Debug (0/2500)]  [Info (0/2455)]  [Warning (5/33)]  [Error (2/12)]
```

### Technical Details
- Counts are calculated when file loads
- Updated when search text changes
- Updated when filter buttons are clicked
- Efficient: No performance impact on large files

---

## Feature 2: Comprehensive Help System

### What's New
Integrated help documentation accessible directly from the application.

### Access Methods
1. **Help Button:** Click `❓ Help` button in toolbar
2. **Keyboard Shortcut:** Press `F1` or `Ctrl+H`
3. **Menu:** Help → Show Help

### Help Dialog Tabs

#### 1. Filters Tab
- Explanation of each filter button (Text, Debug, Info, Warning, Error)
- Patterns matched for each level
- Examples of matching log lines
- Color coding explanation
- How to combine filters
- Usage tips

#### 2. Search Tab
- Basic search usage
- Search navigation buttons
- Keyboard shortcuts for search
- Combining search with filters
- Search result highlighting
- Tips and tricks

#### 3. Shortcuts Tab
- Complete keyboard shortcut reference
- Organized by category:
  - File Operations (Ctrl+O, Ctrl+W, Ctrl+R, etc.)
  - Search (Ctrl+F, F3, Ctrl+Up/Down, etc.)
  - Navigation (Arrow keys, Page Up/Down, Ctrl+Home/End, etc.)
  - Clipboard (Ctrl+C, Ctrl+A)
- Easy-to-scan table format
- Visual key representations

#### 4. About Tab
- Version information
- Features list
- File format support
- GitHub link
- Requirements
- Credits

### Benefits
- **Onboarding:** New users can learn features quickly
- **Reference:** Quick lookup for keyboard shortcuts
- **Discovery:** Users learn about features they didn't know existed
- **Self-Service:** Reduces need for external documentation

---

## Usage Examples

### Example 1: Quick Error Check
```
1. Open log file
2. Look at Error button: "Error (45)"
3. Know immediately there are 45 errors
4. Click button to see them all
```

### Example 2: Find Specific Warnings
```
1. Open log file
2. See "Warning (123)"
3. Type "deprecated" in search
4. See "Warning (8/123)"
5. Know 8 warnings contain "deprecated"
```

### Example 3: Learn Keyboard Shortcuts
```
1. Click "❓ Help" button
2. Go to "Shortcuts" tab
3. Learn Ctrl+Up/Down navigates search results
4. Start using shortcuts for faster workflow
```

---

## Implementation Details

### Count Badges
- **File:** `LogViewer.py`
- **Methods Added:**
  - `count_levels()` - Count lines per level
  - `count_filtered_levels()` - Count filtered lines per level
  - `update_level_button_text()` - Update button text with counts
- **Storage:**
  - `self.levelCounts` - Total counts per level
  - `self.filteredCounts` - Filtered counts per level
- **Update Triggers:**
  - On file load
  - On search text change
  - On filter button click

### Help System
- **Files Modified:**
  - `LogViewer.py` - Help dialog and content
  - `LogViewTab.py` - Help menu in menu bar
- **Components:**
  - `self.helpButton` - Toolbar button
  - `show_help_dialog()` - Display help dialog
  - `_get_*_help_html()` - Generate help content
- **Features:**
  - Tabbed interface for organized content
  - Rich HTML formatting
  - Color-coded examples
  - External links support (GitHub)

---

## User Interface Changes

### Before
```
[🔄] [Text] [Debug] [Info] [Warning] [Error] [Clear] [🔍 Search...]
```

### After
```
[🔄] [Text (5000)] [Debug (2500)] [Info (2455)] [Warning (33)] [Error (12)] [Clear] [🔍 Search...] [❓ Help]
```

---

## Testing

### Test Cases
1. ✅ Load file - counts appear on buttons
2. ✅ Search text - counts update to filtered/total
3. ✅ Click filter - counts remain accurate
4. ✅ Clear filters - counts show total again
5. ✅ Reload file - counts recalculate correctly
6. ✅ Help button - dialog opens
7. ✅ F1 shortcut - dialog opens
8. ✅ Help menu - dialog opens
9. ✅ All tabs - content displays correctly
10. ✅ Zero counts - show (0) correctly

### Performance
- No noticeable performance impact on large files (tested with 100K+ lines)
- Count calculation is fast (O(n) single pass)
- UI updates are smooth

---

## Future Enhancements (Potential)

### Count Badges
- [ ] Show percentage: `Error (12) 0.12%`
- [ ] Color-code buttons by count severity
- [ ] Hover tooltip with detailed breakdown

### Help System
- [ ] Search within help dialog
- [ ] Animated GIF examples
- [ ] Video tutorials
- [ ] Interactive tour on first launch

---

## Version History

### v1.1.1 (2025-11-21)
- 🐛 **CRITICAL FIX:** Fixed memory corruption crash in help dialog
- 🔧 Replaced QTextBrowser+HTML with QTextEdit+plain text for stability
- ✅ Help dialog now scrollable without crashes

### v1.1.0 (2025-11-21)
- ✨ Added level count badges on filter buttons
- ✨ Added comprehensive help system with 4 tabs
- ✨ Added Help button to toolbar
- ✨ Added Help menu with F1/Ctrl+H shortcuts
- 📝 Enhanced tooltips with count information
- 🎨 Improved user experience with better feedback

### v1.0.0 (2025-11-21)
- 🎉 Initial release
- Python launcher with diagnostics
- Multi-tab interface
- Log level filtering
- Search functionality
- Clickable file links

---

## Credits

Developed by: avice @ NVIDIA  
Python Version: 3.11.9  
Framework: PyQt5

---

## Feedback

For issues, feature requests, or contributions:
- GitHub: https://github.com/avice-NVDA/tablog
- Open an issue or submit a pull request

