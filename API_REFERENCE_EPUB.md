# Sigal EPUB Exporter - API Reference

## Module: `sigal.epub_exporter`

Complete API documentation for the EPUB generation system.

## Classes

### `MediaFile` (dataclass)

Represents a single media item (image or video).

#### Attributes

```python
path: pathlib.Path          # Path to media file
title: str                  # Display title
description: str = ""       # Long description
exif: str = ""             # EXIF/metadata text
is_video: bool = False     # True for videos, False for images
```

#### Methods

```python
def exists(self) -> bool:
    """Check if media file exists on disk"""
```

#### Example

```python
from pathlib import Path
from sigal.epub_exporter import MediaFile

photo = MediaFile(
    path=Path("/photos/sunset.jpg"),
    title="Sunset at the Beach",
    description="Beautiful sunset at California coast",
    exif="Camera: Canon EOS 5D\nISO: 100\nShutter: 1/125",
    is_video=False
)
```

---

### `VideoThumbnailGenerator`

Static utility class for video thumbnail extraction.

#### Static Methods

##### `get_video_duration(video_path: pathlib.Path) -> Optional[float]`

Get video duration in seconds using ffprobe.

**Parameters:**
- `video_path`: Path to video file

**Returns:**
- Duration in seconds, or None if unable to determine

**Example:**
```python
from sigal.epub_exporter import VideoThumbnailGenerator
from pathlib import Path

duration = VideoThumbnailGenerator.get_video_duration(Path("video.mp4"))
print(f"Duration: {duration} seconds")
```

##### `extract_thumbnail(video_path: pathlib.Path, output_path: pathlib.Path, timestamp: float = 2.0) -> bool`

Extract a single frame from video and save as JPEG.

**Parameters:**
- `video_path`: Path to input video file
- `output_path`: Path to save thumbnail JPEG
- `timestamp`: Seconds into video to extract (default: 2.0)

**Returns:**
- True if successful, False otherwise

**Requirements:**
- ffmpeg must be installed
- output_path parent directory must exist or be creatable

**Example:**
```python
from sigal.epub_exporter import VideoThumbnailGenerator
from pathlib import Path

success = VideoThumbnailGenerator.extract_thumbnail(
    video_path=Path("video.mp4"),
    output_path=Path("thumb.jpg"),
    timestamp=5.0  # Extract frame at 5 seconds
)

if success:
    print("Thumbnail created successfully")
else:
    print("Failed to extract thumbnail")
```

---

### `EPUBBuilder`

Main class for building EPUB files.

#### Constructor

```python
def __init__(self, 
             title: str = "Photo Gallery",
             album_path: Optional[pathlib.Path] = None):
```

**Parameters:**
- `title`: EPUB title (appears in readers)
- `album_path`: Optional album directory path (for context)

**Example:**
```python
from sigal.epub_exporter import EPUBBuilder

builder = EPUBBuilder(
    title="My Photo Album",
    album_path=Path("/home/user/photos")
)
```

#### Instance Attributes

```python
title: str                          # Album title
album_path: pathlib.Path           # Album directory
uuid: str                          # Unique identifier
media_list: List[MediaFile]        # Added media files
temp_dir: Optional[pathlib.Path]  # Temporary build directory
epub_path: Optional[pathlib.Path] # Generated EPUB path
```

#### Methods

##### `add_media(media: MediaFile) -> None`

Add a media file to the EPUB.

**Parameters:**
- `media`: MediaFile instance to add

**Example:**
```python
builder.add_media(MediaFile(
    path=Path("photo.jpg"),
    title="My Photo",
    is_video=False
))
```

##### `build(output_path: pathlib.Path) -> bool`

Generate the EPUB file.

**Parameters:**
- `output_path`: Path where EPUB file will be created

**Returns:**
- True if successful, False if generation failed

**Side Effects:**
- Creates temporary files during build (cleaned up automatically)
- Can overwrite existing file

**Example:**
```python
builder = EPUBBuilder(title="Album")
builder.add_media(MediaFile(Path("photo.jpg"), "Photo 1"))

success = builder.build(Path("album.epub"))
if success:
    print(f"EPUB created: album.epub")
```

#### Private Methods (Internal Use)

