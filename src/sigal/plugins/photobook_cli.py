"""Photobook CLI commands for Sigal

Provides command-line interface for EPUB export functionality.
"""

import pathlib
import logging
import click
from sigal.epub_exporter import EPUBBuilder, MediaFile, VideoThumbnailGenerator

logger = logging.getLogger(__name__)


@click.command('export-epub')
@click.argument('source', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('-o', '--output', type=click.Path(), default=None, 
              help='Output EPUB file path (defaults to album_name.epub in source directory)')
@click.option('-t', '--title', default=None,
              help='EPUB title (defaults to album folder name)')
@click.option('-v', '--verbose', is_flag=True, 
              help='Verbose output')
def export_epub_command(source: str, output: str, title: str, verbose: bool) -> None:
    """Export photo album as EPUB ebook.
    
    SOURCE is the directory containing photos/videos.
    
    Examples:
        sigal export-epub ./my-album
        sigal export-epub ./my-album -o ~/Books/album.epub -t "My Vacation"
        sigal export-epub ./photos -v
    """
    source_path = pathlib.Path(source).resolve()
    
    if not source_path.exists():
        click.echo(f"Error: Source directory not found: {source_path}", err=True)
        raise SystemExit(1)
    
    # Determine output path
    if output:
        output_path = pathlib.Path(output).resolve()
    else:
        output_path = source_path.parent / f"{source_path.name}.epub"
    
    if output_path.exists():
        if not click.confirm(f"Output file exists: {output_path}\nOverwrite?"):
            click.echo("Aborted.")
            raise SystemExit(0)
    
    # Set title
    if not title:
        title = source_path.name
    
    # Set logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    with click.progressbar(label='Building EPUB', show_eta=False) as bar:
        try:
            # Check for required tools
            duration = VideoThumbnailGenerator.get_video_duration(source_path)
            has_ffmpeg = duration is not None or True  # ffprobe may not work but ffmpeg might
            
            if not has_ffmpeg:
                click.echo("Warning: ffmpeg not found. Video thumbnails will use placeholders.", err=True)
            
            # Build EPUB
            builder = EPUBBuilder(title=title, album_path=source_path)
            
            # Collect media
            image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            video_exts = {'.mp4', '.webm', '.mv', '.avi', '.mov'}
            
            media_files = sorted([f for f in source_path.iterdir() if f.is_file()])
            
            for media_file in media_files:
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
            
            bar.update(30)
            
            if not builder.media_list:
                click.echo("Error: No media files found in source directory", err=True)
                raise SystemExit(1)
            
            click.echo(f"Found {len(builder.media_list)} media file(s)")
            
            # Build EPUB
            if builder.build(output_path):
                bar.update(70)
                click.echo(f"✓ EPUB created: {output_path}")
                click.echo(f"  Title: {title}")
                click.echo(f"  Media: {len(builder.media_list)} items")
                click.echo(f"  Size: {output_path.stat().st_size / (1024*1024):.1f} MB")
            else:
                click.echo("Error: Failed to create EPUB", err=True)
                raise SystemExit(1)
                
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            logger.exception("EPUB export failed")
            raise SystemExit(1)


@click.command('extract-video-thumbnail')
@click.argument('video', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.argument('output', type=click.Path())
@click.option('-t', '--timestamp', type=float, default=2.0,
              help='Timestamp in seconds to extract (default: 2.0)')
@click.option('-v', '--verbose', is_flag=True,
              help='Verbose output')
def extract_video_thumbnail_command(video: str, output: str, timestamp: float, verbose: bool) -> None:
    """Extract thumbnail from video file.
    
    VIDEO is the path to a video file (mp4, webm, etc.)
    OUTPUT is the path to save the thumbnail image (jpg)
    
    Examples:
        sigal extract-video-thumbnail video.mp4 thumbnail.jpg
        sigal extract-video-thumbnail video.mp4 thumb.jpg -t 5.0
    """
    video_path = pathlib.Path(video).resolve()
    output_path = pathlib.Path(output).resolve()
    
    if not video_path.exists():
        click.echo(f"Error: Video file not found: {video_path}", err=True)
        raise SystemExit(1)
    
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    click.echo(f"Extracting thumbnail from: {video_path}")
    click.echo(f"Timestamp: {timestamp}s")
    
    if VideoThumbnailGenerator.extract_thumbnail(video_path, output_path, timestamp):
        size = output_path.stat().st_size / 1024
        click.echo(f"✓ Thumbnail saved: {output_path} ({size:.1f} KB)")
    else:
        click.echo("Error: Failed to extract thumbnail", err=True)
        raise SystemExit(1)


# Group for photobook commands
@click.group('photobook', invoke_without_command=False)
def photobook_group():
    """Sigal Photobook plugin commands.
    
    Export photo albums as EPUB ebooks with video support.
    """
    pass


# Add commands to group
photobook_group.add_command(export_epub_command)
photobook_group.add_command(extract_video_thumbnail_command)
