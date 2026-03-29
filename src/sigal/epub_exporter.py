"""EPUB Exporter for Sigal Photo Gallery

Generates EPUB files from gallery albums with video support.
"""

import os
import pathlib
import logging
import json
import tempfile
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import subprocess
from urllib.parse import quote
import uuid as uuid_module

try:
    from PIL import Image
except ImportError:
    Image = None

logger = logging.getLogger(__name__)


@dataclass
class MediaFile:
    """Represents a media file (image or video)"""
    path: pathlib.Path
    title: str
    description: str = ""
    exif: str = ""
    is_video: bool = False
    filename: str = ""  # Original filename for display
    source_file: Optional[str] = None  # Path to source file for extraction
    
    def exists(self) -> bool:
        return self.path.exists()


class VideoThumbnailGenerator:
    """Generate thumbnails from video files"""
    
    @staticmethod
    def get_video_duration(video_path: pathlib.Path) -> Optional[float]:
        """Get video duration in seconds using ffprobe"""
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error', '-show_entries',
                    'format=duration', '-of',
                    'default=noprint_wrappers=1:nokey=1:noprint_wrappers=1',
                    str(video_path)
                ],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        return None
    
    @staticmethod
    def extract_thumbnail(video_path: pathlib.Path, 
                         output_path: pathlib.Path,
                         timestamp: float = 2.0) -> bool:
        """Extract thumbnail from video at given timestamp
        
        Args:
            video_path: Path to video file
            output_path: Path to save thumbnail
            timestamp: Seconds into video to extract
            
        Returns:
            True if successful
        """
        try:
            # Get video duration to ensure timestamp is valid
            duration = VideoThumbnailGenerator.get_video_duration(video_path)
            if duration is None:
                logger.warning(f"Could not determine duration of {video_path}")
                timestamp = 1.0
            elif timestamp > duration:
                # Use middle of video
                timestamp = max(1.0, duration / 2)
            
            result = subprocess.run(
                [
                    'ffmpeg', '-i', str(video_path), '-ss', str(timestamp),
                    '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease',
                    '-vframes', '1', '-y', str(output_path)
                ],
                capture_output=True, timeout=30
            )
            
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Generated thumbnail: {output_path}")
                return True
            else:
                logger.warning(f"ffmpeg failed for {video_path}: {result.stderr.decode()}")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"Failed to extract thumbnail: {e}")
            return False


