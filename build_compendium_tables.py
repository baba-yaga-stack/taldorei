#!/usr/bin/env python3
"""
build_compendium_tables.py — resolve Obsidian .base embeds into static HTML tables
and inject them into Website/compendium.html.

Why this exists:
  Obsidian Bases (.base files) are live database views over note frontmatter.
  They only render inside Obsidian, so the markdown->HTML export leaves their
  sections empty. This script reads the same frontmatter Obsidian uses, renders
  the tables, and injects them into the compendium.

Usage:
  python3 build_compendium_tables.py
  (run from anywhere; paths are resolved relative to this file)

Idempotent: rerunning replaces previously injected tables (marker comments).
"""

import os
import re
import sys
from pathlib import Path

import yaml

# The Website repo lives inside the D&D Campaign Management hub, alongside the
# Obsidian vaults: Taldorei/ and Striesara/ are siblings of Website/. Derive the
# vault from this file's location so it survives folder moves; override with
# TALDOREI_VAULT / STRIESARA_VAULT if a vault ever lives elsewhere.
WEBSITE = Path(__file__).resolve().parent
HUB = WEBSITE.parent

# Map: section header (as it appears in compendium.html, HTML-escaped) ->
#      (header tag, .base file relative to vault)
# All targets live inside the article id='party-quick-reference'.
# Both vaults use the same base names (System/Bases migration, June 2026).
INJECTIONS = [
    ("h2", "Combat Stats", "System/Bases/Party Stat Tracker.base"),
    ("h2", "Languages &amp; Abilities", "System/Bases/Party Abilities.base"),
    ("h2", "Party Wealth", "System/Bases/Party Gold Tracker.base"),
    ("h2", "Magic Items &amp; Equipment", "System/Bases/Magic Items Tracker.base"),
    ("h3", "Consumables", "System/Bases/Consumables Tracker.base"),
]

# Per-campaign configuration (extended to Striesara 2026-08-14 — Improvement
# Plan item 11). pc_items: the per-PC magic-item injection needs a
# "<h3>Magic Items</h3>" anchor in each PC article; the Striesara compendium's
# PC articles use hand-written "Equipment &amp; Inventory" sections instead,
# so per-PC injection stays Tal'Dorei-only until that structure exists.
CAMPAIGNS = [
    {
        "name": "taldorei",
        "vault": Path(os.environ.get("TALDOREI_VAULT", str(HUB / "Taldorei"))),
        # Output lives alongside this script (the Website repo), not in the vault.
        "compendium": WEBSITE / "taldorei" / "compendium.html",
        # Items hidden from the player-facing site (DM secrets). Edit as needed.
        "secret_items": {
            "Invisible Crown of Lolth",
            "Circlet of Barbed Vision (Exalted)",  # proper name of the Crown — still secret
            # Mind Lash is public knowledge (acquired openly, Session 6) — not listed here
        },
        "pc_items": True,
    },
    {
        "name": "striesara",
        "vault": Path(os.environ.get("STRIESARA_VAULT", str(HUB / "Striesara"))),
        "compendium": WEBSITE / "striesara" / "compendium.html",
        "secret_items": set(),  # none known for Striesara yet
        "pc_items": False,
    },
]

# Set per campaign in the __main__ loop; module-level so the existing helper
# functions keep their signatures.
VAULT = CAMPAIGNS[0]["vault"]
SECRET_ITEMS = CAMPAIGNS[0]["secret_items"]

# Folders never scanned for notes
EXCLUDE_DIRS = {".obsidian", ".trash", ".git", "Website", "System"}

COLUMN_LABELS = {
    "file.name": "Character",
    "passive_perception": "Passive Perception",
    "armor_class": "AC",
    "hit_points": "HP",
    "race": "Race",
    "class": "Class",
    "languages": "Languages",
    "gold": "Gold",
    "magic_items": "Magic Items",
    "level": "Level",
    "player": "Player",
    "initiative": "Initiative",
    "speed": "Speed",
    "proficiency_bonus": "Prof. Bonus",
}

WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def strip_wikilinks(text):
    return WIKILINK.sub(lambda m: m.group(2) or m.group(1).split("/")[-1], text)


def read_frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    try:
        fm = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def collect_notes():
    """All vault notes with frontmatter, as (name, frontmatter, folder)
    triples. folder is the note's parent dir relative to the vault, posix
    style, so base filters like file.folder == "Characters/PCs" can match."""
    notes = []
    for path in VAULT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        fm = read_frontmatter(path)
        if fm:
            folder = path.parent.relative_to(VAULT).as_posix()
            notes.append((path.stem, fm, "" if folder == "." else folder))
    return notes


def get_tags(fm):
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return [str(t) for t in tags]


