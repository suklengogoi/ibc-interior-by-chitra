/* =========================================================================
   IBC 360 room viewer  —  no libraries, no build step.

   Three renderers, chosen automatically:
     webgl  textured cylinder (best, needs http/https)
     css    CSS 3D cylinder of panels (works from file://)
     flat   scrollable strip (last resort)

   WebGL cannot read images loaded from file://, so opening index.html
   straight off the disk falls back to the CSS renderer on purpose.
   Force one with  ?pano=webgl | css | flat
   ========================================================================= */
(function () {
  'use strict';

  var ROOMS = window.IBC_ROOMS || [];
  if (!ROOMS.length) return;

  window.IBCPano = function (sectionEl, opts) {
  opts = opts || {};
  if (!sectionEl) return;
  var root = sectionEl.querySelector('.pano');
  if (!root) return;

  var stageEl = root.querySelector('[data-pano-stage]');
  var tabsEl = sectionEl.querySelector('[data-pano-tabs]');
  var matsEl = sectionEl.querySelector('[data-pano-mats]');
  var hintEl = root.querySelector('[data-pano-hint]');
  var modeEl = root.querySelector('[data-pano-mode]');
  var liveEl = sectionEl.querySelector('[data-pano-live]');
  var btnFull = root.querySelector('[data-pano-full]');
  var btnSpin = root.querySelector('[data-pano-spin]');
  var btnLeft = root.querySelector('[data-pano-left]');
  var btnRight = root.querySelector('[data-pano-right]');

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------------ renderer */
  function param(name) {
    var m = new RegExp('[?&]' + name + '=([^&]+)').exec(location.search);
    return m ? decodeURIComponent(m[1]) : null;
  }

  function webglOK() {
    if (location.protocol === 'file:') return false;
    try {
      var c = document.createElement('canvas');
      var gl = c.getContext('webgl') || c.getContext('experimental-webgl');
      if (!gl) return false;
      var lose = gl.getExtension('WEBGL_lose_context');
      if (lose) lose.loseContext();
      return true;
    } catch (e) { return false; }
  }

  var forced = param('pano');
  if (forced === 'css') forced = 'canvas';          // older links keep working
  var MODE = forced === 'webgl' || forced === 'canvas' || forced === 'flat'
    ? forced
    : (webglOK() ? 'webgl' : 'canvas');

  /* --------------------------------------------------------------- state */
  var state = {
    room: opts.room || 0, yaw: 0, zoom: opts.zoom || 1, spin: !reduced,
    vel: 0, dragging: false, lastX: 0, lastY: 0, pitch: opts.pitch || 0,
    target: null, img: null, ready: false
  };

  var MIN_ZOOM = 1.0, MAX_ZOOM = 2.8;

  function room() { return ROOMS[state.room]; }

  function yawLimits() {
    var r = room();
    var vis = visibleFov();
    if (r.hfov >= 352) return null;               // effectively a full turn
    var half = Math.max(0, (r.hfov - vis) / 2);
    return [-half, half];
  }

  function visibleFov() {
    // horizontal degrees currently on screen
    var r = room();
    var box = stageEl.getBoundingClientRect();
    var f = pxPerDeg();
    return box.width / f;
  }

  function pxPerDeg() {
    var r = room();
    var box = stageEl.getBoundingClientRect();
    var scale = (box.height / r.h) * state.zoom;
    return (r.w / r.hfov) * scale;
  }

  function clampYaw() {
    var lim = yawLimits();
    if (!lim) {
      if (state.yaw > 180) state.yaw -= 360;
      if (state.yaw < -180) state.yaw += 360;
    } else {
      if (state.yaw < lim[0]) { state.yaw = lim[0]; state.vel = 0; }
      if (state.yaw > lim[1]) { state.yaw = lim[1]; state.vel = 0; }
    }
  }

  /* ------------------------------------------------------------ renderers */
  var renderer = null;

  /* Canvas 2D cylindrical renderer.
     Re-projects the cylindrical panorama into a proper rectilinear view, one
     thin vertical strip at a time. Each screen column maps to a vertical line
     in the source, so a plain drawImage per strip is geometrically exact —
     no panel seams, and it works from file:// because we never read pixels
     back off the canvas (which is what would taint it). */
  function CanvasRenderer() {
    var canvas = document.createElement('canvas');
    canvas.className = 'pano-canvas';
    this.el = canvas;
    var ctx = canvas.getContext('2d');
    var img = null, cur = null, dpr = 1, W = 0, H = 0;

    this.build = function (r, src, imgEl) {
      cur = r;
      img = imgEl;
      this.layout();
    };

    this.layout = function () {
      var box = stageEl.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = Math.max(1, Math.round(box.width));
      H = Math.max(1, Math.round(box.height));
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      canvas.style.width = W + 'px';
      canvas.style.height = H + 'px';
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
    };

    this.focal = function () {
      if (!cur) return 1;
      var fPano = cur.w / (cur.hfov * Math.PI / 180);
      return fPano * (H * state.zoom) / cur.h;      // screen focal, css px
    };

    this.draw = function () {
      if (!img || !cur || !W) return;
      var fPano = cur.w / (cur.hfov * Math.PI / 180);
      var fs = this.focal();
      var yaw = state.yaw * Math.PI / 180;
      var step = W > 1100 ? 4 : 3;
      var halfW = W / 2;
      var pitchPx = Math.tan(state.pitch * Math.PI / 180) * fs;

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = '#17140f';
      ctx.fillRect(0, 0, W, H);

      for (var x = 0; x < W; x += step) {
        var xs = x + step / 2 - halfW;
        var d = Math.sqrt(xs * xs + fs * fs);
        var theta = Math.atan(xs / fs) + yaw;   // sign must match the WebGL path
        var u = cur.w / 2 + fPano * theta;
        // width of this strip measured back in the source image
        var dTheta = step * fs / (xs * xs + fs * fs);
        var su = fPano * dTheta;
        if (u + su < 0 || u > cur.w) continue;
        var destH = cur.h * d / fPano;
        var sx = u - su / 2;
        var sw = su;
        if (sx < 0) { sw += sx; sx = 0; }
        if (sx + sw > cur.w) sw = cur.w - sx;
        if (sw <= 0) continue;
        try {
          ctx.drawImage(img, sx, 0, sw, cur.h,
                        x, (H - destH) / 2 + pitchPx, step + 1, destH);
        } catch (e) { return; }
      }
    };

    this.destroy = function () { img = null; };
  }

  function FlatRenderer() {
    var wrap = document.createElement('div');
    wrap.className = 'pano-flat';
    var img = document.createElement('img');
    img.alt = '';
    wrap.appendChild(img);
    this.el = wrap;
    var cur = null;
    this.build = function (r, src) { cur = r; img.src = src; this.layout(); };
    this.layout = function () {
      if (!cur) return;
      var box = stageEl.getBoundingClientRect();
      img.style.height = (box.height * state.zoom) + 'px';
      img.style.width = 'auto';
    };
    this.draw = function () {
      if (!cur) return;
      var box = stageEl.getBoundingClientRect();
      var total = img.offsetWidth;
      var span = Math.max(1, total - box.width);
      var lim = (cur.hfov >= 352) ? 180 : cur.hfov / 2;
      var t = (state.yaw + lim) / (2 * lim);
      wrap.scrollLeft = t * span;
    };
    this.destroy = function () { img.removeAttribute('src'); };
  }

  function GlRenderer() {
    var canvas = document.createElement('canvas');
    canvas.className = 'pano-gl';
    this.el = canvas;
    var gl = canvas.getContext('webgl', { alpha: false, antialias: true });
    var prog, buf, tex, loc = {}, cur = null, count = 0;

    var VS = 'attribute vec3 p;attribute vec2 t;uniform mat4 m;varying vec2 v;' +
      'void main(){v=t;gl_Position=m*vec4(p,1.0);}';
    var FS = 'precision mediump float;varying vec2 v;uniform sampler2D s;' +
      'void main(){gl_FragColor=texture2D(s,v);}';

    function sh(type, src) {
      var s = gl.createShader(type);
      gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error('shader');
      return s;
    }

    prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    gl.useProgram(prog);
    loc.p = gl.getAttribLocation(prog, 'p');
    loc.t = gl.getAttribLocation(prog, 't');
    loc.m = gl.getUniformLocation(prog, 'm');
    buf = gl.createBuffer();

    this.build = function (r, src, imgEl) {
      cur = r;
      var seg = 128, data = [], hr = r.hfov * Math.PI / 180;
      var hh = Math.tan((r.vfov / 2) * Math.PI / 180);
      for (var i = 0; i < seg; i++) {
        for (var k = 0; k < 2; k++) {
          var a0 = -hr / 2 + hr * (i + k) / seg;
          var u = (i + k) / seg;
          data.push(Math.sin(a0), hh, -Math.cos(a0), u, 0);
          data.push(Math.sin(a0), -hh, -Math.cos(a0), u, 1);
        }
      }
      count = data.length / 5;
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(data), gl.STATIC_DRAW);
      if (tex) gl.deleteTexture(tex);
      tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, imgEl);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      this.layout();
    };

    this.layout = function () {
      var box = stageEl.getBoundingClientRect();
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.round(box.width * dpr));
      canvas.height = Math.max(1, Math.round(box.height * dpr));
      gl.viewport(0, 0, canvas.width, canvas.height);
    };

    this.draw = function () {
      if (!cur || !tex) return;
      var box = stageEl.getBoundingClientRect();
      var aspect = box.width / Math.max(1, box.height);
      var vf = (cur.vfov / state.zoom) * Math.PI / 180;
      var fy = 1 / Math.tan(vf / 2), near = 0.1, far = 10;
      var proj = [fy / aspect, 0, 0, 0, 0, fy, 0, 0, 0, 0,
        (far + near) / (near - far), -1, 0, 0, 2 * far * near / (near - far), 0];
      var y = state.yaw * Math.PI / 180, c = Math.cos(y), s = Math.sin(y);
      var yawM = [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1];
      var px = state.pitch * Math.PI / 180, cp = Math.cos(px), sp = Math.sin(px);
      var pitchM = [1, 0, 0, 0, 0, cp, sp, 0, 0, -sp, cp, 0, 0, 0, 0, 1];
      var m = mul(proj, mul(pitchM, yawM));
      gl.clearColor(0.09, 0.08, 0.07, 1);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(prog);
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.enableVertexAttribArray(loc.p);
      gl.vertexAttribPointer(loc.p, 3, gl.FLOAT, false, 20, 0);
      gl.enableVertexAttribArray(loc.t);
      gl.vertexAttribPointer(loc.t, 2, gl.FLOAT, false, 20, 12);
      gl.uniformMatrix4fv(loc.m, false, new Float32Array(m));
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, count);
    };

    this.destroy = function () { if (tex) gl.deleteTexture(tex); };

    function mul(a, b) {
      var o = new Array(16);
      for (var i = 0; i < 4; i++)
        for (var j = 0; j < 4; j++) {
          var v = 0;
          for (var k = 0; k < 4; k++) v += a[k * 4 + j] * b[i * 4 + k];
          o[i * 4 + j] = v;
        }
      return o;
    }
  }

  function makeRenderer(mode) {
    try {
      if (mode === 'webgl') return new GlRenderer();
      if (mode === 'flat') return new FlatRenderer();
      return new CanvasRenderer();
    } catch (e) {
      return null;
    }
  }

  function setMode(mode) {
    if (renderer) { try { renderer.destroy(); } catch (e) {} }
    stageEl.innerHTML = '';
    renderer = makeRenderer(mode);
    if (!renderer && mode !== 'flat') { MODE = 'flat'; renderer = makeRenderer('flat'); }
    MODE = mode;
    stageEl.appendChild(renderer.el);
    if (modeEl) {
      modeEl.textContent = mode === 'webgl' ? 'WebGL' : (mode === 'canvas' ? 'Canvas 3D' : 'Flat');
    }
    root.dataset.mode = mode;
  }

  /* ----------------------------------------------------------- room load */
  function load(i, announce) {
    state.room = i;
    state.yaw = ROOMS[i] && typeof ROOMS[i].startYaw === 'number' ? ROOMS[i].startYaw : 0;
    swayBase = state.yaw;
    swayT = 0;
    state.vel = 0;
    state.zoom = opts.zoom || 1;
    state.pitch = opts.pitch || 0;
    state.ready = false;
    var r = room();
    root.classList.add('is-loading');

    Array.prototype.forEach.call((tabsEl ? tabsEl.querySelectorAll('button') : []), function (b, n) {
      b.setAttribute('aria-selected', n === i ? 'true' : 'false');
      b.tabIndex = n === i ? 0 : -1;
    });
    buildMaterials(r);

    var preview = new Image();
    preview.onload = function () {
      if (state.room !== i) return;
      applyImage(r, r.preview, preview);
      root.classList.remove('is-loading');
      var full = new Image();
      full.onload = function () {
        if (state.room !== i) return;
        applyImage(r, r.src, full);
        state.ready = true;
      };
      full.onerror = function () { state.ready = true; };
      full.src = r.src;
    };
    preview.onerror = function () {
      root.classList.remove('is-loading');
      if (MODE !== 'flat') { setMode('flat'); }
    };
    preview.src = r.preview;

    if (announce && liveEl) liveEl.textContent = r.name + ' — drag to look around.';
  }

  function applyImage(r, src, imgEl) {
    try {
      renderer.build(r, src, imgEl);
    } catch (e) {
      // a WebGL texture upload can fail (file://, memory) — step down a level
      if (MODE === 'webgl') { setMode('canvas'); renderer.build(r, src, imgEl); }
      else if (MODE === 'canvas') { setMode('flat'); renderer.build(r, src, imgEl); }
    }
    clampYaw();
    renderer.draw();
    if (opts.hero) {
      var media = document.getElementById('hero-pano');
      if (media) media.classList.add('is-live');
    }
  }

  /* ------------------------------------------------------- material chips */
  function buildMaterials(r) {
    if (!matsEl) return;
    matsEl.innerHTML = '';
    (r.materials || []).forEach(function (m) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'mat';
      b.innerHTML = '<span class="mat__dot" style="background:' + m.hex + '"></span>' +
        '<span class="mat__name">' + m.name + '</span>';
      b.title = 'Look at the ' + m.name.toLowerCase();
      b.addEventListener('click', function () {
        state.target = m.yaw;
        state.spin = false;
        syncSpin();
        if (liveEl) liveEl.textContent = 'Looking at ' + m.name + '.';
      });
      matsEl.appendChild(b);
    });
  }

  /* --------------------------------------------------------- interaction */
  function onDown(x, y, e) {
    state.dragging = true;
    state.lastX = x; state.lastY = y;
    state.vel = 0; state.target = null;
    root.classList.add('is-grabbing');
    if (hintEl) hintEl.classList.add('is-hidden');
  }

  function onMove(x, y) {
    if (!state.dragging) return;
    var dx = x - state.lastX, dy = y - state.lastY;
    state.lastX = x; state.lastY = y;
    var deg = dx / Math.max(1, pxPerDeg());
    state.yaw -= deg;                       // content follows the finger
    state.vel = -deg;
    state.pitch = Math.max(-14, Math.min(14, state.pitch + dy * 0.05));
    clampYaw();
  }

  function onUp() {
    state.dragging = false;
    root.classList.remove('is-grabbing');
    swayBase = state.yaw;      // sway resumes from wherever they left it
    swayT = 0;
  }

  stageEl.addEventListener('mousedown', function (e) {
    e.preventDefault(); onDown(e.clientX, e.clientY, e);
  });
  window.addEventListener('mousemove', function (e) { onMove(e.clientX, e.clientY); });
  window.addEventListener('mouseup', onUp);

  var pinch = null;
  stageEl.addEventListener('touchstart', function (e) {
    if (e.touches.length === 2) {
      pinch = dist(e.touches); state.dragging = false;
    } else {
      onDown(e.touches[0].clientX, e.touches[0].clientY, e);
    }
  }, { passive: true });

  stageEl.addEventListener('touchmove', function (e) {
    if (e.touches.length === 2 && pinch) {
      var d = dist(e.touches);
      setZoom(state.zoom * (d / pinch));
      pinch = d;
      e.preventDefault();
      return;
    }
    if (state.dragging) {
      onMove(e.touches[0].clientX, e.touches[0].clientY);
      e.preventDefault();
    }
  }, { passive: false });

  stageEl.addEventListener('touchend', function () { pinch = null; onUp(); });

  function dist(t) {
    var dx = t[0].clientX - t[1].clientX, dy = t[0].clientY - t[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }

  stageEl.addEventListener('wheel', function (e) {
    if (!e.ctrlKey) return;              // plain scroll still scrolls the page
    e.preventDefault();
    setZoom(state.zoom * (e.deltaY < 0 ? 1.08 : 0.93));
  }, { passive: false });

  function setZoom(z) {
    state.zoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, z));
    if (renderer && renderer.layout) renderer.layout();
    clampYaw();
  }

  stageEl.setAttribute('tabindex', '0');
  stageEl.addEventListener('keydown', function (e) {
    var k = e.key, step = 6;
    if (k === 'ArrowLeft') { state.yaw -= step; state.target = null; }
    else if (k === 'ArrowRight') { state.yaw += step; state.target = null; }
    else if (k === 'ArrowUp') { state.pitch = Math.min(14, state.pitch + 2); }
    else if (k === 'ArrowDown') { state.pitch = Math.max(-14, state.pitch - 2); }
    else if (k === '+' || k === '=') { setZoom(state.zoom * 1.1); }
    else if (k === '-') { setZoom(state.zoom * 0.9); }
    else return;
    e.preventDefault();
    state.spin = false; syncSpin(); clampYaw();
  });

  if (btnLeft) btnLeft.addEventListener('click', function () {
    state.yaw -= 25; state.spin = false; syncSpin(); clampYaw();
  });
  if (btnRight) btnRight.addEventListener('click', function () {
    state.yaw += 25; state.spin = false; syncSpin(); clampYaw();
  });

  function syncSpin() {
    if (!btnSpin || !btnSpin.querySelector('[data-spin-label]')) return;
    btnSpin.setAttribute('aria-pressed', state.spin ? 'true' : 'false');
    btnSpin.querySelector('[data-spin-label]').textContent =
      state.spin ? 'Pause' : 'Auto-rotate';
  }

  if (btnSpin) btnSpin.addEventListener('click', function () {
    state.spin = !state.spin; state.target = null; syncSpin();
  });

  /* ------------------------------------------------------------ fullscreen */
  function fsSupported() {
    return !!(root.requestFullscreen || root.webkitRequestFullscreen);
  }

  if (btnFull) btnFull.addEventListener('click', function () {
    var isPseudo = root.classList.contains('is-pseudo-full');
    var inFs = document.fullscreenElement || document.webkitFullscreenElement;
    if (inFs) {
      (document.exitFullscreen || document.webkitExitFullscreen).call(document);
      return;
    }
    if (isPseudo) { root.classList.remove('is-pseudo-full'); relayout(); return; }
    if (fsSupported()) {
      var p = (root.requestFullscreen || root.webkitRequestFullscreen).call(root);
      if (p && p.catch) p.catch(pseudo);
    } else { pseudo(); }
    function pseudo() { root.classList.add('is-pseudo-full'); relayout(); }
  });

  document.addEventListener('fullscreenchange', relayout);
  document.addEventListener('webkitfullscreenchange', relayout);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && root.classList.contains('is-pseudo-full')) {
      root.classList.remove('is-pseudo-full'); relayout();
    }
  });

  function relayout() {
    setTimeout(function () {
      if (renderer && renderer.layout) renderer.layout();
      clampYaw();
      if (renderer) renderer.draw();
    }, 60);
  }

  window.addEventListener('resize', relayout);
  window.addEventListener('orientationchange', relayout);

  /* ------------------------------------------------------------- tabs */
  if (tabsEl) ROOMS.forEach(function (r, i) {
    var b = document.createElement('button');
    b.type = 'button';
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-selected', i === 0 ? 'true' : 'false');
    b.tabIndex = i === 0 ? 0 : -1;
    b.innerHTML = '<span class="tab__n">' + String(i + 1).padStart(2, '0') +
      '</span><span class="tab__t">' + r.name + '</span>' +
      '<span class="tab__d">' + Math.round(r.hfov) + '&deg;</span>';
    b.addEventListener('click', function () { load(i, true); });
    b.addEventListener('keydown', function (e) {
      var n = null;
      if (e.key === 'ArrowRight') n = (i + 1) % ROOMS.length;
      if (e.key === 'ArrowLeft') n = (i - 1 + ROOMS.length) % ROOMS.length;
      if (n === null) return;
      e.preventDefault();
      load(n, true);
      tabsEl.querySelectorAll('button')[n].focus();
    });
    tabsEl.appendChild(b);
  });

  /* ------------------------------------------------------------- loop */
  var running = false;
  var spinDir = 1;
  var swayBase = 0, swayT = 0;
  function tick() {
    if (!running) return;
    if (state.target !== null) {
      var d = state.target - state.yaw;
      if (Math.abs(d) < 0.15) { state.yaw = state.target; state.target = null; }
      else state.yaw += d * 0.08;
    } else if (state.spin && !state.dragging && opts.sway) {
      // A hero that drifts the whole way round eventually parks on a blank
      // wall. Sway gently around the opening angle instead.
      swayT += 0.0016;
      state.yaw = swayBase + opts.sway * Math.sin(swayT);
    } else if (state.spin && !state.dragging) {
      state.yaw += (opts.spinSpeed || 0.045) * spinDir;
      var lim = yawLimits();
      if (lim && (state.yaw >= lim[1] || state.yaw <= lim[0])) {
        state.yaw = Math.max(lim[0], Math.min(lim[1], state.yaw));
        // bounce gently instead of jamming at the end of a partial sweep
        spinDir = -spinDir;
      }
    } else if (!state.dragging && Math.abs(state.vel) > 0.01) {
      state.yaw += state.vel;
      state.vel *= 0.94;
    }
    clampYaw();
    if (renderer) renderer.draw();
    requestAnimationFrame(tick);
  }

  function start() {
    if (running) return;
    running = true;
    requestAnimationFrame(tick);
  }
  function stop() { running = false; }

  // only animate while the viewer is actually on screen
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es) {
      es.forEach(function (e) { e.isIntersecting ? start() : stop(); });
    }, { threshold: 0.05 }).observe(root);
  } else { start(); }

  document.addEventListener('visibilitychange', function () {
    document.hidden ? stop() : start();
  });

  setMode(MODE);
  syncSpin();
  load(state.room, false);
  relayout();

  return {
    go: function (i) { load(i, true); },
    yaw: function () { return state.yaw; },
    setSpin: function (on) { state.spin = !!on; },
    relayout: relayout,
    current: function () { return state.room; }
  };
  };

  var tour = document.getElementById('tour');
  if (tour) window.IBC_TOUR = window.IBCPano(tour, {});
  var heroPano = document.getElementById('hero-pano');
  if (heroPano) window.IBC_HERO = window.IBCPano(heroPano, {
    room: 0, hero: true, sway: 15, zoom: 1.42, pitch: -5
  });
})();
