#!/usr/bin/env node
// Link-check gate: verify every <a href> in built site/*.html resolves.
// Usage: node scripts/check-links.js [--skip-external]

'use strict';

const { readFileSync, existsSync, appendFileSync, readdirSync } = require('node:fs');
const { join, resolve } = require('node:path');

const SKIP_EXTERNAL = process.argv.includes('--skip-external');
const dirArg = (() => {
  const i = process.argv.indexOf('--dir');
  return i !== -1 ? process.argv[i + 1] : null;
})();
const SITE_DIR = resolve(process.cwd(), dirArg ?? 'site');

// ── helpers ──────────────────────────────────────────────────────────────────

function htmlFiles() {
  return readdirSync(SITE_DIR)
    .filter(f => f.endsWith('.html'))
    .map(f => ({ name: f, path: join(SITE_DIR, f), content: readFileSync(join(SITE_DIR, f), 'utf8') }));
}

function extractHrefs(html) {
  // Only check navigation links (<a href>), not resource links (<link href>).
  const hrefs = [];
  for (const m of html.matchAll(/<a\s[^>]*href="([^"]+)"/gi)) hrefs.push(m[1]);
  return hrefs;
}

function resolveInternalPath(href) {
  // /packages → site/packages.html; /packages#cat → site/packages.html; / → site/index.html
  const path = href.split('#')[0].replace(/^\//, '') || 'index';
  const candidates = [
    join(SITE_DIR, path + '.html'),
    join(SITE_DIR, path, 'index.html'),
    join(SITE_DIR, path),
  ];
  return candidates.find(existsSync) ?? null;
}

async function fetchHead(url, retries = 2) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, {
        method: 'HEAD',
        signal: AbortSignal.timeout(10_000),
        headers: { 'User-Agent': 'foundrylinux-link-checker/1.0' },
      });
      if (res.ok || res.status === 405) return { ok: true, status: res.status };
      if (res.status < 500 || attempt === retries) return { ok: false, status: res.status };
    } catch (err) {
      if (attempt === retries) return { ok: false, status: err.message };
    }
    await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
  }
}

// ── main ─────────────────────────────────────────────────────────────────────

async function main() {
  const pages = htmlFiles();
  if (!pages.length) {
    console.error('No HTML files found in site/ — run task site-build first.');
    process.exit(1);
  }

  const results = [];              // { href, source, kind, ok, detail }
  const externalQueue = new Map(); // url → [sourceFiles]

  for (const page of pages) {
    const hrefs = [...new Set(extractHrefs(page.content))];

    for (const href of hrefs) {
      if (href.startsWith('magnet:')) {
        results.push({ href, source: page.name, kind: 'skip', ok: true, detail: 'magnet (skipped)' });
        continue;
      }

      if (href.startsWith('#')) {
        const id = href.slice(1);
        const found = page.content.includes(`id="${id}"`);
        results.push({ href, source: page.name, kind: 'anchor', ok: found,
          detail: found ? 'found' : `id="${id}" not in ${page.name}` });
        continue;
      }

      if (href.startsWith('/')) {
        const resolved = resolveInternalPath(href);
        const ok = resolved !== null;
        results.push({ href, source: page.name, kind: 'path', ok,
          detail: ok ? resolved.replace(SITE_DIR + '/', '') : `no file for ${href}` });
        continue;
      }

      if (/^https?:\/\//.test(href)) {
        if (!externalQueue.has(href)) externalQueue.set(href, []);
        externalQueue.get(href).push(page.name);
        continue;
      }

      results.push({ href, source: page.name, kind: 'unknown', ok: false, detail: 'unrecognised scheme' });
    }
  }

  // Check external URLs
  if (!SKIP_EXTERNAL && externalQueue.size) {
    console.log(`Checking ${externalQueue.size} unique external URL(s)…`);
    const fetched = await Promise.all(
      [...externalQueue.entries()].map(async ([url, sources]) => {
        const r = await fetchHead(url);
        return { url, sources, ok: r.ok, detail: String(r.status) };
      })
    );
    for (const { url, sources, ok, detail } of fetched) {
      for (const source of sources) {
        results.push({ href: url, source, kind: 'external', ok, detail });
      }
    }
  } else if (SKIP_EXTERNAL && externalQueue.size) {
    for (const [url, sources] of externalQueue) {
      for (const source of sources) {
        results.push({ href: url, source, kind: 'external', ok: true, detail: 'skipped' });
      }
    }
  }

  // ── report ────────────────────────────────────────────────────────────────

  const failures = results.filter(r => !r.ok);
  const checks   = results.filter(r => r.kind !== 'skip');

  function table(rows) {
    const lines = [
      '| Status | Href | Source | Detail |',
      '|:---:|---|---|---|',
    ];
    for (const r of rows) {
      const icon = r.ok ? (r.detail === 'skipped' ? '⏭' : '✓') : '✗';
      lines.push(`| ${icon} | \`${r.href}\` | ${r.source} | ${r.detail} |`);
    }
    return lines.join('\n');
  }

  const summary = [
    `## Link check — ${new Date().toISOString().slice(0, 10)}`,
    '',
    `**${checks.length}** links checked across **${pages.length}** page(s)` +
      (SKIP_EXTERNAL ? ' (external links skipped)' : '') + '.',
    '',
    failures.length ? `### ✗ ${failures.length} broken` : '### All links OK',
    '',
    table(failures.length ? failures : checks),
  ].join('\n');

  console.log(summary);

  if (process.env.GITHUB_STEP_SUMMARY) {
    appendFileSync(process.env.GITHUB_STEP_SUMMARY, '\n' + summary + '\n');
  }

  if (failures.length) {
    console.error(`\n${failures.length} broken link(s) — fix before publishing.`);
    process.exit(1);
  }
}

main().catch(err => { console.error(err); process.exit(1); });