def matches_filters(name, fm, folder, filters):
    """Supports the filter forms used by both vaults' .base files."""
    for cond in filters.get("and", []):
        cond = str(cond)
        m = re.match(r'file\.tags\.contains\("([^"]+)"\)', cond)
        if m:
            if m.group(1) not in get_tags(fm):
                return False
            continue
        m = re.match(r"(\w+)\.length > 0", cond)
        if m:
            val = fm.get(m.group(1))
            if not val:
                return False
            continue
        # file.folder == "Characters/PCs" (used by Striesara's bases)
        m = re.match(r'file\.folder\s*==\s*"([^"]+)"', cond)
        if m:
            if folder != m.group(1).strip("/"):
                return False
            continue
        # Unknown condition: fail closed so we never leak unintended rows
        print(f"  ! unsupported filter skipped row check: {cond}")
        return False
    return True


def render_value(field, value):
    if value is None:
        return "&mdash;"
    if isinstance(value, list):
        if field == "magic_items":
            value = [v for v in value if strip_wikilinks(str(v)) not in SECRET_ITEMS]
        parts = [strip_wikilinks(str(v)) for v in value if v is not None]
        out = ", ".join(p for p in parts if p.strip())
    else:
        out = strip_wikilinks(str(value))
    out = out.strip()
    if out in ("", "[TBD]", "TBD", "None"):
        return "&mdash;"
    return out.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") \
              .replace("&amp;mdash;", "&mdash;")


def render_table(base_rel, notes):
    base_path = VAULT / base_rel
    spec = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    view = next(v for v in spec["views"] if v.get("type") == "table")
    filters = view.get("filters") or {}
    columns = view.get("order") or ["file.name"]

    rows = []
    for name, fm, folder in sorted(notes, key=lambda n: n[0].lower()):
        if not matches_filters(name, fm, folder, filters):
            continue
        cells = []
        for col in columns:
            if col == "file.name":
                cells.append(name)
            else:
                cells.append(render_value(col, fm.get(col)))
        rows.append(cells)

    if not rows:
        return "<p><em>No matching records found in the vault.</em></p>"

    head = "".join(f"<th>{COLUMN_LABELS.get(c, c.replace('_', ' ').title())}</th>"
                   for c in columns)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"
                   for cells in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def inject(html, notes):
    # Work only inside the party-quick-reference article
    start = html.index("<article id='party-quick-reference'>")
    end = html.index("<article ", start + 1)
    article = html[start:end]

    for tag, header, base_rel in INJECTIONS:
        if not (VAULT / base_rel).exists():
            print(f"  ! base file missing, skipped: {base_rel}")
            continue
        marker_a = f"<!-- base:{base_rel} -->"
        marker_b = f"<!-- /base:{base_rel} -->"
        table = render_table(base_rel, notes)
        block = f"{marker_a}{table}{marker_b}"

        if marker_a in article:  # rerun: replace previous injection
            article = re.sub(
                re.escape(marker_a) + ".*?" + re.escape(marker_b),
                block, article, flags=re.S)
            print(f"  ~ refreshed: {header}")
        else:
            anchor = f"<{tag}>{header}</{tag}>"
            if anchor not in article:
                print(f"  ! header not found, skipped: {header}")
                continue
            article = article.replace(anchor, anchor + "\n" + block, 1)
            print(f"  + injected: {header}")

    return html[:start] + article + html[end:]


# ---------------------------------------------------------------------------
# Per-character magic item lists.
# Same source as the Party Quick Reference table: each PC note's
# magic_items: frontmatter, enriched with detail text from the note's
# body "Magic Items" section. SECRET_ITEMS are filtered here too.
# ---------------------------------------------------------------------------

