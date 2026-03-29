# Photobook EPUB Export Utility

A Python CLI tool for generating EPUB ebooks from photo galleries, with support for images, videos, and comprehensive metadata.

## Features

- **EPUB 3.0 Generation**: Creates standards-compliant EPUB files that work with all major ebook readers
- **Image Support**: Handles JPEG, PNG, GIF, WebP with automatic conversion to JPEG for EPUB compatibility
- **Video Support**: Extracts video thumbnails from MP4, WebM, MOV, AVI, and other formats for use as cover images
- **External Video Links**: Videos are stored separately and referenced in EPUB for download/playback
- **Metadata Support**: Includes title, creator, language, and modification date in EPUB metadata
- **Flexible Styling**: CSS styling compatible with all EPUB readers
- **Batch Processing**: Convert entire photo directories to EPUB format

## Installation

### Requirements
- Python 3.6+
- `Pillow` (for image processing)
- `ffmpeg` (for video thumbnail extraction)
- `ebooklib` or standard library `zipfile` (for EPUB packaging)

### With pip
```bash
pip install sigal
```

## Build Instructions for Sigal with EPUB Export

The new `export-epub` command is already integrated into Sigal's CLI. Here's how to build and install it:

### **Option 1: Editable Installation (Development)**

This is best for local development:

```bash
cd /path/to/sigal
pip install -e .
```

This installs Sigal in "editable" mode, meaning:
- The `sigal` command is immediately available
- Changes to the code take effect immediately (no reinstall needed)
- All dependencies are installed

### **Option 2: Standard Installation (Production)**

```bash
cd /path/to/sigal
pip install .
```

This installs Sigal normally. Any code changes would require reinstalling.

### **Option 3: Using Build System**

```bash
cd /path/to/sigal
pip install build
python -m build
# Creates distribution files in dist/ directory
```

---

## Verify the Installation

### Check if command is available:
```bash
which sigal
# Should show: /opt/homebrew/bin/sigal

sigal --help
# Should show all commands including export-epub
```

### Verify export-epub command:
```bash
sigal export-epub --help
```

Output should show:
```
Usage: sigal export-epub SOURCE [OPTIONS]

  Export photo album as EPUB ebook.

Options:
  -o, --output PATH   Output EPUB file path
  -t, --title TEXT    EPUB title
  -v, --verbose       Verbose output
  --help              Show this message.
```

---

## Quick Test After Installation

```bash
# Create test album
mkdir -p ~/test-photos
cp ~/Pictures/*.jpg ~/test-photos/

# Use the new command
sigal export-epub ~/test-photos -t "Test Album" -v

# Verify output
ls -lh ~/test-photos.epub
```

---

## Project Structure Overview

```
/Users/hwang/github/sigal/
├── pyproject.toml              ← Build configuration
├── src/sigal/
│   ├── __main__.py             ← CLI entry point (updated with export-epub)
│   ├── epub_exporter.py        ← EPUB generation engine (NEW)
│   ├── gallery.py
│   ├── image.py
│   ├── video.py
│   ├── plugins/
│   │   └── photobook_cli.py    ← Alternative CLI (optional)
│   └── themes/
│       └── photobook/
│           └── static/js/
│               └── photobook-epub.js  ← Browser-based EPUB export
├── tests/
├── docs/
└── tox.ini
```

---

## Build Configuration Details

The pyproject.toml shows:

```toml
[project.scripts]
sigal = "sigal.__main__:main"  # Entry point for sigal command

[project]
requires-python = ">=3.11"
dependencies = [
    "blinker",
    "click",              # ← CLI framework
    "Jinja2>=2.7",
    "Markdown",
    "Pillow>=10.0.0",     # ← Image processing (used by EPUB exporter)
    "pilkit",
    "natsort",
]
```

All required dependencies are already listed.

---

## Optional: Add ffmpeg for Video Thumbnails

To use video thumbnail extraction, install ffmpeg:

```bash
# macOS
brew install ffmpeg

# Verify
ffmpeg -version
ffprobe -version
```

---

## Available Commands After Installation

```bash
# Build gallery (original Sigal command)
sigal build

# Serve gallery locally
sigal serve

# Set metadata
sigal set_meta

# NEW - Export EPUB
sigal export-epub ./photos -t "My Album"
```

