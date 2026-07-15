# Tal'Dorei Dossier Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an isolated, responsive Tal'Dorei Nights campaign-hub prototype with original heroic-occult artwork and player-facing session intelligence.

**Architecture:** A dependency-free static site separates structured campaign content from rendering and presentation. `content.js` exports immutable data, `app.js` renders only that data into semantic regions in `index.html`, and `styles.css` supplies the responsive visual system. A Node built-in test validates the content schema and rendered document structure without a browser framework.

**Tech Stack:** HTML5, CSS custom properties, vanilla ES modules, Node.js built-in test runner, original generated PNG artwork.

## Global Constraints

- Create and modify files only under `Website/taldorei-dossier-prototype/`; do not modify `Website/taldorei/` or `Website/striesara/`.
- Do not add external runtime dependencies, build tools, or remote fonts.
- Use original campaign-specific assets; do not recreate a specific existing game, magazine, or artist's style.
- Use campaign facts from `Campaign Dashboard.md` and `Last Session Quick Rundown.md` as player-facing copy.
- Provide visible keyboard focus, reduced-motion support, meaningful hero alt text, and mobile navigation without hover-only controls.

---

## File structure

| Path | Responsibility |
| --- | --- |
| `index.html` | Semantic page shell, navigation, empty data regions, and module entry point. |
| `styles.css` | Tokens, responsive layout, typography, visual treatments, and accessibility states. |
| `content.js` | Frozen structured data for status, brief, threats, party, and map annotations. |
| `app.js` | Escaped rendering helpers and module initialization. |
| `assets/shadebarrow-hero.png` | Original wide campaign hero artwork. |
| `assets/map-taldorei.png` | Prototype-local map copy for the evidence panel. |
| `tests/site.test.mjs` | Content-schema and static-document checks. |
| `package.json` | A single `test` command using Node's built-in test runner. |

### Task 1: Establish the isolated static-site contract

**Files:**
- Create: `Website/taldorei-dossier-prototype/package.json`
- Create: `Website/taldorei-dossier-prototype/tests/site.test.mjs`
- Create: `Website/taldorei-dossier-prototype/content.js`

**Interfaces:**
- Produces: `campaign` exported from `content.js` with `title`, `status`, `brief`, `powers`, `party`, and `map` fields.
- Produces: `npm test`, which executes `node --test tests/site.test.mjs`.

- [ ] **Step 1: Write the failing content-contract test**

```js
import assert from 'node:assert/strict';
import test from 'node:test';
import { campaign } from '../content.js';

test('campaign data provides the player-facing next-session brief', () => {
  assert.equal(campaign.title, 'Tal’Dorei Nights');
  assert.equal(campaign.brief.title, 'The road to Ebonroot');
  assert.match(campaign.brief.objective, /Shadebarrow/);
  assert.equal(campaign.powers.length, 4);
  assert.equal(campaign.party.length, 6);
});
```

- [ ] **Step 2: Add the test command and run it to verify failure**

```json
{
  "private": true,
  "type": "module",
  "scripts": { "test": "node --test tests/site.test.mjs" }
}
```

Run: `npm test` from `Website/taldorei-dossier-prototype`.

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `content.js`.

- [ ] **Step 3: Implement the smallest valid content module**

```js
export const campaign = Object.freeze({
  title: 'Tal’Dorei Nights',
  status: 'Year 1836 · Westruun → Ebonroot · Threat level: critical',
  brief: Object.freeze({
    title: 'The road to Ebonroot',
    objective: 'Reach the Shadebarrow before Blaine Kraverrogg and the Cult of Vecna.',
    consequence: 'Grai now carries the curse echoes: 4d10 psychic damage at the end of every long rest.',
    threat: 'Blaine likely holds the second family ring and knows the way to the iron gate.',
    route: 'Ride northeast from Westruun; find the split-tongue monolith, cross the mud, and reach the gate.'
  }),
  powers: Object.freeze([
    Object.freeze({ name: 'The Whispered Truth', detail: 'Vecna’s cult excavates the Orcus-sealed vault.', tone: 'violet' }),
    Object.freeze({ name: 'Graz’zt', detail: 'A demon prince walks the Prime Material beyond the divine gate.', tone: 'ember' }),
    Object.freeze({ name: 'Lolth', detail: 'The Spider Queen’s influence gathers beyond the rifts.', tone: 'ink' }),
    Object.freeze({ name: 'The Broken Weave', detail: 'Magic frays as interdimensional wounds widen.', tone: 'brass' })
  ]),
  party: Object.freeze([
    Object.freeze({ name: 'Anastasia “Ana” Ravenswood', role: 'Human artificer', mark: 'gear' }),
    Object.freeze({ name: 'Bohdi Shadowtwist', role: 'Bugbear sorcerer', mark: 'spark' }),
    Object.freeze({ name: 'Finnick Marigold Mossglow', role: 'Gnome illrigger', mark: 'blade' }),
    Object.freeze({ name: 'Grai Malin', role: 'Half-orc barbarian', mark: 'axe' }),
    Object.freeze({ name: 'Imdra d’Vadalis', role: 'Human druid', mark: 'branch' }),
    Object.freeze({ name: 'Ki Nightwhisper', role: 'Aarakocra bard', mark: 'wing' })
  ]),
  map: Object.freeze({ alt: 'Tal’Dorei map showing the route from Westruun northeast toward Ebonroot and the Shadebarrow.', caption: 'The road ends at a barrow no one visits and ever truly leaves.' })
});
```

