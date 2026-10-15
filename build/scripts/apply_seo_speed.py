#!/usr/bin/env python3
"""Apply SEO audit items 1-9 + mobile speed pass to docs/*.html (and free-quote override)."""
from __future__ import annotations
import html as htmlmod
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OVERRIDE = ROOT / "build" / "overrides" / "free-quote.html"
SITE = "https://lasvegaspackandship.com"
GA_ID = "G-XWKXL9ZN6F"

# Darker gold for TEXT on light backgrounds (passes ~4.5:1). Decorative #D6A441 stays.
ACCENT_TEXT = "#8A6A14"

PAGE_META = {
    "index.html": {
        "title": "Las Vegas Pack and Ship | Packing, Shipping, Crating & Fine Art Logistics",
        "description": "Local pack and ship stores in Las Vegas for packing, shipping, custom crating, and fine art logistics. Call (702) 509-9630 for a free quote.",
        "canonical": f"{SITE}/",
        "og_image": f"{SITE}/uploads/20260430_101325%20(1).webp",
        "type": "website",
        "schema": "localbusiness",
    },
    "local-packing-and-shipping-store.html": {
        "title": "Local Packing & Shipping Store in Las Vegas | Las Vegas Pack and Ship",
        "description": "Walk-in packing and shipping store in Las Vegas for boxes, custom packing, and carrier drop-off. Serving Las Vegas and Henderson.",
        "canonical": f"{SITE}/local-packing-and-shipping-store",
        "type": "service",
        "service_name": "Local Packing and Shipping Store",
    },
    "electronic-packing-and-shipping.html": {
        "title": "Electronic Packing & Shipping in Las Vegas | Las Vegas Pack and Ship",
        "description": "Safe packing and shipping for electronics in Las Vegas — computers, TVs, instruments, and fragile gear with custom protection.",
        "canonical": f"{SITE}/electronic-packing-and-shipping",
        "type": "service",
        "service_name": "Electronic Packing and Shipping",
    },
    "local-packing-and-shipping-supplies.html": {
        "title": "Packing, Shipping & Moving Supplies in Las Vegas | Las Vegas Pack and Ship",
        "description": "Boxes, tape, bubble wrap, and moving supplies at our Las Vegas pack and ship store. Competitive pricing, open for walk-ins.",
        "canonical": f"{SITE}/local-packing-and-shipping-supplies",
        "type": "service",
        "service_name": "Packing, Shipping and Moving Supplies",
    },
    "corrugated-fiberboard-packaging.html": {
        "title": "Custom Crating & Corrugated Fiberboard Packaging | Las Vegas Pack and Ship",
        "description": "Custom wooden crates and corrugated fiberboard packaging in Las Vegas for art, antiques, freight, and trade-show shipments.",
        "canonical": f"{SITE}/corrugated-fiberboard-packaging",
        "type": "service",
        "service_name": "Custom Crating and Corrugated Fiberboard Packaging",
    },
    "fine-art-shipping.html": {
        "title": "Fine Art Shipping in Las Vegas | Las Vegas Pack and Ship",
        "description": "Fine art shipping from Las Vegas — museum-quality packing, crating, courier, and domestic or international transport.",
        "canonical": f"{SITE}/fine-art-shipping",
        "type": "service",
        "service_name": "Fine Art Shipping",
    },
    "fine-art-moving-and-packing.html": {
        "title": "Fine Art Moving and Packing in Las Vegas | Las Vegas Pack and Ship",
        "description": "Professional fine art moving and packing in Las Vegas for galleries, collectors, and residences. Soft packing and custom crates.",
        "canonical": f"{SITE}/fine-art-moving-and-packing",
        "type": "service",
        "service_name": "Fine Art Moving and Packing",
    },
    "art-courier-service.html": {
        "title": "Art Courier Service in Las Vegas | Las Vegas Pack and Ship",
        "description": "Dedicated art courier service in Las Vegas for high-value pieces — white-glove handling from pickup to delivery.",
        "canonical": f"{SITE}/art-courier-service",
        "type": "service",
        "service_name": "Art Courier Service",
    },
    "art-consultation.html": {
        "title": "Art Consultation in Las Vegas | Las Vegas Pack and Ship",
        "description": "Art packing and shipping consultation in Las Vegas — planning, materials, and logistics for collections and single pieces.",
        "canonical": f"{SITE}/art-consultation",
        "type": "service",
        "service_name": "Art Consultation",
    },
    "art-installation.html": {
        "title": "Art Installation in Las Vegas | Las Vegas Pack and Ship",
        "description": "Professional art installation in Las Vegas for homes, galleries, and commercial spaces. Careful handling and placement.",
        "canonical": f"{SITE}/art-installation",
        "type": "service",
        "service_name": "Art Installation",
    },
    "vapor-barrier-bag-shipping.html": {
        "title": "Vapor Barrier Bag Shipping in Las Vegas | Las Vegas Pack and Ship",
        "description": "Vapor barrier bag packing and shipping in Las Vegas for moisture-sensitive freight, electronics, and fine art.",
        "canonical": f"{SITE}/vapor-barrier-bag-shipping",
        "type": "service",
        "service_name": "Vapor Barrier Bag Shipping",
    },
    "ricks-restoration.html": {
        "title": "Rick's Restoration Project | Las Vegas Pack and Ship",
        "description": "How Las Vegas Pack and Ship packed and shipped landmark pieces for Rick's Restoration — custom crating and logistics.",
        "canonical": f"{SITE}/ricks-restoration",
        "type": "article",
        "article_title": "Rick's Restoration Project",
    },
    "contact.html": {
        "title": "Contact Las Vegas Pack and Ship | Packing & Shipping Experts",
        "description": "Contact Las Vegas Pack and Ship at (702) 509-9630. Two Polaris Ave locations serving Las Vegas and Henderson.",
        "canonical": f"{SITE}/contact",
        "type": "website",
    },
    "free-quote.html": {
        "title": "Free Packing & Shipping Quote | Las Vegas Pack and Ship",
        "description": "Request a free quote for packing, shipping, crating, or fine art logistics in Las Vegas. Fast response within one business day.",
        "canonical": f"{SITE}/free-quote",
        "type": "website",
    },
    "privacy-policy.html": {
        "title": "Privacy Policy | Las Vegas Pack and Ship",
        "description": "Privacy policy for Las Vegas Pack and Ship — how we collect, use, and protect information from our website and forms.",
        "canonical": f"{SITE}/privacy-policy",
        "type": "website",
    },
    "can-you-re-use-recycled-cardboard-boxes-for-packing-and-shipping.html": {
        "title": "Can You Re-Use Recycled Cardboard Boxes for Packing and Shipping? | Las Vegas Pack and Ship",
        "description": "When reused cardboard boxes are safe for packing and shipping — and when fresh materials are the smarter choice.",
        "canonical": f"{SITE}/can-you-re-use-recycled-cardboard-boxes-for-packing-and-shipping",
        "type": "article",
        "article_title": "Can You Re-Use Recycled Cardboard Boxes for Packing and Shipping?",
    },
    "on-site-crating.html": {
        "title": "How On-Site Crating Works | Las Vegas Pack and Ship",
        "description": "On-site custom crating in Las Vegas — we build crates at your location to save time, handling, and risk.",
        "canonical": f"{SITE}/on-site-crating",
        "type": "article",
        "article_title": "How On-Site Crating Works",
    },
    "pallet-vs-crate-shipping.html": {
        "title": "Pallet vs Crate Shipping: What's the Difference? | Las Vegas Pack and Ship",
        "description": "Pallet shipping vs custom crate shipping — when each method fits, and how Las Vegas Pack and Ship helps you choose.",
        "canonical": f"{SITE}/pallet-vs-crate-shipping",
        "type": "article",
        "article_title": "Pallet and Crate Shipping: What's the Difference?",
    },
    "freight-shipping.html": {
        "title": "Freight Shipping in Las Vegas | Las Vegas Pack and Ship",
        "description": "Freight shipping from Las Vegas: LTL and full truckload, pickup and delivery, crating, palletizing, and warehouse storage.",
        "canonical": f"{SITE}/freight-shipping",
        "type": "service",
        "service_name": "Freight Shipping",
    },
    "furniture-moving.html": {
        "title": "Furniture Moving in Las Vegas | Las Vegas Pack and Ship",
        "description": "Furniture moving and packing in Las Vegas — careful handling for antiques, oversized pieces, and residential moves.",
        "canonical": f"{SITE}/furniture-moving",
        "type": "service",
        "service_name": "Furniture Moving",
    },
    "las-vegas-nv-international-shipping.html": {
        "title": "International Shipping from Las Vegas, NV | Las Vegas Pack and Ship",
        "description": "International packing and shipping from Las Vegas, NV — customs-aware packing, crating, and worldwide freight options.",
        "canonical": f"{SITE}/las-vegas-nv-international-shipping",
        "type": "service",
        "service_name": "International Shipping",
    },
    "wine-and-alcohol-shipping.html": {
        "title": "Wine & Alcohol Shipping in Las Vegas | Las Vegas Pack and Ship",
        "description": "Wine and alcohol shipping from Las Vegas with compliant packing, temperature-aware materials, and carrier options.",
        "canonical": f"{SITE}/wine-and-alcohol-shipping",
        "type": "service",
        "service_name": "Wine and Alcohol Shipping",
    },
    "404.html": {
        "title": "Page Not Found | Las Vegas Pack and Ship",
        "description": "That page could not be found. Return to Las Vegas Pack and Ship for packing, shipping, and fine art logistics.",
        "canonical": f"{SITE}/404",
        "type": "website",
        "noindex": True,
    },
}

