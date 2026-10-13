  ### Fix Summary

  The route map display now uses the map provider configured in settings.py:65 ("googlemaps" or "openstreetmap").
  ──────
  ### Changes Made

  1. Route Map Tile Layer Integration (map.html:400-480)
      • Replaced the hardcoded L.tileLayer.provider('{{ settings.leaflet_provider }}') with createTileLayers & setRouteMapProvider.
      • When photobook_map_provider is set to "googlemaps" (default):
          • Renders Google Maps tile layers (https://{s}.google.com/vt/lyrs=m...).
          • Adds a layer control allowing users to switch between Google Streets, Satellite, Hybrid, and Terrain layers.
      • When photobook_map_provider is set to "openstreetmap":
          • Uses OpenStreetMap tiles (settings.leaflet_provider).
      • Exposed window.setRouteMapProvider(provider) globally to allow runtime switching.
      • In the location album modal, the external map link dynamically directs to Google Maps or OpenStreetMap based on the active provider.
  2. JavaScript Map Provider Synchronization (photobook.js:14-824)
      • Defaulted config.mapProvider to 'googlemaps' to align with settings.py and sigal.conf.py.
      • Updated Photobook.setMapProvider(provider) to invoke window.setRouteMapProvider(provider) so calling Photobook.setMapProvider(...) updates the route map tiles live at
      runtime.
  3. Documentation & Tests
      • Updated README.md:57-77 to reflect that photobook_map_provider controls both the route map display tiles and external GPS links.
      • Added test_gallery.py:375-432 in tests/test_gallery.py verifying both "googlemaps" and "openstreetmap" outputs.
      • Verified that all 120 tests pass in pytest.

---
  I have updated the video conversion configuration to preserve the original video's highest resolution instead of downscaling it:

  ### Changes Made

  1. Default video_size set to None (settings.py:104)
      • Changed the default video_size from (480, 360) to None.
      • When converting video files (e.g. .mov, .avi, .mkv, .mp4) to browser-playable HTML5 formats (.mp4 / .webm), no downscaling filter is applied, keeping the video at its
      highest original resolution (1080p, 4K, etc.).
      • Explicit custom resolution resizing remains available if a user manually specifies video_size = (width, height) in their configuration.
  2. Template & Documentation Updates
      • Updated sigal.conf.py:214-216 to document that video_size = None is the default and preserves original resolution.
      • Clarified behavior in getting_started.rst:22-25.
  3. Automated Tests (test_video.py:125-159 & test_settings.py:14)
      • Added test_video.py:125-128 to ensure video_size defaults to None.
      • Added test_video.py:131-159 to test converting high-resolution videos to both .mp4 and .webm without reducing dimensions.
      • All 119 tests pass cleanly in pytest.

---
  ### Summary of Motion Photo / Motion Picture Support

  I have implemented full support for detecting motion photos, extracting the embedded video during gallery generation, and providing a Google Photos-style motion button across
  album views.
  ──────
  ### Key Features Implemented

  1. Motion Photo Detection & Video Extraction (motion_photo.py)
      • Google Camera Motion Photos: Supports both legacy (GCamera:MicroVideoOffset) and modern Container Directory (Container:Directory with Item:Length and
      Item:Semantic="MotionPhoto") XMP metadata schemas.
      • Samsung Motion Photos: Detects MotionPhoto_Data markers embedded before the MP4 stream.
      • Generic / Appended MP4s: Identifies MP4 ftyp box signatures appended following JPEG EOI (0xFFD9).
      • Paired / Live Photo Files: Automatically links paired <basename>.mp4 or <basename>.mov video files located alongside the photo.
      • Markdown Metadata: Supports motion_video: <filename> overrides in <basename>.md.
      • Zero Re-encoding Extraction: Streams the MP4 portion directly to <dst_dir>/<basename>.motion.mp4 without re-encoding overhead.
  2. Core Integration & Settings
      • Added motion_photos: True (default) to settings.py:76.
      • Added gallery.py:487-506, gallery.py:518-525, and gallery.py:532-545.
      • Incremental build aware: Reprocesses image assets if the extracted motion video is missing from the destination.
      • Integrated into map marker items in Album.map_markers.
  3. Google Photos-Style UI & Interaction
      • Visual Design (style.css:1066-1155):
          • Google Photos-style floating pill badge featuring the concentric motion ring / play icon and "MOTION" text.
          • Active toggle styling with play/pause icon transitions and active highlight border.
      • Slides & Book Views (album.html:52-71):
          • Motion button overlaid on photo items. Clicking toggles seamless inline looped video playback on top of the still photo.
      • Outline View:
          • Motion photo badge displayed on thumbnail items.
      • Media Viewer Modal (album.html:265-279 & photobook.js:547-596):
          • Motion button in header bar.
          • Pressing m toggles motion video playback in the modal.
          • Video automatically pauses and resets when navigating or closing.
      • Map & Other Themes:
          • Added motion button & video player to location lightbox in map.html:187-198.
          • Added data-motion-video attributes to album_items.html:16-18 and album.html:18-20 templates.

  ──────
  ### Verification

  • Ran the complete test suite with pytest:
      • 116 passed, 3 skipped (all 10 new motion photo tests passed in test_motion_photo.py).

---
Implemented an album-level travel map using GPS metadata, grouped markers, and a route line.

## What changed

- gallery.py
  - Added `Media.gps` fallback and video GPS parsing.
  - Added `Album.map_markers`/`Album.route` to group media by location and order them by timestamp.
  - Albums now compute a route polyline and grouped marker payloads for templates.

- map.html
  - Updated map rendering to use grouped markers with thumbnail popups.
  - Added route polyline rendering on the map.

- Theme templates now include maps on:
  - album_list.html
  - album.html
  - album_list.html
  - album_list.html

## Notes

- This uses existing Leaflet assets in the `default` theme.
- Album index pages now use `album.map_markers` rather than only album media GPS.
- Clicking marker popups links to the album view for media taken at that location.

If you want, I can also add a small unit test covering `Album.map_markers` and `Album.route`.

---
✅ Fixed the multiprocessing error.

### What changed
- Removed `Media.album` assignment from gallery.py
- This avoids sending a non-picklable album object into multiprocessing worker tasks

### Result
- `sigal build` should now work again with the `photobook` theme and multiprocessing enabled

---
Inspecting the photobook theme templates to confirm where the trip map should be inserted.

✅ Updated the photobook theme test coverage.

## What changed
- Added `test_photobook_theme_renders_trip_map_feature` in test_gallery.py
- Confirms the photobook album and album list pages render map.html
- Verifies Leaflet script reference and `mapid` map container are present

## Verification
- Ran `pytest -q test_gallery.py -k 'photobook_theme_renders_trip_map_feature or map_template_uses_items_key_across_themes or build_with_multiprocessing or album_map_markers_and_route'`
- Result: `4 passed`

---
  I have added the requested map, Polarsteps/FindPenguins-style route itinerary, creation date location grouping, and location album viewer modal to Sigal.

  ### Summary of Changes

  1. Albums Index & Individual Album Index Page Map (settings.py, gallery.py):
      • Defaulted show_map to True so maps render automatically on both the root albums index page (index.html) and each album's index page whenever location data is available.
  2. Creation Date & GPS Location Grouping (src/sigal/gallery.py):
      • Enhanced Image.gps to support EXIF GPS coordinates and markdown location metadata.
      • Added Album.gps_medias and updated Album.map_markers so media lacking EXIF or metadata GPS/timestamp fall back to their file creation date (_get_file_date()) and are
      grouped at the location of media taken on the same date or nearest timestamp.
  3. Polarsteps & FindPenguins Style Route Itinerary & Map Markers (src/sigal/themes/default/templates/map.html):
      • Interactive Route Itinerary Bar: Displays a top step bar listing journey stops (#1 Stop, #2 Stop, ...) chronologically with photo/video counts. Clicking a step chip
      smoothly pans the map and highlights the location.
      • Custom Map Markers: Rendered as styled Polaroid-like thumbnail pins on Leaflet with step number badges (#1, #2) and media count badges.
      • Route Line: A connected polyline path (#2563eb) connects stops in chronological timestamp order.
  4. Location Album View Modal (map.html):
      • Clicking any thumbnail marker on the map opens an interactive Location Album Modal:
          • Header: Shows stop number, location caption, date, and total media count.
          • Media Grid: Displays thumbnails of all photos and videos taken at that location (with video badges).
          • Lightbox Slideshow: Clicking any item in the modal opens a full-screen viewer for photos and videos with Next/Prev and keyboard arrow navigation.

  5. Test Coverage (tests/test_gallery.py):
      • Added unit test test_polarsteps_map_route_and_creation_date_grouping verifying location grouping by creation date, itinerary route ordering, and template rendering.
      All 109 tests pass.

---
  I have added the GPX and KML route export functionality for sharing trip itineraries.

  ### Summary of Export Features

  1. Static GPX & KML Route File Generation (src/sigal/gallery.py, src/sigal/writer.py):
      • Added Album.gpx and Album.kml properties that generate standard GPX 1.1 (<gpx>, <wpt>, <trk>, <trkpt>) and KML 2.2 (<kml>, <Placemark>, <Point>, <LineString>) route
      files.
      • Updated AbstractWriter.write() in writer.py to automatically write route.gpx and route.kml into the output directory whenever map routes exist.
  2. One-Click Map UI Export Buttons (src/sigal/themes/default/templates/map.html):
      • Added � GPX and � KML export action buttons in the map itinerary bar.
    • Clicking these buttons in the browser dynamically generates and triggers an instant download of the route itinerary in .gpx or .kml format.
  3. Test Suite Verification (tests/test_gallery.py):
      • Added automated tests verifying GPX/KML XML output and file writing during gallery build. All 106 tests pass.

---
  I have updated the layout of the route export buttons.

  ### Summary of Changes

  • Header Alignment (src/sigal/themes/default/templates/map.html):
      • Moved the � GPX an d � KML export buttons directly inside the � JOURNEY ROUTE header badge container (.itinerary-badge-title).
      • Added CSS rules (margin-left: 8px; display: inline-flex; flex-shrink: 0;) so the export buttons sit neatly on the right side of the header before the step chips.

---
  I have updated both the GPX and KML exporters to be fully compliant with Google Maps / Google My Maps requirements.

  ### Fixes Applied for Google Maps Compatibility

  1. XML Declaration (<?xml version="1.0" encoding="UTF-8"?>):
      • Fixed the GPX XML header to use standard version="1.0". Google Maps rejects files declaring XML version="1.1".
  2. Schema & Namespace Specifications:
      • Added full GPX 1.1 schema declarations (xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.
      topografix.com/GPX/1/1/gpx.xsd") so Google Maps XML validation passes.
  3. ISO 8601 UTC Timestamp Formatting:
      • Ensured all <time> tags in GPX use strict ISO 8601 UTC strings (YYYY-MM-DDTHH:MM:SSZ), resolving parsing errors triggered by arbitrary datetime string formats.
  4. KML Document & Styling Structure:
      • Enclosed KML placemarks inside a standard <Document> root with a <Style> block (LineStyle width and color) and formatted coordinates as longitude,latitude,0 separated
      by spaces.

---
  I have added travel direction indicators and waypoint timestamps to both the interactive route map and the exported GPX and KML route files.

  ### Summary of Enhancements

  1. Route Map (map.html):
      • Directional Segment Arrows (➤): Rendered midway along each route line segment on the map, rotated according to the exact bearing angle pointing from one stop to the
      next.
      • Waypoint Timestamps & Direction Indicators in Itinerary Chips: Each itinerary step chip displays the stop's media timestamp (� 2026-0 8-01 10:00 AM) and the cardinal
      direction to the next stop (➔ NE).
      • Map Marker Tooltips: Hovering over map marker pins displays the stop sequence, formatted timestamp, count of media items, and travel direction to the next stop (➔ Next
      stop: NE (45.0°)).
  2. GPX Export File (Album.gpx & JS exporter):
      • Waypoint Timestamps: Formatted in standard ISO 8601 UTC format (<time>2026-08-01T10:00:00Z</time>) under each <wpt> and trackpoint <trkpt>.
      • Travel Direction Metadata: Added <cmt> and <desc> fields detailing the heading bearing in degrees and cardinal direction (e.g., <cmt>Heading to Stop #2: NE (45.
      0°)</cmt>).
  3. KML Export File (Album.kml & JS exporter):
      • Waypoint Timestamps: Uses standard KML <TimeStamp><when>2026-08-01T10:00:00Z</when></TimeStamp> elements.
      • Rich HTML Placemark Descriptions: Formatted placemark <description> blocks containing the stop title, media timestamp, and direction to the next stop.