```python
def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe use in filesystems"""
    
def _escape_xml(text: str) -> str:
    """Escape special XML characters"""
    
def _format_description(text: str) -> str:
    """Format description paragraph with HTML markup"""
    
def _format_exif(exif_text: str) -> str:
    """Format EXIF data as structured HTML"""
    
def _create_container_xml(self) -> str:
    """Create META-INF/container.xml"""
    
def _create_package_opf(self) -> str:
    """Create OEBPS/package.opf (manifest and metadata)"""
    
def _create_nav_xhtml(self) -> str:
    """Create OEBPS/nav.xhtml (table of contents)"""
    
def _create_page_xhtml(media: MediaFile, idx: int) -> str:
    """Create individual page XHTML"""
    
def _create_style_css(self) -> str:
    """Create OEBPS/style/style.css"""
    
def _prepare_media(output_dir: pathlib.Path) -> bool:
    """Process media files and generate thumbnails"""

def _create_placeholder_image(path: pathlib.Path) -> None:
    """Create placeholder image for missing thumbnails"""
```

---

## Functions

### `create_epub_from_directory(source_dir: pathlib.Path, output_path: pathlib.Path, title: Optional[str] = None) -> bool`

Convenience function to create EPUB from a directory of photos.

**Parameters:**
- `source_dir`: Directory containing media files (photos/videos)
- `output_path`: Path where EPUB file will be saved
- `title`: Optional EPUB title (defaults to directory name)

**Returns:**
- True if successful, False otherwise

**Supported Formats:**
- Images: .jpg, .jpeg, .png, .gif, .webp
- Videos: .mp4, .webm, .mov, .avi, .mv

**Example:**
```python
from pathlib import Path
from sigal.epub_exporter import create_epub_from_directory

create_epub_from_directory(
    source_dir=Path("/home/user/vacation_photos"),
    output_path=Path("vacation.epub"),
    title="Summer Vacation 2024"
)
```

---

## CLI Integration

The EPUB exporter is integrated into Sigal's main CLI via a new command.

### Command: `export-epub`

```bash
sigal export-epub SOURCE [OPTIONS]
```

**Arguments:**
- `SOURCE`: Directory containing photos/videos

**Options:**
- `-o, --output PATH`: Output EPUB file path (default: SOURCE.epub in parent dir)
- `-t, --title TEXT`: EPUB title (default: directory name)
- `-v, --verbose`: Show detailed output

**Examples:**
```bash
# Basic usage
sigal export-epub ./my-photos

# Custom output
sigal export-epub ./photos -o ~/Books/album.epub

# With title and verbose
sigal export-epub ./photos -t "My Album" -v

# All options
sigal export-epub /path/to/photos \
    -o ~/ebooks/my-album.epub \
    -t "My Photo Collection" \
    -v
```

---

## Complete Example

### Simple EPUB Generation

```python
from pathlib import Path
from sigal.epub_exporter import EPUBBuilder, MediaFile

# Create builder
builder = EPUBBuilder(title="Beach Vacation")

# Add photos
builder.add_media(MediaFile(
    path=Path("sunset.jpg"),
    title="Sunset",
    description="Beautiful golden hour sunset",
    exif="Camera: iPhone 13\nISO: 100\nTime: 6:30 PM"
))

# Add video with thumbnail
builder.add_media(MediaFile(
    path=Path("waves.mp4"),
    title="Ocean Waves",
    description="Relaxing waves at the beach",
    is_video=True
))

# Generate EPUB
builder.build(Path("vacation.epub"))
```

### Advanced Example with Error Handling

```python
import logging
from pathlib import Path
from sigal.epub_exporter import EPUBBuilder, MediaFile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_photo_epub(directory: Path, output: Path) -> bool:
    """Create EPUB from photo directory with error handling"""
    
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return False
    
    builder = EPUBBuilder(title=directory.name)
    
    # Collect media files
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    video_exts = {'.mp4', '.webm', '.mov'}
    
    for file in sorted(directory.iterdir()):
        if file.is_file():
            if file.suffix.lower() in image_exts:
                builder.add_media(MediaFile(
                    path=file,
                    title=file.stem,
                    is_video=False
                ))
            elif file.suffix.lower() in video_exts:
                builder.add_media(MediaFile(
                    path=file,
                    title=file.stem,
                    is_video=True
                ))
    
    if not builder.media_list:
        logger.error("No media files found")
        return False
    
    logger.info(f"Building EPUB with {len(builder.media_list)} media files")
    
    try:
        success = builder.build(output)
        if success:
            size_mb = output.stat().st_size / (1024 * 1024)
            logger.info(f"EPUB created: {output} ({size_mb:.1f} MB)")
        return success
    except Exception as e:
        logger.error(f"EPUB creation failed: {e}")
        return False

# Usage
create_photo_epub(
    directory=Path("./my-photos"),
    output=Path("album.epub")
)
```

