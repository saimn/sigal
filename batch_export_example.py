#!/usr/bin/env python3
"""
Example: Batch EPUB Export from Multiple Photo Albums

This script demonstrates how to process multiple photo directories
and generate EPUB files for each.
"""

import sys
import pathlib
from datetime import datetime

# Add sigal to path if needed
sys.path.insert(0, str(pathlib.Path(__file__).parent / 'src'))

from sigal.epub_exporter import create_epub_from_directory


def batch_export_albums(config: dict) -> None:
    """Export multiple photo albums as EPUB files.
    
    Args:
        config: Dictionary mapping source directories to titles
        Example: {
            "/path/to/vacation": "Summer Vacation 2024",
            "/path/to/family": "Family Photos",
            "/path/to/events": "Special Events",
        }
    """
    print("="*60)
    print("BATCH EPUB EXPORT")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    for source_path_str, title in config.items():
        source_path = pathlib.Path(source_path_str).expanduser()
        
        # Validate source
        if not source_path.exists():
            print(f"⊘ SKIPPED: {source_path} (not found)")
            results['skipped'].append(source_path_str)
            continue
        
        if not source_path.is_dir():
            print(f"⊘ SKIPPED: {source_path} (not a directory)")
            results['skipped'].append(source_path_str)
            continue
        
        # Determine output path
        output_path = pathlib.Path.home() / 'Books' / f"{title.replace(' ', '_')}.epub"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check for existing file
        if output_path.exists():
            print(f"⊘ SKIPPED: {output_path} (already exists)")
            results['skipped'].append(source_path_str)
            continue
        
        # Generate EPUB
        print(f"⟳ Processing: {title}")
        print(f"  Source: {source_path}")
        print(f"  Output: {output_path}")
        
        try:
            if create_epub_from_directory(source_path, output_path, title=title):
                size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"✓ SUCCESS: {title} ({size_mb:.1f} MB)")
                results['success'].append(title)
            else:
                print(f"✗ FAILED: {title} (generation error)")
                results['failed'].append(title)
        except Exception as e:
            print(f"✗ FAILED: {title} ({e})")
            results['failed'].append(title)
        
        print()
    
    # Print summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✓ Successful: {len(results['success'])}")
    for item in results['success']:
        print(f"  • {item}")
    print()
    
    if results['failed']:
        print(f"✗ Failed: {len(results['failed'])}")
        for item in results['failed']:
            print(f"  • {item}")
        print()
    
    if results['skipped']:
        print(f"⊘ Skipped: {len(results['skipped'])}")
        for item in results['skipped']:
            print(f"  • {item}")
        print()
    
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)


# ============================================================================
# EXAMPLE 1: Basic Photo Album Batch Processing
# ============================================================================

def example_basic_batch():
    """Example: Process a collection of photo albums"""
    albums = {
        # Source directory → Album title
        "~/Pictures/Vacation_2024": "Summer Vacation 2024",
        "~/Pictures/Family_Reunion": "Family Reunion 2024",
        "~/Pictures/Hiking_Trip": "Hiking Adventures",
    }
    batch_export_albums(albums)


# ============================================================================
# EXAMPLE 2: Archive by Year and Month
# ============================================================================

def example_archive_by_date():
    """Example: Organize EPUBs by date"""
    albums = {
        "~/Photos/2024/January": "January 2024",
        "~/Photos/2024/February": "February 2024",
        "~/Photos/2024/March": "March 2024",
    }
    batch_export_albums(albums)


# ============================================================================
# EXAMPLE 3: Family Photo Collection
# ============================================================================

def example_family_photos():
    """Example: Organize EPUBs by family member/category"""
    albums = {
        "~/FamilyPhotos/Sarah": "Sarah's photo collection",
        "~/FamilyPhotos/Mike": "Mike's photo collection",
        "~/FamilyPhotos/BirthdayParties": "Birthday Parties",
        "~/FamilyPhotos/Holidays": "Holiday Memories",
    }
    batch_export_albums(albums)


# ============================================================================
# EXAMPLE 4: Event Photography
# ============================================================================

def example_events():
    """Example: Process event photography"""
    albums = {
        "~/Events/Wedding_2024": "Wedding - June 2024",
        "~/Events/Corporate_Conference": "Tech Conference 2024",
        "~/Events/Festival": "Summer Festival 2024",
        "~/Events/Sports_Day": "School Sports Day",
    }
    batch_export_albums(albums)


# ============================================================================
# ADVANCED EXAMPLE: Dynamic Discovery
# ============================================================================

def example_dynamic_discovery():
    """Example: Automatically discover and process all subdirectories"""
    base_path = pathlib.Path.home() / "Pictures"
    
    # Find all directories with photos
    albums = {}
    for album_dir in sorted(base_path.iterdir()):
        if album_dir.is_dir():
            # Check if directory contains any photo files
            photo_count = len(list(album_dir.glob('*.jpg'))) + \
                         len(list(album_dir.glob('*.png'))) + \
                         len(list(album_dir.glob('*.jpeg')))
            
            if photo_count > 0:
                title = album_dir.name.replace('_', ' ').title()
                albums[str(album_dir)] = f"{title} ({photo_count} photos)"
    
    if albums:
        print(f"Discovered {len(albums)} albums")
        batch_export_albums(albums)
    else:
        print("No photo albums found")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Batch export photo albums to EPUB format"
    )
    parser.add_argument(
        "--example",
        choices=['basic', 'date', 'family', 'events', 'dynamic'],
        default='basic',
        help="Which example to run"
    )
    
    args = parser.parse_args()
    
    examples = {
        'basic': example_basic_batch,
        'date': example_archive_by_date,
        'family': example_family_photos,
        'events': example_events,
        'dynamic': example_dynamic_discovery,
    }
    
    print(f"\nRunning example: {args.example}\n")
    examples[args.example]()
    
    # Tip
    print()
    print("TIPS:")
    print("1. Edit the script to customize album paths")
    print("2. Run with different --example options to see other patterns")
    print("3. Use 'ls -la ~/Books/*.epub' to verify generated files")
    print()