# Map .html hrefs to clean paths
HTML_TO_PATH = {
    "index.html": "/",
    "local-packing-and-shipping-store.html": "/local-packing-and-shipping-store",
    "electronic-packing-and-shipping.html": "/electronic-packing-and-shipping",
    "local-packing-and-shipping-supplies.html": "/local-packing-and-shipping-supplies",
    "corrugated-fiberboard-packaging.html": "/corrugated-fiberboard-packaging",
    "fine-art-shipping.html": "/fine-art-shipping",
    "fine-art-moving-and-packing.html": "/fine-art-moving-and-packing",
    "art-courier-service.html": "/art-courier-service",
    "art-consultation.html": "/art-consultation",
    "art-installation.html": "/art-installation",
    "vapor-barrier-bag-shipping.html": "/vapor-barrier-bag-shipping",
    "ricks-restoration.html": "/ricks-restoration",
    "contact.html": "/contact",
    "free-quote.html": "/free-quote",
    "privacy-policy.html": "/privacy-policy",
    "can-you-re-use-recycled-cardboard-boxes-for-packing-and-shipping.html":
        "/can-you-re-use-recycled-cardboard-boxes-for-packing-and-shipping",
    "on-site-crating.html": "/on-site-crating",
    "pallet-vs-crate-shipping.html": "/pallet-vs-crate-shipping",
    "freight-shipping.html": "/freight-shipping",
    "furniture-moving.html": "/furniture-moving",
    "las-vegas-nv-international-shipping.html": "/las-vegas-nv-international-shipping",
    "wine-and-alcohol-shipping.html": "/wine-and-alcohol-shipping",
    "sitemap.xml": "/sitemap.xml",
}

