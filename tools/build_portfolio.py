#!/usr/bin/env python3
"""
Build portfolio.html — a paginated, print-exact portfolio.

Every page is a real A4 landscape sheet (297x210mm) so what the visitor scrolls
on screen is literally what the PDF contains; the PDF is produced by printing
this same file, so the two can never drift apart.
"""
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ROOT = _os.path.dirname(_HERE)          # the site folder
import json, html

SITE = _ROOT
man = json.load(open(_os.path.join(_HERE, 'manifest.json')))

PHONE, WA = '9365333187', '919365333187'
EMAIL = 'Chitraranjanneog38@gmail.com'
IG = 'https://www.instagram.com/interiorbychitra'

SECTIONS = [
    ('living-room', 'Living Room', 'Seating, media walls, feature stone and layered ceilings.'),
    ('modular-kitchen', 'Modular Kitchen', 'Modular runs, marble counters, islands and breakfast bars.'),
    ('bathrooms', 'Bathrooms', 'Vanities, backlit mirrors, stone and walk-in showers.'),
    ('bedrooms', 'Bedrooms', 'Bedroom schemes with fitted storage and panelling.'),
    ('wardrobes', 'Wardrobes', 'Fitted wardrobes, tall units and study desks.'),
    ('shelving', 'Shelving', 'Open joinery, display niches and bench seating.'),
    ('ongoing-work', 'Ongoing Work', 'Joinery currently on site, photographed during execution.'),
]

SERVICES = [
    ('Custom interior design',
     'A complete scheme drawn around how you actually live — layouts, joinery, finishes, '
     'lighting and furniture chosen together rather than piece by piece.'),
    ('Modular kitchen',
     'Kitchens planned around the real work triangle, then built with the storage that suits '
     'your cooking, and finishes that survive an Assam summer.'),
    ('Room makeovers',
     'A single room brought up to the standard of the rest of the house, when a full '
     'renovation is not on the table.'),
    ('Space planning',
     'Circulation, storage volume, daylight and the small dimensional decisions that make a '
     'compact home feel larger.'),
    ('Furniture & décor selection',
     'Sourcing and specifying the loose pieces, lighting and textiles so the finished room '
     'reads as one considered whole.'),
]

PROCESS = [
    ('Planning &amp; design', 'Understand your vision, assess the space, and develop a design that '
     'balances how the room looks, how it works and how you live in it.'),
    ('Cost estimation', 'A transparent, itemised estimate covering materials and execution, kept '
     'inside the budget you have planned for.'),
    ('Building phase', 'The approved design brought to life through coordinated execution and '
     'careful craftsmanship.'),
    ('Final touches', 'Finishes, furnishings, lighting and decorative pieces that pull the whole '
     'room together.'),
    ('Project completion', 'Final inspections, remaining work resolved, and the space handed over '
     'ready to be lived in.'),
]


# the full-bleed image on each section divider, chosen by TITLE (slugs carry a
# counter that shifts whenever the image set changes; titles do not)
HERO = {
 'living-room':     'Living room with media wall',
 'modular-kitchen': 'Green kitchen with patterned marble floor',
 'bathrooms':       'Dark marble bath with sunken tub',
 'bedrooms':        'Bedroom with panelled wall',
 'wardrobes':       'Wardrobe with amber glass columns',
 'shelving':        'Display unit and fluted panelling',
 # no person in frame, and the joinery reads clearly at full-bleed size
 'ongoing-work':    'Open shelving and bench at carcass stage',
}


def esc(s):
    return html.escape(s, quote=True)


def img(m, cls=''):
    return (f'<img class="{cls}" src="assets/img/work/{m["folder"]}/{m["slug"]}.webp" '
            f'alt="{esc(m["title"])} — IBC, Tezpur" loading="lazy" decoding="async">')


def band(titles):
    """A full-bleed strip of three images across the foot of a text page.

    The services and process pages are short, and a half-empty A4 sheet reads
    as unfinished rather than generous. The strip fills it with work.
    """
    cells = []
    for t in titles:
        m = next(x for x in man if x['title'] == t)
        cells.append(f'<figure>{img(m)}{tag(m)}</figure>')
    return '<div class="pf-band">' + ''.join(cells) + '</div>'


def tag(m):
    # design drawings go unbadged — see the note in rebuild_index.py
    if m['kind'] == 'ongoing':
        return '<span class="pf-tag">On site</span>'
    return ''


pages = []
pn = [0]


def page(inner, cls='', label=''):
    pn[0] += 1
    foot = (f'<footer class="pf-foot"><span>IBC — Interior by Chitra</span>'
            f'<span>{esc(label)}</span><span class="num">{pn[0]:02d}</span></footer>')
    pages.append(f'<section class="pf-page {cls}">{inner}{foot}</section>')


