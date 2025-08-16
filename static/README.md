# Static Files

This directory contains all static assets for the URL Shortener project.

## Structure

```
static/
├── css/
│   └── style.css          # Custom styles for the URL shortener
├── js/
│   └── clipboard.js       # Clipboard functionality for copying URLs
└── README.md              # This file
```

## Files Description

### CSS Files

- **`css/style.css`**: Contains all custom styles for the URL shortener interface
  - Copy button animations and states
  - URL display styling
  - Form improvements
  - Responsive design adjustments
  - Table and badge styling

### JavaScript Files

- **`js/clipboard.js`**: Handles clipboard functionality
  - Modern Clipboard API implementation
  - Fallback support for older browsers
  - Visual feedback for copy operations
  - Error handling and user notifications
  - DOM ready initialization

## Usage

These files are automatically served by Django's static file handling system. The files are referenced in templates using the `{% static %}` template tag:

```html
<link rel="stylesheet" href="{% static 'css/style.css' %}">
<script src="{% static 'js/clipboard.js' %}"></script>
```

## Development

When making changes to static files:

1. Edit the files in the `static/` directory
2. Run `python manage.py collectstatic` to collect files for production
3. The development server will automatically serve static files when `DEBUG = True`

## Browser Support

- **CSS**: Modern browsers with CSS3 support
- **JavaScript**: 
  - Modern browsers with Clipboard API support
  - Fallback support for older browsers using `document.execCommand`