DEFERRED_GTAG = f'''<!-- Deferred Google tag (GA4): stub + idle/interaction load so LCP is not blocked. -->
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  (function () {{
    function loadGtag() {{
      if (window.__gtagLoading) return;
      window.__gtagLoading = true;
      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://www.googletagmanager.com/gtag/js?id={GA_ID}';
      s.onload = function () {{
        gtag('js', new Date());
        gtag('config', '{GA_ID}');
        window.__gtagReady = true;
        window.dispatchEvent(new Event('gtag-ready'));
      }};
      document.head.appendChild(s);
    }}
    function schedule() {{
      var done = false;
      function go() {{
        if (done) return;
        done = true;
        ['pointerdown','keydown','scroll','touchstart'].forEach(function (ev) {{
          window.removeEventListener(ev, go, {{ capture: true }});
        }});
        loadGtag();
      }}
      ['pointerdown','keydown','scroll','touchstart'].forEach(function (ev) {{
        window.addEventListener(ev, go, {{ capture: true, passive: true, once: true }});
      }});
      setTimeout(go, 8000);
    }}
    if (document.readyState === 'complete') schedule();
    else window.addEventListener('load', schedule);
  }})();
</script>'''

FONTS_CSS = (DOCS / "fonts.css").read_text()
# Minify fonts css for inline on homepage
def minify_css(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};:,])\s*", r"\1", css).replace(";}", "}").strip()
    # keep "and (" readable for media if any
    return css

FONTS_MIN = minify_css(FONTS_CSS)
SITE_CSS = (DOCS / "site.css").read_text()
SITE_CSS_MIN = minify_css(SITE_CSS)

# Preload Oswald latin (headings / LCP text) + Work Sans latin
OSWALD_LATIN = "/fonts/TK3IWkUHHAIjg75cFRf3bXL8LICs1_Fv40pKlN4NNSeSASz7FmlWHYg.woff2"
WORK_LATIN = "/fonts/QGYsz_wNahGAdqQ43Rh_fKDp.woff2"

FOOTER_EXTRA = '''
        <div style="color:#FFFFFF;font-size:15px;font-weight:600;margin-bottom:14px;">More Services</div>
        <p style="font-size:14px;line-height:1.9;margin:0;">
          <a href="/freight-shipping" style="color:#cfcdc4;">Freight Shipping</a><br>
          <a href="/furniture-moving" style="color:#cfcdc4;">Furniture Moving</a><br>
          <a href="/las-vegas-nv-international-shipping" style="color:#cfcdc4;">International Shipping</a><br>
          <a href="/wine-and-alcohol-shipping" style="color:#cfcdc4;">Wine &amp; Alcohol Shipping</a>
        </p>'''


