// 301-redirect www.<DOMAIN> → <DOMAIN> (path/query/hash preserved),
// fall through to static-assets binding for everything else. Both
// hostnames are bound to this Worker via Terraform
// (cloudflare_workers_custom_domain in infrastructure/cloudflare/global/).

interface Env {
	ASSETS: { fetch: (request: Request) => Promise<Response> };
}

// HTMLRewriter is a Cloudflare Workers global; declared here because this
// project uses the DOM tsconfig (not @cloudflare/workers-types).
declare class HTMLRewriter {
	on(selector: string, handler: {
		element(el: { setAttribute(name: string, value: string): void }): void;
	}): HTMLRewriter;
	transform(response: Response): Response;
}

const APEX = "<DOMAIN>";
const WWW = "www.<DOMAIN>";

function generateNonce(): string {
	const bytes = new Uint8Array(16);
	crypto.getRandomValues(bytes);
	return btoa(String.fromCharCode(...bytes));
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		if (url.hostname === WWW) {
			url.hostname = APEX;
			return Response.redirect(url.toString(), 301);
		}

		const response = await env.ASSETS.fetch(request);
		const ct = response.headers.get("content-type") ?? "";

		if (ct.includes("text/html")) {
			// Per-request nonce. Astro inlines scripts as <script type="module">
			// tags; a nonce lets us keep script-src tight while those execute.
			// 'unsafe-inline' is present as a fallback for CSP-Level-1 browsers;
			// in CSP-Level-2+ browsers the nonce takes precedence and
			// 'unsafe-inline' is ignored. HTMLRewriter stamps nonce onto every
			// <script> tag so the policy is coherent.
			const nonce = generateNonce();
			const headers = new Headers(response.headers);
			headers.set("Cache-Control", "no-store");
			headers.set("X-Content-Type-Options", "nosniff");
			headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
			headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
			headers.set(
				"Content-Security-Policy",
				`default-src 'self'; ` +
				`font-src 'self'; ` +
				`style-src 'self' 'unsafe-inline'; ` +
				`script-src 'self' 'nonce-${nonce}' 'unsafe-inline'; ` +
				`img-src 'self' data:; ` +
				`object-src 'none'; ` +
				`base-uri 'self'; ` +
				`frame-ancestors 'none'`
			);
			return new HTMLRewriter()
				.on("script", {
					element(el) { el.setAttribute("nonce", nonce); },
				})
				.transform(new Response(response.body, { status: response.status, statusText: response.statusText, headers }));
		}

		return response;
	},
};