# ---------------------------------------------------------------- 1. cover
cover = next(m for m in man if m['slug'].startswith('living-living-room-with-panelled-feature-wall'))
pn[0] = 0
pages.append(f'''<section class="pf-page pf-cover">
  <div class="pf-cover__img">{img(cover)}</div>
  <div class="pf-cover__panel">
    <img class="pf-cover__mark" src="assets/img/logo-mark.png" alt="" width="120" height="75">
    <p class="pf-kicker">Tezpur &middot; Assam</p>
    <h1>Portfolio</h1>
    <p class="pf-cover__sub">Residential and commercial interiors, planned and built end to
      end &mdash; drawings, a transparent estimate, execution, and a space handed over ready
      to live in.</p>
    <div class="pf-cover__meta">
      <div><dt>Studio</dt><dd>IBC &mdash; Interior by Chitra</dd></div>
      <div><dt>Founder</dt><dd>Chitra Ranjan Neog</dd></div>
      <div><dt>Contact</dt><dd>+91 {PHONE}</dd></div>
    </div>
  </div>
</section>''')

# ---------------------------------------------------------------- 2. studio
facts = [('Based in', 'Tezpur, Sonitpur — working across Assam'),
         ('Scope', 'Residential and commercial interiors'),
         ('Delivery', 'Drawings, estimate, execution, handover'),
         ('Led by', 'Chitra Ranjan Neog')]
page(f'''<div class="pf-split">
  <figure class="pf-portrait">
    <img src="assets/img/studio/chitra-neog.webp" alt="Chitra Ranjan Neog on site"
         loading="lazy" decoding="async">
    <figcaption>Chitra Ranjan Neog &middot; Founder</figcaption>
  </figure>
  <div>
    <p class="pf-kicker">01 &mdash; The studio</p>
    <h2>Design that starts with<br><em>how you live</em>.</h2>
    <p class="pf-lede">IBC &mdash; Interior by Chitra is an interior design studio based in Tezpur,
      working on homes and commercial spaces across Assam. The work is built around one idea:
      a space should reflect the person using it, and it should be effortless to live in once
      the site team leaves.</p>
    <p>Every project runs through the same sequence &mdash; understand the brief, plan the space,
      price it honestly, build it properly, and hand it over finished. Chitra stays involved from
      the first measured survey through to the last piece of hardware.</p>
    <blockquote class="pf-quote">A space should reflect the person using it &mdash; and it
      should be effortless to live in once the site team leaves.</blockquote>
    <dl class="pf-facts">''' +
     ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in facts) +
     '</dl></div></div>', label='The studio')

# ------------------------------------------------------- 3. services + process
page('<p class="pf-kicker">02 &mdash; Services</p>'
     '<h2>What the studio <em>takes on</em>.</h2>'
     '<div class="pf-svc">' +
     ''.join(f'<div class="pf-svc__i"><span class="num">{i:02d}</span>'
             f'<h3>{t}</h3><p>{d}</p></div>'
             for i, (t, d) in enumerate(SERVICES, 1)) +
     '</div>' +
     band(['Media wall in marble and fluted oak',
           'Modular kitchen run with marble counter',
           'Wardrobe with amber glass columns']),
     cls='pf-page--band', label='Services')

page('<p class="pf-kicker">03 &mdash; Process</p>'
     '<h2>Five stages, and <em>no surprises</em>.</h2>'
     '<div class="pf-proc">' +
     ''.join(f'<div class="pf-proc__i"><span class="num">{i:02d}</span>'
             f'<h3>{t}</h3><p>{d}</p></div>'
             for i, (t, d) in enumerate(PROCESS, 1)) +
     '</div>' +
     # the process page is the one place site photographs belong: they show
     # the stages the text describes
     band(['Ceiling and curtain track being finished',
           'Timber partition and wardrobe carcass',
           'Corner joinery under installation']),
     cls='pf-page--band', label='Process')

# ----------------------------------------------------------- 4. project pages
sec_no = 4
for folder, name, blurb in SECTIONS:
    items = [m for m in man if m['folder'] == folder]
    if not items:
        continue
    assert HERO.get(folder) in [m['title'] for m in items], \
        f'divider hero missing for {folder}: {HERO.get(folder)}'
    hero = next(m for m in items if m['title'] == HERO[folder])
    rest = [m for m in items if m is not hero]
    page(f'<div class="pf-divider">'
         f'<div class="pf-divider__img">{img(hero)}{tag(hero)}</div>'
         f'<div class="pf-divider__txt">'
         f'<p class="pf-kicker">{sec_no:02d} &mdash; Portfolio</p>'
         f'<h2>{esc(name)}</h2><p class="pf-lede">{esc(blurb)}</p>'
         f'<p class="pf-count num">{len(items)} images</p></div></div>',
         cls='pf-page--divider', label=name)
    sec_no += 1
    per = 6
    for i in range(0, len(rest), per):
        chunk = rest[i:i + per]
        grid = ''.join(f'<figure class="pf-cell">{img(m)}{tag(m)}'
                       f'<figcaption>{esc(m["title"])}</figcaption></figure>' for m in chunk)
        page(f'<div class="pf-gridhead"><h3>{esc(name)}</h3>'
             f'<span class="num">{i + 1}&ndash;{i + len(chunk)} of {len(rest)}</span></div>'
             f'<div class="pf-grid pf-grid--{len(chunk)}">{grid}</div>', label=name)