class EPUBBuilder:
    """Build EPUB files from media collections"""
    
    MIMETYPE_CONTENT = "application/epub+zip"
    
    def __init__(self, title: str = "Photo Gallery", 
                 album_path: Optional[pathlib.Path] = None,
                 theme: str = "default",
                 leaflet_provider: str = "OpenStreetMap.Mapnik"):
        self.title = title
        self.album_path = album_path or pathlib.Path.cwd()
        self.theme = theme
        self.leaflet_provider = leaflet_provider
        self.uuid = str(uuid_module.uuid4())
        self.media_list: List[MediaFile] = []
        self.temp_dir = None
        self.epub_path = None
        
    def add_media(self, media: MediaFile) -> None:
        """Add media file to EPUB"""
        if media.exists():
            self.media_list.append(media)
            logger.debug(f"Added media: {media.path.name} (video={media.is_video})")
        else:
            logger.warning(f"Media file not found: {media.path}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe use in filesystems"""
        import re
        # Replace problematic characters
        filename = re.sub(r'[/:?*"<>|]', '_', filename)
        # Replace spaces with underscore
        filename = re.sub(r'\s+', '_', filename)
        # Collapse multiple underscores
        filename = re.sub(r'_+', '_', filename)
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        return filename[:200]
    
    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters"""
        if not text:
            return ''
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
    
    def _format_description(self, text: str) -> str:
        """Format description with HTML markup
        
        Preserves HTML tags from markdown rendering, only escapes plain text.
        """
        if not text:
            return ''
        
        # Don't escape - description may contain HTML from markdown conversion
        text = text.strip()
        
        # If text already contains HTML tags, it's already formatted - return as-is
        if '<p>' in text or '<div>' in text or '<h' in text or '<ul>' in text or '<ol>' in text:
            return text
        
        # Otherwise, treat as plain text and convert to HTML
        text = self._escape_xml(text)
        # Convert double newlines to paragraphs
        html = text.replace('\n\n', '</p><p>')
        html = html.replace('\n', '<br/>')
        return f'<p>{html}</p>'
    
    def _format_exif(self, exif_text: str, source_file: Optional[str] = None) -> str:
        """Format EXIF data as structured HTML matching photobook theme book-exif structure
        
        Args:
            exif_text: Newline-separated EXIF data in "Label: Value" format
            source_file: Unused (kept for compatibility)
            
        Returns:
            HTML formatted EXIF data using book-exif-item structure
        """
        if not exif_text:
            return ''
        
        lines = []
        
        # Parse EXIF lines
        exif_escaped = self._escape_xml(exif_text)
        exif_lines = [x.strip() for x in exif_escaped.split('\n') if x.strip()]
        
        for line in exif_lines:
            # Try to parse "Label: Value" format
            if ':' in line:
                parts = line.split(':', 1)
                label = parts[0].strip()
                value = parts[1].strip()
                
                # Check if this is a Location (GPS) line
                if label.lower() == 'location':
                    # Parse GPS coordinates: "N37.770000, W122.410000"
                    try:
                        coords = value.split(',')
                        if len(coords) == 2:
                            lat_str = coords[0].strip()
                            lon_str = coords[1].strip()
                            
                            # Parse latitude (N/S prefix)
                            lat_dir = lat_str[0]
                            lat_val = float(lat_str[1:])
                            if lat_dir == 'S':
                                lat_val = -lat_val
                            
                            # Parse longitude (E/W prefix)
                            lon_dir = lon_str[0]
                            lon_val = float(lon_str[1:])
                            if lon_dir == 'W':
                                lon_val = -lon_val
                            
                            # Create map link based on leaflet provider
                            if 'Mapbox' in self.leaflet_provider:
                                map_url = f"https://www.mapbox.com/maps?q={lat_val},{lon_val}&z=14"
                            elif 'Google' in self.leaflet_provider:
                                map_url = f"https://maps.google.com/?q={lat_val},{lon_val}"
                            else:
                                # Default to OpenStreetMap
                                map_url = f"https://www.openstreetmap.org/?mlat={lat_val}&mlon={lon_val}&zoom=14"
                            
                            lines.append(f'      <div class="book-exif-item"><strong>{label}:</strong> <a href="{map_url}" class="gps-link">{value}</a></div>')
                            continue
                    except (ValueError, IndexError):
                        pass  # Fall through to default formatting
                
                # Default formatting for non-GPS lines
                lines.append(f'      <div class="book-exif-item"><strong>{label}:</strong> <span>{value}</span></div>')
            else:
                lines.append(f'      <div class="book-exif-item">{line}</div>')
        
        if not lines:
            return ''
        
        return '\n'.join(lines)
    
    def _create_container_xml(self) -> str:
        """Create META-INF/container.xml"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
</container>'''
    
    def _create_package_opf(self) -> str:
        """Create OEBPS/package.opf"""
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Build manifest items
        manifest_items = '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n'
        
        for idx, media in enumerate(self.media_list):
            # All media get images (for videos, the poster)
            manifest_items += f'    <item id="img_{idx}" href="images/image_{idx}.jpg" media-type="image/jpeg"/>\n'
            manifest_items += f'    <item id="page_{idx}" href="xhtml/page_{idx}.xhtml" media-type="application/xhtml+xml"/>\n'
        
        manifest_items += '    <item id="style" href="style/style.css" media-type="text/css"/>\n'
        
        # Build spine
        spine_items = ''
        for idx in range(len(self.media_list)):
            spine_items += f'    <itemref idref="page_{idx}"/>\n'
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:opf="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uuid" xml:lang="en" dir="ltr">
  <metadata>
    <dc:identifier id="uuid">urn:uuid:{self.uuid}</dc:identifier>
    <dc:title>{self._escape_xml(self.title)}</dc:title>
    <dc:creator opf:role="aut">Sigal Photo Gallery</dc:creator>
    <dc:language>en</dc:language>
    <dcterms:issued>{now}</dcterms:issued>
    <meta property="dcterms:modified">{now}</meta>
  </metadata>
  <manifest>
{manifest_items}  </manifest>
  <spine>
{spine_items}  </spine>
</package>'''
    
    def _create_nav_xhtml(self) -> str:
        """Create OEBPS/nav.xhtml"""
        nav_items = ''
        for idx, media in enumerate(self.media_list):
            title = self._escape_xml(media.title)
            nav_items += f'    <li><a href="xhtml/page_{idx}.xhtml">{title}</a></li>\n'
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
  <head>
    <meta charset="UTF-8"/>
    <title>{self._escape_xml(self.title)}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <link rel="stylesheet" type="text/css" href="style/style.css"/>
  </head>
  <body>
    <nav epub:type="toc" id="toc">
      <h1>Table of Contents</h1>
      <ol>
{nav_items}      </ol>
    </nav>
  </body>
</html>'''
    
    def _create_page_xhtml(self, media: MediaFile, idx: int) -> str:
        """Create individual page XHTML using photobook book-view structure"""
        
        # Build book-entry structure matching photobook theme
        book_media_html = ''
        if media.is_video:
            book_media_html = f'''    <div class="book-media">
      <video controls class="book-video" poster="../images/image_{idx}.jpg">
        <source src="../sources/{media.path.name}" type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </div>'''
        else:
            book_media_html = f'''    <div class="book-media">
      <img src="../images/image_{idx}.jpg" alt="{self._escape_xml(media.title)}" class="book-image" />
    </div>'''
        
        # Description section
        description_html = ''
        if media.description:
            description_html = f'''    <div class="book-description">
      {self._format_description(media.description)}
    </div>
'''
        
        # Filename section - display as plain text (no link to avoid Calibre issues)
        filename_html = ''
        if media.source_file or media.filename:
            filename_html = f'''    <div class="book-filename">
      <strong>File:</strong> {self._escape_xml(media.filename)}
    </div>
'''
        
        # EXIF section using book-exif structure
        exif_html = ''
        if media.exif or media.source_file:
            exif_content = self._format_exif(media.exif, media.source_file)
            if exif_content:
                exif_html = f'''    <div class="book-exif">
{exif_content}
    </div>
'''
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
  <head>
    <meta charset="UTF-8"/>
    <title>{self._escape_xml(media.title)}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <link rel="stylesheet" type="text/css" href="../style/style.css"/>
  </head>
  <body>
    <div class="book-entry">
{book_media_html}
      <div class="book-caption">
        <h2>{self._escape_xml(media.title)}</h2>
{description_html}{filename_html}{exif_html}      </div>
    </div>
  </body>
</html>'''
    
    def _create_style_css(self) -> str:
        """Create OEBPS/style/style.css - load from photobook theme or use fallback
        
        For photobook theme, loads CSS from the theme directory.
        For other themes, returns minimal compatible CSS.
        """
        if self.theme == 'photobook':
            # Try to load CSS from photobook theme
            try:
                import os
                # Find theme CSS - check multiple possible locations
                theme_css_paths = [
                    pathlib.Path(__file__).parent / 'themes' / 'photobook' / 'static' / 'css' / 'style.css',
                    pathlib.Path('src/sigal/themes/photobook/static/css/style.css'),
                    pathlib.Path('themes/photobook/static/css/style.css'),
                ]
                
                for theme_css_path in theme_css_paths:
                    if theme_css_path.exists():
                        logger.info(f"Loading photobook theme CSS from: {theme_css_path}")
                        css_content = theme_css_path.read_text(encoding='utf-8')
                        
                        # Add EPUB-specific overrides for interactive elements
                        epub_overrides = '''
/* EPUB-specific overrides */
.photobook-controls,
.photobook-nav,
#outline-btn, #slides-btn, #book-btn, #epub-export-btn,
.photobook-nav-controls,
#prev-btn, #next-btn,
.page-counter {
    display: none;
}

#outline-view,
#slides-view {
    display: none !important;
}

#book-view {
    display: block !important;
}

.photobook-view.active {
    display: block !important;
}

.continuous-book {
    display: block;
}

.book-entry {
    page-break-after: always;
    page-break-inside: avoid;
    margin: 0;
    padding: 2em 1.5em;
}

/* Make source file links work in EPUB */
.book-filename a,
.source-link,
.gps-link {
    color: #0066cc;
    text-decoration: underline;
    cursor: pointer;
}
'''
                        return css_content + epub_overrides
                    
                logger.warning("Photobook theme CSS not found, using fallback")
            except Exception as e:
                logger.warning(f"Could not load theme CSS: {e}")
            
            # Fallback for photobook theme
            return '''/* Photobook Theme EPUB Styles */
* {
    margin: 0;
    padding: 0;
    border: 0;
    box-sizing: border-box;
}

html, body {
    margin: 0;
    padding: 0;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 1em;
    line-height: 1.6;
    color: #333333;
    background-color: #ffffff;
}

.page {
    display: block;
    clear: both;
    margin: 0;
    padding: 2em 1.5em;
    page-break-after: always;
    page-break-inside: avoid;
    background-color: #ffffff;
}

.page-media {
    display: block;
    clear: both;
    text-align: center;
    margin: 0 0 2.5em 0;
    padding: 0;
}

.page-media img {
    display: block;
    max-width: 100%;
    max-height: 65%;
    height: auto;
    width: auto;
    margin: 0 auto;
    padding: 0;
    border: none;
    object-fit: contain;
}

.video-container {
    position: relative;
    display: inline-block;
    text-align: center;
    width: 100%;
}

.video-poster {
    max-width: 100%;
    height: auto;
    display: block;
    border: 1px solid #ddd;
}

.video-link-overlay {
    text-align: center;
    margin-top: 1em;
}

.video-link-btn {
    display: inline-block;
    padding: 0.75em 1.5em;
    background-color: #222222;
    color: #ffffff;
    text-decoration: none;
    border: 1px solid #222222;
    font-weight: 500;
    font-size: 0.95em;
    border-radius: 2px;
    transition: all 0.3s ease;
}

.video-link-btn:hover {
    background-color: #444444;
    border-color: #444444;
}

.video-link-btn:visited {
    color: #ffffff;
}

.video-note {
    text-align: center;
    margin-top: 1em;
    padding: 0.75em 1.5em;
    color: #666666;
    font-size: 0.9em;
    font-style: italic;
}

.page-caption {
    display: block;
    clear: both;
    margin: 2.5em 0 0 0;
    padding: 1.5em 0;
    border-top: 2px solid #e0e0e0;
}

.page-title {
    display: block;
    font-size: 1.5em;
    font-weight: 700;
    margin: 0 0 1em 0;
    padding: 0;
    color: #222222;
}

.page-description {
    display: block;
    margin: 1em 0;
    padding: 1em;
    font-size: 0.95em;
    line-height: 1.6;
    color: #333333;
    background-color: #f9f9f9;
    border-left: 3px solid #cccccc;
}

.page-description p {
    margin: 0.5em 0;
    padding: 0;
}

.page-exif {
    display: block;
    margin: 1.5em 0;
    padding: 0;
    font-size: 0.85em;
    clear: both;
}

.exif-list {
    display: block;
    padding: 1em;
    background-color: #f5f5f5;
    border-left: 3px solid #e0e0e0;
}

.exif-item {
    display: block;
    margin: 0.5em 0;
    padding: 0.25em 0;
    word-break: break-word;
    line-height: 1.4;
}

.exif-item strong {
    font-weight: 700;
    color: #222222;
}

.exif-item span {
    color: #666666;
}

.gps-link {
    color: #0066cc;
    text-decoration: none;
    font-weight: 500;
}

.gps-link:hover {
    text-decoration: underline;
}
'''
        else:
            # Default/legacy EPUB styling
            return '''/* Photobook EPUB Styles - Compatible with all readers */
* {
    margin: 0;
    padding: 0;
    border: 0;
}

html, body {
    margin: 0;
    padding: 0;
}

body {
    font-family: Georgia, serif;
    font-size: 1em;
    line-height: 1.5;
    color: #000;
    background-color: #fff;
}

.page {
    display: block;
    clear: both;
    margin: 0;
    padding: 1em;
    page-break-after: always;
    page-break-inside: avoid;
}

.page-media {
    display: block;
    clear: both;
    text-align: center;
    margin: 0 0 2em 0;
    padding: 0;
}

.page-media img {
    display: block;
    max-width: 100%;
    max-height: 70%;
    height: auto;
    width: auto;
    margin: 0 auto;
    padding: 0;
    border: none;
}

.video-container {
    position: relative;
    display: inline-block;
    text-align: center;
    width: 100%;
}

.video-poster {
    max-width: 100%;
    height: auto;
    display: block;
}

.video-link-overlay {
    text-align: center;
    margin-top: 0.75em;
}

.video-link-btn {
    display: inline-block;
    padding: 0.5em 1em;
    background-color: #333;
    color: #fff;
    text-decoration: none;
    border: 1px solid #000;
    font-weight: bold;
    font-size: 0.95em;
}

.video-link-btn:visited {
    color: #fff;
}

.video-note {
    text-align: center;
    margin-top: 0.75em;
    padding: 0.5em 1em;
    color: #666;
    font-size: 0.85em;
    font-style: italic;
}

.page-caption {
    display: block;
    clear: both;
    margin: 2em 0 0 0;
    padding: 1em 0;
    border-top: 1px solid #ddd;
}

.page-title {
    display: block;
    font-size: 1.3em;
    font-weight: bold;
    margin: 0 0 1em 0;
    padding: 0;
    color: #000;
}

.page-description {
    display: block;
    margin: 1em 0;
    padding: 0.5em;
    font-size: 0.95em;
    line-height: 1.5;
    color: #333;
    border-left: 0.2em solid #ccc;
}

.page-description p {
    margin: 0.5em 0;
    padding: 0;
}

.page-exif {
    display: block;
    margin: 1em 0;
    padding: 0;
    font-size: 0.9em;
    clear: both;
}

.exif-list {
    display: block;
    padding: 0.5em;
    background-color: #f9f9f9;
    border-left: 0.2em solid #ddd;
}

.exif-item {
    display: block;
    margin: 0.5em 0;
    padding: 0.25em 0;
    word-break: break-word;
}

.exif-item strong {
    font-weight: bold;
    color: #333;
}

.exif-item span {
    color: #666;
}

.gps-link {
    color: #0066cc;
    text-decoration: none;
    font-weight: 500;
}

.gps-link:hover {
    text-decoration: underline;
}
'''
    
    def _prepare_media(self, output_dir: pathlib.Path) -> bool:
        """Process media files and generate thumbnails/images
        
        Returns:
            True if successful
        """
        images_dir = output_dir / 'OEBPS' / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            for idx, media in enumerate(self.media_list):
                image_path = images_dir / f'image_{idx}.jpg'
                
                if media.is_video:
                    # Generate thumbnail from video
                    logger.info(f"Generating thumbnail for video: {media.path}")
                    if VideoThumbnailGenerator.extract_thumbnail(media.path, image_path):
                        logger.info(f"Thumbnail created: {image_path}")
                    else:
                        logger.warning(f"Failed to generate thumbnail for {media.path}")
                        # Create a placeholder if thumbnail generation fails
                        self._create_placeholder_image(image_path)
                else:
                    # For images, convert to JPEG
                    if Image:
                        try:
                            img = Image.open(media.path)
                            if img.mode in ('RGBA', 'P'):
                                # Convert to RGB
                                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                                rgb_img.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                                rgb_img.save(image_path, quality=90)
                            else:
                                img.save(image_path, quality=90)
                            logger.info(f"Converted image: {image_path}")
                        except Exception as e:
                            logger.error(f"Failed to convert image {media.path}: {e}")
                            return False
                    else:
                        # Fallback: copy image as-is
                        shutil.copy2(media.path, image_path)
                        logger.info(f"Copied image: {image_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error preparing media: {e}")
            return False
    
    def _create_placeholder_image(self, path: pathlib.Path) -> None:
        """Create a placeholder image for missing thumbnails"""
        if not Image:
            return
        
        try:
            # Create a simple placeholder image
            img = Image.new('RGB', (1280, 720), color=(128, 128, 128))
            img.save(path, quality=90)
        except Exception as e:
            logger.warning(f"Could not create placeholder image: {e}")
    
    def build(self, output_path: pathlib.Path) -> bool:
        """Build EPUB file
        
        Args:
            output_path: Path where EPUB file will be saved
            
        Returns:
            True if successful
        """
        import zipfile
        
        if not self.media_list:
            logger.error("No media files to export")
            return False
        
        # Use temporary directory
        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix='epub_'))
        output_dir = self.temp_dir / 'epub'
        output_dir.mkdir(parents=True)
        
        try:
            # Create directory structure
            (output_dir / 'META-INF').mkdir()
            (output_dir / 'OEBPS' / 'xhtml').mkdir(parents=True)
            (output_dir / 'OEBPS' / 'style').mkdir(parents=True)
            
            # Create core files
            (output_dir / 'mimetype').write_text(self.MIMETYPE_CONTENT, encoding='utf-8')
            (output_dir / 'META-INF' / 'container.xml').write_text(self._create_container_xml(), encoding='utf-8')
            (output_dir / 'OEBPS' / 'package.opf').write_text(self._create_package_opf(), encoding='utf-8')
            (output_dir / 'OEBPS' / 'nav.xhtml').write_text(self._create_nav_xhtml(), encoding='utf-8')
            (output_dir / 'OEBPS' / 'style' / 'style.css').write_text(self._create_style_css(), encoding='utf-8')
            
            # Create pages
            for idx, media in enumerate(self.media_list):
                page_path = output_dir / 'OEBPS' / 'xhtml' / f'page_{idx}.xhtml'
                page_path.write_text(self._create_page_xhtml(media, idx), encoding='utf-8')
            
            # Process media
            if not self._prepare_media(output_dir):
                logger.error("Failed to prepare media files")
                return False
            
            # Create ZIP (EPUB) file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
                # Add mimetype without compression (must be first)
                mimetype_path = output_dir / 'mimetype'
                epub.write(mimetype_path, arcname='mimetype', compress_type=zipfile.ZIP_STORED)
                
                # Add all other files
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file == 'mimetype':
                            continue
                        file_path = pathlib.Path(root) / file
                        arcname = str(file_path.relative_to(output_dir))
                        epub.write(file_path, arcname=arcname)
            
            logger.info(f"EPUB created: {output_path}")
            self.epub_path = output_path
            return True
            
        except Exception as e:
            logger.error(f"Error building EPUB: {e}")
            return False
        finally:
            # Clean up temporary directory
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temp directory: {self.temp_dir}")