def local_business_schema() -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "Las Vegas Pack and Ship",
        "url": f"{SITE}/",
        "telephone": "+1-702-509-9630",
        "email": "contact@lasvegaspackandship.com",
        "image": f"{SITE}/assets/logo-color.png",
        "address": [
            {
                "@type": "PostalAddress",
                "streetAddress": "4640 S. Polaris Ave.",
                "addressLocality": "Las Vegas",
                "addressRegion": "NV",
                "postalCode": "89103",
                "addressCountry": "US",
            },
            {
                "@type": "PostalAddress",
                "streetAddress": "4610 S. Polaris Ave.",
                "addressLocality": "Las Vegas",
                "addressRegion": "NV",
                "postalCode": "89103",
                "addressCountry": "US",
            },
        ],
        "areaServed": ["Las Vegas", "Henderson", "Nevada"],
        "priceRange": "$$",
    }
    return '<script type="application/ld+json">' + json.dumps(data, separators=(",", ":")) + "</script>"


def service_schema(name: str, description: str, url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": name,
        "description": description,
        "url": url,
        "provider": {
            "@type": "LocalBusiness",
            "name": "Las Vegas Pack and Ship",
            "telephone": "+1-702-509-9630",
            "url": f"{SITE}/",
        },
        "areaServed": {"@type": "AdministrativeArea", "name": "Las Vegas, NV"},
    }
    return '<script type="application/ld+json">' + json.dumps(data, separators=(",", ":")) + "</script>"


def article_schema(title: str, description: str, url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": url,
        "author": {"@type": "Organization", "name": "Las Vegas Pack and Ship"},
        "publisher": {
            "@type": "Organization",
            "name": "Las Vegas Pack and Ship",
            "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/logo-color.png"},
        },
        "mainEntityOfPage": url,
    }
    return '<script type="application/ld+json">' + json.dumps(data, separators=(",", ":")) + "</script>"


def build_head_extras(name: str, meta: dict, is_home: bool) -> str:
    title = meta["title"]
    desc = meta["description"]
    canon = meta["canonical"]
    og_image = meta.get("og_image", f"{SITE}/assets/logo-color.png")
    og_type = "article" if meta.get("type") == "article" else "website"
    parts = []
    if meta.get("noindex"):
        parts.append('<meta name="robots" content="noindex">')
    # verification only on home
    if is_home:
        parts.append('<meta name="google-site-verification" content="pebzJ2yOh-yRMffAeeUoHHF31iwLxnMm8FmEcUMSXAE" />')
    parts.append(f'<meta name="description" content="{htmlmod.escape(desc, quote=True)}">')
    parts.append(f'<link rel="canonical" href="{canon}">')
    parts.append('<meta property="og:type" content="' + og_type + '">')
    parts.append('<meta property="og:site_name" content="Las Vegas Pack and Ship">')
    parts.append(f'<meta property="og:title" content="{htmlmod.escape(title, quote=True)}">')
    parts.append(f'<meta property="og:description" content="{htmlmod.escape(desc, quote=True)}">')
    parts.append(f'<meta property="og:url" content="{canon}">')
    parts.append(f'<meta property="og:image" content="{og_image}">')
    parts.append('<meta name="twitter:card" content="summary_large_image">')
    parts.append(f'<meta name="twitter:title" content="{htmlmod.escape(title, quote=True)}">')
    parts.append(f'<meta name="twitter:description" content="{htmlmod.escape(desc, quote=True)}">')
    parts.append(f'<meta name="twitter:image" content="{og_image}">')
    # fonts
    if is_home:
        parts.append(f'<style id="fonts-css">{FONTS_MIN}</style>')
        parts.append(f'<link rel="preload" as="font" type="font/woff2" href="{OSWALD_LATIN}" crossorigin>')
        parts.append(f'<link rel="preload" as="font" type="font/woff2" href="{WORK_LATIN}" crossorigin>')
        parts.append(f'<style id="site-css">{SITE_CSS_MIN}</style>')
        parts.append('<link rel="preload" as="image" href="/uploads/20260430_101325%20(1).webp" fetchpriority="high">')
    else:
        parts.append('<link rel="stylesheet" href="/fonts.css">')
        parts.append(f'<link rel="preload" as="font" type="font/woff2" href="{OSWALD_LATIN}" crossorigin>')
    # schema
    t = meta.get("type")
    if t == "localbusiness" or is_home:
        parts.append(local_business_schema())
    elif t == "service":
        parts.append(service_schema(meta["service_name"], desc, canon))
    elif t == "article":
        parts.append(article_schema(meta.get("article_title", title), desc, canon))
    return "\n".join(parts)


