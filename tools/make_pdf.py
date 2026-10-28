#!/usr/bin/env python3
"""
Print portfolio.html to PDF.

The PDF comes from the same file the visitor scrolls, so the download always
matches the page. Lazy loading has to be switched off first, or Chromium
prints the pages that never scrolled into view with empty image boxes.
"""
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ROOT = _os.path.dirname(_HERE)          # the site folder
import os, sys, json, glob
from PIL import Image
from playwright.sync_api import sync_playwright

SITE = _ROOT
OUT = f'{SITE}/IBC-Interior-by-Chitra-Portfolio.pdf'


def build_print_jpegs():
    """JPEG copies of every image, made fresh each run.

    Chromium re-encodes WebP into a PDF losslessly and the file reaches
    163 MB; it passes JPEG data straight through instead. 1400px is more
    than the largest box on any sheet (the full-bleed divider image is
    178mm wide, so this is about 200dpi). These are build artefacts and are
    not committed — .gitignore keeps them out.
    """
    man = json.load(open(_os.path.join(_HERE, 'manifest.json')))
    jobs = [(f"{SITE}/assets/img/work/{m['folder']}/{m['slug']}.webp",
             f"{SITE}/assets/img/print/work/{m['folder']}/{m['slug']}.jpg", 82)
            for m in man]
    jobs.append((f'{SITE}/assets/img/studio/chitra-neog.webp',
                 f'{SITE}/assets/img/print/studio/chitra-neog.jpg', 85))
    made = 0
    for src, dst, q in jobs:
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im = Image.open(src).convert('RGB')
        im.thumbnail((1400, 1400), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=q, optimize=True)
        made += 1
    print(f'print jpegs: {made} rebuilt, {len(jobs)} total')


build_print_jpegs()

with sync_playwright() as p:
    b = p.chromium.launch(args=['--allow-file-access-from-files'])
    pg = b.new_context(viewport={'width': 1400, 'height': 1000}).new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:80]))
    pg.goto('file://' + SITE + '/portfolio.html', wait_until='load')

    # Swap in the print JPEGs. Chromium's PDF writer re-encodes WebP losslessly
    # and the file balloons to ~160 MB; it passes JPEG data straight through,
    # so the same pages come out around a tenth of the size at the same
    # on-page resolution. Nothing about the layout changes.
    pg.evaluate("""
      [...document.images].forEach(i => {
        const m = i.getAttribute('src')
          .match(/assets\\/img\\/(work|studio)\\/(.+?)(-sm)?\\.webp$/);
        if (m) i.src = `assets/img/print/${m[1]}/${m[2]}.jpg`;
        i.removeAttribute('srcset');
      });
    """)

    # force every image to load, then wait for each one to actually decode
    pg.evaluate("[...document.images].forEach(i => { i.loading = 'eager'; })")
    pg.wait_for_function(
        "() => [...document.images].every(i => i.complete && i.naturalWidth > 0)",
        timeout=120000)
    pg.wait_for_timeout(1200)

    total = pg.evaluate("document.querySelectorAll('.pf-page').length")
    loaded = pg.evaluate("[...document.images].filter(i=>i.naturalWidth>0).length")
    print(f'pages {total}, images decoded {loaded}/{pg.evaluate("document.images.length")}')

    pg.pdf(path=OUT, width='297mm', height='210mm', landscape=False,
           print_background=True, prefer_css_page_size=True,
           margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
    b.close()

size = os.path.getsize(OUT)
print(f'PDF {size/1024/1024:.2f} MB -> {OUT}')
if errs:
    print('page errors:', errs[:3])