def create_epub_from_directory(source_dir: pathlib.Path, 
                               output_path: pathlib.Path,
                               title: Optional[str] = None) -> bool:
    """Create EPUB from a directory of images and videos
    
    Args:
        source_dir: Directory containing media files
        output_path: Path for output EPUB file  
        title: Optional title for EPUB (defaults to directory name)
        
    Returns:
        True if successful
    """
    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return False
    
    if not title:
        title = source_dir.name
    
    builder = EPUBBuilder(title=title, album_path=source_dir)
    
    # Supported media extensions
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    video_exts = {'.mp4', '.webm', '.mv', '.avi', '.mov'}
    
    # Collect media files
    media_files = sorted(source_dir.glob('*'))
    for media_file in media_files:
        if media_file.is_file():
            suffix = media_file.suffix.lower()
            
            if suffix in image_exts:
                builder.add_media(MediaFile(
                    path=media_file,
                    title=media_file.stem,
                    is_video=False
                ))
            elif suffix in video_exts:
                builder.add_media(MediaFile(
                    path=media_file,
                    title=media_file.stem,
                    is_video=True
                ))
    
    if builder.media_list:
        return builder.build(output_path)
    else:
        logger.error("No media files found in directory")
        return False


def build_photobook_epub(album, title: str, output_path: pathlib.Path, 
                         leaflet_provider: str = "OpenStreetMap.Mapnik") -> bool:
    """Build EPUB from a Sigal album using photobook theme structure
    
    Args:
        album: Album object from Gallery
        title: Title for the EPUB
        output_path: Path where EPUB file will be saved
        leaflet_provider: Map provider for GPS links (e.g., 'OpenStreetMap.Mapnik')
        
    Returns:
        True if successful
    """
    import zipfile
    
    if not album.medias:
        logger.error("Album has no media")
        return False
    
    builder = EPUBBuilder(title=title, theme='photobook', leaflet_provider=leaflet_provider)
    
    # Extract media from album with all metadata
    for media in album.medias:
        try:
            # Get media file path (src_path already includes filename)
            media_path = pathlib.Path(media.src_path)
            
            # Extract description and EXIF
            description = getattr(media, 'description', '')
            exif_text = ''
            
            # Collect EXIF data if available
            if hasattr(media, 'exif'):
                exif_dict = media.exif or {}
                exif_parts = []
                if exif_dict.get('datetime'):
                    exif_parts.append(f"Date: {exif_dict['datetime']}")
                if exif_dict.get('Make') or exif_dict.get('Model'):
                    exif_parts.append(f"Camera: {exif_dict.get('Make', '')} {exif_dict.get('Model', '')}".strip())
                if exif_dict.get('iso'):
                    exif_parts.append(f"ISO: {exif_dict['iso']}")
                if exif_dict.get('exposure'):
                    exif_parts.append(f"Exposure: {exif_dict['exposure']}")
                if exif_dict.get('fstop'):
                    exif_parts.append(f"F-stop: {exif_dict['fstop']}")
                if exif_dict.get('focal'):
                    exif_parts.append(f"Focal: {exif_dict['focal']}")
                # Add GPS location if available
                if exif_dict.get('gps'):
                    gps = exif_dict['gps']
                    lat_str = f"N{gps['lat']:.6f}" if gps.get('lat', 0) >= 0 else f"S{-gps['lat']:.6f}"
                    lon_str = f"E{gps['lon']:.6f}" if gps.get('lon', 0) >= 0 else f"W{-gps['lon']:.6f}"
                    exif_parts.append(f"Location: {lat_str}, {lon_str}")
                exif_text = '\n'.join(exif_parts)
            
            # Create media file entry (keeps videos for page creation)
            mf = MediaFile(
                path=media_path,
                title=getattr(media, 'title', media.src_filename),
                description=description,
                exif=exif_text,
                is_video=(media.type == 'video'),
                filename=media.src_filename
                # source_file will be set during _prepare_media()
            )
            
            if mf.path.exists():
                builder.add_media(mf)
            else:
                logger.warning(f"Media file not found: {mf.path}")
                
        except Exception as e:
            logger.warning(f"Error processing media {media}: {e}")
            continue
    
    if not builder.media_list:
        logger.error("No valid media files in album")
        return False
    
    # Build EPUB
    return builder.build(output_path)