OLD_GTAG_RE = re.compile(
    r"<!-- Google tag \(gtag\.js\) -->\s*"
    r"<script async src=\"https://www\.googletagmanager\.com/gtag/js\?id=G-[A-Z0-9]+\"></script>\s*"
    r"<script>\s*window\.dataLayer[\s\S]*?gtag\('config',\s*'G-[A-Z0-9]+'\);\s*</script>",
    re.M,
)
GOOGLE_FONTS_RE = re.compile(
    r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\s*'
    r'<link href="https://fonts\.googleapis\.com/css2\?[^"]+" rel="stylesheet">\s*',
    re.M,
)
# also handle single-line variants / gstatic preconnect
GOOGLE_FONTS_RE2 = re.compile(
    r'<link[^>]+fonts\.googleapis\.com[^>]*>\s*'
    r'(?:<link[^>]+fonts\.gstatic\.com[^>]*>\s*)?'
    r'<link[^>]+fonts\.googleapis\.com/css2[^>]*>\s*',
    re.M,
)
TITLE_RE = re.compile(r"<title>.*?</title>", re.S)
DESC_RE = re.compile(r'<meta\s+name="description"[^>]*>\s*', re.I)
CANON_RE = re.compile(r'<link\s+rel="canonical"[^>]*>\s*', re.I)
OG_RE = re.compile(r'<meta\s+(?:property|name)="(?:og|twitter):[^"]*"[^>]*>\s*', re.I)
LD_RE = re.compile(r'<script type="application/ld\+json">[\s\S]*?</script>\s*', re.I)
VERIFY_RE = re.compile(r'<meta\s+name="google-site-verification"[^>]*>\s*', re.I)
SITE_CSS_LINK_RE = re.compile(r'<link rel="stylesheet" href="(?:\./)?site\.css">\s*')
FONTS_CSS_STYLE_RE = re.compile(r'<style id="fonts-css">.*?</style>\s*', re.S)
SITE_CSS_STYLE_RE = re.compile(r'<style id="site-css">.*?</style>\s*', re.S)


def clean_internal_links(text: str) -> str:
    # href="foo.html" -> href="/foo"
    # href="foo.html#bar" -> href="/foo#bar"
    # href="index.html" -> href="/"
    # href="index.html#home" -> href="/#home"
    def repl(m):
        href = m.group(1)
        # skip absolute / http / mailto / tel / # only
        if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:", "/")):
            # still rewrite absolute path with .html
            pass
        path, frag = href, ""
        if "#" in href:
            path, frag = href.split("#", 1)
            frag = "#" + frag
        # strip leading ./
        path = path[2:] if path.startswith("./") else path
        base = path.split("?")[0]
        if base in HTML_TO_PATH:
            new = HTML_TO_PATH[base] + frag
            return f'href="{new}"'
        if base.endswith(".html") and "/" not in base:
            slug = "/" + base[:-5]
            return f'href="{slug}{frag}"'
        return m.group(0)

    text = re.sub(r'href="([^"]+)"', repl, text)
    # fix sitemap dead link
    text = text.replace('href="#" style="color:#cfcdc4;">Sitemap</a>', 'href="/sitemap.xml" style="color:#cfcdc4;">Sitemap</a>')
    return text


def fix_contrast_text(text: str) -> str:
    """Darken gold when used as foreground text on light surfaces; keep decorative uses."""
    # Common kicker / label patterns: color:#D6A441 on light (not on buttons with dark bg)
    # Replace color:#D6A441 in non-button text contexts carefully.
    # Safe approach: replace standalone color:#D6A441 with ACCENT_TEXT, then restore
    # decorative / on-dark uses we care about.
    # Actually buttons use background:#D6A441, borders use border-color:#D6A441,
    # underlines use background:#D6A441 for bars, stars use color:#D6A441 (decorative OK for stars?).
    # Stars ★★★★★ are decorative; Lighthouse flagged text labels.
    # Patterns flagged: font-weight 600/700 labels at 13-14px with color #D6A441 on white/FAF8F4.
    # Also #8c8677 on white for small text.

    # Replace label-like gold text: color:#D6A441 with dark gold when paired with letter-spacing
    # (kickers) or when it's a text color not background.
    def darken_color_attr(m):
        style = m.group(0)
        # skip if background is dark or this is a button-ish with background #D6A441
        if re.search(r"background\s*:\s*#D6A441", style, re.I):
            return style
        if re.search(r"background\s*:\s*#0C0B09", style, re.I):
            return style  # gold text on dark is fine / better
        if re.search(r"background\s*:\s*#(?:0C0B09|1A1712|000)", style, re.I):
            return style
        # stars line often has letter-spacing:1px and only stars — leave decorative stars
        if "★★" in style or (m.string[max(0, m.start() - 80) : m.end() + 80].count("★") >= 3):
            # check surrounding
            pass
        # Darken text color gold on light
        style2 = re.sub(r"color\s*:\s*#D6A441\b", f"color:{ACCENT_TEXT}", style, flags=re.I)
        # Improve muted gray #8c8677 / #8a8880 on white for small text
        style2 = re.sub(r"color\s*:\s*#8[Cc]8677\b", "color:#5c5648", style2)
        style2 = re.sub(r"color\s*:\s*#8a8880\b", "color:#5c5648", style2)
        return style2

    text = re.sub(r'style="[^"]*"', darken_color_attr, text)
    # CSS rules for link color and hover gold on light
    text = text.replace("a { color: #D6A441;", f"a {{ color: {ACCENT_TEXT};")
    text = text.replace("a { color:#D6A441;", f"a {{ color:{ACCENT_TEXT};")
    # nav dropdown hover text gold → darker
    text = text.replace(".nav-dropdown a:hover { background: #FAF8F4; color: #D6A441;",
                        f".nav-dropdown a:hover {{ background: #FAF8F4; color: {ACCENT_TEXT};")
    return text


