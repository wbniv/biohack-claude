// @ts-check
import { defineConfig, fontProviders } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import rehypeExternalLinks from 'rehype-external-links';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
	site: 'https://<DOMAIN>',
	integrations: [sitemap()],
	build: {
		// Inline all compiled CSS into each HTML response — eliminates the
		// render-blocking <link rel="stylesheet"> that Lighthouse flags as
		// the dominant FCP cost on a small static site.
		inlineStylesheets: 'always',
	},
	// Self-host Space Grotesk via the Astro Fonts API. Downloads the woff2
	// at build time, Latin-subsetted, into dist/_astro/fonts/, served
	// same-origin via Workers Static Assets — no cross-origin round-trip
	// to fonts.googleapis.com / fonts.gstatic.com. The <Font /> component
	// in Base.astro emits the @font-face + preload tags. Ending the
	// fallbacks array with a generic family triggers optimizedFallbacks
	// (metric-matched fallback face derived from the downloaded woff2).
	fonts: [
		{
			provider: fontProviders.google(),
			name: 'Space Grotesk',
			cssVariable: '--font-space-grotesk',
			weights: ['400', '500', '700'],
			styles: ['normal'],
			subsets: ['latin'],
			display: 'optional',
			fallbacks: ['system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
		},
	],
	markdown: {
		rehypePlugins: [
			[
				rehypeExternalLinks,
				{
					target: '_blank',
					rel: ['noopener', 'noreferrer'],
					properties: { 'data-external': 'true' },
				},
			],
		],
	},
	vite: {
		plugins: [tailwindcss()],
	},
});