- [ ] **Step 4: Run the test to verify success**

Run: `npm test` from `Website/taldorei-dossier-prototype`.

Expected: PASS with one passing subtest.

- [ ] **Step 5: Commit the isolated data contract**

```bash
git -C Website add taldorei-dossier-prototype/package.json taldorei-dossier-prototype/content.js taldorei-dossier-prototype/tests/site.test.mjs
git -C Website commit -m "feat: add dossier campaign content contract"
```

### Task 2: Build the semantic page shell and safe renderer

**Files:**
- Create: `Website/taldorei-dossier-prototype/index.html`
- Create: `Website/taldorei-dossier-prototype/app.js`
- Modify: `Website/taldorei-dossier-prototype/tests/site.test.mjs`

**Interfaces:**
- Consumes: `campaign` from `content.js`.
- Produces: `renderText(value)`, `renderPowers(items)`, and `renderParty(items)` in `app.js`.
- Produces: HTML regions with IDs `campaign-status`, `brief-title`, `brief-grid`, `powers-list`, and `party-list`.

- [ ] **Step 1: Extend the failing static-document test**

```js
import { readFile } from 'node:fs/promises';

test('page declares the dossier landmarks and module entry point', async () => {
  const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
  for (const id of ['campaign-status', 'brief-title', 'brief-grid', 'powers-list', 'party-list']) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
  assert.match(html, /<main/);
  assert.match(html, /<script type="module" src="app\.js"><\/script>/);
});
```

- [ ] **Step 2: Run the test to verify failure**

Run: `npm test` from `Website/taldorei-dossier-prototype`.

Expected: FAIL with `ENOENT` for `index.html`.

- [ ] **Step 3: Implement the semantic shell and renderer**

Use this minimum document structure:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Tal’Dorei Nights: player-facing campaign intelligence for the road to Ebonroot.">
  <title>Tal’Dorei Nights — The Road to Ebonroot</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <a class="skip-link" href="#brief">Skip to next-session brief</a>
  <header class="masthead"><a class="wordmark" href="#top">Tal’Dorei Nights</a><button class="nav-toggle" aria-expanded="false" aria-controls="site-nav">Menu</button><nav id="site-nav" aria-label="Prototype sections"><a href="#brief">Brief</a><a href="#powers">Powers</a><a href="#party">Party</a><a href="#route">Route</a></nav></header>
  <main id="top"><section class="hero" aria-labelledby="page-title"><img src="assets/shadebarrow-hero.png" alt="Six adventurers stand before the haunted Shadebarrow, its iron gate lit by candles beneath rifts in a storm-dark sky."><div class="hero-copy"><p id="campaign-status" class="eyebrow"></p><h1 id="page-title">Tal’Dorei Nights</h1><p>A race to an Orcus-sealed vault beneath a wounded sky.</p><a class="button" href="#brief">Read the next session brief</a></div></section><section id="brief" class="brief" aria-labelledby="brief-title"><p class="section-label">Current intelligence</p><h2 id="brief-title"></h2><div id="brief-grid" class="brief-grid"></div></section><section id="powers" aria-labelledby="powers-heading"><p class="section-label">Known powers</p><h2 id="powers-heading">What is moving in the dark</h2><div id="powers-list" class="powers-list"></div></section><section id="party" aria-labelledby="party-heading"><p class="section-label">The party</p><h2 id="party-heading">Six against the rift</h2><ul id="party-list" class="party-list"></ul></section><section id="route" class="route" aria-labelledby="route-heading"><img src="assets/map-taldorei.png" alt=""><div><p class="section-label">Field map</p><h2 id="route-heading">The route to the gate</h2><p id="map-caption"></p></div></section></main>
  <footer>Tal’Dorei Nights · player dossier prototype</footer>
  <script type="module" src="app.js"></script>