def fix_headings(text: str, is_home: bool) -> str:
    if is_home:
        # H1 keyword tweak — keep same visual styling
        text = text.replace(
            ">Save time and money with our local pack &amp; ship stores</h1>",
            ">Las Vegas packing, shipping &amp; fine art crating — save time and money</h1>",
        )
        # Our Clients is h3 after h1 — promote to h2
        text = re.sub(
            r"<h3(\s+style=\"text-align:center;font-family:'Oswald'[^\"]*\")>(Our Clients)",
            r"<h2\1>\2",
            text,
            count=1,
        )
        text = text.replace("</h3>", "</h2>", 1) if False else text
        # Fix closing tag for Our Clients specifically
        text = re.sub(
            r"(<h2 style=\"text-align:center;font-family:'Oswald'[^\"]*>Our Clients<span[^>]*>.*?</span>)</h3>",
            r"\1</h2>",
            text,
            count=1,
            flags=re.S,
        )
    # Generic: demote orphaned h4 that follow h2 incorrectly — change leading h4 after h1/h2 skips
    # On blog pages, structure is h1 then h2 — OK. Problem is h3/h4 after h1 without h2.
    # Convert first content h3 that appears before any h2 into h2 (non-home already handled).
    return text


def fix_empty_alts(text: str) -> str:
    # Decorative images with empty alt are OK for a11y; Lighthouse image-alt score was 1.
    # Add meaningful alts where empty and clearly content:
    replacements = [
        ('alt="" class="wwd-photo"', 'alt="Packing and shipping service photo" class="wwd-photo"'),
        ('src="assets/wwd-section-bg.webp" alt=""', 'src="assets/wwd-section-bg.webp" alt=""'),  # decorative bg OK
        ('src="assets/cta-boxes.webp" alt=""', 'src="assets/cta-boxes.webp" alt=""'),
        ('src="assets/logo-bw.png" alt=""', 'src="assets/logo-bw.png" alt=""'),
        ('src="assets/icon-affordable-shipping.svg" alt=""',
         'src="assets/icon-affordable-shipping.svg" alt="Affordable shipping"'),
        ('src="assets/icon-safe-secure.svg" alt=""',
         'src="assets/icon-safe-secure.svg" alt="Safe and secure packing"'),
        ('src="assets/icon-store-value.svg" alt=""',
         'src="assets/icon-store-value.svg" alt="Store full of value"'),
        ('src="assets/icon-we-sell-boxes.svg" alt=""',
         'src="assets/icon-we-sell-boxes.svg" alt="We sell boxes"'),
    ]
    for a, b in replacements:
        text = text.replace(a, b)
    # Numbered wwd photos
    for i in range(1, 9):
        text = text.replace(
            f'src="assets/wwd-fix-{i}.webp" alt=""',
            f'src="assets/wwd-fix-{i}.webp" alt="What we pack and ship — photo {i}"',
        )
    return text


def add_footer_links(text: str) -> str:
    if "More Services" in text and "/freight-shipping" in text:
        return text
    # Insert a More Services column before the closing of the footer grid
    # Look for the Strip Crating column and add after it
    marker = (
        '<div style="color:#FFFFFF;font-size:15px;font-weight:600;margin-bottom:14px;">'
        "Las Vegas Strip Crating &amp; Logistics</div>"
    )
    idx = text.find(marker)
    if idx < 0:
        return text
    # Find end of that column's </div></div> after the address paragraph
    # Structure: <div> heading + <p>address</p> </div>
    end = text.find("</div>", text.find("</p>", idx)) + len("</div>")
    text = text[:end] + "\n      <div>" + FOOTER_EXTRA + "\n      </div>" + text[end:]
    return text


