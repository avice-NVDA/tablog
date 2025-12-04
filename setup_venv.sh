#!/bin/bash
# Setup script for TabLog v1.2.0
# Creates the virtual environment with PyQt5 5.15.6

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "TabLog v1.2.0 - Virtual Environment Setup"
echo "=========================================="
echo ""

# Check if venv already exists
if [ -d "venv_pyqt5_rebuild" ]; then
    echo "✅ Virtual environment already exists!"
    echo ""
    echo "To reinstall, first remove it:"
    echo "  rm -rf venv_pyqt5_rebuild"
    echo "  ./setup_venv.sh"
    echo ""
    exit 0
fi

# Check for Python 3.11.9
PYTHON_EXE="/home/utils/Python/builds/3.11.9-20250715/bin/python3"

if [ ! -f "$PYTHON_EXE" ]; then
    echo "❌ Error: Required Python not found at:"
    echo "   $PYTHON_EXE"
    echo ""
    echo "Please install Python 3.11.9 or update PYTHON_EXE in this script."
    exit 1
fi

echo "Found Python: $($PYTHON_EXE --version)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_EXE -m venv venv_pyqt5_rebuild
echo "✅ Virtual environment created"
echo ""

# Activate and install dependencies
echo "Installing dependencies..."
source venv_pyqt5_rebuild/bin/activate

echo "  - Upgrading pip..."
pip install --upgrade pip -q

echo "  - Installing PyQt5 5.15.6..."
pip install PyQt5==5.15.6 -q

echo "  - Installing PyQt5-sip..."
pip install PyQt5-sip -q

echo "  - Installing ansi2html..."
pip install ansi2html -q

echo "✅ Dependencies installed"
echo ""

# Verify installation
echo "Verifying installation..."
python -c "from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR; print('  Qt:', QT_VERSION_STR); print('  PyQt5:', PYQT_VERSION_STR)"
python -c "import ansi2html; print('  ansi2html: OK')"
echo ""

# Check size
VENV_SIZE=$(du -sh venv_pyqt5_rebuild | cut -f1)
echo "Virtual environment size: $VENV_SIZE"
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "TabLog is ready to use:"
echo "  ./tablog example.log"
echo ""
echo "For help:"
echo "  ./tablog --help"
echo ""

