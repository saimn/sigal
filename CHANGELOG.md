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