def link_new_pages_in_content(text: str, name: str) -> str:
    """Light in-text / card links to the 4 new pages — not in main nav."""
    if name == "index.html":
        # Furniture Moving svc-card currently points to #local-store
        text = text.replace(
            '<a href="#local-store" class="svc-card" style="display:flex;align-items:center;gap:18px;min-height:104px;padding:22px 26px;text-decoration:none;background:linear-gradient(100deg, #0C0B09 0%, #1A1712 38%, #8A6A22 78%, #D6A441 100%);border:1px solid rgba(214,164,65,0.35);">\n'
            '          <span style="font-size:24px;flex-shrink:0;">🪑</span>\n'
            '          <span style="font-family:\'Oswald\',sans-serif;text-transform:uppercase;letter-spacing:0.04em;font-size:18px;line-height:1.25;color:#FFFFFF;">Furniture Moving</span>',
            '<a href="/furniture-moving" class="svc-card" style="display:flex;align-items:center;gap:18px;min-height:104px;padding:22px 26px;text-decoration:none;background:linear-gradient(100deg, #0C0B09 0%, #1A1712 38%, #8A6A22 78%, #D6A441 100%);border:1px solid rgba(214,164,65,0.35);">\n'
            '          <span style="font-size:24px;flex-shrink:0;">🪑</span>\n'
            '          <span style="font-family:\'Oswald\',sans-serif;text-transform:uppercase;letter-spacing:0.04em;font-size:18px;line-height:1.25;color:#FFFFFF;">Furniture Moving</span>',
        )
        # Air & Sea Fine Art Shipping -> international
        text = text.replace(
            '<a href="#fine-art" class="svc-card" style="display:flex;align-items:center;gap:18px;min-height:104px;padding:22px 26px;text-decoration:none;background:linear-gradient(100deg, #0C0B09 0%, #1A1712 38%, #8A6A22 78%, #D6A441 100%);border:1px solid rgba(214,164,65,0.35);">\n'
            '          <span style="font-size:24px;flex-shrink:0;">✈</span>\n'
            '          <span style="font-family:\'Oswald\',sans-serif;text-transform:uppercase;letter-spacing:0.04em;font-size:18px;line-height:1.25;color:#FFFFFF;">Air &amp; Sea Fine Art Shipping</span>',
            '<a href="/las-vegas-nv-international-shipping" class="svc-card" style="display:flex;align-items:center;gap:18px;min-height:104px;padding:22px 26px;text-decoration:none;background:linear-gradient(100deg, #0C0B09 0%, #1A1712 38%, #8A6A22 78%, #D6A441 100%);border:1px solid rgba(214,164,65,0.35);">\n'
            '          <span style="font-size:24px;flex-shrink:0;">✈</span>\n'
            '          <span style="font-family:\'Oswald\',sans-serif;text-transform:uppercase;letter-spacing:0.04em;font-size:18px;line-height:1.25;color:#FFFFFF;">Air &amp; Sea Fine Art Shipping</span>',
        )
        # Custom Crating card -> corrugated (already has some links) — also add freight near pallet blog
        text = text.replace(
            'alt="Palletised freight staged for shipping"',
            'alt="Palletised freight staged for shipping"',
        )
        # Add a short related-services line near Explore Our Services heading area — skip, cards enough
    # Cross-link from related existing pages via a small related block before footer
    related_map = {
        "corrugated-fiberboard-packaging.html": [
            ("/freight-shipping", "Freight Shipping"),
            ("/on-site-crating", "On-Site Crating"),
        ],
        "local-packing-and-shipping-store.html": [
            ("/furniture-moving", "Furniture Moving"),
            ("/wine-and-alcohol-shipping", "Wine & Alcohol Shipping"),
            ("/las-vegas-nv-international-shipping", "International Shipping"),
        ],
        "fine-art-shipping.html": [
            ("/las-vegas-nv-international-shipping", "International Shipping"),
            ("/freight-shipping", "Freight Shipping"),
        ],
        "pallet-vs-crate-shipping.html": [
            ("/freight-shipping", "Freight Shipping"),
            ("/on-site-crating", "On-Site Crating"),
        ],
        "electronic-packing-and-shipping.html": [
            ("/furniture-moving", "Furniture Moving"),
            ("/freight-shipping", "Freight Shipping"),
        ],
    }
    if name in related_map and "Related services" not in text:
        links = " · ".join(
            f'<a href="{href}" style="color:{ACCENT_TEXT};">{htmlmod.escape(label)}</a>'
            for href, label in related_map[name]
        )
        block = (
            f'<div style="max-width:900px;margin:0 auto 48px;padding:0 24px;font-size:14px;color:#5a5952;">'
            f'<strong style="color:#0C0B09;">Related services:</strong> {links}</div>\n'
        )
        text = text.replace("  <!-- FOOTER -->", block + "  <!-- FOOTER -->")
        text = text.replace("  <footer ", block + "  <footer ", 1) if "Related services" not in text else text
    return text


def hero_img_attrs(text: str) -> str:
    # Ensure hero img has width/height and fetchpriority
    text = re.sub(
        r'(<img src="uploads/20260430_101325 \(1\)\.webp"[^>]*?)>',
        lambda m: (
            m.group(1)
            if "fetchpriority" in m.group(1)
            else m.group(1)
            + ' width="1600" height="900" fetchpriority="high" decoding="async"'
        )
        + ">",
        text,
        count=1,
    )
    # Also fix if already has style and we doubled
    text = text.replace(
        'fetchpriority="high" decoding="async" width="1600" height="900" fetchpriority="high" decoding="async"',
        'width="1600" height="900" fetchpriority="high" decoding="async"',
    )
    return text


