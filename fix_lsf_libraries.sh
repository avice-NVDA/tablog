#!/bin/bash
# Fix LSF Shell Library Dependencies for TabLog
# This script copies required system libraries to Qt's lib directory
# so Qt can find them via its RUNPATH ($ORIGIN)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
QT_LIB="$SCRIPT_DIR/venv_pyqt5_rebuild/lib/python3.11/site-packages/PyQt5/Qt5/lib"

echo "=========================================="
echo "TabLog - Fix LSF Library Dependencies"
echo "=========================================="
echo ""

if [ ! -d "$QT_LIB" ]; then
    echo "❌ Error: Qt lib directory not found at:"
    echo "   $QT_LIB"
    echo ""
    echo "Please run setup_venv.sh first to create the virtual environment."
    exit 1
fi

echo "Qt lib directory: $QT_LIB"
echo ""

# Function to copy library if needed
copy_lib() {
    local lib_name=$1
    local system_path=$2
    
    if [ -f "$QT_LIB/$lib_name" ]; then
        echo "✅ $lib_name already present"
        return 0
    fi
    
    if [ ! -f "$system_path" ]; then
        echo "❌ $lib_name not found at $system_path"
        return 1
    fi
    
    echo "Copying $lib_name..."
    cp -v "$system_path"* "$QT_LIB/" 2>/dev/null || cp -v "$system_path" "$QT_LIB/"
    echo "✅ $lib_name copied"
}

echo "Checking and copying required libraries..."
echo ""

# Copy FreeType (for FT_Get_Font_Format symbol)
copy_lib "libfreetype.so.6" "/lib64/libfreetype.so.6"

# Copy libpng16 (required by xcb platform plugin)
copy_lib "libpng16.so.16" "/usr/lib64/libpng16.so.16"

# Copy zlib (libpng16 requires ZLIB_1.2.9)
copy_lib "libz.so.1" "/lib64/libz.so.1"

echo ""
echo "=========================================="
echo "Verifying xcb plugin dependencies..."
echo "=========================================="
echo ""

XCB_PLUGIN="$SCRIPT_DIR/venv_pyqt5_rebuild/lib/python3.11/site-packages/PyQt5/Qt5/plugins/platforms/libqxcb.so"

if [ ! -f "$XCB_PLUGIN" ]; then
    echo "❌ xcb plugin not found!"
    exit 1
fi

# Check dependencies with Qt lib in path
export LD_LIBRARY_PATH="$QT_LIB:$LD_LIBRARY_PATH"
MISSING=$(ldd "$XCB_PLUGIN" 2>&1 | grep "not found" || true)

if [ -n "$MISSING" ]; then
    echo "❌ Still missing dependencies:"
    echo "$MISSING"
    echo ""
    echo "Please report this issue with the output above."
    exit 1
else
    echo "✅ All xcb plugin dependencies satisfied!"
fi

echo ""
echo "=========================================="
echo "✅ LSF Library Fix Complete!"
echo "=========================================="
echo ""
echo "TabLog should now work in LSF shells."
echo ""
echo "Test it:"
echo "  bsub -Is bash"
echo "  export DISPLAY=:3  # or your DISPLAY value"
echo "  cd $SCRIPT_DIR"
echo "  ./tablog example.log"
echo ""