def build_album_and_export_epub(settings: Dict,
                                output_path: pathlib.Path,
                                title: Optional[str] = None) -> bool:
    """Build album with photobook theme and export to EPUB
    
    Uses the settings dict (from sigal.conf.py) to:
    1. Build the album with Gallery and photobook theme to destination folder
    2. Extract the photobook view and build EPUB
    
    Args:
        settings: Settings dictionary from read_settings()
        output_path: Output EPUB path
        title: Optional EPUB title override
        
    Returns:
        True if successful
    """
    from .gallery import Gallery
    from .utils import init_plugins
    
    source_path = pathlib.Path(settings['source'])
    
    if not source_path.exists():
        logger.error(f"Source directory not found: {source_path}")
        return False
    
    # Force photobook theme
    settings['theme'] = 'photobook'
    
    try:
        # Initialize plugins and build gallery
        logger.info(f"Building album from: {source_path}")
        init_plugins(settings)
        gallery = Gallery(settings, show_progress=False)
        
        logger.info(f"Found {len(gallery.albums)} album(s)")
        
        # Build the gallery (generates HTML files with photobook theme to destination)
        gallery.build(force=True)
        
        # Get first album
        if not gallery.albums:
            logger.error("No albums found after building")
            return False
        
        album = next(iter(gallery.albums.values()))
        
        # Determine title
        epub_title = title or album.title or source_path.name
        
        logger.info(f"Built album: {album.title} with {len(album.medias)} media")
        
        # Get leaflet provider setting (for GPS map links)
        leaflet_provider = settings.get('leaflet_provider', 'OpenStreetMap.Mapnik')
        
        # Now export the photobook album to EPUB
        return build_photobook_epub(album, epub_title, output_path, leaflet_provider)
        
    except Exception as e:
        logger.error(f"Error building album and exporting to EPUB: {e}")
        return False