### Batch Processing

```python
from pathlib import Path
from sigal.epub_exporter import create_epub_from_directory

# Process multiple albums
albums = {
    Path.home() / "Pictures/Vacation": "Vacation 2024",
    Path.home() / "Pictures/Family": "Family Photos",
    Path.home() / "Pictures/Events": "Special Events",
}

output_dir = Path.home() / "Books"
output_dir.mkdir(exist_ok=True)

for album_path, title in albums.items():
    output_file = output_dir / f"{title.replace(' ', '_')}.epub"
    
    if create_epub_from_directory(album_path, output_file, title):
        print(f"✓ Created: {output_file}")
    else:
        print(f"✗ Failed: {title}")
```

---

## Data Format

### EPUB File Structure

Generated EPUB files follow the EPUB 3.0 standard:

```
album.epub (ZIP file)
├── mimetype
│   └── (application/epub+zip - no compression)
├── META-INF/
│   └── container.xml (root file reference)
└── OEBPS/
    ├── package.opf (metadata and manifest)
    ├── nav.xhtml (navigation/TOC)
    ├── style/
    │   └── style.css
    ├── xhtml/
    │   ├── page_0.xhtml
    │   ├── page_1.xhtml
    │   └── page_N.xhtml
    ├── images/
    │   ├── image_0.jpg
    │   ├── image_1.jpg
    │   └── image_N.jpg
    └── videos/ (if videos present)
        ├── video_0.mp4
        └── video_N.mp4
```

### Metadata

Each EPUB includes:
- **UUID**: Unique identifier
- **Title**: Album title
- **Creator**: "Sigal Photo Gallery"
- **Language**: "en"
- **Issued**: ISO datetime
- **Modified**: ISO datetime

---

## Error Handling

Common error scenarios and handling:

### Video Thumbnail Extraction Fails

```python
success = VideoThumbnailGenerator.extract_thumbnail(...)
if not success:
    logger.warning("Thumbnail extraction failed, will use placeholder")
    # A grey placeholder image will be created automatically
```

### Medium File Processing Failed

```python
def handle_missing_media(builder, media):
    if not media.exists():
        logger.warning(f"Media file not found: {media.path}")
        # add_media() automatically skips non-existent files
```

### EPUB Build Error

```python
if not builder.build(output_path):
    logger.error("EPUB build failed - check disk space, permissions, etc.")
    # Review log messages for specific error
```

---

## Dependencies

### Required
- Python 3.6+
- Standard library: `pathlib`, `logging`, `json`, `tempfile`, `shutil`, `datetime`, `subprocess`, `uuid`, `zipfile`

### Optional
- `Pillow` (PIL) - For image processing (PNG/GIF/WebP → JPEG conversion)
  - Install: `pip install Pillow`
  - If not available, images are copied as-is (may reduce compatibility)

### For Video Thumbnails
- `ffmpeg` installed on system PATH
  - Install on macOS: `brew install ffmpeg`
  - Install on Linux: `sudo apt-get install ffmpeg`
  - Install on Windows: Download from https://ffmpeg.org

---

## Performance

### Typical Build Times

- **Small album** (10 photos): < 1 second
- **Medium album** (50 photos): 5-10 seconds
- **Large album** (500 photos): 30-60 seconds
- **Video thumbnail** extraction: 1-3 seconds per video

Performance depends on:
- Image resolution and format
- File count and total size
- Video file sizes
- System CPU/disk speed
- Whether ffmpeg needs to process video frames

### Memory Usage

- Small albums: < 50 MB
- Medium albums: 100-200 MB
- Large albums: 500+ MB

Memory is primarily used for image buffers during conversion.

---

## Troubleshooting

### ImportError: No module named 'PIL'

Install Pillow:
```bash
pip install Pillow
```

### ffmpeg not found

Install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Permission Denied error

Ensure output directory is writable:
```bash
chmod 755 /path/to/output
```

### EPUB not opening in reader

Typically caused by:
1. Invalid XML/XHTML - check epub_exporter.py formatting methods
2. Missing namespace declarations - verify package.opf generation
3. Corrupted ZIP - ensure extraction succeeds

Use online EPUB validator: https://www.w3.org/publishing/epubcheck/

---

## References

- [EPUB 3.0 Specification](https://www.w3.org/publishing/epub32/)
- [EPUB Best Practices](https://idpf.github.io/epub-best-practices/)
- [Sigal Documentation](https://sigal.readthedocs.io/)
- [Click Framework](https://click.palletsprojects.com/)
