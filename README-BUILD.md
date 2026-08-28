# Las Vegas Pack and Ship — static site

The implementation of the Claude Design handoff in `project/`. Eighteen pages of
plain HTML/CSS/JS, no build step needed to serve them: open `docs/index.html` in
a browser or drop `docs/` on any static host.

## Layout

```
project/        the original Claude Design handoff (unchanged, read-only reference)
build/          the tooling that produced docs/
  convert.py    turns each .dc.html into a standalone page
  site.css      shared styles for behaviour the DC runtime used to provide
  site.js       the ported interaction logic
  smoke.js      headless Playwright check over all 18 pages
docs/           the built site — this is the deliverable
```

Rebuild after editing anything in `build/`:

```
python3 build/convert.py && cp build/site.css build/site.js docs/
node build/smoke.js          # optional: headless verification (needs playwright-core)
```

`smoke.js` opens all 18 pages in headless Chromium and checks that each one
loads with no JS errors and no missing files, that the header/footer/nav are
present, and that every ported interaction actually works — sticky bar, mobile
menu, testimonial and gallery carousels, arrow galleries, lightbox, form
submission and image-slot geometry. It blocks outbound requests, so it does not
need the network.

Editing pages directly in `docs/` is fine too — nothing regenerates unless you
run the converter, and if you do it will overwrite `docs/*.html`.

## Hosting

The folder is called `docs/` because that is one of the two locations GitHub
Pages will serve from. To publish: **Settings → Pages → Source: Deploy from a
branch → `main` / `/docs`**. The site is live at
`https://<owner>.github.io/<repo>/` a minute or so later.

Every link in the site is relative, so it works just as well served from a
subdirectory, from a domain root, or opened straight off disk. Any other static
host (Netlify, Vercel, S3, the existing web host) just needs `docs/` as its
publish directory.

## Pages

| Page | File |
| --- | --- |
| Homepage | `index.html` |
| Local Packing & Shipping Store | `local-packing-and-shipping-store.html` |
| Electronic Packing & Shipping | `electronic-packing-and-shipping.html` |
| Packing, Shipping & Moving Supplies | `local-packing-and-shipping-supplies.html` |
| Custom Crating & Corrugated Fiberboard | `corrugated-fiberboard-packaging.html` |
| Fine Art Shipping | `fine-art-shipping.html` |
| Fine Art Moving and Packing | `fine-art-moving-and-packing.html` |
| Art Courier Service | `art-courier-service.html` |
| Art Consultation | `art-consultation.html` |
| Art Installation | `art-installation.html` |
| Vapor Barrier Bag Shipping | `vapor-barrier-bag-shipping.html` |
| Rick's Restoration | `ricks-restoration.html` |
| Contact Us | `contact.html` |
| Free Quote | `free-quote.html` |
| Privacy Policy | `privacy-policy.html` |
| Blog — recycled boxes | `can-you-re-use-recycled-cardboard-boxes-for-packing-and-shipping.html` |
| Blog — on-site crating | `on-site-crating.html` |
| Blog — pallet vs crate | `pallet-vs-crate-shipping.html` |

Filenames follow the ones named in the original build briefs. All internal
links, nav dropdowns, sticky-bar links and mobile-menu links were rewritten to
match, and are verified by the link audit.

## What the conversion did

The prototypes ran on Claude Design's component runtime (`support.js`,
`image-slot.js`). None of that ships. Each construct was replaced with a plain
equivalent:

| Prototype | Built site |
| --- | --- |
| `<x-dc>` / `<helmet>` | normal `<head>` and `<body>` |
| `<sc-if value="{{ cond }}">` | `<div class="dc-if" data-cond="cond">`, toggled by `site.js` |
| `src="{{ lightboxSrc }}"` | an `<img>` whose src `site.js` fills in on open |
| `onClick="{{ handler }}"` | `data-dc-click="handler"`, bound on load |
| `style-hover="…"` | real `:hover` CSS rules, deduplicated per page |
| `background:{{ dot0 }}` | `.dc-dot` / `.dc-dot.is-active` |
| `<image-slot>` | a clipping frame plus an `<img>`; the stored pan/zoom of each photo is reproduced by `layoutSlot()` |
| `class Component extends DCLogic` | one shared `site.js` |

Conditions that are true in the component's initial state (first testimonial,
first gallery slide, un-submitted form) render visible in the HTML, so pages are
correct before JavaScript runs and never flash.

Ported interactions: sticky condensed header on scroll, nav dropdowns, mobile
hamburger menu, the 6-review testimonial carousel (dots, drag/swipe,
auto-advance every 5s pausing on hover), Rick's Restoration 5-photo gallery,
the ten arrow galleries with slow auto-scroll, the price-list lightbox (now also
closes on Escape), and the quote-form submitted state.

The three blog photos were stored inside the design bundle rather than as files;
they were extracted to `docs/assets/blog-*.webp`. Only the images the pages
actually reference were copied over — 92 files, ~13 MB, out of the ~18 MB of
uploads in the bundle.

## Known gaps — these need content, not code

Both were already flagged to you in the design chats and are carried over as-is:

1. **`assets/MIL-D-3464E.pdf`** is linked from the Vapor Barrier Bag Shipping
   page but was never added to the bundle. The link 404s until the PDF is
   dropped into `docs/assets/`.
2. **`antique-packing-and-moving.html`** is linked from Rick's Restoration but
   that page was never built.

Still open from the transcripts, unchanged here because they are yours to
decide:

- The **MIL-PRF-131K Class 1** spec number is used consistently but was never
  verified.
- **Bonhams and Sotheby's** are named as clients on the Fine Art Moving and
  Packing page, and their logos appear in the homepage client strip. Confirm
  before this goes live.
- The four directory citations on the Contact page list the business as
  "Las Vegas Crating and Logistics".
- Forms are front-end only: submitting shows a confirmation state and sends
  nothing. Wire them to a mail handler before launch.
