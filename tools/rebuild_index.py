#!/usr/bin/env python3
"""Rebuild the Selected Work folders in index.html from the merged manifest,
remove the Voices section, update the map link and wire in the portfolio page."""
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ROOT = _os.path.dirname(_HERE)          # the site folder
import json, re, html

SITE = _ROOT
man = json.load(open(_os.path.join(_HERE, 'manifest.json')))

ORDER = ['living-room', 'modular-kitchen', 'bathrooms', 'bedrooms',
         'wardrobes', 'shelving', 'ongoing-work']
META = {
 'living-room':    ('Living Room',     'Seating, media walls, feature walls and ceiling details.'),
 'modular-kitchen':('Modular Kitchen', 'Modular runs, marble counters, islands and breakfast bars.'),
 'bathrooms':      ('Bathrooms',       'Vanities, backlit mirrors, stone and walk-in showers.'),
 'bedrooms':       ('Bedrooms',        'Bedroom schemes with fitted storage and panelling.'),
 'wardrobes':      ('Wardrobes',       'Fitted wardrobes, tall units and study desks.'),
 'shelving':       ('Shelving',        'Open joinery, display niches and bench seating.'),
 'ongoing-work':   ('Ongoing Work',    'Joinery currently on site, photographed during execution.'),
}
# cover image per folder, chosen by TITLE — slugs carry a counter that shifts
# whenever the set changes, titles do not.
COVER = {
 'living-room':     'Media wall in marble and fluted oak',
 'modular-kitchen': 'Modular kitchen run with marble counter',
 'bathrooms':       'Dark marble bath with sunken tub',
 'bedrooms':        'Bedroom with study and wardrobe',
 'wardrobes':       'Wardrobe with amber glass columns',
 'shelving':        'Open shelving with study bench',
 'ongoing-work':    'Kitchen joinery under installation',
}


def esc(s):
    return html.escape(s, quote=True)


def tiles(folder):
    out = []
    for m in [x for x in man if x['folder'] == folder]:
        t, k = esc(m['title']), m['kind']
        # Only on-site work carries a badge. The design drawings are the
        # studio's own work for its own schemes, and badging each one made
        # the page read as a list of caveats rather than a portfolio.
        tag = '<span class="tag">On site</span>\n' if k == 'ongoing' else ''
        kind = {'ongoing': 'work in progress'}.get(k, 'an IBC interior')
        out.append(
            f'<figure class="work__item" data-cat="{esc(META[folder][0])}" data-title="{t}">\n'
            f'{tag}'
            f'<button aria-label="Open larger view: {t}" type="button">\n'
            f'<img alt="{t} — {kind} by IBC, Tezpur" '
            f'data-full="assets/img/work/{folder}/{m["slug"]}.webp" decoding="async" '
            f'height="{m["h"]}" loading="lazy" '
            f'src="assets/img/work/{folder}/{m["slug"]}-sm.webp" width="{m["w"]}"/>\n'
            f'</button>\n<figcaption>{t}</figcaption>\n</figure>')
    return '\n'.join(out)


cards, bodies = [], []
for i, folder in enumerate(ORDER, 1):
    items = [x for x in man if x['folder'] == folder]
    if not items:
        continue
    name, blurb = META[folder]
    cover = next((x['slug'] for x in items if x['title'] == COVER.get(folder)),
                 items[0]['slug'])
    assert COVER.get(folder) in [x['title'] for x in items], \
        f'cover title missing for {folder}: {COVER.get(folder)}'
    noun = 'images' if folder != 'ongoing-work' else 'photographs'
    cards.append(
        f'<button aria-expanded="false" class="fcard rv" data-open="{folder}" '
        f'data-scope="work" type="button">\n'
        f'<span aria-hidden="true" class="fcard__stack">\n'
        f'<span class="fcard__sheet"></span><span class="fcard__sheet"></span>\n'
        f'<img alt="" decoding="async" loading="lazy" '
        f'src="assets/img/work/{folder}/{cover}-sm.webp"/>\n</span>\n'
        f'<span class="fcard__meta">\n<span class="fcard__n num">{i:02d}</span>\n'
        f'<span class="fcard__t">{esc(name)}</span>\n'
        f'<span class="fcard__d">{esc(blurb)}</span>\n'
        f'<span class="fcard__c num">{len(items)} {noun}</span>\n</span>\n</button>')
    bodies.append(
        f'<div class="fbody" data-body="{folder}" data-scope="work" hidden="">\n'
        f'<div class="work">\n{tiles(folder)}\n</div>\n</div>')

h = open(f'{SITE}/index.html').read()

# ---- swap the folder grid and the open panel ------------------------------
a = h.index('<div class="fgrid" data-grid="work">')
b = h.index('<div class="fopen" data-panel="work"')
h = h[:a] + '<div class="fgrid" data-grid="work">' + ''.join(cards) + '</div>\n' + h[b:]

