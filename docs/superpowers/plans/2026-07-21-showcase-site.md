# Transmission Cleaner Showcase Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an English-first, Italian-selectable, responsive product showcase in `docs/` and publish it through GitHub Pages without changing the Python application.

**Architecture:** A dependency-free static site separates semantic content (`index.html`), presentation (`styles.css`), and progressive-enhancement behavior/translation data (`site.js`). A dedicated Pages workflow publishes only the `docs/` artifact; existing application workflows remain untouched.

**Tech Stack:** HTML5, CSS3, vanilla JavaScript, GitHub Pages Actions.

## Global Constraints

- English is the default language; Italian must be selectable and persisted locally.
- Product claims must match README and version `1.1.0`.
- No build step or runtime dependency is required to preview the site.
- The site must be responsive, keyboard accessible, semantic, high contrast, and reduced-motion aware.
- `/docs/superpowers/` remains ignored except for intentionally force-added design/plan artifacts.
- No application secrets, tracking, or runtime configuration may enter the site.

### Task 1: Create the semantic showcase page

**Files:**
- Create: `docs/index.html`

**Interfaces:**
- Consumes: `docs/styles.css` and `docs/site.js` created by later tasks.
- Produces: the complete semantic page structure, translation keys, dashboard preview hooks, language selector, and accessible disclosure elements.

- [ ] **Step 1: Add document metadata and landmarks**

Create an HTML5 document with `lang="en"`, viewport, description, Open Graph/Twitter metadata, skip link, header/nav, `main`, and footer. Link only to local CSS/JS plus optional font enhancement.

- [ ] **Step 2: Add the content sections from the approved design**

Add hero, trust strip, problem/solution, feature grid, decision flow, dashboard preview, deployment cards, configuration snippets, FAQ, and final CTA. Use stable `data-i18n` keys for every user-facing string and `data-i18n-aria` for translated accessible labels.

- [ ] **Step 3: Add content-accurate links and code examples**

Use canonical repository URLs, Docker image names from README, version `1.1.0`, MIT license wording, and concise Compose/`servers.json`/environment examples. Keep exhaustive configuration in README and link to it.

- [ ] **Step 4: Add keyboard-friendly controls**

Implement the language selector as a labeled `<select>` and FAQ entries as native `<details>/<summary>` elements. Ensure buttons/links have visible text and the dashboard preview is marked as illustrative where appropriate.

- [ ] **Step 5: Validate the static HTML structure**

Run `git diff --check` and inspect the file for duplicate IDs, missing section headings, empty links, and untranslated visible text.

- [ ] **Step 6: Commit the page skeleton**

Run:

```powershell
git add docs/index.html
git commit -m "feat: add showcase page structure"
```

### Task 2: Implement the visual system and responsive layout

**Files:**
- Create: `docs/styles.css`

**Interfaces:**
- Consumes: class names and structural hooks from `docs/index.html`.
- Produces: responsive layout, control-room visual language, dashboard mockup, focus states, and reduced-motion behavior.

- [ ] **Step 1: Define tokens and base styles**

Add CSS custom properties for navy surfaces, cyan/lime accents, warning red, text colors, spacing, radii, and shadows. Set system font fallbacks, `box-sizing`, body background, readable line height, and selection colors.

- [ ] **Step 2: Style the page hierarchy**

Implement header/nav, hero grid, trust strip, section headings, feature cards, decision-flow cards, deployment cards, code blocks, FAQ, and footer using grid/flex layouts with a desktop-first composition that collapses cleanly below 760px.

- [ ] **Step 3: Build the dashboard preview in CSS**

Style the static dashboard table, status pills, stat cards, progress bars, and deletion-highlight rows to echo the existing application UI while remaining readable on small screens via horizontal overflow or stacked cards.

- [ ] **Step 4: Add interaction and accessibility states**

Define `:focus-visible`, hover, active, disabled, high-contrast-safe borders, `prefers-reduced-motion`, and `prefers-color-scheme`-independent colors. Do not rely on color alone for deletion/keep meaning.

- [ ] **Step 5: Verify layout without a build step**

Run `git diff --check`; use a local static server if available and inspect at approximately 375px, 768px, and 1440px widths. Confirm no horizontal overflow outside the intentionally scrollable preview.

- [ ] **Step 6: Commit the visual system**

Run:

