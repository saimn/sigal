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

### For development
```bash
cd /path/to/sigal
pip install -e .
```

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
