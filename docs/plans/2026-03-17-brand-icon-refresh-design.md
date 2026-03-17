# Brand Icon Refresh Design

## Goal
Replace the current awkward sidebar avatar and missing browser tab icon with a single, consistent brand icon derived from the user-provided reference image.

## Scope
- Extract the clearest central subject from the provided reference image.
- Export a square brand asset suitable for in-app branding.
- Export a favicon-sized asset for browser tabs.
- Wire the new icon into the sidebar brand avatar and `index.html` favicon.

## Approach
Use the supplied reference image as source material, crop to the most legible subject, then generate a compact icon set from the crop. This keeps the visual identity aligned with the requested image while avoiding the blur that would come from shrinking the full image directly to favicon size.

## Files Expected
- `src/assets/brand-icon.png`
- `public` is not present, so favicon will be referenced from `src/assets` via Vite-compatible path handling in `index.html`.
- `src/App.jsx` / existing brand image imports if needed
- `index.html`

## Verification
- Sidebar displays the new icon.
- Browser tab references the new favicon.
- Production build succeeds.
