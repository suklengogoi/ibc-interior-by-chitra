/* =========================================================================
   IBC — Interior by Chitra · site behaviour (vanilla, no dependencies)
   ========================================================================= */
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  root.classList.remove('no-js');

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced) root.classList.add('reduced');

  function $(s, c) { return (c || doc).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || doc).querySelectorAll(s)); }

  /* ----------------------------------------------------------- preloader */
  var pre = $('#pre');
  if (pre) {
    var seen = false;
    try { seen = sessionStorage.getItem('ibc-seen') === '1'; } catch (e) {}
    var wait = (seen || reduced) ? 60 : 1150;
    var finish = function () {
      pre.classList.add('done');
      try { sessionStorage.setItem('ibc-seen', '1'); } catch (e) {}
      setTimeout(function () { if (pre.parentNode) pre.parentNode.removeChild(pre); }, 800);
      var hero = $('.hero');
      if (hero) hero.classList.add('ready');
    };
    if (seen || reduced) { pre.style.transition = 'none'; finish(); }
    else { window.setTimeout(finish, wait); }
    // never let a stalled asset trap the visitor behind the preloader
    window.setTimeout(finish, 4000);
  }

  /* -------------------------------------------------------------- header */
  var hdr = $('.hdr');
  var lastY = window.pageYOffset;
  var ticking = false;

  function onScroll() {
    var y = window.pageYOffset;
    if (hdr) {
      hdr.classList.toggle('solid', y > 40);
      if (!menuOpen) {
        hdr.classList.toggle('hide', y > lastY && y > 300);
      }
    }
    lastY = y;
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();

  /* ---------------------------------------------------------- mobile menu */
  var burger = $('.burger');
  var menu = $('.menu');
  var menuOpen = false;

  function setMenu(open) {
    menuOpen = open;
    if (!menu || !burger) return;
    menu.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    doc.body.classList.toggle('locked', open);
    menu.setAttribute('aria-hidden', open ? 'false' : 'true');
    if (open) { hdr && hdr.classList.remove('hide'); }
  }

  if (burger) burger.addEventListener('click', function () { setMenu(!menuOpen); });
  if (menu) {
    $$('a', menu).forEach(function (a) {
      a.addEventListener('click', function () { setMenu(false); });
    });
  }
  doc.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && menuOpen) { setMenu(false); burger && burger.focus(); }
  });
  setMenu(false);

  /* ------------------------------------------------------------- reveals */
  var revs = $$('.rv');
  function showAll() { revs.forEach(function (el) { el.classList.add('in'); }); }

  if (reduced || !('IntersectionObserver' in window)) {
    showAll();
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.04 });
    revs.forEach(function (el) { io.observe(el); });

    // safety sweep: nothing may stay invisible after a fast scroll or #anchor jump
    var sweep = function () {
      var vh = window.innerHeight;
      revs.forEach(function (el) {
        if (el.classList.contains('in')) return;
        var r = el.getBoundingClientRect();
        if (r.top < vh * 0.98 && r.bottom > -vh * 0.2) el.classList.add('in');
      });
    };
    window.addEventListener('scroll', sweep, { passive: true });
    window.addEventListener('resize', sweep);
    window.addEventListener('hashchange', function () { setTimeout(sweep, 60); });
    window.addEventListener('load', function () { setTimeout(sweep, 120); });
    setTimeout(sweep, 400);
    setTimeout(showAll, 8000);
  }

  /* ---------------------------------------------------------------- hero */
  var hero = $('.hero');
  if (hero) {
    if (!pre) hero.classList.add('ready');
    var chips = $$('[data-hero-room]', hero);
    var nameEl = $('[data-hero-roomname]', hero);
    var matsEl = $('[data-hero-mats]', hero);

    function paintRoom(i) {
      var r = (window.IBC_ROOMS || [])[i];
      if (!r) return;
      if (nameEl) nameEl.textContent = r.name;
      if (matsEl) {
        matsEl.innerHTML = '';
        (r.materials || []).forEach(function (m, n) {
          var sp = doc.createElement('span');
          sp.style.background = m.hex;
          sp.style.animationDelay = (n * 0.06) + 's';
          sp.title = m.name;
          matsEl.appendChild(sp);
        });
      }
    }

    chips.forEach(function (b) {
      b.addEventListener('click', function () {
        var i = +b.dataset.heroRoom;
        chips.forEach(function (x) {
          x.setAttribute('aria-current', x === b ? 'true' : 'false');
        });
        if (window.IBC_HERO) window.IBC_HERO.go(i);
        paintRoom(i);
      });
    });
    paintRoom(0);
  }

  /* ------------------------------------------------------------- folders */
  var items = $$('.work__item');
  var visible = [];
  var savedScroll = {};

  function bodiesFor(scope) { return $$('.fbody[data-scope="' + scope + '"]'); }

  function refreshVisible() {
    visible = items.filter(function (el) { return el.offsetParent !== null; });
  }

  function openFolder(scope, key, card) {
    var grid = $('.fgrid[data-grid="' + scope + '"]');
    var panel = $('.fopen[data-panel="' + scope + '"]');
    if (!grid || !panel) return;
    savedScroll[scope] = window.pageYOffset;

    bodiesFor(scope).forEach(function (bd) { bd.hidden = bd.dataset.body !== key; });
    var body = $('.fbody[data-body="' + key + '"][data-scope="' + scope + '"]');
    var title = $('[data-title="' + scope + '"]');
    var count = $('[data-count="' + scope + '"]');
    if (title) title.textContent = card ? $('.fcard__t', card).textContent : key;
    if (count && body) {
      var n = $$('figure', body).length;
      count.textContent = n + (scope === 'draw' ? ' renders' : ' photographs');
    }

    panel.hidden = false;
    doc.body.classList.add('folder-open');
    void panel.offsetHeight;          // let the start state paint before animating
    panel.classList.add('is-in');
    $$('.fcard[data-scope="' + scope + '"]').forEach(function (c) {
      c.setAttribute('aria-expanded', c === card ? 'true' : 'false');
    });
    refreshVisible();

    if (!reduced && panel.animate) {
      if (body) {
        $$('figure', body).forEach(function (fig, i) {
          fig.animate([{ opacity: 0, transform: 'translateY(18px) scale(.97)' },
                       { opacity: 1, transform: 'none' }],
                      { duration: 520, delay: Math.min(i, 8) * 55,
                        easing: 'cubic-bezier(.16,.84,.32,1)', fill: 'backwards' });
        });
      }
    }
    if (title) title.focus({ preventScroll: true });
  }

  function closeFolder(scope) {
    var grid = $('.fgrid[data-grid="' + scope + '"]');
    var panel = $('.fopen[data-panel="' + scope + '"]');
    if (!grid || !panel) return;
    var openCard = $('.fcard[data-scope="' + scope + '"][aria-expanded="true"]');

    panel.classList.remove('is-in');
    doc.body.classList.remove('folder-open');
    var finish = function () {
      panel.hidden = true;
      bodiesFor(scope).forEach(function (bd) { bd.hidden = true; });
    };
    if (reduced) finish(); else setTimeout(finish, 420);
    $$('.fcard[data-scope="' + scope + '"]').forEach(function (c) {
      c.setAttribute('aria-expanded', 'false');
    });
    refreshVisible();

    if (savedScroll[scope] !== undefined) {
      // Put the visitor back exactly where they were. The page height changes
      // when the grid returns, so force a layout first, then correct once more
      // on the next frame in case the browser clamped the first attempt.
      var y = savedScroll[scope];
      var jump = function () {
        try { window.scrollTo({ top: y, behavior: 'instant' }); }
        catch (e) { window.scrollTo(0, y); }
      };
      jump();
      requestAnimationFrame(function () { jump(); });
    }


    if (openCard) openCard.focus({ preventScroll: true });
  }

  $$('.fcard').forEach(function (card) {
    card.addEventListener('click', function () {
      openFolder(card.dataset.scope, card.dataset.open, card);
    });
  });
  $$('[data-close]').forEach(function (btn) {
    btn.addEventListener('click', function () { closeFolder(btn.dataset.close); });
  });
  doc.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var open = $('.fopen:not([hidden])');
    if (open && !$('.lb.open')) closeFolder(open.dataset.panel);
  });
  refreshVisible();

  /* ------------------------------------------------------------ lightbox */
  var lb = $('.lb');
  if (lb && items.length) {
    var lbImg = $('.lb__fig img', lb);
    var lbCap = $('.lb__cap', lb);
    var idx = 0, opener = null;

    function open(i, from) {
      refreshVisible();
      idx = i;
      opener = from || null;
      paint();
      lb.classList.add('open');
      lb.setAttribute('aria-hidden', 'false');
      doc.body.classList.add('locked');
      $('.lb__close', lb).focus();
    }
    function close() {
      lb.classList.remove('open');
      lb.setAttribute('aria-hidden', 'true');
      doc.body.classList.remove('locked');
      if (opener) opener.focus();
    }
    function paint() {
      var el = visible[idx];
      if (!el) return;
      var img = $('img', el);
      lbImg.src = img.dataset.full || img.src;
      lbImg.alt = img.alt;
      lbCap.textContent = (el.dataset.title || '') + ' — ' + (el.dataset.cat || '');
    }
    function step(d) { idx = (idx + d + visible.length) % visible.length; paint(); }

    items.forEach(function (it) {
      var btn = $('button', it);
      if (!btn) return;
      btn.addEventListener('click', function () {
        refreshVisible();
        open(visible.indexOf(it), btn);
      });
    });
    $('.lb__close', lb).addEventListener('click', close);
    $('.lb__btn.prev', lb).addEventListener('click', function () { step(-1); });
    $('.lb__btn.next', lb).addEventListener('click', function () { step(1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    doc.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowRight') step(1);
      else if (e.key === 'ArrowLeft') step(-1);
      else return;
      e.preventDefault();
    });
  }

  /* ------------------------------------------------------------ accordion */
  var accItems = $$('.acc__item');
  accItems.forEach(function (item) {
    var btn = $('.acc__btn', item);
    var panel = $('.acc__panel', item);
    var inner = $('.acc__inner', item);
    if (!btn || !panel) return;

    function setOpen(open) {
      item.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      panel.style.height = open ? inner.offsetHeight + 'px' : '0px';
    }
    setOpen(item.classList.contains('open'));
    btn.addEventListener('click', function () {
      var willOpen = !item.classList.contains('open');
      accItems.forEach(function (o) {
        if (o !== item) {
          o.classList.remove('open');
          $('.acc__btn', o).setAttribute('aria-expanded', 'false');
          $('.acc__panel', o).style.height = '0px';
        }
      });
      setOpen(willOpen);
    });
    window.addEventListener('resize', function () {
      if (item.classList.contains('open')) panel.style.height = inner.offsetHeight + 'px';
    });
  });

  /* ------------------------------------------------- accordion hover art */
  var prev = $('.acc__preview');
  if (prev && window.matchMedia('(min-width: 860px)').matches && !reduced) {
    var prevImg = $('img', prev);
    accItems.forEach(function (item) {
      var src = item.dataset.preview;
      if (!src) return;
      item.addEventListener('mouseenter', function () {
        prevImg.src = src; prev.classList.add('on');
      });
      item.addEventListener('mouseleave', function () { prev.classList.remove('on'); });
      item.addEventListener('mousemove', function (e) {
        prev.style.left = e.clientX + 'px';
        prev.style.top = e.clientY + 'px';
      });
    });
  }

  /* --------------------------------------------------------------- video */
  var vids = $$('video[data-lazy]');
  if (vids.length && 'IntersectionObserver' in window) {
    // Wait a beat before fetching: scrolling straight past a reel should not
    // start a download the browser then has to abort.
    var timers = new WeakMap();
    var vio = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        var v = en.target;
        var t = timers.get(v);
        if (t) { clearTimeout(t); timers.delete(v); }
        if (en.isIntersecting && !reduced) {
          timers.set(v, setTimeout(function () {
            timers.delete(v);
            if (!v.dataset.loaded) {
              $$('source', v).forEach(function (s) { s.src = s.dataset.src; });
              v.load();
              v.dataset.loaded = '1';
            }
            var p = v.play();
            if (p && p.catch) p.catch(function () {});
          }, 600));
        } else if (v.dataset.loaded) { v.pause(); }
      });
    }, { threshold: 0.5 });
    vids.forEach(function (v) { vio.observe(v); });
  }

  /* ----------------------------------------------------------------- map */
  var map = $('.map');
  if (map && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (es, obs) {
      es.forEach(function (en) {
        if (!en.isIntersecting) return;
        obs.disconnect();
      });
    }, { rootMargin: '250px' }).observe(map);
  }

  /* ---------------------------------------------------------------- form */
  var form = $('#enquiry');
  if (form) {
    var PHONE = '919365333187';
    var EMAIL = 'Chitraranjanneog38@gmail.com';

    function setErr(name, msg) {
      var f = form.querySelector('[data-field="' + name + '"]');
      if (!f) return;
      f.classList.toggle('bad', !!msg);
      var e = $('.err', f);
      if (e) e.textContent = msg || '';
      var input = $('input, textarea, select', f);
      if (input) input.setAttribute('aria-invalid', msg ? 'true' : 'false');
    }

    function validate() {
      var ok = true;
      var name = form.name_.value.trim();
      var phone = form.phone.value.replace(/[^\d]/g, '');
      if (name.length < 2) { setErr('name', 'Please tell us your name.'); ok = false; }
      else setErr('name', '');
      if (phone.length < 10) { setErr('phone', 'Enter a 10-digit mobile number.'); ok = false; }
      else setErr('phone', '');
      return ok;
    }

    function message() {
      var g = function (n) { return (form[n] && form[n].value || '').trim(); };
      return 'Hello IBC — Interior by Chitra.\n\n'
        + 'Name: ' + g('name_') + '\n'
        + 'Phone: ' + g('phone') + '\n'
        + 'Property: ' + g('ptype') + '\n'
        + 'Scope: ' + g('scope') + '\n'
        + 'Location: ' + (g('city') || '—') + '\n\n'
        + (g('brief') || 'I would like to discuss an interior project.');
    }

    $$('[data-send]', form).forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        if (!validate()) {
          var bad = form.querySelector('.field.bad input, .field.bad textarea');
          if (bad) bad.focus();
          return;
        }
        var body = message();
        if (btn.dataset.send === 'wa') {
          window.open('https://wa.me/' + PHONE + '?text=' + encodeURIComponent(body), '_blank', 'noopener');
        } else {
          window.location.href = 'mailto:' + EMAIL
            + '?subject=' + encodeURIComponent('Interior enquiry — ' + (form.name_.value.trim() || 'Website'))
            + '&body=' + encodeURIComponent(body);
        }
      });
    });

    form.addEventListener('submit', function (e) { e.preventDefault(); });
    ['name_', 'phone'].forEach(function (n) {
      if (form[n]) form[n].addEventListener('input', function () {
        var f = form.querySelector('[data-field="' + (n === 'name_' ? 'name' : n) + '"]');
        if (f && f.classList.contains('bad')) validate();
      });
    });
  }

  /* -------------------------------------------------------------- cursor */
  if (window.matchMedia('(min-width: 1024px) and (hover: hover)').matches && !reduced) {
    var cur2 = doc.createElement('div');
    cur2.className = 'cursor';
    cur2.setAttribute('aria-hidden', 'true');
    doc.body.appendChild(cur2);
    var cx = 0, cy = 0, tx = 0, ty = 0;
    doc.addEventListener('mousemove', function (e) { tx = e.clientX; ty = e.clientY; });
    (function loop() {
      cx += (tx - cx) * 0.18; cy += (ty - cy) * 0.18;
      cur2.style.transform = 'translate3d(' + cx + 'px,' + cy + 'px,0)';
      requestAnimationFrame(loop);
    })();
    doc.addEventListener('mouseover', function (e) {
      var t = e.target.closest ? e.target.closest('a, button, .work__item, .pano__stage') : null;
      cur2.classList.toggle('big', !!t);
    });
  }

  /* ------------------------------------------------------------ year */
  $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
