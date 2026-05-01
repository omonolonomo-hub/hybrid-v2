# Font Usage Guide

## Font Hierarchy

### Ghora (Display Font)
**Usage:** Titles, headings, and primary action buttons
- Main menu title: "AUTOCHESS HYBRID"
- Lobby screen title: "PLAYER LOBBY"
- Primary buttons: "NEW GAME", "START MATCH", "BACK"

**Characteristics:**
- Bold, impactful display font
- Used for emphasis and visual hierarchy
- Creates strong brand identity

### Butler (Body Font)
**Usage:** All lobby screen content and UI elements
- Player names and slot numbers
- Strategy labels and descriptions
- Panel headers and labels
- Dropdown menus and options
- Counter text

**Characteristics:**
- Clean, readable sans-serif
- Professional and modern
- Excellent for UI elements and body text

### MinimapCat (Legacy)
**Status:** Being phased out in favor of Butler
- Previously used for all UI text in lobby
- Now only used in main menu for specific elements

## Implementation

### Main Menu (index.html + style.css)
- Title: **Ghora**
- Buttons: **Ghora**
- Body text: **Ghora** (minimal text)

### Lobby Screen (lobby.html + lobby.css)
- Title (h1): **Ghora** ✓
- Body default: **Butler** ✓
- All content: **Butler** ✓
- Buttons: **Ghora** ✓

## Font Files

Located in `v2/assets/fonts/`:
- `Ghore.ttf` - Display font (note: filename is "Ghore" but font-family is "Ghora")
- `Butler-Free-SBd-St.otf` - Body font
- `minimap_category_names.ttf` - Legacy font (still used in main menu)

## Loading Strategy

Fonts are preloaded in HTML `<head>` for optimal performance:
```html
<link rel="preload" href="../../assets/fonts/Ghore.ttf" as="font" type="font/ttf">
<link rel="preload" href="../../assets/fonts/Butler-Free-SBd-St.otf" as="font" type="font/otf">
```

JavaScript waits for fonts before revealing UI:
```javascript
Promise.all([
  document.fonts.load('68px "Ghora"'),
  document.fonts.load('16px "Butler"'),
])
```

This prevents FOUT (Flash of Unstyled Text) and ensures smooth rendering.
