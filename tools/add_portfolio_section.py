#!/usr/bin/env python3
"""
Give the portfolio its own section on the home page, and renumber what follows.

The portfolio page existed but was reachable only from a nav link, which is the
easiest thing on a page to miss. It now gets a numbered section of its own
directly after Selected Work — the moment a visitor has just finished looking
at rooms is the moment to offer them the whole document.
"""
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ROOT = _os.path.dirname(_HERE)          # the site folder
import re, os, json

SITE = _ROOT
PDF = 'IBC-Interior-by-Chitra-Portfolio.pdf'
h = open(f'{SITE}/index.html').read()
man = json.load(open(_os.path.join(_HERE, 'manifest.json')))
pdf_mb = round(os.path.getsize(f'{SITE}/{PDF}') / 1048576)


def once(old, new, label):
    global h
    assert h.count(old) == 1, f'{label}: {h.count(old)} matches'
    h = h.replace(old, new)


# ---------------------------------------------------------------- the section
section = f'''<section class="section pfp-sec" id="portfolio">
<div class="wrap">
<p class="label rv"><span class="num">03</span> — The portfolio</p>
<div class="pfp">
<div class="pfp__txt">
<h2 class="rv">The whole studio,<br/><em>in one document</em>.</h2>
<p class="lede rv rv-d1" style="margin-top:1.1rem;max-width:46ch">
      Twenty-six pages laid out as real A4 sheets — every room, how the studio works, and how to
      reach it. Read it here, or take the PDF with you.</p>
<dl class="pfp__facts rv rv-d1">
<div><dt>Pages</dt><dd class="num">26</dd></div>
<div><dt>Projects shown</dt><dd class="num">{len(man)}</dd></div>
<div><dt>Format</dt><dd>A4 landscape</dd></div>
</dl>
<div class="pfp__cta rv rv-d2">
<a class="btn btn--solid" href="portfolio.html"><span>Open the portfolio</span></a>
<a class="btn" download="" href="{PDF}"><span>Download PDF · {pdf_mb} MB</span></a>
</div>
</div>
<a aria-label="Open the portfolio" class="pfp__sheets rv rv-d1" href="portfolio.html">
<img alt="" class="pfp__sheet pfp__sheet--3" decoding="async" height="923" loading="lazy" src="assets/img/portfolio/sheet-grid.webp" width="1305"/>
<img alt="" class="pfp__sheet pfp__sheet--2" decoding="async" height="923" loading="lazy" src="assets/img/portfolio/sheet-divider.webp" width="1305"/>
<img alt="The first page of the IBC portfolio document" class="pfp__sheet pfp__sheet--1" decoding="async" height="923" loading="lazy" src="assets/img/portfolio/sheet-cover.webp" width="1305"/>
<span class="pfp__badge num">26 pages</span>
</a>
</div>
</div>
</section>
'''

# slot it in directly before the 360 tour, i.e. straight after Selected Work
anchor = '<section class="section section--dark tour" id="tour">'
once(anchor, section + anchor, 'tour section anchor')

# ------------------------------------------------------------- renumber 03-08
for old, new, name in ((3, 4, 'Step inside'), (4, 5, 'Services'),
                       (5, 6, 'Process'), (6, 7, 'On site'), (7, 8, 'Contact')):
    pat = f'<span class="num">{old:02d}</span> — {name}'
    assert h.count(pat) == 1, f'renumber {name}: {h.count(pat)} matches'
    h = h.replace(pat, f'<span class="num">{new:02d}</span> — {name}')

# ------------------------------------------------------------------- the navs
once('<a href="#tour">360 Tour</a>\n<a href="portfolio.html">Portfolio</a>',
     '<a href="#tour">360 Tour</a>\n'
     '<a class="hdr__nav-pf" href="#portfolio">Portfolio</a>',
     'desktop nav')

# the mobile menu had two 04s; rebuild it with the new order
old_menu = ('<a href="#studio"><span class="num">01</span>Studio</a>\n'
            '<a href="#work"><span class="num">02</span>Work</a>\n'
            '<a href="#tour"><span class="num">03</span>360 Tour</a>\n'
            '<a href="portfolio.html"><span class="num">04</span>Portfolio</a>\n'
            '<a href="#services"><span class="num">04</span>Services</a>\n'
            '<a href="#process"><span class="num">05</span>Process</a>\n'
            '<a href="#contact"><span class="num">06</span>Contact</a>')
new_menu = ('<a href="#studio"><span class="num">01</span>Studio</a>\n'
            '<a href="#work"><span class="num">02</span>Work</a>\n'
            '<a href="#portfolio"><span class="num">03</span>Portfolio</a>\n'
            '<a href="#tour"><span class="num">04</span>360 Tour</a>\n'
            '<a href="#services"><span class="num">05</span>Services</a>\n'
            '<a href="#process"><span class="num">06</span>Process</a>\n'
            '<a href="#contact"><span class="num">07</span>Contact</a>')
once(old_menu, new_menu, 'mobile menu')

open(f'{SITE}/index.html', 'w').write(h)
print('portfolio section added; sections renumbered to 08')
print('nav links ->', h.count('href="#portfolio"'), 'in-page,',
      h.count('href="portfolio.html"'), 'to the page')
