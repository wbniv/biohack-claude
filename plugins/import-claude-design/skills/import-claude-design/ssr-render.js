#!/usr/bin/env node
// Renders site/app.jsx to a fully-static site/index.html (no React runtime needed).
// Reads the imported index.html as the HTML shell template, strips React/bundle script
// tags, injects the SSR-rendered body, and adds a vanilla copy-button handler.
// Run via: node scripts/ssr-render.js  (or: task site-build)
'use strict';

const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');
const os = require('os');

const root = path.resolve(__dirname, '..');
const bundle = path.join(os.tmpdir(), 'foundry-ssr.cjs');
const entry = path.join(os.tmpdir(), 'foundry-ssr-entry.jsx');

// Temp entry: bundle App + react-dom/server together and export the rendered HTML.
fs.writeFileSync(entry, [
  `import { App } from '${path.join(root, 'site/app.jsx')}';`,
  `import { renderToStaticMarkup } from 'react-dom/server';`,
  `import { createElement } from 'react';`,
  `export const html = renderToStaticMarkup(createElement(App));`,
].join('\n'));

esbuild.buildSync({
  entryPoints: [entry],
  bundle: true,
  platform: 'node',
  format: 'cjs',
  jsx: 'automatic',
  outfile: bundle,
  nodePaths: [path.join(root, 'node_modules')],
});

delete require.cache[bundle];
const { html: body } = require(bundle);

// Use the imported index.html as the shell template — it has the correct
// <title>, <meta>, font preloads, and <link rel="stylesheet"> from the design.
let page = fs.readFileSync(path.join(root, 'site/index.html'), 'utf-8');

// Strip React CDN scripts and compiled JS bundles (added by Claude Design export).
page = page.replace(/<script[^>]+src="[^"]*(?:react|react-dom)[^"]*"[^>]*><\/script>\s*/gi, '');
page = page.replace(/<script[^>]+src="(?:icons|sections|app|tweaks-panel)\.js"[^>]*><\/script>\s*/gi, '');

// Inject SSR-rendered body into the root div.
page = page.replace(/<div id="root"><\/div>/, `<div id="root">${body}</div>`);

// Add vanilla copy-button handler before </body>.
// Reads the command text from the DOM so this works for any site.
page = page.replace('</body>', `  <script>
    /* Copy button — replaces the React useState handler */
    document.querySelector('.copy')?.addEventListener('click', function() {
      var cmd = this.closest('[class*="apt"]')?.querySelector('[class*="cmd"]');
      navigator.clipboard?.writeText(cmd ? cmd.textContent : '');
      this.lastChild.textContent = 'COPIED';
      var btn = this;
      setTimeout(function() { btn.lastChild.textContent = 'COPY'; }, 1400);
    });
  </script>
</body>`);

fs.writeFileSync(path.join(root, 'site/index.html'), page);
const kb = Math.round(body.length / 1024);
console.log(`✓ site/index.html rendered (${kb} KB of markup, no React runtime)`);
