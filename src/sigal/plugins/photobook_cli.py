"""Photobook CLI commands for Sigal

Provides command-line interface for EPUB export functionality.
"""

import os
import pathlib
import logging
import tempfile
import click
from sigal.epub_exporter import build_album_and_export_epub, get_album_title
from sigal.settings import read_settings

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_FILE = "sigal.conf.py"


@click.command('export-epub')
@click.argument('source', type=click.Path(exists=True, file_okay=False, dir_okay=True), required=False)
@click.option('-o', '--output', type=click.Path(), default=None, 
              help='Output EPUB file path (defaults to destination/album.epub)')
@click.option('-t', '--title', default=None,
              help='EPUB title (defaults to album folder name)')
@click.option('-c', '--config', type=click.Path(exists=True, file_okay=True),
              default=_DEFAULT_CONFIG_FILE,
              help='Configuration file path (default: sigal.conf.py)')
@click.option('-v', '--verbose', is_flag=True, 
              help='Verbose output')
def export_epub_command(source: str, output: str, title: str, config: str, verbose: bool) -> None:
    """Export photo album as EPUB ebook with photobook theme.
    
    Reads sigal.conf.py, builds the album with photobook theme,
    then exports to EPUB using the "Photo Book" view mode.
    
    SOURCE is optional - if not provided, uses source from config.
    
    Examples:
        sigal export-epub
        sigal export-epub -c myconfig.py -o ~/Books/album.epub
        sigal export-epub ./photos -t "My Vacation" -v
    """
    # Set logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        # Read settings from config
        if not os.path.isfile(config):
            click.echo(f"Error: Settings file not found: {config}", err=True)
            raise SystemExit(1)
        
        settings = read_settings(config)
        
        # Override source if provided
        if source:
            settings['source'] = os.path.abspath(source)
        
        # Validate source directory
        if not settings['source'] or not os.path.isdir(settings['source']):
            click.echo(f"Error: Source directory not found: {settings['source']}", err=True)
            raise SystemExit(1)
        
        # Force photobook theme
        settings['theme'] = 'photobook'
        
        # Determine output EPUB path
        if output:
            epub_output_path = pathlib.Path(output).resolve()
        else:
            # Get album title from built index.html for default filename
            album_title = get_album_title(settings)
            # Sanitize title for use as filename (remove/replace problematic characters)
            safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in album_title).rstrip()
            if not safe_filename:
                safe_filename = pathlib.Path(settings['source']).name
            epub_output_path = pathlib.Path.cwd() / f"{safe_filename}.epub"
        
        if epub_output_path.exists():
            if not click.confirm(f"Output file exists: {epub_output_path}\nOverwrite?"):
                click.echo("Aborted.")
                raise SystemExit(0)
        
        click.echo(f"Source directory: {settings['source']}")
        click.echo(f"Build destination: {settings['destination']}")
        click.echo(f"EPUB output: {epub_output_path}")
        click.echo(f"Theme: photobook\n")
        
        with click.progressbar(length=100, label='Building and exporting') as bar:
            bar.update(20)
            
            if build_album_and_export_epub(settings, epub_output_path, title):
                bar.update(80)
                click.echo("\n✓ EPUB created successfully")
                click.echo(f"  Path: {epub_output_path}")
                click.echo(f"  Title: {title or pathlib.Path(settings['source']).name}")
                click.echo(f"  Size: {epub_output_path.stat().st_size / (1024*1024):.1f} MB")
            else:
                click.echo("\nError: Failed to create EPUB", err=True)
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
    from sigal.epub_exporter import VideoThumbnailGenerator
    
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
