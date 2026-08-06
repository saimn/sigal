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

