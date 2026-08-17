#!/usr/bin/env python3
"""
build_compendium_articles.py — generate compendium articles for vault notes
that don't have one yet, and inject them into taldorei/compendium.html.

Why this exists:
  The compendium's articles were exported from Obsidian once and have been
  hand-maintained since. Notes written after that export never appeared on the
  site: as of 2026-08-15 that was 30 NPC and location notes, including most of
  Session 78. This script closes that gap and keeps it closed, so "every
  location and NPC we encounter" gets an entry.

What it will and will not touch:
  ADDITIVE ONLY. Generated articles are wrapped in <!-- gen:slug --> markers.
  A rerun replaces only marked blocks. Hand-authored articles are never read,
  rewritten, or reordered. If you hand-edit a generated article, delete its
  markers and this script will leave it alone forever after.

Safety:
  Vault sections listed in BLOCKED_SECTIONS (DM Notes, unrevealed mysteries,
  secrets) are never published. See Runbooks/Website Publish.md — the site
  carries group-recorded knowledge only.

Usage:
  python3 build_compendium_articles.py            # write
  python3 build_compendium_articles.py --dry-run  # report only, no write

Run it before build_compendium_tables.py, then commit both files together.
"""

import argparse
import re
import sys
from pathlib import Path

# Reuse the table builder's vault plumbing so both scripts agree on paths,
# frontmatter parsing, slugs, and escaping.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_compendium_tables import (  # noqa: E402
    HTML_COMMENT,
    WIKILINK,
    esc,
    read_frontmatter,
    slugify,
    strip_wikilinks,
)

WEBSITE = Path(__file__).resolve().parent
HUB = WEBSITE.parent
VAULT = HUB / "Taldorei"
COMPENDIUM = WEBSITE / "taldorei" / "compendium.html"

EXCLUDE_DIRS = {".obsidian", ".trash", ".git", "Website", "System"}

# Vault notes that are templates or utility indexes, not campaign entities.
SKIP_NOTES = {"Regional Maps"}
SKIP_PREFIXES = ("Example ",)

# Never published. The site is player-facing and reflects group-recorded
# knowledge only; these headings hold DM-side or unrevealed material.
BLOCKED_SECTIONS = {
    "dm notes",
    "secrets & hidden information",
    "secrets and hidden information",
    "mysteries / open questions",
    "mysteries/open questions",
    "open questions",
}

# Vault bookkeeping headings: real content, but meaningless to a reader.
SKIP_SECTIONS = {"quick reference", "map", "session history"}

# Which compendium section a note belongs to, decided by its tags.
# (tag, section id, singular label used in log output)
ROUTES = [
    ("npc", "cat-people-of-taldorei-npcs", "NPC"),
    ("location", "cat-locations", "location"),
]

# Frontmatter -> meta line, in display order, per route.
META_FIELDS = {
    "npc": [
        ("race", "Race"),
        ("occupation", "Occupation"),
        ("status", "Status"),
        ("affiliation", "Affiliation"),
        ("faction", "Affiliation"),
        ("location", "Location"),
        ("first_met", "First met"),
    ],
    "location": [
        ("location_type", "Type"),
        ("status", "Status"),
        ("region", "Region"),
        ("first_visited", "First visited"),
    ],
}

EMPTY_VALUES = {"", "none", "unknown", "[tbd]", "tbd", "n/a", "-"}


# ---------------------------------------------------------------------------
# vault reading
# ---------------------------------------------------------------------------


def get_tags(fm):
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return [str(t).lower() for t in tags]


def collect_notes():
    """(name, frontmatter, body, tags) for every taggable vault note."""
    out = []
    for path in sorted(VAULT.rglob("*.md")):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        name = path.stem
        if name in SKIP_NOTES or name.startswith(SKIP_PREFIXES):
            continue
        fm = read_frontmatter(path)
        if not fm:
            continue
        text = path.read_text(encoding="utf-8")
        body = text[text.find("\n---", 3) + 4:]
        out.append((name, fm, body, get_tags(fm)))
    return out


# ---------------------------------------------------------------------------
# markdown -> compendium HTML
# ---------------------------------------------------------------------------

BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<![\*\w])\*([^\*\n]+?)\*(?!\*)")
EMBED = re.compile(r"!\[\[[^\]]+\]\]")
MDIMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def inline(text, anchors):
    """Escape, then re-add the inline markup the compendium uses."""
    text = EMBED.sub("", MDIMG.sub("", text))
    out = esc(text.strip())

    def link(m):
        target = m.group(1).split("/")[-1].split("#")[0].strip()
        label = m.group(2) or target
        slug = slugify(target.replace("&amp;", "&"))
        if slug in anchors:
            return f'<a href="#{slug}">{esc(label)}</a>'
        # No article to point at (session notes, lore stubs). Plain text, so we
        # don't nest <strong> inside the note's own ** ** emphasis.
        return esc(label)

    out = WIKILINK.sub(link, out)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    out = ITALIC.sub(r"<em>\1</em>", out)
    return out.replace("—", "&mdash;").replace("–", "&ndash;")


