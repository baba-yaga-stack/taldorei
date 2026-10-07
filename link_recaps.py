#!/usr/bin/env python3
"""
link_recaps.py - link compendium entries mentioned in Tal'Dorei session recaps.

For each recap article in taldorei/sessions.html, the FIRST mention of anything
that has a compendium entry becomes a link to it (compendium.html#slug).
Later mentions in the same recap stay plain text so the page doesn't turn blue.

Usage (run from anywhere; paths resolve relative to this file):
  python3 link_recaps.py              # newest recap only
  python3 link_recaps.py 81 80        # specific sessions
  python3 link_recaps.py --all        # every recap
  add --dry-run to print the links without writing

Rules:
  - Text inside headings (h1-h4), the meta line, existing links, and tag attributes is never touched.
  - Longest names win (Cult of Vecna is linked before Vecna can match inside it).
  - Idempotent: a recap that already links an entry is skipped for that entry.
  - Names are matched case-sensitively, except a leading "The" (the Dark Gardens).
Run build_compendium_articles.py first so new people and places have entries.
"""
import html
import re
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parent / "taldorei"
SESSIONS = WEB / "sessions.html"
COMPENDIUM = WEB / "compendium.html"

# Short names and alternate phrasings used in recaps -> compendium id.
ALIASES = {
    "Ana": "anastasia-ravenswood",
    "Bohdi": "bohdi-shadowtwist",
    "Finn": "finnick-marigold-mossglow",
    "Grai": "grai-malin",
    "Ki": "ki-nightwhisper",
    "Imdra": "imdra-d-vadalis",
    "Camellia": "camellia-springshower",
    "failed garden": "the-dark-gardens",
    "dead garden": "the-dark-gardens",
    "dreaming garden": "the-dark-gardens",
}
# Entry titles too generic to auto-link.
SKIP_TITLES = {"Library"}
# Compendium sections whose entries are reference pages, not things named in play.
SKIP_SECTIONS = {"cat-quick-reference"}

SKIP_TAGS = {"a", "h1", "h2", "h3", "h4", "script", "style"}
TOKEN = re.compile(r"(<[^>]+>)")


def load_entries():
    c = COMPENDIUM.read_text(encoding="utf-8")
    sections = [(m.start(), m.group(1)) for m in re.finditer(r"id='(cat-[^']+)'", c)]
    names = {}
    for m in re.finditer(r"<article id='([^']+)'><h3 class='title'>(.*?)</h3>", c):
        sec = [s for p, s in sections if p < m.start()]
        if sec and sec[-1] in SKIP_SECTIONS:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        if title in SKIP_TITLES:
            continue
        names.setdefault(title, m.group(1))
        if title.startswith("The "):
            names.setdefault("the " + title[4:], m.group(1))
    for k, v in ALIASES.items():
        names.setdefault(k, v)
    valid = set(re.findall(r"<article id='([^']+)'", c))
    return {n: i for n, i in names.items() if i in valid}


def link_article(art, entries):
    """Link the earliest mention of each entry, trying all of its names."""
    by_slug = {}
    for name, slug in entries.items():
        by_slug.setdefault(slug, []).append(name)
    # Entries with longer names go first, so "Cult of Vecna" claims its text
    # before "Vecna" could match inside it.
    order = sorted(by_slug, key=lambda g: max(len(n) for n in by_slug[g]), reverse=True)
    containers = {
        g: [html.escape(o, quote=False) for o in entries
            if entries[o] != g and any(n in o and n != o for n in by_slug[g])]
        for g in by_slug
    }
    made = []
    for slug in order:
        if f'compendium.html#{slug}"' in art:
            continue
        pats = [(n, re.compile(r"(?<![\w'&#-])" + re.escape(html.escape(n, quote=False)) + r"(?![\w-])"))
                for n in by_slug[slug]]
        parts = TOKEN.split(art)
        stack = []
        for idx, part in enumerate(parts):
            if part.startswith("<"):
                m = re.match(r"<(/?)(\w+)", part)
                if m and m.group(2).lower() == "p":
                    # The meta line (date, chapter) is a header, not prose.
                    if not m.group(1) and 'class="meta"' in part:
                        stack.append("p")
                    elif m.group(1) and stack and stack[-1] == "p":
                        stack.pop()
                elif m and m.group(2).lower() in SKIP_TAGS:
                    if m.group(1):
                        if stack:
                            stack.pop()
                    elif not part.endswith("/>"):
                        stack.append(m.group(2).lower())
                continue
            if stack:
                continue
            # Hide longer entry names that contain this one ("Vecna" inside
            # "Cult of Vecna"), so a short name never matches inside a long one.
            masked = part
            for longer in containers[slug]:
                masked = masked.replace(longer, "\0" * len(longer))
            hits = [(h.start(), n, h) for n, pat in pats for h in [pat.search(masked)] if h]
            if hits:
                _, name, hit = min(hits, key=lambda x: x[0])
                parts[idx] = (part[:hit.start()] + f'<a href="compendium.html#{slug}">'
                              + hit.group(0) + "</a>" + part[hit.end():])
                art = "".join(parts)
                made.append((name, slug))
                break
    return art, made


def main(argv):
    dry = "--dry-run" in argv
    args = [a for a in argv if not a.startswith("--")]
    s = SESSIONS.read_text(encoding="utf-8")
    starts = [(m.start(), int(m.group(1))) for m in re.finditer(r"<article id='session-(\d+)'", s)]
    if "--all" in argv:
        wanted = {n for _, n in starts}
    elif args:
        wanted = {int(a) for a in args}
    else:
        wanted = {max(n for _, n in starts)}
    entries = load_entries()
    out, last = [], 0
    for i, (pos, num) in enumerate(starts):
        end = s.find("</article>", pos) + len("</article>")
        out.append(s[last:pos])
        art = s[pos:end]
        if num in wanted:
            art, made = link_article(art, entries)
            print(f"Session {num}: {len(made)} links" + "".join(f"\n  {n} -> #{g}" for n, g in made))
        out.append(art)
        last = end
    out.append(s[last:])
    new = "".join(out)
    if dry:
        print("dry run, nothing written")
    elif new != s:
        SESSIONS.write_text(new, encoding="utf-8")
        print("wrote sessions.html")
    else:
        print("no change")


if __name__ == "__main__":
    main(sys.argv[1:])