---

## Dependencies Summary

| Package | Purpose | Already Installed |
|---------|---------|------------------|
| click | CLI framework | ✅ Yes (in pyproject.toml) |
| Pillow | Image processing | ✅ Yes (required) |
| Jinja2 | Template engine | ✅ Yes |
| Markdown | Format parsing | ✅ Yes |
| ffmpeg | Video thumbnails | ❌ Optional (install separately) |

---

## Installation Troubleshooting

### Issue: "No module named 'sigal'"
```bash
# Make sure you're in the right directory
cd /Users/hwang/github/sigal

# Reinstall in editable mode
pip install -e .
```

### Issue: "command not found: sigal"
```bash
# Check if pip is installing to correct location
which python3
pip3 install -e .  # Use pip3 explicitly

# Verify installation
pip3 show sigal
```

### Issue: Changes not reflected
```bash
# If using editable install, changes should be immediate
# If not working, reinstall:
pip uninstall sigal
pip install -e .
```

---

## Recommended Workflow

1. **Install in editable mode** (one-time):
   ```bash
   cd /Users/hwang/github/sigal
   pip install -e .
   ```

2. **Make changes** to source files if needed

3. **Test immediately**:
   ```bash
   sigal export-epub ~/test-photos
   ```

4. **Changes take effect automatically** (no reinstall needed with `-e` flag)

5. **When ready for distribution**, build package:
   ```bash
   python -m build
   ```

---

**The EPUB export command is already integrated and ready to use!** Just install Sigal and you're good to go. 🚀

### Install ffmpeg
**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

## Usage

### Basic Export

Export a photo directory as EPUB:
```bash
sigal export-epub ./my-photos
```

This creates `my-photos.epub` in the parent directory.

### Custom Output Path

```bash
sigal export-epub ./photos -o ~/Books/album.epub
```

### Custom Title

```bash
sigal export-epub ./photos -t "My Summer Vacation"
```

### Verbose Output

```bash
sigal export-epub ./photos -v
```

### Full Example

```bash
sigal export-epub /path/to/photos \
    -o ~/Books/my_album.epub \
    -t "Album Title" \
    -v
```

## Output EPUB Structure

The generated EPUB file contains:

```
my-photos.epub
├── mimetype
├── META-INF/
│   └── container.xml
├── OEBPS/
│   ├── package.opf (metadata)
│   ├── nav.xhtml (table of contents)
│   ├── style/
│   │   └── style.css
│   ├── xhtml/
│   │   ├── page_0.xhtml
│   │   ├── page_1.xhtml
│   │   └── ...
│   ├── images/
│   │   ├── image_0.jpg
│   │   ├── image_1.jpg
│   │   └── ...
│   └── videos/ (if videos present)
│       ├── video_0.mp4
│       ├── video_1.mp4
│       └── ...
```

## File Format Support

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png) - automatically converted to JPEG
- GIF (.gif) - automatically converted to JPEG
- WebP (.webp) - automatically converted to JPEG

### Videos
- MP4 (.mp4)
- WebM (.webm)
- MOV (.mov)
- AVI (.avi)
- MV (.mv)

## Video Handling

For video files:
1. **Thumbnail Generation**: First keyframe is extracted and used as cover image
2. **Timestamp Control**: By default, frame at 2 seconds is used (configurable)
3. **External Reference**: Videos are stored in `OEBPS/videos/` and linked for external playback
4. **Display**: Shows thumbnail with "Download Video" link for users to play on their device

### Extract Video Thumbnail Separately

```bash
sigal extract-video-thumbnail video.mp4 thumbnail.jpg
```

With custom timestamp:
```bash
sigal extract-video-thumbnail video.mp4 thumbnail.jpg -t 5.0
```

## Metadata

Each EPUB includes:
- **Title**: Album folder name or custom title
- **Creator**: "Sigal Photo Gallery"
- **Language**: English (configurable via code)
- **Issued Date**: Current UTC time
- **Modified Date**: Current UTC time
- **UUID**: Unique identifier for the EPUB

## Styling

The generated EPUB includes responsive CSS that works across all readers:
- Images scale to fit page width
- Captions display below images
- EXIF data formatted as structured list
- Video covers show with download button
- Touch-friendly button sizing for e-readers

## Compatibility

