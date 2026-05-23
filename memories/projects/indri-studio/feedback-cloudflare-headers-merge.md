---
name: feedback-cloudflare-headers-merge
description: Cloudflare WSA _headers merges all matching rules — never use /* catch-all alongside specific path rules for the same header
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3559c85f-9aa3-411f-b9ee-c1a289282866
---

Cloudflare Workers Static Assets `_headers` **merges all matching rules** rather than replacing earlier ones with later ones. Despite Cloudflare docs saying "only the headers from the last matching path are applied," the actual behaviour is header accumulation.

**Why:** Discovered in v0.1.35 when `/*: Cache-Control: no-store` was added before `/_astro/*: Cache-Control: public, max-age=31536000, immutable`. The `_astro/*` responses received both values concatenated: `no-store, public, max-age=31536000, immutable`. Per RFC 9111 `no-store` (most restrictive) won, killing the immutable cache for all images/JS/fonts.

**How to apply:** Never use a `/*` catch-all in `_headers` alongside specific path rules that set the same header. Use the **Worker** for per-content-type header overrides — after `env.ASSETS.fetch()`, check `content-type` and call `headers.set()` on the response before returning it.