def export_photobook_album_to_epub(source_path: pathlib.Path,
                                   output_path: pathlib.Path,
                                   title: Optional[str] = None,
                                   settings: Optional[Dict] = None) -> bool:
    """DEPRECATED: Use build_album_and_export_epub instead
    
    Build EPUB from a photo album by first building it with photobook theme
    
    This function:
    1. Builds the album using Gallery with photobook theme
    2. Extracts the built photobook HTML/media
    3. Generates EPUB from the photobook view
    
    Args:
        source_path: Source photo directory
        output_path: Output EPUB path
        title: Optional EPUB title
        settings: Optional custom settings dict
        
    Returns:
        True if successful
    """
    from .gallery import Gallery
    from .settings import read_settings
    from .utils import init_plugins
    
    if not source_path.exists():
        logger.error(f"Source directory not found: {source_path}")
        return False
    
    # Create settings with photobook theme
    if settings is None:
        settings = read_settings(None)
    
    settings['source'] = str(source_path)
    settings['theme'] = 'photobook'
    
    # Use temp directory for build output
    temp_build_dir = pathlib.Path(tempfile.mkdtemp(prefix='sigal_epub_'))
    settings['destination'] = str(temp_build_dir)
    
    try:
        # Initialize plugins and build gallery
        init_plugins(settings)
        gallery = Gallery(settings, show_progress=False)
        
        logger.info(f"Building album with {len(gallery.albums)} album(s)")
        
        # Build the gallery (generates HTML files with photobook theme)
        gallery.build(force=True)
        
        # Get first album
        if not gallery.albums:
            logger.error("No albums found after building")
            return False
        
        album = next(iter(gallery.albums.values()))
        
        # Determine title
        epub_title = title or album.title or source_path.name
        
        logger.info(f"Built album: {album.title} with {len(album.medias)} media")
        
        # Now export the photobook album to EPUB
        return build_photobook_epub(album, epub_title, output_path)
        
    except Exception as e:
        logger.error(f"Error exporting album to EPUB: {e}")
        return False
    finally:
        # Clean up temp directory
        if temp_build_dir.exists():
            try:
                shutil.rmtree(temp_build_dir)
                logger.debug(f"Cleaned up temp directory: {temp_build_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
