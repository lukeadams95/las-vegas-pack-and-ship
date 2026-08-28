#!/usr/bin/env python3
"""Convert the Claude Design .dc.html handoff into a plain static site.

Strips the Design Components runtime (x-dc / helmet / sc-if / {{ bindings }} /
image-slot) and emits standard HTML that renders identically with nothing but
site.css + site.js.
"""
import base64
import html
import json
import os
import re
import shutil
import struct

SRC = os.path.join(os.path.dirname(__file__), "..", "project")
OUT = os.path.join(os.path.dirname(__file__), "..", "docs")
SRC = os.path.abspath(SRC)
OUT = os.path.abspath(OUT)

# design file (without .dc.html)  ->  published filename
PAGES = {
    "Las Vegas Pack and Ship": "index.html",
    "Local Packing and Shipping Store": "local-packing-and-shipping-store.html",
    "Electronic Packing and Shipping": "electronic-packing-and-shipping.html",
    "Local Packing and Shipping Supplies": "local-packing-and-shipping-supplies.html",
    "Corrugated Fiberboard Packaging": "corrugated-fiberboard-packaging.html",
    "Contact Us": "contact.html",
    "Art Courier Service": "art-courier-service.html",
    "Fine Art Shipping": "fine-art-shipping.html",
    "Fine Art Moving and Packing": "fine-art-moving-and-packing.html",
    "Art Installation": "art-installation.html",
    "Art Consultation": "art-consultation.html",
    "Vapor Barrier Bag Shipping": "vapor-barrier-bag-shipping.html",
    "Rick's Restoration": "ricks-restoration.html",
    "Privacy Policy": "privacy-policy.html",
    "Free Quote": "free-quote.html",
    "Blog - Reused Cardboard Boxes":
        "can-you-re-use-recycled-cardboard-boxes-for-packing-and-shipping.html",
    "Blog - On-Site Crating": "on-site-crating.html",
    "Blog - Pallet and Crate Shipping": "pallet-vs-crate-shipping.html",
}

# <title> per page (the .dc.html files carry no title of their own)
TITLES = {
    "index.html": "Las Vegas Pack and Ship | Packing, Shipping & Fine Art Crating",
    "local-packing-and-shipping-store.html": "Local Packing and Shipping Store | Las Vegas Pack and Ship",
    "electronic-packing-and-shipping.html": "Electronic Packing and Shipping | Las Vegas Pack and Ship",
    "local-packing-and-shipping-supplies.html": "Local Packing and Shipping Supplies in Las Vegas | Las Vegas Pack and Ship",
    "corrugated-fiberboard-packaging.html": "Corrugated Fiberboard Packaging | Las Vegas Pack and Ship",
    "contact.html": "Contact Us | Las Vegas Pack and Ship",
    "art-courier-service.html": "Art Courier Service | Las Vegas Pack and Ship",
    "fine-art-shipping.html": "Fine Art Shipping | Las Vegas Pack and Ship",
    "fine-art-moving-and-packing.html": "Fine Art Moving and Packing | Las Vegas Pack and Ship",
    "art-installation.html": "Art Installation | Las Vegas Pack and Ship",
    "art-consultation.html": "Art Consultation | Las Vegas Pack and Ship",
    "vapor-barrier-bag-shipping.html": "Vapor Barrier Bag Shipping | Las Vegas Pack and Ship",
    "ricks-restoration.html": "Rick's Restoration | Las Vegas Pack and Ship",
    "privacy-policy.html": "Privacy Policy | Las Vegas Pack and Ship",
    "free-quote.html": "Free Quote | Las Vegas Pack and Ship",
    "can-you-re-use-recycled-cardboard-boxes-for-packing-and-shipping.html":
        "Can You Re-Use Recycled Cardboard Boxes for Packing and Shipping? | Las Vegas Pack and Ship",
    "on-site-crating.html": "How On-Site Crating Works | Las Vegas Pack and Ship",
    "pallet-vs-crate-shipping.html": "Pallet and Crate Shipping: What's the Difference? | Las Vegas Pack and Ship",
}