def patch_file(path: Path) -> bool:
    name = path.name
    meta = PAGE_META.get(name)
    if not meta:
        print("skip (no meta)", name)
        return False
    text = path.read_text(encoding="utf-8")
    is_home = name == "index.html"
    original = text

    # Remove old gtag / fonts / seo tags we'll rebuild
    text = OLD_GTAG_RE.sub("", text)
    text = GOOGLE_FONTS_RE.sub("", text)
    text = GOOGLE_FONTS_RE2.sub("", text)
    text = VERIFY_RE.sub("", text)
    text = DESC_RE.sub("", text)
    text = CANON_RE.sub("", text)
    text = OG_RE.sub("", text)
    text = LD_RE.sub("", text)
    text = FONTS_CSS_STYLE_RE.sub("", text)
    text = SITE_CSS_STYLE_RE.sub("", text)

    # Title
    title_html = f"<title>{htmlmod.escape(meta['title'])}</title>"
    if TITLE_RE.search(text):
        text = TITLE_RE.sub(title_html, text, count=1)
    else:
        text = text.replace("<head>", "<head>\n" + title_html, 1)

    # Strip site.css link on homepage (inlined); keep on others but use absolute path
    if is_home:
        text = SITE_CSS_LINK_RE.sub("", text)
    else:
        text = SITE_CSS_LINK_RE.sub('<link rel="stylesheet" href="/site.css">\n', text)

    extras = build_head_extras(name, meta, is_home)

    # Insert deferred gtag + charset-first order right after <head>
    # Ensure charset/viewport first
    # Remove existing charset/viewport to re-order
    charset = '<meta charset="utf-8">'
    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1">'
    text = re.sub(r'<meta charset="[^"]*">\s*', "", text)
    text = re.sub(r'<meta name="viewport"[^>]*>\s*', "", text)

    injection = (
        f"<head>\n{charset}\n{viewport}\n{DEFERRED_GTAG}\n{extras}\n"
    )
    text = text.replace("<head>", injection, 1)

    # Clean duplicate title if extras somehow — title should remain once
    # Fix icon paths to root-absolute
    for ico in [
        "favicon.ico",
        "favicon-32x32.png",
        "favicon-16x16.png",
        "apple-touch-icon.png",
        "site.webmanifest",
        "android-chrome-192x192.png",
        "android-chrome-512x512.png",
    ]:
        text = text.replace(f'href="{ico}"', f'href="/{ico}"')
        text = text.replace(f"href='{ico}'", f"href='/{ico}'")

    text = clean_internal_links(text)
    text = fix_contrast_text(text)
    text = fix_headings(text, is_home)
    text = fix_empty_alts(text)
    text = add_footer_links(text)
    text = link_new_pages_in_content(text, name)
    if is_home or "20260430_101325" in text:
        text = hero_img_attrs(text)

    # Asset paths: make assets/uploads absolute for consistency after clean URLs
    # Relative assets/ still work from /page but not from nested — Pages has flat URLs so OK.
    # Prefer absolute for resilience:
    text = re.sub(r'(src|href)="(assets/[^"]+)"', r'\1="/\2"', text)
    text = re.sub(r'(src|href)="(uploads/[^"]+)"', r'\1="/\2"', text)
    text = re.sub(r"url\((['\"]?)(assets/[^)'\"]+)\1\)", r"url(/\2)", text)
    text = text.replace('href="site.js"', 'href="/site.js"')
    text = text.replace('src="site.js"', 'src="/site.js"')
    text = text.replace('href="site.css"', 'href="/site.css"')

    # Fix related-services double-insert if any
    # Ensure script defer remains at end

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    changed = []
    for path in sorted(DOCS.glob("*.html")):
        if patch_file(path):
            changed.append(path.name)
            print("patched", path.name)
        else:
            print("unchanged?", path.name)
    # Also patch override so rebuild keeps free-quote SEO
    if OVERRIDE.exists():
        # copy from docs after patch
        docs_fq = DOCS / "free-quote.html"
        if docs_fq.exists():
            OVERRIDE.write_text(docs_fq.read_text(encoding="utf-8"), encoding="utf-8")
            print("synced override free-quote.html")
    # Copy fonts.css into build/static
    static = ROOT / "build" / "static"
    static.mkdir(exist_ok=True)
    (static / "fonts.css").write_text((DOCS / "fonts.css").read_text())
    fonts_src = DOCS / "fonts"
    fonts_dst = static / "fonts"
    fonts_dst.mkdir(exist_ok=True)
    import shutil
    for f in fonts_src.glob("*.woff2"):
        shutil.copy2(f, fonts_dst / f.name)
    print("changed", len(changed), "files")


if __name__ == "__main__":
    main()
