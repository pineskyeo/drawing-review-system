#!/bin/bash
# Drawing Review System - macOS Setup

echo "=== Drawing Review System Setup (macOS) ==="
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Install from https://python.org"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p data/{chroma_db,standards-pdfs,cache} inbox in_progress reports logs

# Check DWG converter
echo
echo "=== DWG Converter Check ==="
if [ -f "/tmp/libredwg/build/dwg2dxf" ]; then
    echo "[OK] LibreDWG dwg2dxf found"
elif command -v dwg2dxf &> /dev/null; then
    echo "[OK] dwg2dxf found in PATH"
else
    echo "[WARN] No DWG converter found."
    echo "       Building LibreDWG from source..."

    # Auto-build LibreDWG
    if command -v cmake &> /dev/null; then
        CMAKE="cmake"
    elif [ -f "/tmp/cmake-3.28.3-macos-universal/CMake.app/Contents/bin/cmake" ]; then
        CMAKE="/tmp/cmake-3.28.3-macos-universal/CMake.app/Contents/bin/cmake"
    else
        echo "       cmake not found. Install cmake first or use DXF directly."
        CMAKE=""
    fi

    if [ -n "$CMAKE" ]; then
        cd /tmp
        [ ! -d libredwg ] && git clone --depth 1 https://github.com/LibreDWG/libredwg.git
        cd libredwg && git submodule update --init --recursive
        mkdir -p build && cd build
        $CMAKE .. -DDISABLE_WERROR=ON \
            -DCMAKE_C_FLAGS="-Wno-unused-command-line-argument -Wno-implicit-function-declaration -Wno-int-to-pointer-cast"
        make -j$(sysctl -n hw.ncpu) dwg2dxf
        cd -
        echo "[OK] LibreDWG built at /tmp/libredwg/build/dwg2dxf"
    fi
fi

echo
echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "  1. Put DWG files in inbox/"
echo "  2. Run: python3 scripts/extract/extract_dwg.py --input inbox/sample.dwg --output data/cache/drawing.json"
