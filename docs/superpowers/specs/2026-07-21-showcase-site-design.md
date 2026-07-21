# Transmission Cleaner Showcase Site — Design Specification

## Goal

Create an English-first, Italian-selectable product showcase for Transmission Cleaner, published from this repository through GitHub Pages. The site should explain the product in a polished, detailed way to both prospective users and self-hosting administrators, without coupling the site to the Python application runtime.

## Scope

The first version is a responsive, static single-page site under `docs/`:

- `docs/index.html` — semantic page structure and content hooks.
- `docs/styles.css` — visual system, responsive layout, dashboard preview, and accessibility states.
- `docs/site.js` — language selection, translated copy, and small progressive-enhancement interactions.
- `.github/workflows/pages.yml` — GitHub Pages deployment workflow for the `docs/` directory.

The existing `docs/superpowers/` directory remains ignored for local design/plan artifacts. The former blanket `/docs` ignore is replaced by `/docs/superpowers/` so the public site can be committed.

## Audience and content

English is the default language. Italian is available through a visible language selector and the choice is persisted locally. The page serves two audiences in one flow:

1. People discovering the product, who need a clear promise, benefits, and a low-friction install path.
2. Self-hosters and administrators, who need accurate operational detail, configuration examples, supported deployment paths, and links to the repository documentation.

Content sections:

1. Hero with product promise, concise explanation, version context, and GitHub/Docker calls to action.
2. Trust strip for current version, MIT license, container registries, and multi-architecture images.
3. Problem/solution narrative focused on automated torrent housekeeping.
4. Detailed feature grid covering multi-server support, rule-based deletion, dry-run, scheduling, dashboard, notifications, persistent history/import, REST API, and health checks.
5. “How it decides” flow showing the four deletion gates: seeding/stopped, complete, old enough, and optional ratio threshold; incomplete downloads are explicitly protected.
6. Static dashboard preview reflecting the existing UI vocabulary and data: server status, total torrents, candidates, retained items, age, ratio, progress, and next run.
7. Deployment cards for Docker Compose, Docker Run, and Portainer, with Compose recommended.
8. Configuration snippets for `servers.json` and key `stack.env` values.
9. FAQ covering requirements, Transmission RPC access, dry-run behavior, notifications, persistence, and API usage.
10. Final CTA and footer links to GitHub, README, releases, and container images.

## Visual and interaction design

Use a dark “control room” visual language that echoes the existing dashboard while feeling like a product site: near-black navy surfaces, electric cyan/lime accents, warm warning red only for deletion-risk examples, restrained grid/noise decoration, rounded panels, and monospace labels for configuration and status data. Keep body copy high-contrast and readable, with generous spacing and a strong mobile layout.

The dashboard preview is built with HTML/CSS rather than an image or external screenshot, so it stays crisp, accessible, and repository-native. Decorative elements must not carry meaning and are hidden from assistive technology.

The selector changes all visible marketing and instructional copy between English and Italian without a page reload, updates the document language, and stores the preference in `localStorage`. If JavaScript is unavailable, English content remains fully usable. External font loading is optional enhancement; the page must render acceptably with system fallbacks.

## GitHub Pages and maintenance

The Pages workflow uses GitHub’s official Pages actions, publishes the `docs/` artifact, and runs only when the site/workflow changes (plus manual dispatch). It must request the minimum Pages/deployment permissions and support the repository’s current default branch workflow. No application secrets or runtime configuration are exposed.

All product claims must match the README and current version (`1.1.0`) at implementation time. Links should point to the repository’s canonical URLs. The site should not duplicate the full configuration reference; it should provide enough detail to orient users and link to the README for exhaustive reference.

## Quality criteria

- Responsive and usable at mobile, tablet, and desktop widths.
- Keyboard-accessible navigation, selector, CTAs, and disclosure controls.
- Semantic landmarks, heading hierarchy, visible focus states, sufficient contrast, and reduced-motion support.
- No build step required to preview the site locally.
- No regression to Python application files or existing tests.
- GitHub Pages workflow syntax is valid and the site assets are self-contained apart from optional external fonts.
- Every translated section has equivalent meaning in English and Italian; no placeholder copy remains.
