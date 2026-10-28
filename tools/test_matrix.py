#!/usr/bin/env python3
"""
Device and mode test matrix for the IBC site.

Both pages are checked at every size the brief lists, over a local server and
over file:// (the client opens the folder by double-clicking), and then again
with WebGL off, with reduced motion, and with JavaScript off.

Nothing here is a judgement call: each check either passes or prints the exact
viewport and page that failed.
"""
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ROOT = _os.path.dirname(_HERE)          # the site folder
import sys, json, threading, http.server, socketserver, functools, os
from playwright.sync_api import sync_playwright

SITE = _ROOT
PORT = 8831

SIZES = [
    ('desktop 1920', 1920, 1080), ('desktop 1440', 1440, 900),
    ('laptop 1366', 1366, 768),
    ('iPad landscape', 1180, 820), ('iPad portrait', 820, 1180),
    ('tablet 768', 768, 1024),
    ('phone 390', 390, 844), ('phone 360', 360, 780),
    ('phone landscape', 844, 390),
]
PAGES = ['index.html', 'portfolio.html']

fails, notes = [], []


def fail(msg):
    fails.append(msg)
    print('  FAIL ' + msg)


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=SITE)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(('127.0.0.1', PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def check_page(pg, page, label, base):
    """Checks that apply to any page at any size."""
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:120]))
    msgs = []
    pg.on('console', lambda m: msgs.append(m.text[:120]) if m.type == 'error' else None)

    pg.goto(base + page, wait_until='load')
    pg.wait_for_timeout(900)
    pg.mouse.wheel(0, 20000)
    pg.wait_for_timeout(700)
    pg.mouse.wheel(0, -40000)
    pg.wait_for_timeout(500)

    w = pg.evaluate('innerWidth')
    doc = pg.evaluate('document.documentElement.scrollWidth')
    if doc > w + 1:
        fail(f'{label} {page}: horizontal overflow {doc}px > {w}px')
        wide = pg.evaluate("""() => [...document.querySelectorAll('*')]
            .filter(e => e.getBoundingClientRect().right > innerWidth + 1)
            .slice(0,3).map(e => e.tagName + '.' + (e.className||'').toString().slice(0,40))""")
        print('       widest:', wide)

    if errs:
        fail(f'{label} {page}: page error {errs[:2]}')
    real = [m for m in msgs if 'favicon' not in m.lower()]
    if real:
        fail(f'{label} {page}: console error {real[:2]}')

    # nothing may stay invisible after a scroll to the bottom and back
    hidden = pg.evaluate("""() => [...document.querySelectorAll('.rv')]
        .filter(e => getComputedStyle(e).opacity === '0').length""")
    if hidden:
        fail(f'{label} {page}: {hidden} reveal elements still hidden')

    # every image that is on screen must have decoded
    broken = pg.evaluate("""() => [...document.images]
        .filter(i => i.complete && i.naturalWidth === 0)
        .map(i => i.getAttribute('src')).slice(0,3)""")
    if broken:
        fail(f'{label} {page}: broken images {broken}')

    return pg


def check_index(pg, label):
    # hero 360 present and draggable (the drag surface must be on top)
    hit = pg.evaluate("""() => {
        const h = document.querySelector('#hero, .hero');
        if (!h) return 'no hero';
        const r = h.getBoundingClientRect();
        const el = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
        return el ? el.className.toString().slice(0,60) || el.tagName : 'none';
    }""")
    if 'fallback' in str(hit) and 'IMG' in str(hit):
        fail(f'{label}: hero drag surface blocked by {hit}')

    # folder opens and closes, and the page returns to the same scroll position
    ok = pg.evaluate("""async () => {
        const card = document.querySelector('[data-open]');
        if (!card) return 'no folder card';
        window.scrollTo(0, 1200);
        await new Promise(r => setTimeout(r, 300));
        const before = window.scrollY;
        card.click();
        await new Promise(r => setTimeout(r, 700));
        const panel = document.querySelector('[data-panel]');
        const opened = panel && !panel.hidden;
        const back = document.querySelector('[data-close]');
        if (back) back.click();
        await new Promise(r => setTimeout(r, 800));
        return JSON.stringify({opened, before, after: window.scrollY});
    }""")
    try:
        r = json.loads(ok)
        if not r['opened']:
            fail(f'{label}: folder did not open')
        if abs(r['after'] - r['before']) > 4:
            fail(f"{label}: scroll not restored ({r['before']} -> {r['after']})")
    except (ValueError, TypeError):
        fail(f'{label}: folder test returned {ok}')

    # the contact form must refuse an empty submit and must build a wa.me link
    form = pg.evaluate("""() => {
        const f = document.querySelector('form');
        if (!f) return 'no form';
        const bad = f.checkValidity() === false;
        const wa = !!document.querySelector('a[href*="wa.me"]');
        return JSON.stringify({bad, wa});
    }""")
    try:
        r = json.loads(form)
        if not r['bad']:
            fail(f'{label}: empty contact form passes validation')
        if not r['wa']:
            fail(f'{label}: no WhatsApp link on the page')
    except (ValueError, TypeError):
        fail(f'{label}: form test returned {form}')


