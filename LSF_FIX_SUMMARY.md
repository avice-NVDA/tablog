# TabLog LSF Shell Compatibility - Fix Summary

## 🎉 Status: RESOLVED ✅

TabLog now works perfectly in both **regular shells** and **LSF shells**!

---

## Problem History

When running TabLog from an LSF interactive shell (`bsub -Is`), the application failed with various errors:

### Initial Errors Encountered:

1. **FreeType Symbol Error** (First issue)
   ```
   undefined symbol: FT_Get_Font_Format
   ```

2. **Qt Platform Plugin Error** (Second issue)
   ```
   no Qt platform plugin could be initialized
   ```

3. **libpng16 Missing** (Third issue)
   ```
   libpng16.so.16 => not found
   ```

4. **ZLIB Version Mismatch** (Final issue)
   ```
   version `ZLIB_1.2.9' not found (required by libpng16.so.16)
   ```

---

## Root Cause

**LSF shells modify `LD_LIBRARY_PATH`** to include LSF-specific libraries, which often contain **older/incompatible versions** of system libraries that conflict with Qt's requirements.

### Specific Issues:

1. **PyQt5 from pip doesn't bundle FreeType** - relies on system library
2. **LSF's old FreeType** doesn't have `FT_Get_Font_Format` symbol
3. **xcb platform plugin** requires libpng16 (not in LSF path)
4. **libpng16** requires ZLIB_1.2.9 (LSF has older version)

### Why LD_LIBRARY_PATH Manipulation Failed:

Qt libraries have `RUNPATH: [$ORIGIN]` which means they search **their own directory FIRST**, before `LD_LIBRARY_PATH`. This is an ELF security feature that cannot be overridden by environment variables.

---

## Solution

**Copy required system libraries to Qt's lib directory** so Qt's `RUNPATH: [$ORIGIN]` finds them first.

### Libraries Copied:

1. **libfreetype.so.6** (from `/lib64/`)
   - Provides `FT_Get_Font_Format` symbol
   - Required by Qt's font rendering

2. **libpng16.so.16** (from `/usr/lib64/`)
   - Required by xcb platform plugin
   - Needed for PNG image support

3. **libz.so.1** (from `/lib64/`)
   - Provides ZLIB_1.2.9
   - Required by libpng16

### Destination:
```
/home/scratch.avice_vlsi/tablog/venv_pyqt5_rebuild/lib/python3.11/site-packages/PyQt5/Qt5/lib/
```

---

## How It Works

1. **Qt's RUNPATH** (`$ORIGIN`) searches its own lib directory first
2. **Copied libraries** are found before LSF's old versions
3. **LSF can't interfere** because RUNPATH has priority over LD_LIBRARY_PATH
4. **Works in both shells** - doesn't depend on environment variables

---

## Files Modified/Created

### Scripts:
- **`fix_lsf_libraries.sh`** - Automated script to copy required libraries
- **`tablog_debug`** - Debug launcher showing environment setup
- **`tablog`** - Main launcher (updated for better compatibility)

### Documentation:
- **`LSF_SHELL_GUIDE.md`** - Complete LSF troubleshooting guide
- **`LSF_FIX_SUMMARY.md`** - This file

### Libraries (in venv, not in git):
- `venv_pyqt5_rebuild/.../Qt5/lib/libfreetype.so.6*`
- `venv_pyqt5_rebuild/.../Qt5/lib/libpng16.so.16*`
- `venv_pyqt5_rebuild/.../Qt5/lib/libz.so.1*`

---

## For Other Users

If a colleague encounters LSF shell issues with TabLog:

### Option 1: Copy Entire Directory (Fastest)
```bash
# Copy from working installation
cp -r /home/scratch.avice_vlsi/tablog /home/scratch.THEIR_USER_vlsi/

# Works immediately - all libraries already in place!
cd /home/scratch.THEIR_USER_vlsi/tablog
./tablog example.log
```

### Option 2: Clone from GitHub
```bash
git clone github.com:avice-NVDA/tablog.git
cd tablog

# Setup virtual environment
./setup_venv.sh

# Copy required system libraries
./fix_lsf_libraries.sh

# Done!
./tablog example.log
```

---

## Testing Checklist

- ✅ Regular shell → Works
- ✅ LSF shell (`bsub -Is bash`) → Works
- ✅ Large log files (29 MB / 135K lines) → Works
- ✅ In-app help dialog → Works (no crashes)
- ✅ All level count badges → Works
- ✅ Search and filter → Works
- ✅ No warnings or errors → Clean output

---

## Technical Details

### Why This Approach Works:

**ELF RUNPATH** takes precedence over `LD_LIBRARY_PATH`:

1. **RUNPATH** (`$ORIGIN`) - Qt's own directory (highest priority)
2. **LD_LIBRARY_PATH** - Environment variable (middle priority)
3. **System paths** (`/lib64`, `/usr/lib64`) - Default (lowest priority)

By placing compatible libraries in Qt's lib directory, they're found via RUNPATH before any LSF or system libraries.

### Verification Command:

```bash
# Check Qt library's RUNPATH
readelf -d venv_pyqt5_rebuild/.../PyQt5/Qt5/lib/libQt5XcbQpa.so.5 | grep RUNPATH
# Output: Library runpath: [$ORIGIN]

# Check xcb plugin dependencies
ldd venv_pyqt5_rebuild/.../PyQt5/Qt5/plugins/platforms/libqxcb.so
# Should show no "not found" errors
```

---

## Lessons Learned

1. **LD_LIBRARY_PATH is not always sufficient** - ELF RUNPATH takes priority
2. **LSF environments are tricky** - They modify many environment variables
3. **PyQt5 from pip has external dependencies** - Doesn't bundle all libraries
4. **Dependencies have dependencies** - libpng16 → zlib chain
5. **Diagnostics are essential** - Created comprehensive test scripts to debug

---

## Version Information

- **TabLog Version:** 1.2.0+
- **Python:** 3.11.9
- **PyQt5:** 5.15.6
- **Qt:** 5.15.2 (bundled with PyQt5)
- **Platform:** RHEL 8 (x86_64)
- **LSF:** IBM Platform LSF

---

## Credits

**Fixed:** December 5, 2025  
**Issue:** LSF shell compatibility  
**Solution:** Copy system libraries to Qt's lib directory (RUNPATH resolution)

---

## Support

For issues or questions:
1. Check `LSF_SHELL_GUIDE.md` for detailed troubleshooting
2. Run `./tablog_debug` to see environment diagnostics
3. Run `./fix_lsf_libraries.sh` to ensure libraries are in place
4. Check GitHub issues or contact maintainer

---

**🎉 TabLog is now fully compatible with LSF shells!** 🎉

