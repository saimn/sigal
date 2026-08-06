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