# ---------------------------------------------------------------- 5. contact
page(f'''<div class="pf-contact">
  <div class="pf-contact__panel">
    <p class="pf-kicker">Contact</p>
    <h2>Let&rsquo;s plan<br><em>your space</em>.</h2>
    <dl class="pf-facts pf-facts--lg">
      <div><dt>Call or WhatsApp</dt><dd>+91 {PHONE}</dd></div>
      <div><dt>Email</dt><dd>{EMAIL}</dd></div>
      <div><dt>Studio</dt><dd>Usha Nagar, Bye Lane 24, Mahabhairab<br>Tezpur 784001, Assam</dd></div>
      <div><dt>Instagram</dt><dd>@interiorbychitra</dd></div>
    </dl>
    <p class="pf-note">Every image in this document is IBC&rsquo;s own work &mdash; completed and
      in-progress projects, and the studio&rsquo;s design drawings for them.</p>
  </div>
  <figure class="pf-contact__img">{img(next(
      m for m in man if m['title'] == 'Living room — drapes and wall sconces'))}</figure>
</div>''', cls='pf-page--contact', label='Contact')

TOTAL = len(pages)
body = '\n'.join(pages)

doc = f'''<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Portfolio — IBC Interior by Chitra | Interior Designer in Tezpur</title>
<meta name="description" content="The full project portfolio of IBC — Interior by Chitra, an interior design studio in Tezpur, Assam. Living rooms, modular kitchens, bathrooms, wardrobes and joinery, with a downloadable PDF.">
<link rel="icon" href="assets/icons/favicon.svg" type="image/svg+xml">
<link rel="icon" href="assets/icons/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="assets/icons/apple-touch-icon.png">
<meta property="og:title" content="Portfolio — IBC Interior by Chitra">
<meta property="og:description" content="Living rooms, modular kitchens, bathrooms and joinery by IBC, Tezpur.">
<meta property="og:type" content="website">
<link rel="stylesheet" href="assets/css/main.css">
<link rel="stylesheet" href="assets/css/portfolio.css">
</head>
<body class="pf-body">

<header class="pf-bar">
  <a class="pf-bar__brand" href="index.html">
    <img src="assets/img/logo-mark.png" alt="" width="34" height="21">
    <span>IBC<small>Interior by Chitra</small></span>
  </a>
  <nav class="pf-bar__nav" aria-label="Portfolio">
    <a href="index.html">&larr; Back to site</a>
    <a class="pf-bar__dl" href="IBC-Interior-by-Chitra-Portfolio.pdf" download>
      <span aria-hidden="true">&#8595;</span> Download PDF</a>
  </nav>
</header>

<main class="pf-doc" id="main">
{body}
</main>

<p class="pf-end">
  <a class="btn btn--solid" href="IBC-Interior-by-Chitra-Portfolio.pdf" download>
    <span>Download this portfolio as PDF</span></a>
  <a class="btn" href="index.html"><span>Back to the website</span></a>
</p>

<a class="wa" href="https://wa.me/{WA}?text=Hello%20IBC%2C%20I%20saw%20your%20portfolio%20and%20would%20like%20to%20discuss%20an%20interior%20project." rel="noopener" target="_blank" aria-label="Chat with IBC on WhatsApp">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12.04 2c-5.46 0-9.9 4.44-9.9 9.9 0 1.74.46 3.45 1.33 4.95L2 22l5.3-1.39a9.86 9.86 0 0 0 4.74 1.21h.01c5.46 0 9.9-4.44 9.9-9.9 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0 0 12.04 2zm0 18.15h-.01a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3.1.81.83-3.03-.2-.31a8.17 8.17 0 0 1-1.26-4.39c0-4.54 3.7-8.23 8.24-8.23 2.2 0 4.27.86 5.82 2.42a8.17 8.17 0 0 1 2.41 5.82c0 4.54-3.69 8.24-8.25 8.24zm4.52-6.17c-.25-.12-1.47-.72-1.69-.81-.23-.08-.39-.12-.56.13-.16.24-.64.8-.78.97-.14.16-.29.18-.54.06-.25-.13-1.05-.39-1.99-1.23-.74-.66-1.23-1.47-1.38-1.72-.14-.25-.01-.38.11-.5.11-.11.25-.29.37-.43.13-.15.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.41-.42-.56-.43h-.48c-.17 0-.43.06-.66.31-.23.25-.86.85-.86 2.07 0 1.22.89 2.4 1.01 2.56.12.17 1.75 2.67 4.23 3.74.59.26 1.05.41 1.41.52.59.19 1.13.16 1.56.1.47-.07 1.47-.6 1.67-1.18.21-.58.21-1.08.15-1.18-.06-.11-.23-.17-.48-.29z"/></svg>
</a>

<script>document.documentElement.classList.remove('no-js');</script>
</body>
</html>
'''

open(f'{SITE}/portfolio.html', 'w').write(doc)
print('portfolio.html pages:', TOTAL)
print('images used:', sum(1 for m in man))
for folder, name, _ in SECTIONS:
    n = len([m for m in man if m['folder'] == folder])
    print(f'  {name:18s} {n:2d}')
