# Shared UI Resources

This directory contains shared constants, utilities, and styles used across multiple web menu pages.

## Files

### `canvas-utils.js`
Shared JavaScript utilities for canvas rendering (loaded as regular script, not ES6 module):
- **CATEGORY_COLORS**: Array of 6 hex color codes used for visual elements
- **DESIGN**: Design dimensions (1920x1080)
- **hexToRgba()**: Converts hex color to rgba string with alpha
- **drawHexLobby()**: Draws a hexagon on canvas context (for lobby.js)

**Used by:**
- `script.js` (main menu)
- `lobby.js` (lobby screen)

**Why not ES6 modules?**
- pywebview has compatibility issues with ES6 module imports
- Functions need to be in global scope for inline event handlers
- Regular script tags work reliably across all environments

### `base.css`
Shared CSS styles:
- **@font-face declarations**: Ghora and MinimapCat fonts
- **:root CSS variables**: Color palette used across all pages
  - `--color-mind`, `--color-connection`, `--color-existence`
  - `--color-neutral`, `--color-bg`, `--color-panel`
  - `--color-border`, `--color-text`, `--color-text-dim`

**Used by:**
- `style.css` (main menu styles)
- `lobby.css` (lobby styles)

## Benefits

1. **Single source of truth**: Constants and utilities defined once
2. **Consistency**: Same colors and behavior across all pages
3. **Maintainability**: Update once, applies everywhere
4. **Reduced duplication**: ~80 lines of code eliminated
5. **Global scope preserved**: Works with pywebview and inline handlers

## Usage

### JavaScript
```html
<!-- Load shared utilities first -->
<script src="shared/canvas-utils.js"></script>
<!-- Then load page-specific code -->
<script src="your-page.js"></script>
```

Variables and functions are automatically available in global scope.

### CSS
```html
<link rel="stylesheet" href="shared/base.css">
<link rel="stylesheet" href="your-page.css">
```

**Note**: Import `base.css` before page-specific CSS to allow overrides.