</body>
</html>
```

Implement rendering with `textContent`, never interpolated content into `innerHTML`:

```js
import { campaign } from './content.js';

const byId = (id) => document.getElementById(id);
const addText = (parent, tag, value) => { const node = document.createElement(tag); node.textContent = value; parent.append(node); return node; };

byId('campaign-status').textContent = campaign.status;
byId('brief-title').textContent = campaign.brief.title;
Object.entries(campaign.brief).filter(([key]) => key !== 'title').forEach(([key, value]) => { const article = document.createElement('article'); article.className = `brief-item brief-item--${key}`; addText(article, 'h3', key); addText(article, 'p', value); byId('brief-grid').append(article); });
campaign.powers.forEach(({ name, detail, tone }) => { const article = document.createElement('article'); article.className = `power power--${tone}`; addText(article, 'h3', name); addText(article, 'p', detail); byId('powers-list').append(article); });
campaign.party.forEach(({ name, role, mark }) => { const item = document.createElement('li'); item.dataset.mark = mark; addText(item, 'strong', name); addText(item, 'span', role); byId('party-list').append(item); });
byId('map-caption').textContent = campaign.map.caption;
document.querySelector('.nav-toggle').addEventListener('click', (event) => { const open = event.currentTarget.getAttribute('aria-expanded') === 'true'; event.currentTarget.setAttribute('aria-expanded', String(!open)); byId('site-nav').dataset.open = String(!open); });
```

- [ ] **Step 4: Run the tests to verify success**

Run: `npm test` from `Website/taldorei-dossier-prototype`.

Expected: PASS with the content-contract and static-document subtests.

- [ ] **Step 5: Commit the semantic page and renderer**

```bash
git -C Website add taldorei-dossier-prototype/index.html taldorei-dossier-prototype/app.js taldorei-dossier-prototype/tests/site.test.mjs
git -C Website commit -m "feat: add dossier page structure and renderer"
```

### Task 3: Create the original Shadebarrow key art and local map asset

**Files:**
- Create: `Website/taldorei-dossier-prototype/assets/shadebarrow-hero.png`
- Create: `Website/taldorei-dossier-prototype/assets/map-taldorei.png`
- Modify: `Website/taldorei-dossier-prototype/tests/site.test.mjs`

**Interfaces:**
- Produces: `shadebarrow-hero.png`, a wide hero image that contains no embedded text and preserves safe negative space for HTML copy.
- Produces: a prototype-local map image referenced by the page shell.

- [ ] **Step 1: Add the failing asset-reference test**

```js
test('page uses only prototype-local visual assets', async () => {
  const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
  assert.match(html, /src="assets\/shadebarrow-hero\.png"/);
  assert.match(html, /src="assets\/map-taldorei\.png"/);
  await Promise.all(['../assets/shadebarrow-hero.png', '../assets/map-taldorei.png'].map((path) => readFile(new URL(path, import.meta.url))));
});
```

- [ ] **Step 2: Run the test to verify failure**

Run: `npm test` from `Website/taldorei-dossier-prototype`.

Expected: FAIL with `ENOENT` for `assets/shadebarrow-hero.png`.

- [ ] **Step 3: Generate and add campaign-specific assets**

Generate an original 16:9 hero image using this brief:

> Original high-fantasy editorial illustration, weathered heroic occult mood. A wide cinematic scene at dusk: six distinct adventurers shown from behind in readable silhouette stand on a rain-dark heath before the haunted Shadebarrow. Include a human artificer with a brass device, a broad bugbear sorcerer with a faint arcane glow, a small gnome knight with a blade, a towering half-orc barbarian with a heavy weapon, a human druid with a branch or staff, and an aarakocra bard with folded wings and instrument. An ancient iron gate and candlelit stones sit in the barrow; a split-tongue monolith points toward the gate. Above them, a fractured storm sky contains distant purple interdimensional rifts and the faint silhouette of a flying ship. Painterly, richly textured, dangerous but resolutely heroic, dramatic moonlight and candlelight, no text, no logos, no watermark. Reserve darker negative space across the upper-left third for HTML title copy.

Copy `Website/taldorei/map-taldorei.png` to `Website/taldorei-dossier-prototype/assets/map-taldorei.png`; do not alter its source image.

- [ ] **Step 4: Run the tests to verify success**

Run: `npm test` from `Website/taldorei-dossier-prototype`.

Expected: PASS with three subtests.

- [ ] **Step 5: Commit the isolated visual assets**

```bash
git -C Website add taldorei-dossier-prototype/assets taldorei-dossier-prototype/tests/site.test.mjs
git -C Website commit -m "feat: add dossier campaign artwork"
```

### Task 4: Implement the responsive dossier visual system

**Files:**
- Create: `Website/taldorei-dossier-prototype/styles.css`
- Modify: `Website/taldorei-dossier-prototype/tests/site.test.mjs`

**Interfaces:**
- Consumes: semantic classes from `index.html` and data-state on `#site-nav` from `app.js`.
- Produces: desktop, narrow-screen, focus-visible, and reduced-motion styling.