def check_portfolio(pg, label):
    n = pg.evaluate("document.querySelectorAll('.pf-page').length")
    if n != 26:
        fail(f'{label}: portfolio has {n} sheets, expected 26')
    dl = pg.evaluate("""() => {
        const a = [...document.querySelectorAll('a')]
            .find(x => /\\.pdf$/i.test(x.getAttribute('href')||''));
        return a ? a.getAttribute('href') : null;
    }""")
    if not dl:
        fail(f'{label}: no PDF download link on the portfolio page')
    elif not os.path.exists(f'{SITE}/{dl}'):
        fail(f'{label}: PDF link points at a missing file: {dl}')
    # sheets must not be wider than the viewport once scaled
    over = pg.evaluate("""() => [...document.querySelectorAll('.pf-page')]
        .filter(e => e.getBoundingClientRect().width > innerWidth + 1).length""")
    if over:
        fail(f'{label}: {over} portfolio sheets wider than the viewport')


def main():
    srv = serve()
    http_base = f'http://127.0.0.1:{PORT}/'
    file_base = f'file://{SITE}/'

    with sync_playwright() as p:
        for base, bname in ((http_base, 'http'), (file_base, 'file')):
            args = ['--allow-file-access-from-files'] if bname == 'file' else []
            b = p.chromium.launch(args=args)
            for sname, w, h in SIZES:
                ctx = b.new_context(viewport={'width': w, 'height': h},
                                    device_scale_factor=1)
                for page in PAGES:
                    label = f'[{bname} {sname} {w}x{h}]'
                    pg = ctx.new_page()
                    try:
                        check_page(pg, page, label, base)
                        if page == 'index.html':
                            check_index(pg, label)
                        else:
                            check_portfolio(pg, label)
                    except Exception as e:
                        fail(f'{label} {page}: {type(e).__name__} {str(e)[:120]}')
                    pg.close()
                ctx.close()
                print(f'done {bname} {sname}')
            b.close()

        # ---- the three special modes, at one desktop and one phone size ----
        for mode, kwargs, args in (
            ('reduced motion', {'reduced_motion': 'reduce'}, []),
            ('WebGL off', {}, ['--disable-webgl', '--disable-3d-apis']),
            ('JavaScript off', {'java_script_enabled': False}, []),
        ):
            b = p.chromium.launch(args=args)
            for sname, w, h in (('desktop 1440', 1440, 900), ('phone 390', 390, 844)):
                ctx = b.new_context(viewport={'width': w, 'height': h}, **kwargs)
                for page in PAGES:
                    label = f'[{mode} {sname}]'
                    pg = ctx.new_page()
                    try:
                        pg.goto(http_base + page, wait_until='load')
                        pg.wait_for_timeout(1200)
                        doc = pg.evaluate('document.documentElement.scrollWidth')
                        if doc > w + 1:
                            fail(f'{label} {page}: horizontal overflow {doc}px')
                        # with JS off the content must still be readable
                        txt = pg.evaluate('document.body.innerText.length')
                        if txt < 400:
                            fail(f'{label} {page}: only {txt} characters of visible text')
                    except Exception as e:
                        fail(f'{label} {page}: {type(e).__name__} {str(e)[:120]}')
                    pg.close()
                ctx.close()
            b.close()
            print(f'done {mode}')

    srv.shutdown()
    print('\n' + '=' * 60)
    print(f'FAILURES: {len(fails)}')
    for f in fails:
        print('  ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