def unwrap_comments(body):
    """The vault keeps published asides inside <!-- --> so Obsidian hides them
    (see Blaine Kraverrogg, Camilla Tenver — both render as plain paragraphs on
    the site today). Unwrap them so this script matches that convention."""
    return HTML_COMMENT.sub(lambda m: m.group(0)[4:-3].strip(), body)


def split_sections(body):
    """[(heading or None, [lines])] — a leading None section holds any prose
    that appears before the first heading (Thistle Farmstead does this)."""
    sections, heading, buf = [], None, []
    for line in body.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            continue  # the note's H1 duplicates the article title
        m = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if m:
            sections.append((heading, buf))
            heading, buf = m.group(2), []
        else:
            buf.append(line)
    sections.append((heading, buf))
    return [(h, b) for h, b in sections if h is not None or any(x.strip() for x in b)]


def render_block(lines, anchors):
    """Bullets -> <ul>, everything else -> <p>. Blockquotes are dropped: the
    vault uses them for stub banners and maintenance notes."""
    html, bullets, para = [], [], []

    def flush_para():
        if para:
            text = inline(" ".join(para).strip(), anchors)
            if text:
                html.append(f"<p>{text}</p>")
            para.clear()

    def flush_bullets():
        if bullets:
            items = "\n".join(f"<li>{b}</li>" for b in bullets if b)
            if items:
                html.append(f"<ul>\n{items}\n</ul>")
            bullets.clear()

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_para()
            continue
        if stripped.startswith(">"):
            continue
        if stripped.startswith("|") or set(stripped) <= set("-| "):
            continue  # markdown tables are handled by the table builder
        m = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if m:
            flush_para()
            item = inline(m.group(1), anchors)
            if item:
                bullets.append(item)
            continue
        flush_bullets()
        para.append(stripped)

    flush_para()
    flush_bullets()
    return "\n".join(html)


def render_meta(fm, route, anchors):
    parts = []
    seen = set()
    for field, label in META_FIELDS[route]:
        if label in seen:
            continue
        val = fm.get(field)
        if isinstance(val, list):
            val = ", ".join(str(v) for v in val if v is not None)
        if val is None:
            continue
        val = str(val).strip()
        # "[Unknown]" and friends are placeholders the vault uses for gaps.
        probe = strip_wikilinks(val).strip().strip("[]").lower()
        if probe in EMPTY_VALUES:
            continue
        parts.append(f"<b>{label}:</b> {inline(val, anchors)}")
        seen.add(label)
    if not parts:
        return ""
    return '<p class="meta">' + " &middot; ".join(parts) + "</p>"


def render_portrait(fm, name):
    """Emit the article's art from a `portrait:` frontmatter field.

    Hand-placing an <img> inside a generated article does not survive, because
    main() strips every gen block before rebuilding. Driving it from the vault
    note is what makes the art durable.

        portrait: portraits/lyra-finch.jpg   square, gold ring (.pcart)
        portrait: scenes/lyra-finch.jpg      wide, keeps its aspect (.locart)

    The directory picks the treatment. The full-size file the viewer opens is
    assumed to sit in a `full/` subfolder alongside, matching the convention
    already used by the party portraits.
    """
    val = fm.get("portrait")
    if isinstance(val, list):
        val = val[0] if val else None
    if val is None:
        return ""
    web = strip_wikilinks(str(val)).strip().strip("[]").strip()
    if not web or web.lower() in EMPTY_VALUES:
        return ""
    web = web.lstrip("/")
    parent, _, filename = web.rpartition("/")
    full = f"{parent}/full/{filename}" if parent else f"full/{filename}"
    square = web.startswith("portraits/")
    cls = "pcart" if square else "locart"
    wide = "" if square else " data-wide"
    alt = esc(f"Portrait of {name}" if square else name)
    return (f'<a class="artlink"{wide} href="{esc(full)}" target="_blank" '
            f'rel="noopener" title="View full size">'
            f'<img class="{cls}" src="{esc(web)}" alt="{alt}" loading="lazy"></a>')


def render_article(name, fm, body, route, anchors):
    slug = slugify(name)
    chunks = []
    blocked = []
    for heading, lines in split_sections(unwrap_comments(body)):
        if heading is None:
            block = render_block(lines, anchors)
            if block:
                chunks.append("<h2>Description</h2>\n" + block)
            continue
        key = heading.strip().lower()
        if key in BLOCKED_SECTIONS:
            blocked.append(heading)
            continue
        if key in SKIP_SECTIONS:
            continue
        block = render_block(lines, anchors)
        if not block:
            continue
        label = "Description" if key == "overview" else heading
        chunks.append(f"<h2>{esc(label)}</h2>\n{block}")

    if not chunks:
        return None, blocked

    meta = render_meta(fm, route, anchors)
    art = render_portrait(fm, name)
    head = f"<article id='{slug}'><h3 class='title'>{esc(name)}</h3>{art}{meta}"
    tail = "<p class='top'><a href='#tw'>&uarr; top</a></p></article>"
    inner = "\n".join(chunks)
    # First heading rides on the opening tag, matching the exported articles.
    if inner.startswith("<h2>"):
        cut = inner.index("\n")
        head += inner[:cut]
        inner = inner[cut + 1:]
    article = f"{head}\n{inner}{tail}"
    return f"<!-- gen:{slug} -->{article}<!-- /gen:{slug} -->\n", blocked