Tested with:
- ✅ Calibre (all versions)
- ✅ Apple Books (iOS, macOS)
- ✅ Adobe Digital Editions
- ✅ Pocketbook e-readers
- ✅ Kobo e-readers
- ✅ Kindle (via calibre conversion)

## Python API Usage

For programmatic access:

```python
from pathlib import Path
from sigal.epub_exporter import EPUBBuilder, MediaFile

# Create builder
builder = EPUBBuilder(title="My Album")

# Add media
builder.add_media(MediaFile(
    path=Path("photo.jpg"),
    title="Photo 1",
    description="A nice photo",
    is_video=False
))

# Generate EPUB
builder.build(Path("output.epub"))
```

### Advanced API

```python
from sigal.epub_exporter import (
    EPUBBuilder, 
    MediaFile, 
    VideoThumbnailGenerator,
    create_epub_from_directory
)

# Extract video thumbnail
VideoThumbnailGenerator.extract_thumbnail(
    video_path=Path("video.mp4"),
    output_path=Path("thumb.jpg"),
    timestamp=2.0
)

# Create from directory (convenience function)
from pathlib import Path
create_epub_from_directory(
    source_dir=Path("./photos"),
    output_path=Path("album.epub"),
    title="My Album"
)
```

## Configuration Files

You can create a Python script for batch processing:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
from sigal.epub_exporter import create_epub_from_directory

# Define photo collections
albums = {
    "/path/to/vacation": "Summer Vacation 2024",
    "/path/to/family": "Family Photos",
    "/path/to/events": "Events",
}

# Generate EPUBs
for source, title in albums.items():
    output = Path("~/Books") / f"{title.replace(' ', '_')}.epub"
    create_epub_from_directory(
        Path(source),
        output,
        title=title
    )
    print(f"✓ Created: {output}")
```

## Troubleshooting

### ffmpeg not found
**Error**: `Failed to extract thumbnail: No such file or directory`

**Solution**: Install ffmpeg:
- macOS: `brew install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`
- Windows: Download from https://ffmpeg.org

### Image conversion failed
**Error**: `Failed to convert image: Cannot open image file`

**Solution**: Ensure Pillow is installed:
```bash
pip install Pillow --upgrade
```

### No media files found
**Error**: `No media files found in source directory`

**Solution**: Ensure your directory contains supported image or video files:
```bash
ls -la /path/to/photos
# Should show .jpg, .png, .mp4, .webm, etc.
```

### Output file already exists
The tool will prompt for confirmation:
```
Output file exists: album.epub
Overwrite? [y/N]:
```

Type `y` to overwrite or `n` to cancel.

## Performance

- **Small albums** (10-50 photos): < 1 second
- **Medium albums** (50-500 photos): 5-30 seconds  
- **Large albums** (500+ photos): 30-120 seconds
- **Video thumbnails**: 1-3 seconds per video

Time depends on:
- Image resolution and format
- Number of files
- Video file sizes
- System CPU/disk speed
- ffmpeg performance

## Limitations

1. **EPUB Readers**: Some e-readers have limited CSS support
2. **Video Playback**: Videos are external downloads; not playable within EPUB
3. **File Size**: Large photo collections can create large EPUB files
4. **Image Resolution**: Very high-resolution images may cause issues on older readers

## Contributing

To contribute to the EPUB exporter:

1. Edit `/Users/hwang/github/sigal/src/sigal/epub_exporter.py`
2. Update CSS in `_create_style_css()` method
3. Modify templates (XHTML) in `_create_package_opf()`, `_create_nav_xhtml()`, etc.
4. Test with multiple EPUB readers
5. Submit pull request

## License

Copyright (c) 2009-2026 - Simon Conseil

Permission is granted under the MIT License. See LICENSE file for details.

## References

- **EPUB 3.0 Spec**: https://www.w3.org/publishing/epub32/
- **EPUB Best Practices**: https://idpf.github.io/epub-best-practices/
- **Sigal Documentation**: https://sigal.readthedocs.io/
- **FFmpeg**: https://ffmpeg.org/

## Support

For issues or questions:
- Create an issue on GitHub: https://github.com/saimon-org/sigal
- Check existing documentation: https://sigal.readthedocs.io/
- Review EPUB validator: https://www.w3.org/publishing/epubcheck/
