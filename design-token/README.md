# WealthLens Design Tokens

Brand-level design tokens for the WealthLens platform.

## Files

### `colors.json`
```json
{
  "primary": "emerald",
  "secondary": "sky",
  "accent": "amber",
  "neutral": "slate"
}
```

These map to TailwindCSS color palettes used throughout the client:
- **Emerald** — primary actions, success states, brand identity
- **Sky** — secondary elements, informational highlights
- **Amber** — accent, warnings, attention indicators
- **Slate** — neutral backgrounds, text, borders

### `typography.json`
```json
{
  "heading": "Inter",
  "body": "Inter",
  "mono": "JetBrains Mono"
}
```

The client uses Geist Sans / Geist Mono as primary fonts with Inter as the design-system fallback. JetBrains Mono is specified for code/data display contexts.

## Usage

These tokens serve as the single source of truth for the WealthLens visual identity. The client's `globals.css` and TailwindCSS configuration consume these values to maintain consistency across all components and widget visualizations.
