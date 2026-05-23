---
name: import-claude-design
description: Import a Claude Design export zip into the site/ directory and deploy. Accepts a zip file path. Extracts the download/ bundle, overwrites site/, commits, and pushes a tag to trigger the Cloudflare Pages deploy workflow. Trigger phrases — "import this design", "put this design on the site", "deploy this Claude Design", "/import-claude-design".
version: 1.3.0
---

# /import-claude-design — Deploy a Claude Design bundle to site/

Accepts a zip file exported from Claude Design (claude.ai/design) and deploys it to the Cloudflare Pages site.

---

## Step 0 — Collect inputs

Ask for any missing values:

```
1. Zip path   — absolute path to the Claude Design export zip
               (e.g. /home/will/Downloads/foundrylinux.zip)
2. Tag        — semver tag to push, or omit to auto-bump patch from latest v* tag
```

---

## Step 1 — Validate zip

```sh
unzip -l <ZIP_PATH> | grep 'download/index.html'
```

Must contain `download/index.html`. If not found, abort with:
> This doesn't look like a Claude Design export — expected `download/index.html` inside the zip.

---

## Step 2 — Extract and overwrite site/

```sh
TMPDIR=$(mktemp -d)
unzip -o <ZIP_PATH> -d "$TMPDIR"
cp "$TMPDIR"/download/* site/
rm -rf "$TMPDIR"
```

This overwrites all files in `site/` with the new design. Any files in `site/` that aren't in the zip (e.g. `robots.txt`, `site/fonts/`) are preserved.

---

## Step 3 — Strip the Tweaks panel

Claude Design bundles ship `tweaks-panel.jsx` — a floating live-design tool for iteration. Remove it before deploy:

```sh
rm -f site/tweaks-panel.jsx site/tweaks-panel.js
git rm --cached site/tweaks-panel.jsx site/tweaks-panel.js 2>/dev/null || true
```

Then strip all Tweaks wiring from `site/app.jsx`. Replace the entire file with a clean App that hardcodes the final design values (material, font, wordmark, background, accent). Example after stripping:

```jsx
// <SITE> — <DOMAIN>

function App() {
  return (
    <>
      <Topbar />
      <main>
        <Hero />
        <Kit />
        <Install />
        <Editions />
      </main>
      <Foot />
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
```

Also remove the `wordmark` prop from `Topbar` if it was passed from tweaks state, and hardcode `data-material`, `data-font`, `data-mark` attributes directly in `Hero` in `sections.jsx`.

Remove the `site/tweaks-panel.jsx` build line from the `site-build` Taskfile task so it isn't rebuilt on the next import.

---

## Step 4 — Self-host fonts

Claude Design bundles load fonts from Google Fonts, which is a render-blocking cross-origin request. Replace with self-hosted woff2 files served from Cloudflare's edge:

**4a — Identify the fonts in use** from `index.html`'s `<link rel="stylesheet" href="https://fonts.googleapis.com/...">`.

**4b — Download the woff2 files:**

```sh
mkdir -p site/fonts

# Fetch the CSS with a modern UA to get woff2 URLs
CSS=$(curl -fsSL -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36" \
  "<GOOGLE_FONTS_URL>")

# Extract unique woff2 URLs and download each
echo "$CSS" | grep -o 'https://fonts.gstatic.com[^)]*' | sort -u | while read url; do
  # derive a meaningful local filename from font name + unicode-range comment above the block
  # e.g. big-shoulders-display-900-latin.woff2
  curl -fsSL -o "site/fonts/<name>.woff2" "$url"
done
```

Only download fonts needed for the **final design** — skip Tweaks-only fonts (Cinzel, Black Ops One, Major Mono Display, etc.). Typically: the wordmark font at the single weight used, the body font at all weights used, the mono font at all weights used.

**4c — Add `@font-face` blocks to `styles.css`** at the very top (before `:root`), using `font-display: swap` and the same `unicode-range` values from the Google Fonts CSS. For variable-weight files shared across weights, use a range syntax: `font-weight: 400 600`.

**4d — Update `index.html`:** remove the `<link rel="preconnect" href="https://fonts.googleapis.com">`, `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>`, and the Google Fonts `<link rel="stylesheet">` entirely. The fonts are now embedded in `styles.css` via `@font-face`.

**4e — Remove `tweaks-panel.js` from the `<script>` tags** in `index.html` if still present.

---

## Step 5 — Restructure JSX for ES modules + SSR

Claude Design bundles use browser globals (`Object.assign(window, {...})`, CDN React). Convert to proper ES modules so the SSR render step can bundle everything together.

**5a — `site/icons.jsx`:** replace the final `Object.assign(window, { ... });` line with:
```jsx
export { IconA, IconB, ... };  // list every exported name
```

**5b — `site/sections.jsx`:** add imports at the top and replace the global export at the bottom:
```jsx
// top of file — add after any existing comments:
import React from 'react';
import { FoundryMark, GearStackIcon, ... } from './icons.jsx';  // all icons used

// bottom of file — replace Object.assign(window, {...}); with:
export { Topbar, Hero, /* ... all section components */ };
```

**5c — `site/app.jsx`:** replace entirely with an import-driven version that exports `App`:
```jsx
// <SITE> — <DOMAIN>
import { Topbar, Hero, /* ... */ } from './sections.jsx';

export function App() {
  return (
    <>
      <Topbar />
      <main>
        <Hero />
        {/* ... remaining sections */}
      </main>
      <Foot />
    </>
  );
}
```
Remove the `ReactDOM.createRoot(...).render(<App />)` call — the SSR render script handles rendering.

