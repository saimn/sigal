# Photobook Theme for Sigal

A beautiful, print-friendly photo gallery theme presenting your images in a modern photo book layout.

## Features

- **Photo Book View**: Browse photos in a paginated, magazine-style layout
- **Outline View**: See all photos as thumbnails in a grid for quick navigation
- **Rich Captions**: Display title, description, filename, and EXIF metadata
- **GPS Support**: Clickable GPS coordinates link to OpenStreetMap
- **Keyboard Navigation**: 
  - Arrow Right / Space: Next page
  - Arrow Left: Previous page
  - Home: First page
  - End: Last page
- **Responsive Design**: Works beautifully on desktop, tablet, and mobile
- **Print-Friendly**: Optimized for printing physical photo books
- **UTF-8 Encoding**: Full Unicode support for all text
- **Helvetica Typography**: Clean, professional Helvetica Neue font

## Installation

1. The photobook theme is installed as part of Sigal
2. Reference it in your `sigal.conf.py`:

```python
theme = 'photobook'
```

## Configuration

Add these settings to your `sigal.conf.py` to customize the photobook theme:

```python
# Theme name
theme = 'photobook'

# Photos per page (default: 1)
# Note: Currently displays 1 photo per page
photobook_photos_per_page = 1

# Enable keyboard navigation (default: True)
photobook_keyboard_nav = True

# Enable outline click navigation (default: True)
photobook_outline_nav = True

# Show album description (default: True)
photobook_show_description = True

# Show EXIF data (default: True)
photobook_show_exif = True

# Show GPS coordinates (default: True)
photobook_show_gps = True

# Map provider for GPS coordinates (default: 'openstreetmap')
# Options: 'openstreetmap' or 'googlemaps'
photobook_map_provider = 'openstreetmap'
```

## Configuration Details

### Map Provider

The theme supports two map providers for GPS coordinates:

- **OpenStreetMap** (default): Free, open-source mapping service
  - Set: `photobook_map_provider = 'openstreetmap'`
  - Links open to: `https://www.openstreetmap.org/`

- **Google Maps**: Google's mapping service (requires internet access)
  - Set: `photobook_map_provider = 'googlemaps'`
  - Links open to: `https://www.google.com/maps/`

You can also change it at runtime using JavaScript:

```javascript
// Switch to Google Maps
Photobook.setMapProvider('googlemaps');

// Switch back to OpenStreetMap
Photobook.setMapProvider('openstreetmap');

// Get current map provider
var current = Photobook.getMapProvider();
```

## Usage

### Document Structure

The photobook theme expects media metadata to be provided by Sigal:

- **Title**: Image filename or custom title
- **Description**: From markdown files or YAML frontmatter
- **EXIF Data**: Automatically extracted from image files (JPG, JPEG, HEIC)
  - Camera make and model
  - ISO, exposure time, aperture, focal length
  - Date/time taken
  - GPS location (if available)
- **Filename**: Full filename with extension

### Adding Descriptions

Create a markdown file with the same name as your image for descriptions:

```
photo.jpg
photo.md
```

Content of `photo.md`:
```markdown
# Photo Title (optional)

This is a detailed description of the photo that appears below the image.
Can include multiple paragraphs and formatting.
```

### Organizing Photos

Place photos in albums (directories):

```
gallery/
├── album1/
│   ├── photo1.jpg
│   ├── photo1.md
│   ├── photo2.jpg
│   └── photo2.md
└── album2/
    ├── trip1.jpg
    └── trip1.md
```

## Features Explained

### Two View Modes

1. **Outline View**: Grid of all thumbnails with titles. Click any thumbnail to jump to that photo in book view.
2. **Photo Book View**: Full-screen image with detailed caption including:
   - Photo title
   - Description (from markdown)
   - Filename
   - Camera information
   - Settings (ISO, exposure, aperture, focal length)
   - GPS location (clickable link to OpenStreetMap)

### Responsive Behavior

- **Desktop**: Two-column layout with image on left, caption on right
- **Tablet**: Single column, image above caption
- **Mobile**: Optimized single column layout with readable font sizes

### Print Support

The theme includes print stylesheets for generating PDF photo books:

```bash
# In your browser, use Print to PDF:
# - File > Print (Ctrl+P / Cmd+P)
# - Select "Save as PDF"
# - Recommended paper size: A4 or Letter
# - Margins: 0.5 inch
```

## Styling and Customization

### Colors

The theme uses a clean white background with these main colors:

- Background: `#ffffff` (white)
- Text: `#333333` (dark gray)
- Borders: `#dddddd` (light gray)
- Links: `#0066cc` (blue)
- Accents: `#f5f5f5` (light gray)

### Font Sizes

- Header: 32px
- Album title: 28px
- Photo title: 22px
- Body text: 16px (15px on tablets, 14px on mobile)
- Metadata: 14px
- Small text: 13px

### Custom CSS

Override theme styles with a custom CSS file:

```python
# In sigal.conf.py
theme = 'photobook'
photobook_custom_css = 'my_custom.css'
```

Create `my_custom.css` in your gallery directory with custom rules:

```css
.photobook-caption h3 {
    color: #cc0000;  /* Make titles red */
}

.photobook-image {
    border: 3px solid #333;  /* Add border to images */
}

body {
    font-size: 18px;  /* Increase base font size */
}
```

## Browser Support

- Chrome/Chromium 60+
- Firefox 55+
- Safari 11+
- Edge 79+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Right Arrow | Next page |
| Space | Next page |
| Left Arrow | Previous page |
| Home | First page |
| End | Last page |

## JavaScript API

For advanced customization, the theme exposes a JavaScript API:

```javascript
// Go to specific page (1-indexed)
Photobook.goToPage(5);

// Navigate
Photobook.nextPage();
Photobook.previousPage();

// Get current state
var current = Photobook.getCurrentPage();  // Returns 1-indexed page
var total = Photobook.getTotalPages();

// Configure pages
Photobook.setPhotosPerPage(2);

// Map provider control
Photobook.setMapProvider('googlemaps');     // Switch to Google Maps
Photobook.setMapProvider('openstreetmap');  // Switch to OpenStreetMap
var provider = Photobook.getMapProvider();  // Get current provider
```

## Performance Notes

- Lazy loading of images is handled by browsers
- Works well with 100-500 photos per album
- Large albums (500+) may benefit from splitting into multiple smaller albums

## Accessibility

- Semantic HTML structure
- Alt text for all images
- Keyboard navigation support
- High contrast text for readability
- Descriptive link text (GPS coordinates link to location names)

## License

This theme is part of Sigal and follows the same license terms.

## Support

For issues or feature requests, visit:
https://github.com/saimon-res/sigal