```powershell
git add docs/styles.css
git commit -m "feat: style showcase site"
```

### Task 3: Add bilingual content and progressive enhancement

**Files:**
- Create: `docs/site.js`
- Modify: `docs/index.html` only if translation hooks need correction

**Interfaces:**
- Consumes: `data-i18n`, `data-i18n-aria`, and `data-lang` hooks from the page.
- Produces: `window.TransmissionCleanerSite` with `setLanguage(language)` and a working default/Italian selector.

- [ ] **Step 1: Define the translation catalog**

Create `en` and `it` dictionaries covering every visible marketing, installation, FAQ, navigation, CTA, dashboard-preview, and accessible-label string. Keep code samples and product identifiers unchanged unless their surrounding explanation is translated.

- [ ] **Step 2: Implement safe text replacement**

On `DOMContentLoaded`, collect `[data-i18n]` elements and set `textContent`; collect `[data-i18n-aria]` elements and set the matching ARIA attribute. Never inject translated HTML with `innerHTML`.

- [ ] **Step 3: Implement language selection and persistence**

Use `localStorage` key `transmission-cleaner-language`, accept only `en` or `it`, default to `en`, update `document.documentElement.lang`, synchronize the selector, and expose `setLanguage` for testing/manual use. If storage access fails, keep the page usable for the current session.

- [ ] **Step 4: Test the language behavior manually**

Run the site through a local static server, switch EN → IT → EN, reload, and confirm the preference persists, all visible strings change, the document language changes, FAQ state remains usable, and English remains available when JavaScript is disabled.

- [ ] **Step 5: Commit bilingual behavior**

Run:

```powershell
git add docs/index.html docs/site.js
git commit -m "feat: add english italian site content"
```

### Task 4: Configure GitHub Pages deployment

**Files:**
- Create: `.github/workflows/pages.yml`

**Interfaces:**
- Consumes: committed `docs/` site assets.
- Produces: a GitHub Pages deployment artifact from `docs/` on site changes or manual dispatch.

- [ ] **Step 1: Define the workflow trigger and permissions**

Trigger on pushes to the repository’s deployment branch when `docs/**` or the workflow changes, plus `workflow_dispatch`. Grant only `contents: read`, `pages: write`, and `id-token: write`.

- [ ] **Step 2: Upload and deploy the Pages artifact**

Use checkout, `actions/configure-pages`, `actions/upload-pages-artifact` with `path: ./docs`, and `actions/deploy-pages`, with a single `github-pages` environment and deployment URL output.

- [ ] **Step 3: Validate workflow and scope**

Parse the YAML if a local YAML parser is available; otherwise inspect it structurally and run `git diff --check`. Confirm no existing workflow was modified and the artifact path is exactly `./docs`.

- [ ] **Step 4: Commit Pages configuration**

Run:

```powershell
git add .github/workflows/pages.yml
git commit -m "ci: deploy showcase with github pages"
```

### Task 5: Final verification and handoff

**Files:**
- Verify: `docs/index.html`, `docs/styles.css`, `docs/site.js`, `.github/workflows/pages.yml`, `.gitignore`

**Interfaces:**
- Consumes: all previous task outputs.
- Produces: evidence-backed readiness for PR review.

- [ ] **Step 1: Run existing application tests**

Run `pytest -q` from the repository root. Expected: all pre-existing tests pass with zero failures.

- [ ] **Step 2: Run static checks**

Run `git diff --check` and `rg -n "TBD|TODO|temporary-copy|lorem ipsum" docs/index.html docs/styles.css docs/site.js .github/workflows/pages.yml`. Expected: no whitespace errors and no temporary-copy matches.

- [ ] **Step 3: Perform browser-level smoke checks**

Serve `docs/` locally with `python -m http.server 4173 --directory docs`, inspect desktop/mobile layout, test all local/remote CTAs, switch languages, reload persistence, keyboard navigation, FAQ disclosure, and reduced motion.

- [ ] **Step 4: Check the final diff**

Run `git status --short`, `git log --oneline -5`, and `git diff main...HEAD --stat`. Confirm only the intended site, workflow, ignore-rule, and Superpowers planning artifacts are present.

- [ ] **Step 5: Report the PR handoff**

Provide the branch name, commits, verification results, and the suggested PR title/body. Do not merge or push unless explicitly requested.
