#!/bin/bash

# Quick Start Guide for Sigal EPUB Export CLI

echo "=========================================="
echo "SIGAL EPUB EXPORT CLI - QUICK START"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.6 or later."
    exit 1
fi
echo "✓ Python 3 found: $(python3 --version)"

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠ ffmpeg not found (optional but needed for video thumbnails)"
    echo "  Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
else
    echo "✓ ffmpeg found"
fi

echo ""
echo "=========================================="
echo "SETUP STEPS"
echo "=========================================="
echo ""

# Step 1: Install dependencies
echo "1. Install Python dependencies:"
echo "   pip install Pillow"
echo ""

# Step 2: Create test album
echo "2. Create a test album with sample photos:"
echo "   mkdir -p ~/test-album"
echo "   cp ~/Pictures/*.jpg ~/test-album/"
echo ""

# Step 3: Generate EPUB
echo "3. Generate EPUB:"
echo "   sigal export-epub ~/test-album -t 'My Album' -o ~/my-album.epub"
echo ""

# Step 4: Open in reader
echo "4. Open the generated EPUB in your favorite reader:"
echo "   open ~/my-album.epub  # macOS"
echo ""

echo "=========================================="
echo "COMMON COMMANDS"
echo "=========================================="
echo ""

echo "Basic export (defaults to album_name.epub):"
echo "  \$ sigal export-epub ./my-photos"
echo ""

echo "Custom output location and title:"
echo "  \$ sigal export-epub ./photos -o ~/Books/vacation.epub -t 'Summer 2024'"
echo ""

echo "Verbose output (shows progress):"
echo "  \$ sigal export-epub ./photos -v"
echo ""

echo "Extract video thumbnail separately:"
echo "  \$ sigal extract-video-thumbnail video.mp4 thumbnail.jpg -t 5.0"
echo ""

echo "=========================================="
echo "FEATURES INCLUDED"
echo "=========================================="
echo ""

echo "✓ Image Support:"
echo "  - JPEG, PNG, GIF, WebP (auto-converted to JPEG)"
echo "  - Responsive scaling for all readers"
echo "  - Full-resolution preservation"
echo ""

echo "✓ Video Support:"
echo "  - Automatic thumbnail extraction"
echo "  - External video file linking"
echo "  - Works with MP4, WebM, MOV, AVI"
echo ""

echo "✓ Metadata:"
echo "  - Album title and creator"
echo "  - Image descriptions and EXIF data"
echo "  - Table of contents navigation"
echo "  - EPUB 3.0 compliant"
echo ""

echo "✓ Compatibility:"
echo "  - Calibre"
echo "  - Apple Books"
echo "  - Adobe Digital Editions"
echo "  - Pocketbook"
echo "  - Kobo"
echo ""

echo "=========================================="
echo "PYTHON API USAGE"
echo "=========================================="
echo ""

echo "

from pathlib import Path
from sigal.epub_exporter import create_epub_from_directory

# Generate EPUB from directory
create_epub_from_directory(
    source_dir=Path('./my-photos'),
    output_path=Path('album.epub'),
    title='My Album'
)
"

echo ""
echo "=========================================="
echo "NEXT STEPS"
echo "=========================================="
echo ""
echo "1. Read the comprehensive guide:"
echo "   cat README_EPUB_EXPORT.md"
echo ""
echo "2. Run the test suite:"
echo "   python3 test_epub_export.py"
echo ""
echo "3. Try with your own photos!"
echo ""
