# Tal'Dorei Dossier Prototype — Design

## Purpose

Build a new, standalone Tal'Dorei Nights player-reference prototype without modifying the existing website. The prototype should feel like a weathered heroic-occult campaign dossier: dramatic and dangerous, but clear enough to use at the table.

## Scope

The prototype lives entirely in `Website/taldorei-dossier-prototype/`. Its first release is one responsive campaign-hub page and its local assets. It does not alter, import, or replace any current page under `Website/taldorei/`.

## Audience and success criteria

Returning players should understand the immediate situation within one screen:

- The party is traveling from Westruun toward Ebonroot and the Shadebarrow.
- The immediate objective is to reach the iron gate before Blaine Kraverrogg and the Cult of Vecna.
- Recent consequences include Grai's curse echoes and Blaine possessing the second family ring.
- The campaign is threatened by cult activity, a demon prince, fractured magic, and interdimensional rifts.

The finished page must feel specific to this campaign rather than like a generic fantasy UI, and it must remain legible on mobile.

## Visual direction

The visual language is **weathered heroic occult fantasy**:

- A near-black blue-green ground with aged parchment, muted brass, ember-red, and cold violet accents.
- One original, painterly hero scene: six race/class-readable party silhouettes at the haunted Shadebarrow. Candlelight and an iron gate establish the foreground; rifts and the campaign's wider cosmic stakes appear in the sky.
- An editorial serif carries the campaign voice; a practical sans-serif carries reference information.
- Ornament is meaningful: map contours, evidence seals, wax, ink, and faction marks. Avoid generic fantasy glyphs, excessive glow, decorative SVG mascots, and dense card grids.

## Page structure

1. **Masthead** — compact title and campaign navigation.
2. **Hero** — original Shadebarrow artwork, campaign title, premise, and a single primary action.
3. **Next-session brief** — the road to Ebonroot: objective, last-session consequence, current threat, and route.
4. **Known powers** — brief cards for the Cult of Vecna, Graz'zt, Lolth, and the broken Weave.
5. **Party roster** — compact entries with distinct race/class silhouettes and roles.
6. **Evidence map** — a map crop and concise route/mission annotations.
7. **Archive footer** — restrained links/placeholders for eventual sessions, compendium, and map pages.

## Content model

A small local data module holds campaign content separately from layout. It provides the masthead status, the next-session brief, known powers, party entries, and map annotations. Facts are copied from player-facing vault notes, chiefly the Campaign Dashboard and Last Session Quick Rundown. The existing pages are not used as dependencies.

## Files and responsibilities

- `index.html`: semantic page structure and data-module inclusion.
- `styles.css`: design tokens, responsive layout, typography, accessibility, and motion preferences.
- `content.js`: the player-facing campaign data rendered by the page.
- `app.js`: safe rendering of structured local data into marked page regions.
- `assets/`: original generated hero artwork and map derivative used only by the prototype.
- `tests/`: static structure/content checks runnable without a browser framework.

## Accessibility and responsive behavior

- Text/background contrast must remain readable; artwork receives a protective gradient behind copy.
- Keyboard focus states are visible and links work without hover-only behavior.
- Navigation collapses into a compact disclosure control on narrow screens.
- Reduced-motion users see no decorative animation.
- The hero has meaningful alt text; purely decorative flourishes are hidden from assistive technology.

## Validation

Before delivery, run the static tests, verify local page links and rendered content, and inspect the page at desktop and mobile viewports. Confirm that the prototype directory is the only new website directory touched.

## Out of scope

- Changes to the existing Tal'Dorei or Striesara sites.
- A full compendium, session archive, authentication, CMS, or deployment configuration.
- Exact recreation of any existing fantasy game, magazine, or individual artist's visual style.