PC_ITEMS_ANCHOR = re.compile(
    r"(<h3>Magic Items</h3>\s*)(<ul>.*?</ul>|<p>.*?</p>)", re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
BOLD = re.compile(r"\*\*(.+?)\*\*")
# Bookkeeping noise that shouldn't appear on the player site
SYNC_NOISE = re.compile(
    r"\s*(?:[—–-]\s*)?Logged from character sheet sync[^.;]*[.;]?",
    re.I)


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def norm(text):
    return re.sub(r"[^a-z0-9]+", "", strip_wikilinks(str(text)).lower())


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def md_to_html(text, anchor_ids):
    """Minimal markdown -> HTML for item text (comments, escaping,
    wikilinks -> in-page anchors where a matching article exists, bold)."""
    out = esc(HTML_COMMENT.sub("", text).strip())

    def link(m):
        target = m.group(1).split("/")[-1]
        label = m.group(2) or target
        slug = slugify(target.replace("&amp;", "&"))
        if slug in anchor_ids:
            return f'<a href="#{slug}">{label}</a>'
        return label

    out = WIKILINK.sub(link, out)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    return out.replace("—", "&mdash;")


def parse_body_items(body):
    """(original, name, detail) for each bullet under the note's
    'Magic Items' body heading."""
    m = re.search(r"^#{2,3} Magic Items\s*$(.*?)(?=^#{1,3} |\Z)",
                  body, re.M | re.S)
    if not m:
        return []
    bullets = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        text = HTML_COMMENT.sub("", line[2:]).strip()
        if not text:
            continue
        bold = re.match(r"\*\*(.+?)\*\*\s*", text)
        if bold:
            name = strip_wikilinks(bold.group(1)).strip()
            detail = text[bold.end():].lstrip(" —–-:").strip()
        else:
            for sep in (" — ", " - "):
                if sep in text:
                    name, detail = (s.strip() for s in text.split(sep, 1))
                    name = strip_wikilinks(name)
                    break
            else:
                name, detail = strip_wikilinks(text).strip(), ""
        bullets.append((text, name, detail))
    return bullets


def render_pc_items(fm, body, anchor_ids):
    listed = fm.get("magic_items") or []
    if isinstance(listed, str):
        listed = [listed]
    bullets = parse_body_items(body)
    used = set()
    lis = []

    for item in listed:
        plain = strip_wikilinks(str(item)).strip()
        if plain in SECRET_ITEMS:
            continue
        orig = detail = ""
        for i, (borig, bname, bdetail) in enumerate(bullets):
            if i in used or not norm(bname):
                continue
            if norm(bname) in norm(plain) or norm(plain) in norm(bname):
                used.add(i)
                orig, detail = borig, bdetail
                break
        detail = SYNC_NOISE.sub("", detail).strip(" —–-;")
        orig = SYNC_NOISE.sub("", orig).strip(" —–-;")
        if norm(detail) and norm(detail) in norm(plain):
            detail = ""  # detail merely repeats a qualifier in the name
        if detail:
            lis.append(f"<li><strong>{esc(plain)}</strong> &mdash; "
                       f"{md_to_html(detail, anchor_ids)}</li>")
        elif orig and len(norm(orig)) > len(norm(plain)):
            # body bullet carries extra context the frontmatter name lacks
            lis.append(f"<li>{md_to_html(orig, anchor_ids)}</li>")
        else:
            lis.append(f"<li><strong>{esc(plain)}</strong></li>")

    # Body-only bullets (notes/quasi-items kept in the same PC file)
    for i, (borig, bname, bdetail) in enumerate(bullets):
        if i in used or strip_wikilinks(bname).strip() in SECRET_ITEMS:
            continue
        text = SYNC_NOISE.sub("", borig).strip(" —–-;")
        if text:
            lis.append(f"<li>{md_to_html(text, anchor_ids)}</li>")

    if not lis:
        return "<p><em>No magic items recorded.</em></p>"
    return "<ul>" + "".join(lis) + "</ul>"


def inject_pc_items(html, pcs):
    anchor_ids = set(re.findall(r"<article id='([^']+)'>", html))
    for name, fm, body in pcs:
        slug = slugify(name)
        try:
            start = html.index(f"<article id='{slug}'>")
        except ValueError:
            print(f"  ! no article for PC, skipped: {name}")
            continue
        end = html.index("<article ", start + 1)
        article = html[start:end]

        marker_a = f"<!-- pc-items:{slug} -->"
        marker_b = f"<!-- /pc-items:{slug} -->"
        block = marker_a + render_pc_items(fm, body, anchor_ids) + marker_b

        if marker_a in article:  # rerun: replace previous injection
            article = re.sub(
                re.escape(marker_a) + ".*?" + re.escape(marker_b),
                lambda m: block, article, flags=re.S)
            print(f"  ~ refreshed items: {name}")
        else:  # first run: replace the hand-written list/placeholder
            m = PC_ITEMS_ANCHOR.search(article)
            if not m:
                print(f"  ! Magic Items section not found, skipped: {name}")
                continue
            article = article[:m.start(2)] + block + article[m.end(2):]
            print(f"  + injected items: {name}")

        html = html[:start] + article + html[end:]
    return html


def collect_pcs():
    """PC notes as (name, frontmatter, full text) triples."""
    pcs = []
    for path in VAULT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        fm = read_frontmatter(path)
        if fm and "pc" in get_tags(fm):
            pcs.append((path.stem, fm, path.read_text(encoding="utf-8")))
    return pcs


if __name__ == "__main__":
    for campaign in CAMPAIGNS:
        VAULT = campaign["vault"]
        SECRET_ITEMS = campaign["secret_items"]
        compendium = campaign["compendium"]
        print(f"\n=== {campaign['name']} ===")
        if not VAULT.exists():
            print(f"  ! vault not found at {VAULT}, skipped")
            continue
        notes = collect_notes()
        pc_count = sum(1 for _, fm, _f in notes if "pc" in get_tags(fm))
        print(f"Scanned {len(notes)} notes with frontmatter ({pc_count} tagged pc)")
        html = compendium.read_text(encoding="utf-8")
        updated = inject(html, notes)
        if campaign["pc_items"]:
            updated = inject_pc_items(updated, collect_pcs())
        compendium.write_text(updated, encoding="utf-8")
        print(f"Wrote {compendium.name} ({len(updated):,} bytes)")
