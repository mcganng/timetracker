# Static Files Directory

This directory contains static assets for the Savant Time Tracker web application.

## Directory Structure

```
static/
├── css/
│   └── style.css       # Main application stylesheet
└── js/                 # JavaScript files (if needed)
```

## Notes

- The application currently uses minimal custom JavaScript
- Most interactivity is provided by Bootstrap 5 and Chart.js loaded from CDN
- If custom JavaScript is needed, create files in the `js/` directory

## CSS Customization

The main stylesheet ([style.css](css/style.css)) provides:
- Custom color schemes (defined in green palette)
- Chart styling overrides
- Responsive layout adjustments
- Print media styles

See [ADMIN_COLOR_SCHEME.md](../ADMIN_COLOR_SCHEME.md) for details on the color scheme.
