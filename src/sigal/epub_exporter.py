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
                 theme: str = "default"):
        self.title = title
        self.album_path = album_path or pathlib.Path.cwd()
        self.theme = theme
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
        """Format description with HTML markup"""
        if not text:
            return ''
        text = self._escape_xml(text)
        # Convert double newlines to paragraphs
        html = text.replace('\n\n', '</p><p>')
        html = html.replace('\n', '<br/>')
        return f'<p>{html}</p>'
    
    def _format_exif(self, exif_text: str) -> str:
        """Format EXIF data as structured HTML"""
        if not exif_text:
            return ''
        
        exif_text = self._escape_xml(exif_text)
        lines = [x.strip() for x in exif_text.split('\n') if x.strip()]
        
        html = '<div class="exif-list">'
        for line in lines:
            # Try to parse "Label: Value" format
            if ':' in line:
                parts = line.split(':', 1)
                html += f'<div class="exif-item"><strong>{parts[0].strip()}:</strong> {parts[1].strip()}</div>'
            else:
                html += f'<div class="exif-item">{line}</div>'
        html += '</div>'
        return html
    
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
        """Create individual page XHTML"""
        # Media content
        if media.is_video:
            media_html = f'''    <div class="page-media" role="figure">
      <div class="video-container">
        <img src="../images/image_{idx}.jpg" alt="{self._escape_xml(media.title)}" class="video-poster"/>
        <div class="video-link-overlay">
          <a href="../videos/video_{idx}.mp4" class="video-link-btn" epub:type="link">Download Video</a>
        </div>
      </div>
    </div>'''
        else:
            media_html = f'''    <div class="page-media" role="figure">
      <img src="../images/image_{idx}.jpg" alt="{self._escape_xml(media.title)}"/>
    </div>'''
        
        # Description
        description_html = ''
        if media.description:
            description_html = f'    <div class="page-description">{self._format_description(media.description)}</div>'
        
        # EXIF
        exif_html = ''
        if media.exif:
            exif_html = f'    <div class="page-exif">{self._format_exif(media.exif)}</div>'
        
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
    <article class="page" epub:type="bodymatter chapter">
{media_html}
      <section class="page-caption">
        <h1 class="page-title">{self._escape_xml(media.title)}</h1>
{description_html}
{exif_html}
      </section>
    </article>
  </body>
</html>'''
    
    def _create_style_css(self) -> str:
        """Create OEBPS/style/style.css with theme-specific styling"""
        if self.theme == 'photobook':
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
'''
    
    def _prepare_media(self, output_dir: pathlib.Path) -> bool:
        """Process media files and generate thumbnails
        
        Returns:
            True if successful
        """
        images_dir = output_dir / 'OEBPS' / 'images'
        videos_dir = output_dir / 'OEBPS' / 'videos'
        images_dir.mkdir(parents=True, exist_ok=True)
        videos_dir.mkdir(parents=True, exist_ok=True)
        
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
                    
                    # Copy video file to videos directory
                    try:
                        video_dest = videos_dir / f'video_{idx}{media.path.suffix}'
                        if media.path.exists():
                            shutil.copy2(media.path, video_dest)
                            logger.info(f"Copied video: {video_dest}")
                    except Exception as e:
                        logger.error(f"Failed to copy video: {e}")
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