a = h.index('<div class="fopen" data-panel="work"')
end_marker = '</div>\n</div>\n</div>\n</section>'
b = h.index('</section>', a)
panel = ('<div class="fopen" data-panel="work" hidden="">\n<div class="fopen__inner">\n'
         '<div class="fopen__bar">\n'
         '<button class="fopen__back" data-close="work" type="button">\n'
         '<span aria-hidden="true">←</span> All folders</button>\n'
         '<h3 class="fopen__t" data-title="work" tabindex="-1"></h3>\n'
         '<span class="fopen__c num" data-count="work"></span>\n</div>\n'
         + '\n'.join(bodies) + '\n</div>\n</div>\n</div>\n</section>')
h = h[:a] + panel + h[b + len('</section>'):]

# ---- remove the Voices section -------------------------------------------
if 'id="voices"' in h:
    a = h.rindex('<section', 0, h.index('id="voices"'))
    b = h.index('</section>', a) + len('</section>')
    h = h[:a] + h[b:].lstrip('\n')
h = h.replace('<span class="num">08</span> — Contact',
              '<span class="num">07</span> — Contact')
h = h.replace('<span class="num">08</span> &mdash; Contact',
              '<span class="num">07</span> &mdash; Contact')

# ---- client's exact map location -----------------------------------------
h = h.replace('https://maps.app.goo.gl/kYUEue5jxnT1ZTCc9',
              'https://maps.app.goo.gl/HRc3474RMWvV86uP8')

# ---- section intro: no per-image labelling, just what the section holds ---
# matches whatever this paragraph currently says, including an earlier run's
# own output, so re-running never leaves half the old wording behind
new_intro = ('IBC projects organised by room — completed interiors and the studio’s own design '
             'work. <em>Ongoing work</em> holds joinery currently on site.')
if new_intro not in h:
    h, n = re.subn(r'(?:Completed )?IBC projects[^<]*?organised by room.*?on site\.',
                   new_intro, h, flags=re.S)
    assert n == 1, f'selected-work intro: {n} matches'

# ---- founder photo: use the new portrait and its small variant ------------
h = h.replace('src="assets/img/studio/chitra-neog.webp"',
              'src="assets/img/studio/chitra-neog-sm.webp"')
h = re.sub(r'(<img alt="Chitra[^>]*?)width="\d+" height="\d+"', r'\1width="702" height="1000"', h)
h = re.sub(r'(<img[^>]*chitra-neog-sm\.webp"[^>]*?)/>',
           r'\1 width="702" height="1000"/>', h)

# ---- portfolio page in the navigation ------------------------------------
# idempotent: only insert if the link is not already there
if 'href="portfolio.html"' not in h:
    h = h.replace('<a href="#tour">360 Tour</a>',
                  '<a href="#tour">360 Tour</a>\n<a href="portfolio.html">Portfolio</a>')
    h = h.replace('<a href="#tour"><span class="num">03</span>360 Tour</a>',
                  '<a href="#tour"><span class="num">03</span>360 Tour</a>\n'
                  '<a href="portfolio.html"><span class="num">04</span>Portfolio</a>')

# ---- repair any hand-written image reference that the rebuild orphaned ----
# The studio collage and the services accordion previews point at specific
# images by name. When an image is dropped from the set those names go dead
# and the browser silently shows nothing, so every missing reference is
# re-pointed at the surviving image whose title shares the most words.
import os

by_slug = {m['slug']: m for m in man}


def best_match(old_slug):
    words = set(old_slug.split('-')[1:-1])
    scored = sorted(man, key=lambda m: -len(
        words & set(m['slug'].split('-')[1:-1])))
    return scored[0]


repaired = []
for ref in sorted(set(re.findall(r'assets/img/work/[^"]+\.webp', h))):
    if os.path.exists(f'{SITE}/{ref}'):
        continue
    folder, fname = ref.split('/')[-2], ref.split('/')[-1]
    small = fname.endswith('-sm.webp')
    old_slug = fname[:-8] if small else fname[:-5]
    m = by_slug.get(old_slug) or best_match(old_slug)
    new = (f"assets/img/work/{m['folder']}/{m['slug']}"
           f"{'-sm' if small else ''}.webp")
    assert os.path.exists(f'{SITE}/{new}'), new
    h = h.replace(ref, new)
    repaired.append((ref.split('/')[-1], m['title']))

open(f'{SITE}/index.html', 'w').write(h)

if repaired:
    print('repaired dead image references:', len(repaired))
    for old, title in repaired:
        print(f'  {old}  ->  {title}')
print('folders:', len(cards))
for f in ORDER:
    n = len([x for x in man if x['folder'] == f])
    if n:
        print(f'  {f:16s} {n}')
print('total tiles:', len(man))
print('voices removed:', 'id="voices"' not in h)
print('new map link:', h.count('HRc3474RMWvV86uP8'))
print('portfolio nav links:', h.count('portfolio.html'))
