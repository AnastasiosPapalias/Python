# ScholarForge — static site

Static HTML/CSS site for ScholarForge. Modelled on feynman.is-style typography:
calm, serif body, generous whitespace, restrained colour.

## Pages
- `index.html` — overview, three promises, positioning
- `features.html` — full feature list, freemium + premium
- `install.html` — install, upgrade, uninstall, API keys
- `cli.html` — complete CLI reference
- `sources.html` — 20 academic sources + trust-label taxonomy
- `pricing.html` — freemium + premium tiers

## Serving locally

```
cd site
python3 -m http.server 8000
# open http://localhost:8000
```

## Deploying
The site is pure HTML + one CSS file. Drop it on GitHub Pages, Netlify,
Cloudflare Pages, or any static host.

## Design notes
- Single stylesheet (`style.css`)
- No JavaScript
- No external fonts (uses system serif + sans stacks)
- Accessible at 100% default font size; no viewport tricks
- Respects prefers-reduced-motion by default (no animations)
