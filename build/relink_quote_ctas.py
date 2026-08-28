#!/usr/bin/env python3
"""Point every Free Quote call-to-action at the Free Quote page.

Edits the .dc.html design sources in place (docs/ is generated from them, so
editing the build output would be undone by the next build). The Free Quote
page itself is skipped: its own buttons scroll to the form further down.
"""
import glob
import os
import re

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "project"))
TARGET = "Free Quote.dc.html"
SKIP = {"Free Quote.dc.html"}

# anchor text that means "take me to a quote form"
LABEL = re.compile(r"^\s*(?:Get a )?Free Quote\s*[↗➜→]?\s*$|^\s*Request Quote\s*$", re.I)
ANCHOR = re.compile(r'(<a\b[^>]*>)(.*?)(</a>)', re.S)
HREF = re.compile(r'href="([^"]*)"')


def relink(text):
    changed = []

    def repl(m):
        open_tag, inner, close = m.groups()
        if not LABEL.match(re.sub(r"<[^>]+>", "", inner)):
            return m.group(0)
        href = HREF.search(open_tag)
        if not href or href.group(1) == TARGET:
            return m.group(0)
        changed.append((href.group(1), inner.strip()))
        return HREF.sub(f'href="{TARGET}"', open_tag, count=1) + inner + close

    return ANCHOR.sub(repl, text), changed


def main():
    total = 0
    for path in sorted(glob.glob(os.path.join(SRC, "*.dc.html"))):
        name = os.path.basename(path)
        if name in SKIP:
            print(f"skip  {name}")
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        new, changed = relink(text)
        if not changed:
            print(f"  --  {name} (no quote CTAs)")
            continue
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
        froms = ", ".join(sorted({c[0] for c in changed}))
        print(f"{len(changed):3d}x  {name}  (was: {froms})")
        total += len(changed)
    print(f"\n{total} call-to-action links now point at the Free Quote page.")


if __name__ == "__main__":
    main()