**5d — Install `scripts/ssr-render.js` and `package.json`** if not already present. The skill ships its own copies:

```sh
# SKILL_DIR is ~/.claude/skills/import-claude-design
mkdir -p scripts
cp "$SKILL_DIR/ssr-render.js" scripts/ssr-render.js
cp "$SKILL_DIR/package.json"  package.json
npm install
```

Skip the copy steps if the files already exist in the project (a previous import installed them).

**5e — Delete old browser JS bundles** (if present from a previous compile step):
```sh
git rm -f site/icons.js site/sections.js site/app.js site/tweaks-panel.js 2>/dev/null || true
rm -f site/embers.js  # untracked orphan if present
```

**5f — Run the SSR render and check links:**
```sh
task site-build
task link-check    # verifies every <a href> in built HTML; exit 1 on broken links
```

`site-build` runs `node scripts/ssr-render.js`, which bundles all JSX (icons → sections → app) together with react-dom/server and writes a fully-static `site/index.html`. No React scripts are loaded at runtime — FCP is instant.

`link-check` runs `node scripts/check-links.js`, checking internal anchors and paths against the built files, and fetching each unique external URL via HTTP HEAD. Fails on broken links before anything is committed or deployed. Pass `-- --skip-external` to check only internal links (faster, no network).

---

## Step 6 — Commit

```sh
git add site/ scripts/ssr-render.js package.json package-lock.json .gitignore
git commit -m "feat(site): import Claude Design bundle"
git push origin main
```

---

## Step 7 — Deploy

```sh
task site-deploy
```

This runs `npx wrangler pages deploy site/ --project-name <PROJECT> --branch main`. Requires
`CLOUDFLARE_API_TOKEN` in the environment. If not set, the user must supply it:

```sh
CLOUDFLARE_API_TOKEN=<token> task site-deploy
```

---

## Step 8 — Lighthouse

```sh
task lighthouse
```

Audits the live URL after deploy (`RUNS=1` for speed — same as CI). Prints a score table
(Perf / A11y / BP / FCP / LCP / TBT / CLS). Then run the threshold gate:

```sh
bash scripts/lighthouse-threshold.sh
```

Exits 0 if all four categories (Perf / A11y / BP / SEO) are ≥ 95. If any score is below threshold, fix before tagging. Common issues:

- **color-contrast** — `--ink-faint` with low alpha on a dark background fails WCAG 4.5:1. Bump the alpha until the effective color has ≥ 4.5:1 contrast against the page background.
- **landmark-one-main** — wrap the main content sections in `<main>` in `app.jsx`.
- **meta-description** — add `<meta name="description" content="...">` to `index.html`.
- **robots-txt** — add `site/robots.txt` (without it Cloudflare Pages returns the SPA HTML for `/robots.txt`).

JSON reports are in `/tmp/lh/latest/` for inspection.

---

## Step 9 — Tag

Auto-bump patch from the latest `v*` tag, or use the tag the user specified:

```sh
# Auto-bump:
LATEST=$(git tag --list 'v*.*.*' | sort -V | tail -1)
LATEST="${LATEST:-v0.0.0}"
IFS='.' read -r MAJ MIN PAT <<< "${LATEST#v}"
NEXT="v${MAJ}.${MIN}.$((PAT + 1))"
git tag "$NEXT" && git push origin "$NEXT"
echo "Tagged $NEXT"
```

---

## Step 10 — Verification

```sh
curl -fsSL https://<DOMAIN>/ | grep -i 'foundry\|linux\|<title'
```

Or open the URL in the browser.

---

## Notes

- **Self-hosted fonts are permanent** — `site/fonts/` is committed to the repo; Cloudflare serves them from the edge. On re-import, update the woff2 files only if the font selection changes.
- **Link-check gate** — `task link-check` (depends on `site-build`) runs `node scripts/check-links.js`. Checks internal anchors (`#id` must exist in same page), internal paths (`/path` must resolve to a file in `site/`), and external URLs (HTTP HEAD, 2 retries). Skips `magnet:` links. CI runs it as a deploy gate (fails before `wrangler pages deploy`). Run locally with `-- --skip-external` to skip the network checks.
- **Build step = SSR render** — `task site-build` runs `node scripts/ssr-render.js`, which bundles all JSX with react-dom/server and writes a fully-static `site/index.html`. No React scripts are loaded at runtime. The `.jsx` files are source only; the output is the single `site/index.html`. Requires `package.json` + `node_modules/` (see Step 5d).
- **Reading reports** — `task lh-report` prints scores from the last run (`/tmp/lh/latest/`). To read an archived bundle: `task lh-report -- v0.0.29`. To read a specific file: `task lh-report -- path/to/file.json`.
- **Lighthouse setup** — requires `scripts/lighthouse-threshold.sh` and a `lighthouse` Taskfile task using `lighthouse@13.3.0` with devtools throttling. See foundrylinux.org as the reference implementation. Threshold: 95 on Perf / A11y / BP / SEO. JSON reports land in `/tmp/lh/latest/`; CI uploads them as a 90-day artifact and archives to `site/lh/<tag>/` for durable URL access.
- **Re-importing** — Running the skill again with a new zip simply overwrites `site/` and bumps the tag. Safe to run repeatedly. The `site/fonts/` directory is preserved (not in the zip); update woff2 files manually only if the font selection changes.