# ---------------------------------------------------------------------------
# injection
# ---------------------------------------------------------------------------

GEN_BLOCK = re.compile(r"<!-- gen:([a-z0-9-]+) -->.*?<!-- /gen:\1 -->\n?", re.S)


def section_bounds(html, section_id):
    start = html.index(f"<section class='cat' id='{section_id}'>")
    end = html.index("</section>", start)
    return start, end


def insert_article(html, section_id, slug, block):
    """Alphabetical by id within the section. Existing articles keep their
    positions; we only choose where the new one lands."""
    start, end = section_bounds(html, section_id)
    body = html[start:end]

    existing = [(m.group(1), m.start()) for m in
                re.finditer(r"<article id='([^']+)'>", body)]
    at = None
    for aid, pos in existing:
        if aid > slug:
            at = pos
            break
    if at is None:
        at = body.rindex("</article>") + len("</article>") + 1
        body = body[:at] + block + body[at:]
    else:
        body = body[:at] + block + body[at:]
    return html[:start] + body + html[end:]


def toc_bounds(html, label):
    marker = f"<summary>{label} ("
    i = html.index(marker)
    j = html.index("</ul>", i)
    return i, j


def rebuild_toc(html, section_id, label):
    """Rewrite one TOC list from the section's actual article order, so the
    list, the (N) in the summary, and the nav card can never drift apart."""
    start, end = section_bounds(html, section_id)
    body = html[start:end]
    entries = []
    for m in re.finditer(
            r"<article id='([^']+)'><h3 class='title'>(.*?)</h3>", body, re.S):
        entries.append((m.group(1), m.group(2)))
    entries.sort(key=lambda e: e[1].lower())

    items = "\n".join(
        f"<li><a href='#{aid}'>{title}</a></li>" for aid, title in entries)
    i, j = toc_bounds(html, label)
    new = f"<summary>{label} ({len(entries)})</summary><ul>\n{items}\n"
    html = html[:i] + new + html[j:]

    # nav card count
    html = re.sub(
        r'(compendium\.html#' + re.escape(section_id) + r'">[^<]*<span class="ct">)\d+',
        lambda m: m.group(1) + str(len(entries)), html)
    return html, len(entries)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; write nothing")
    args = ap.parse_args()

    html = COMPENDIUM.read_text(encoding="utf-8")
    original = html

    # Drop previously generated blocks so a rerun is a clean regeneration.
    regenerated = set(GEN_BLOCK.findall(html))
    html = GEN_BLOCK.sub("", html)

    hand_authored = set(re.findall(r"<article id='([^']+)'>", html))
    notes = collect_notes()
    # Only link to slugs that will actually exist as an article. Session notes
    # and untagged lore live in the vault but never get a compendium entry, so
    # linking them would manufacture dead anchors.
    will_generate = {slugify(n) for n, _f, _b, t in notes
                     if any(r[0] in t for r in ROUTES)}
    anchors = hand_authored | will_generate

    added, skipped, blocked_report = [], [], []
    for name, fm, body, tags in notes:
        route = next((r for r in ROUTES if r[0] in tags), None)
        if not route:
            continue
        _tag, section_id, kind = route
        slug = slugify(name)
        if slug in hand_authored:
            continue
        article, blocked = render_article(name, fm, body, _tag, anchors)
        if blocked:
            blocked_report.append((name, blocked))
        if not article:
            skipped.append((name, kind, "no publishable content"))
            continue
        html = insert_article(html, section_id, slug, article)
        added.append((name, kind, slug in regenerated))

    counts = {}
    for _tag, section_id, _kind in ROUTES:
        label = {"cat-people-of-taldorei-npcs": "People of Taldorei (NPCs)",
                 "cat-locations": "Locations"}[section_id]
        html, n = rebuild_toc(html, section_id, label)
        counts[label] = n

    new = [a for a in added if not a[2]]
    print(f"generated {len(added)} articles "
          f"({len(new)} new, {len(added) - len(new)} refreshed)")
    for name, kind, was in sorted(new):
        print(f"  + {kind:8} {name}")
    for label, n in counts.items():
        print(f"  = {label}: {n}")
    for name, sections in blocked_report:
        print(f"  ! withheld from {name}: {', '.join(sections)}")
    for name, kind, why in skipped:
        print(f"  ! skipped {kind} {name}: {why}")

    if args.dry_run:
        print("dry run, nothing written")
        return
    if html == original:
        print("no change")
        return
    COMPENDIUM.write_text(html, encoding="utf-8")
    print(f"wrote {COMPENDIUM.name} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