- [ ] **Step 1: Add the failing stylesheet-contract test**

```js
test('stylesheet includes responsive, focus, and reduced-motion rules', async () => {
  const css = await readFile(new URL('../styles.css', import.meta.url), 'utf8');
  for (const rule of [':focus-visible', '@media (max-width: 720px)', '@media (prefers-reduced-motion: reduce)', '--ink', '--parchment']) {
    assert.ok(css.includes(rule), `missing ${rule}`);
  }
});
```

- [ ] **Step 2: Run the test to verify failure**

Run: `npm test` from `Website/taldorei-dossier-prototype`.

Expected: FAIL with `ENOENT` for `styles.css`.

- [ ] **Step 3: Implement the visual system**

Define the following token layer first:

```css
:root { --ink:#071016; --ink-raised:#0e1a21; --parchment:#e3d3ad; --brass:#c6a36a; --ember:#ae5140; --violet:#8f7bbb; --mist:#b7c1bb; --line:rgba(227,211,173,.22); --display:Georgia,serif; --body:ui-sans-serif,system-ui,sans-serif; }
* { box-sizing:border-box; }
body { margin:0; color:var(--parchment); background:radial-gradient(circle at 75% 0,rgba(89,65,111,.32),transparent 34rem),var(--ink); font-family:var(--body); line-height:1.55; }
:focus-visible { outline:3px solid #f0d388; outline-offset:4px; }
```

Then implement these specific behaviors:

- A maximum content width of 1200px with 24px minimum inline padding.
- A 64px masthead with an always-visible wordmark; desktop links inline, mobile links hidden unless `#site-nav[data-open="true"]`.
- A 16:9 hero capped at 720px tall; its image uses `object-fit:cover`; a bottom-to-top and left-to-right ink gradient protects the copy.
- The hero copy is limited to 680px and uses a responsive `clamp(2.8rem, 7vw, 6.5rem)` display title.
- The brief uses a four-column grid above 960px, two columns above 640px, and one column below 640px; objective receives a brass left border.
- Powers use a four-column grid that collapses to two and then one; their tone classes use only a border-top accent.
- The party is a six-cell grid with CSS-only role marks created using the `data-mark` attribute; do not add generic icons.
- The route panel is a two-column map/copy composition that stacks below 720px.
- All animation is omitted; the reduced-motion rule explicitly disables smooth scroll if a browser applies it.

- [ ] **Step 4: Run the tests to verify success**

Run: `npm test` from `Website/taldorei-dossier-prototype`.

Expected: PASS with four subtests.

- [ ] **Step 5: Commit the responsive visual system**

```bash
git -C Website add taldorei-dossier-prototype/styles.css taldorei-dossier-prototype/tests/site.test.mjs
git -C Website commit -m "feat: style responsive Tal'Dorei dossier"
```

### Task 5: Verify render behavior and preserve isolation

**Files:**
- Verify: `Website/taldorei-dossier-prototype/`

**Interfaces:**
- Consumes: the complete prototype directory.
- Produces: evidence that the prototype is self-contained, responsive, and does not depend on legacy website files.

- [ ] **Step 1: Ensure the final static references remain local**

The final `index.html` may reference only `styles.css`, `app.js`, and `assets/` paths. It must not contain `../taldorei/`, `../striesara/`, external font URLs, or remote image URLs.

- [ ] **Step 2: Run the full test suite and static checks**

Run:

```bash
npm test
rg -n "\.\./taldorei/|\.\./striesara/|https?://|flaming-donkey" index.html app.js styles.css content.js
git -C Website diff --check
```

Expected: all tests PASS; `rg` returns no matches; `git diff --check` has no output.

- [ ] **Step 3: Inspect desktop and mobile renders locally**

Serve only the prototype directory, open `index.html`, and inspect at 1440px and 390px widths. Confirm the hero copy remains readable, the menu can be opened by keyboard, the session objective is visible near the first screen, and the layout has no horizontal overflow.

- [ ] **Step 4: Commit the completed prototype**

```bash
git -C Website add taldorei-dossier-prototype
git -C Website commit -m "feat: build Tal'Dorei dossier prototype"
```