def webp_size(data):
    """Natural (width, height) of a WebP byte string, or None."""
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    fourcc = data[12:16]
    if fourcc == b"VP8X":
        w = int.from_bytes(data[24:27], "little") + 1
        h = int.from_bytes(data[27:30], "little") + 1
        return w, h
    if fourcc == b"VP8L":
        b = data[21:25]
        bits = int.from_bytes(b, "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if fourcc == b"VP8 ":
        w, h = struct.unpack("<HH", data[26:30])
        return w & 0x3FFF, h & 0x3FFF
    return None


def extract_slot_images(state_path, assets_out):
    """Write stored <image-slot> photos out as real files; return id -> info."""
    slots = {}
    if not os.path.exists(state_path):
        return slots
    with open(state_path) as fh:
        state = json.load(fh)
    for slot_id, val in state.items():
        if not isinstance(val, dict) or "u" not in val:
            continue
        url = val["u"]
        m = re.match(r"data:image/(\w+);base64,(.*)$", url, re.S)
        if not m:
            continue
        ext, b64 = m.group(1), m.group(2)
        data = base64.b64decode(b64)
        name = f"{slot_id}.{ext}"
        with open(os.path.join(assets_out, name), "wb") as out:
            out.write(data)
        slots[slot_id] = {
            "src": f"assets/{name}",
            "s": val.get("s", 1),
            "x": val.get("x", 0),
            "y": val.get("y", 0),
            "size": webp_size(data),
        }
    return slots


def attrs_of(tag_text):
    """Parse an element's attributes into an ordered dict."""
    out = {}
    for m in re.finditer(r'([:@\w-]+)\s*=\s*"([^"]*)"', tag_text):
        out[m.group(1)] = m.group(2)
    return out


class Converter:
    def __init__(self, slots):
        self.slots = slots
        self.hover_rules = {}  # declarations -> class name, deduped per page

    # -- image slots -------------------------------------------------------
    # The prototype's placeholder captions make poor alt text for the three
    # blog thumbnails ("Blog photo"), so those get real descriptions.
    SLOT_ALT = {
        "blog-post-photo": "Stacked recycled cardboard shipping boxes",
        "blog-crating-photo": "A custom wooden crate being built on site",
        "blog-pallet-photo": "Palletised freight staged for shipping",
    }

    def convert_image_slots(self, body):
        def repl(m):
            a = attrs_of(m.group(0))
            slot_id = a.get("id", "")
            info = self.slots.get(slot_id)
            src = info["src"] if info else a.get("src", "")
            view = info if info else {"s": 1, "x": 0, "y": 0}
            alt = html.escape(self.SLOT_ALT.get(slot_id, a.get("placeholder", "")), quote=True)
            frame_style = a.get("style", "").rstrip().rstrip(";")
            if "position:" not in frame_style:
                frame_style += ";position:relative"
            if "overflow:" not in frame_style:
                frame_style += ";overflow:hidden"
            radius = a.get("radius")
            if radius and a.get("shape") == "rounded" and "border-radius" not in frame_style:
                frame_style += f";border-radius:{radius}px"
            return (
                f'<div class="img-slot" style="{frame_style}">'
                f'<img class="img-slot-img" src="{src}" alt="{alt}" '
                f'data-view-s="{view["s"]}" data-view-x="{view["x"]}" data-view-y="{view["y"]}">'
                f"</div>"
            )

        return re.sub(r"<image-slot\b[^>]*>\s*</image-slot>", repl, body)

    # -- sc-if -------------------------------------------------------------
    # Conditions true in the component's initial state render un-hidden, so the
    # page is correct before site.js runs (and never flashes).
    INITIALLY_TRUE = {"isT0", "isG0", "notSubmitted"}

    def convert_sc_if(self, body):
        def repl(m):
            cond = m.group(1)
            hidden = "" if cond in self.INITIALLY_TRUE else " hidden"
            return f'<div class="dc-if" data-cond="{cond}"{hidden}>'

        body = re.sub(r'<sc-if\s+value="\{\{\s*(\w+)\s*\}\}"[^>]*>', repl, body)
        return body.replace("</sc-if>", "</div>")

    # -- event bindings ----------------------------------------------------
    def convert_events(self, body):
        return re.sub(
            r'\bon([A-Z]\w+)="\{\{\s*(\w+)\s*\}\}"',
            lambda m: f'data-dc-{m.group(1).lower()}="{m.group(2)}"',
            body,
        )

    # -- carousel dots -----------------------------------------------------
    def convert_dots(self, body):
        def repl(m):
            tag, kind, idx = m.group(0), m.group(1), m.group(2)
            tag = re.sub(r"background:\{\{\s*\w+\s*\}\};?", "", tag)
            group = "t" if kind == "dot" else "g"
            classes = "dc-dot is-active" if idx == "0" else "dc-dot"
            tag = tag[:-1] + f' data-dot-group="{group}" data-dot-index="{idx}">'
            # some dots already carry a class (Rick's gallery) — merge, don't
            # emit a second class attribute, which browsers silently ignore
            if re.search(r'\bclass="', tag):
                return re.sub(
                    r'\bclass="([^"]*)"', lambda c: f'class="{c.group(1)} {classes}"', tag, count=1
                )
            return tag[:-1] + f' class="{classes}">'

        return re.sub(r"<span[^>]*background:\{\{\s*(dot|dotG)(\d+)\s*\}\}[^>]*>", repl, body)

    # -- lightbox image ----------------------------------------------------
    # No src attribute at all: an empty one makes the browser re-request the
    # page itself. site.js sets it when the lightbox opens.
    def convert_lightbox(self, body):
        return body.replace('src="{{ lightboxSrc }}" ', 'id="lightbox-img" ')

    # -- style-hover -> real CSS ------------------------------------------
    def convert_hover(self, body, page_slug):
        def repl(m):
            decls = html.unescape(m.group(1)).strip().rstrip(";")
            name = self.hover_rules.get(decls)
            if name is None:
                name = f"hv-{page_slug}-{len(self.hover_rules)}"
                self.hover_rules[decls] = name
            return f'data-hv="{name}"'

        body = re.sub(r'style-hover="([^"]*)"', repl, body)
        # fold the generated marker into a real class attribute
        def fold(m):
            tag = m.group(0)
            cls = re.search(r'data-hv="([\w-]+)"', tag).group(1)
            tag = re.sub(r'\s*data-hv="[\w-]+"', "", tag)
            if re.search(r'\bclass="', tag):
                return re.sub(r'\bclass="([^"]*)"', lambda c: f'class="{c.group(1)} {cls}"', tag, count=1)
            return tag[:-1] + f' class="{cls}">'

        return re.sub(r"<[^>]*data-hv=\"[\w-]+\"[^>]*>", fold, body)

    # -- links -------------------------------------------------------------
    def convert_links(self, body):
        def repl(m):
            quote, name, frag = m.group(1), m.group(2), m.group(3) or ""
            target = PAGES.get(html.unescape(name))
            if target is None:
                raise SystemExit(f"unmapped page link: {name}")
            # a bare "#" fragment pointing at the homepage is a dead anchor
            if frag == "#":
                frag = ""
            return f"href={quote}{target}{frag}{quote}"

        # page names may contain an apostrophe ("Rick's Restoration"), so the
        # name is only bounded by the attribute's own quote character
        return re.sub(r'href=(")([^"#]+)\.dc\.html(#[^"]*)?\1', repl, body)

    # -- misc cleanup ------------------------------------------------------
    def cleanup(self, body):
        body = body.replace('required="true"', "required")
        # leftover editor hints such as hint-placeholder-val="{{ true }}"
        body = re.sub(r'\s+[\w-]+="\{\{[^"]*\}\}"', "", body)
        return body

    def convert(self, text, page_slug):
        helmet = re.search(r"<helmet>(.*?)</helmet>", text, re.S).group(1)
        body = re.search(r"</helmet>(.*?)</x-dc>", text, re.S).group(1)

        # head: drop the runtime script, keep fonts + page CSS
        helmet = re.sub(r'<script src="\./image-slot\.js"></script>\s*', "", helmet)

        body = self.convert_image_slots(body)
        body = self.convert_sc_if(body)
        body = self.convert_events(body)
        body = self.convert_dots(body)
        body = self.convert_lightbox(body)
        body = self.convert_hover(body, page_slug)
        body = self.convert_links(body)
        body = self.cleanup(body)
        return helmet.strip(), body.strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    assets_out = os.path.join(OUT, "assets")
    os.makedirs(assets_out, exist_ok=True)

    slots = extract_slot_images(os.path.join(SRC, ".image-slots.state.json"), assets_out)

    referenced = set()
    written = []

    for design_name, out_name in PAGES.items():
        src_path = os.path.join(SRC, f"{design_name}.dc.html")
        with open(src_path, encoding="utf-8") as fh:
            text = fh.read()

        slug = re.sub(r"[^a-z0-9]+", "-", out_name.replace(".html", "").lower()).strip("-")
        conv = Converter(slots)
        helmet, body = conv.convert(text, slug)

        hover_css = "\n".join(
            f".{name}:hover{{{decls};}}" for decls, name in conv.hover_rules.items()
        )

        title = html.escape(TITLES[out_name])
        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{helmet}
<link rel="stylesheet" href="site.css">
<style>
{hover_css}
</style>
</head>
<body>
{body}
<script src="site.js" defer></script>
</body>
</html>
"""
        with open(os.path.join(OUT, out_name), "w", encoding="utf-8") as fh:
            fh.write(page)
        written.append(out_name)

        for m in re.finditer(r'(?:src|href)="((?:assets|uploads)/[^"]+)"', page):
            referenced.add(html.unescape(m.group(1)))
        for m in re.finditer(r"url\((['\"]?)((?:assets|uploads)/[^)'\"]+)\1\)", page):
            referenced.add(html.unescape(m.group(2)))

    # copy only the assets the built pages actually reference
    copied = 0
    missing = []
    for rel in sorted(referenced):
        src_file = os.path.join(SRC, rel)
        dst_file = os.path.join(OUT, rel)
        if not os.path.exists(src_file):
            if not os.path.exists(dst_file):  # slot images are generated, not copied
                missing.append(rel)
            continue
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        shutil.copy2(src_file, dst_file)
        copied += 1

    print(f"pages:  {len(written)}")
    print(f"assets: {copied} copied, {len(slots)} extracted from image slots")
    if missing:
        print("MISSING ASSETS:")
        for m in missing:
            print("  ", m)


if __name__ == "__main__":
    main()
