/* war/daynight.js - day/night phases, night theme for the forces, firing flashes and sun-position shadows for the /war battle maps (MOCKUP for the owner, 10-21; loaded only with ?daynight=1,
   so the held pages are unchanged without it). ONE shared solar calculation (NOAA general solar position: declination, equation of time, hour angle) drives the map tint, the
   dawn/dusk/sunrise/sunset times shown on the page, and the shadow direction and length. Flashes: one shared function, 150-300 ms, max 3 per second per unit, small radius,
   none under prefers-reduced-motion. Nothing here calls a network service (no GA hit from the mockup). */
(function () {
  var RAD = Math.PI / 180;

  // ---- the solar calculation (NOAA): date 'YYYY-MM-DD', clock minute of the day in the scene's civil time (tz hours east of UTC), place lat/lon -> {elev, az} degrees
  function jdOf(y, m, d, utcMin) {
    if (m <= 2) { y -= 1; m += 12; }
    var A = Math.floor(y / 100), B = 2 - A + Math.floor(A / 4);
    return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + B - 1524.5 + utcMin / 1440;
  }
  function solar(jd) {
    var T = (jd - 2451545) / 36525;
    var L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360;
    var M = 357.52911 + T * (35999.05029 - 0.0001537 * T);
    var e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T);
    var C = Math.sin(M * RAD) * (1.914602 - T * (0.004817 + 0.000014 * T)) + Math.sin(2 * M * RAD) * (0.019993 - 0.000101 * T) + Math.sin(3 * M * RAD) * 0.000289;
    var trueLong = L0 + C, omega = 125.04 - 1934.136 * T;
    var lambda = trueLong - 0.00569 - 0.00478 * Math.sin(omega * RAD);
    var eps0 = 23 + (26 + ((21.448 - T * (46.815 + T * (0.00059 - T * 0.001813)))) / 60) / 60;
    var eps = eps0 + 0.00256 * Math.cos(omega * RAD);
    var decl = Math.asin(Math.sin(eps * RAD) * Math.sin(lambda * RAD)) / RAD;
    var y = Math.tan(eps * RAD / 2); y *= y;
    var eqt = 4 * (y * Math.sin(2 * L0 * RAD) - 2 * e * Math.sin(M * RAD) + 4 * e * y * Math.sin(M * RAD) * Math.cos(2 * L0 * RAD) - 0.5 * y * y * Math.sin(4 * L0 * RAD) - 1.25 * e * e * Math.sin(2 * M * RAD)) / RAD;
    return { decl: decl, eqt: eqt };
  }
  function parts(date) { var p = date.split('-'); return [+p[0], +p[1], +p[2]]; }
  function sunAt(date, minLocal, lat, lon, tz) {
    var p = parts(date), utc = minLocal - tz * 60, s = solar(jdOf(p[0], p[1], p[2], utc));
    var tst = ((utc + s.eqt + 4 * lon) % 1440 + 1440) % 1440, ha = tst / 4 - 180;
    var la = lat * RAD, de = s.decl * RAD, h = ha * RAD;
    var cz = Math.sin(la) * Math.sin(de) + Math.cos(la) * Math.cos(de) * Math.cos(h);
    var zen = Math.acos(Math.max(-1, Math.min(1, cz))) / RAD, elev = 90 - zen;
    var az = (Math.atan2(Math.sin(h), Math.cos(h) * Math.sin(la) - Math.tan(de) * Math.cos(la)) / RAD + 180 + 360) % 360;    // clockwise from north
    return { elev: elev, az: az };
  }
  // minute (local civil time) at which the sun crosses a given elevation, morning or evening, by bisection on the daily arc
  function crossing(date, lat, lon, tz, elev, evening) {
    var lo = evening ? 12 * 60 : 0, hi = evening ? 24 * 60 : 12 * 60;
    var noon = 12 * 60, f = function (m) { return sunAt(date, m, lat, lon, tz).elev - elev; };
    var a = lo, b = hi, fa = f(a), fb = f(b);
    if (evening) { a = noon; fa = f(a); } else { b = noon; fb = f(b); }
    if (fa * fb > 0) return null;
    for (var i = 0; i < 40; i++) { var m = (a + b) / 2, fm = f(m); if ((fm > 0) === (fa > 0)) { a = m; fa = fm; } else { b = m; } }
    return (a + b) / 2;
  }
  function times(date, lat, lon, tz) {
    return { dawn: crossing(date, lat, lon, tz, -6, false), sunrise: crossing(date, lat, lon, tz, -0.833, false), sunset: crossing(date, lat, lon, tz, -0.833, true), dusk: crossing(date, lat, lon, tz, -6, true) };
  }
  function hhmm(m) { if (m == null) return '--:--'; m = Math.round(m); var h = Math.floor(m / 60), mm = m % 60; return (h < 10 ? '0' : '') + h + ':' + (mm < 10 ? '0' : '') + mm; }
  window.GoinfoSun = { sunAt: sunAt, times: times, hhmm: hhmm };

  // ---- phase from elevation: night factor n in [0,1] (0 = full day, 1 = dark), warm factor w in [0,1] (low sun)
  function phaseOf(elev) {
    var n = Math.max(0, Math.min(1, (4 - elev) / 18));        // elev >= 4 deg: day; 4 .. -14: twilight (evening stays visibly lighter than night); <= -14: night
    n = n * n * (3 - 2 * n);
    var w = elev > -4 && elev < 10 ? Math.max(0, 1 - Math.abs(elev - 3) / 7) : 0;
    var name = elev >= 6 ? 'יום' : elev >= -0.833 ? (w > 0.3 ? 'שחר / שקיעה (שמש נמוכה)' : 'יום') : elev >= -6 ? 'דמדומים אזרחיים' : 'לילה';
    return { n: n, w: w, name: name };
  }


  // ---- unit symbols: what the label says, nothing invented. Echelon from the label word; aircraft = one four-aircraft wing symbol per item (assumption shown on the panel)
  // small icons in one style: tank, soldier, gun; 2 icons = division, 1 = brigade/battalion/company (a size cue, not a vehicle count)
  var ICON = {
    tank: '<svg viewBox="0 0 24 14" width="15" height="9"><rect x="2" y="8" width="20" height="5" rx="2.5" fill="currentColor"/><rect x="6" y="4" width="11" height="5" rx="1" fill="currentColor"/><rect x="15" y="5.2" width="8" height="1.8" fill="currentColor"/></svg>',
    inf: '<svg viewBox="0 0 14 16" width="9" height="11"><circle cx="7" cy="3" r="2.6" fill="currentColor"/><path d="M2 15v-6a5 5 0 0 1 10 0v6z" fill="currentColor"/><rect x="9" y="6" width="5" height="1.6" fill="currentColor"/></svg>',
    art: '<svg viewBox="0 0 24 14" width="15" height="9"><circle cx="7" cy="10" r="3.6" fill="currentColor"/><rect x="8" y="3" width="15" height="2.2" transform="rotate(-12 8 4)" fill="currentColor"/><rect x="5" y="7" width="8" height="2" fill="currentColor"/></svg>'
  };
  var TANKSVG = '<svg viewBox="0 0 26 14" width="24" height="13"><rect x="1" y="1" width="18" height="12" rx="3" fill="CLR" stroke="#fff" stroke-width="1.3"/><g class="dn-gun"><rect x="8" y="3.5" width="8" height="7" rx="2" fill="CLR" stroke="#fff" stroke-width="1"/><rect x="15" y="6" width="10.5" height="2.4" fill="CLR" stroke="#fff" stroke-width=".8"/></g></svg>';
  var ECHNAME = { XX: 'אוגדה', X: 'חטיבה', II: 'גדוד', I: 'פלוגה' };
  function echelon(label) {
    var t = label || '';
    if (/אוגד|דיוויז/.test(t)) return 'XX';
    if (/חטיב|חטמ"ר|חט"ר/.test(t)) return 'X';
    if (/גדוד/.test(t)) return 'II';
    if (/פלוג/.test(t)) return 'I';
    return null;
  }
  function isSorties(label) { return /תקיפות/.test(label || ''); }                  // "כ-300 תקיפות" counts strikes (sorties), not aircraft: no aircraft multiplier from it
  function wingCount(label) {
    var m = /(\d+)\s*(?:מיג|מטוס|האנטר|טופולב)/.exec(label || '') || /כ-?(\d+)\s*תקיפות/.exec(label || '');
    return m ? +m[1] : 4;
  }
  // formation breathing: while a flight or column moves, its sub-shapes open and close a few px (deterministic: function of the scene clock and the item index); still when stationary; none for reduced motion
  function col0(moving) { return moving ? 11 : 8; }                          // half gap: column (one behind the other) vs abreast (side by side)
  // heading in screen radians, from the movement data (never from the marker's jumps): moving = along the current segment; before the first move = the first segment; stopped = the last
  // heading; attacking (an impact or shell target within 15 km during the last 2 s) = toward it
  function bearing(map, a, b) { var p = map.latLngToContainerPoint(a), q = map.latLngToContainerPoint(b); return Math.atan2(q.y - p.y, q.x - p.x); }
  function easeF(f) { f = Math.max(0, Math.min(1, f)); return f < 0.5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2; }   // identical to the map's ease()
  function segAt(path, f) {
    var L = [], tot = 0, i;
    for (i = 0; i + 1 < path.length; i++) { var d = Math.hypot(path[i + 1][0] - path[i][0], (path[i + 1][1] - path[i][1]) * 0.84); L.push(d); tot += d; }
    var want = Math.max(0, Math.min(0.9999, f)) * tot, acc = 0;
    for (i = 0; i < L.length; i++) { if (acc + L[i] >= want) return [path[i], path[i + 1]]; acc += L[i]; }
    return [path[path.length - 2], path[path.length - 1]];
  }
  function headingOf(map, it, T, items, m) {
    var seg = null, moving = false;
    if (it.type === 'arrow') {
      var f = easeF((T - it.t0) / Math.max(1e-6, it.t1 - it.t0)); moving = T >= it.t0 && T <= it.t1; seg = segAt(it.path, f);          // same eased fraction the map uses to place the unit
    } else {
      var legs = it.legs || [], l = null;
      for (var k = 0; k < legs.length; k++) { if (T <= legs[k].t1) { l = legs[k]; break; } }
      if (!l) { l = legs[legs.length - 1]; seg = segAt(l.path, 1); }
      else { moving = T >= l.t0; seg = segAt(l.path, moving ? easeF((T - l.t0) / Math.max(1e-6, l.t1 - l.t0)) : 0); }
    }
    if (!moving) {                                                                   // parked: face the target of a firing/impact that just happened nearby
      var at = m.getLatLng(), best = null, bd = 15000;
      items.forEach(function (x) {
        var tgt = x.type === 'boom' && T >= x.t - 0.2 && T <= x.t + 2 ? x.at : (x.type === 'shell' && T >= x.t0 && T <= x.t1 ? x.to : null);
        if (!tgt) return; var d = map.distance(at, L.latLng(tgt)); if (d < bd && d > 300) { bd = d; best = tgt; }
      });
      if (best) return bearing(map, at, best);
    }
    return bearing(map, seg[0], seg[1]);
  }

  // ---- movement sound (the owner 10-21): tanks = engine, aircraft = jet engine, foot soldiers = marching boots (CC0 loops, see below).
  // Opt-in through the page's speaker button (default off, remembered there); starts only after a tap; silent while paused / tab hidden / above 4x / reversed; 0.3 s fades.
  // Level per type scales with the number of that type moving AND visible (on screen), capped. Stopped or attacking tanks: silence.
  var SND = { n: { tank: 0, jet: 0, foot: 0 }, g: null, loading: false };
  var MIX = { tank: 0.8, jet: 0.6, foot: 0.8 };
  function A_speed() { var A = sndA(); return A && A.sp ? A.sp : 1; }
  function sndA() { return window.__a67 && window.__a67.A; }
  function sndOK(A) { return A && A.ctx && A.ctx.state === 'running' && !A.muted && !document.hidden && A.sp <= 4 && A.dir > 0 && A.playing; }
  function sndCount(map, markers, items, T) {
    var n = { tank: 0, jet: 0, foot: 0 }, sz = map.getSize();
    items.forEach(function (it, i) {
      if (it.type !== 'walk' && it.type !== 'arrow' && it.type !== 'fly') return;
      var mv = it.type === 'arrow' ? (T >= it.t0 && T <= it.t1) : (it.legs || []).some(function (l) { return T >= l.t0 && T <= l.t1; }); if (!mv) return;
      var m = markers['s' + i + (it.type === 'arrow' ? 't' : '')]; if (!m || !m.getLatLng || !m.options || !(m.options.opacity > 0.15)) return;
      var pt = map.latLngToContainerPoint(m.getLatLng()); if (pt.x < 0 || pt.y < 0 || pt.x > sz.x || pt.y > sz.y) return;
      if (it.type === 'fly') n.jet++;
      else if (it.trail === 'tank') n.tank++;
      else if (!/תותח|ארטיל|מרגמ|סוללה/.test(it.label || '')) n.foot++;
    });
    SND.n = n;
  }
  // the owner's picks (10-21): tanks = "Military Vehicle Humming" (qubodup, CC0), aircraft = "Jet loop 01" (MickBoere, CC0), marching = "marching-concrete-loop" (stib, CC0); licences and
  // sources in war/sound/SOURCES.md. Three short loops (mp3, ~0.5 MB together) fetched once, only after the visitor turned sound on; looped by Web Audio, one gain per type.
  var SND_VER = '20261021b';       // bump when a loop file changes (the files are cached by the browser)
  var SND_FILES = { tank: 'tank.mp3', jet: 'jet.mp3', foot: 'march.mp3' };
  function sndLoad(A) {
    if (SND.loading) return; SND.loading = true;
    var sc = document.currentScript || [].slice.call(document.scripts).filter(function (x) { return /daynight\.js/.test(x.src); })[0], base = sc ? sc.src.replace(/daynight\.js.*$/, '../../sound/') : null;
    if (!base) return;
    var g = {}, n = 0, kinds = Object.keys(SND_FILES);
    kinds.forEach(function (k) {
      fetch(base + SND_FILES[k] + '?v=' + SND_VER).then(function (r) { return r.arrayBuffer(); }).then(function (ab) { return A.ctx.decodeAudioData(ab); }).then(function (buf) {
        var src = A.ctx.createBufferSource(), gn = A.ctx.createGain(); src.buffer = buf; src.loop = true; gn.gain.value = 0; src.connect(gn); gn.connect(A.master); src.start();
        g[k] = gn; if (++n === kinds.length) SND.g = g;
      }).catch(function () {});
    });
  }
  function sndTick() {
    var A = sndA(); if (!A || !A.ctx || !A.master) return;
    var ok = sndOK(A); if (ok && !SND.g) { sndLoad(A); return; }
    if (!SND.g) return;
    var now = A.ctx.currentTime, cap = function (n) { return n ? Math.min(1, 0.4 + 0.2 * n) : 0; };
    kindsOf().forEach(function (k) { SND.g[k].gain.setTargetAtTime(ok ? cap(SND.n[k]) * MIX[k] : 0, now, 0.1); });     // ~0.3 s fade in / out
  }
  function kindsOf() { return Object.keys(SND_FILES); }
  setInterval(sndTick, 120);


  // ---- guns / artillery sound (the owner 10-21: "2 boom: when it fires, and then a whistle and then another boom on the hit"). Our own synthesis, computed into buffers at first use
  // (no samples, no licence question; see war/sound/SOURCES.md). Per shot of a shell item: boom at the gun when it fires, a falling whistle for the flight (one period long),
  // a deeper boom at the target on arrival. Louder and centred on screen when the point is near the view centre, quiet when off screen, panned by x position;
  // at most 6 voices at once, at most one shot per gun every 0.35 s; same silence rules as the other layers (paused / hidden / above 4x / reversed / sound off).
  var GUN = { buf: null, voices: [], last: {}, shots: 0, whistles: {} };
  function gunRnd(seed) { var a = seed >>> 0; return function () { a = (a + 0x6D2B79F5) >>> 0; var t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function gunMake(ctx, secs, fn) { var n = Math.round(ctx.sampleRate * secs), b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0); fn(d, ctx.sampleRate, n); return b; }
  // Artillery, not rifle (the owner 10-21: "need a lower boom"): a 35-75 Hz thump with a long low-passed decay, almost no crack, a gentle 110-150 Hz body so a phone speaker still gives something,
  // a dark rolling tail, and a peak limiter. Fire boom level = about half of the hit boom (the owner 10-22: the fire boom smaller/quieter than the hit boom). Variant A (default) deep, B (?gun=B in the page address) the deepest. The hit boom is deeper and longer than the fire boom.
  var GUN_VAR = (/[?&]gun=A/.test(location.search)) ? 'A' : 'C';       // C (default, the owner 10-21 "slower, louder, lower"); ?gun=A keeps the earlier deep version for comparison
  var GUN_P = {
    A: { fire: { f0: 46, f1: 34, k: 12, dec: 3.0, body: 135, bodyDec: 14, bodyAmp: 0.32, noise: 0.35, noiseDec: 7, tail: 1.6, crack: 0.12, secs: 2.4 },
         hit:  { f0: 38, f1: 28, k: 9,  dec: 2.0, body: 115, bodyDec: 11, bodyAmp: 0.28, noise: 0.40, noiseDec: 5, tail: 1.2, crack: 0.0,  secs: 3.4 } },
    C: { fire: { f0: 30, f1: 21, k: 5,  dec: 1.15, body: 125, bodyDec: 6,  bodyAmp: 0.5, noise: 0.30, noiseDec: 3.2, tail: 1.8, crack: 0.04, secs: 4.4, attack: 0.03, harm: 0.55, roll: 0.35, tailDec: 0.9 },
         hit:  { f0: 25, f1: 18, k: 4,  dec: 0.8,  body: 105, bodyDec: 5,  bodyAmp: 0.45, noise: 0.34, noiseDec: 2.4, tail: 2.2, crack: 0.0,  secs: 6.2, attack: 0.04, harm: 0.6,  roll: 0.4, tailDec: 0.8 } }
  };
  function gunBoom(ctx, kind) {
    var P = GUN_P[GUN_VAR][kind], att = P.attack || 0.006, harm = P.harm || 0, roll = P.roll || 0;
    return gunMake(ctx, P.secs, function (d, sr, n) {
      var r = gunRnd(kind === 'fire' ? 11 : 23), lp = 0, lp2 = 0, ph = 0, ph2 = 0, i;
      for (i = 0; i < n; i++) {
        var t = i / sr, w = r() * 2 - 1;
        lp += 0.02 * (w - lp);                                                              // noise through a ~140 Hz low-pass: the blast's dull body
        lp2 += 0.004 * (w - lp2);                                                           // ~30 Hz rumble
        ph += 2 * Math.PI * (P.f1 + (P.f0 - P.f1) * Math.exp(-t * P.k)) / sr;               // the thump: pitch falls from f0 to f1
        ph2 += 2 * Math.PI * P.body / sr;
        var env = Math.min(1, t / att);                                                     // slower attack = a drawn-out boom, not a snap
        d[i] = env * (1.0 * Math.sin(ph) * Math.exp(-t * P.dec)
          + harm * (0.6 * Math.sin(2 * ph + 0.5) + 0.3 * Math.sin(3 * ph + 1.1)) * Math.exp(-t * P.dec * 1.25)       // harmonics of the sub, so a small speaker still reproduces the boom
          + P.bodyAmp * Math.sin(ph2) * Math.exp(-t * P.bodyDec)
          + P.noise * 3.0 * lp * Math.exp(-t * P.noiseDec)
          + P.tail * 7.0 * lp2 * Math.exp(-t * (P.tailDec || 1.5)) * (1 + roll * Math.sin(2 * Math.PI * 6.5 * t))
          + (t < 0.008 ? P.crack * w * (1 - t / 0.008) : 0));
      }
      var pk = 0, k = Math.round(0.05 * sr); for (i = 0; i < n; i++) pk = Math.max(pk, Math.abs(d[i]));
      var g = pk > 0 ? 0.85 / pk : 1; for (i = 0; i < n; i++) d[i] = Math.tanh(d[i] * g * 1.3) / Math.tanh(1.3) * 0.95;       // normalise, then a soft limiter: no clipping
      for (i = 0; i < k; i++) d[n - 1 - i] *= i / k;
    });
  }
  function gunWhistle(ctx, secs) {             // a falling tone with a little air: ~2600 Hz down to ~900 Hz over the flight
    return gunMake(ctx, secs, function (d, sr, n) {
      var r = gunRnd(5), ph = 0, lp = 0, i;
      for (i = 0; i < n; i++) {
        var f = i / n, fr = 2600 * Math.pow(900 / 2600, f * f * 0.6 + f * 0.4); ph += 2 * Math.PI * fr / sr;
        lp += 0.35 * ((r() * 2 - 1) - lp);
        var env = Math.min(1, i / (0.08 * sr)) * Math.min(1, (n - i) / (0.05 * sr)) * (0.45 + 0.55 * f);
        d[i] = (0.5 * Math.sin(ph) + 0.18 * Math.sin(2 * ph) + 0.25 * lp) * env;
      }
    });
  }
  function gunPlace(map, ll) {                // level and pan from where the point is on screen
    var sz = map.getSize(), pt = map.latLngToContainerPoint(ll), inV = pt.x >= 0 && pt.y >= 0 && pt.x <= sz.x && pt.y <= sz.y;
    var d = Math.min(1, Math.hypot(pt.x - sz.x / 2, pt.y - sz.y / 2) / Math.hypot(sz.x / 2, sz.y / 2));
    return { gain: inV ? 1 - 0.5 * d : 0.1, pan: Math.max(-0.8, Math.min(0.8, (pt.x - sz.x / 2) / (sz.x / 2) * 0.7)) };
  }
  function gunPlay(A, buf, when, place, level) {
    var c = A.ctx, now = c.currentTime;
    GUN.voices = GUN.voices.filter(function (e) { return e > now; });
    if (GUN.voices.length >= 6) return false;
    var src = c.createBufferSource(), gn = c.createGain(), pn = c.createStereoPanner ? c.createStereoPanner() : null;
    src.buffer = buf; gn.gain.value = level * place.gain; src.connect(gn); if (pn) { pn.pan.value = place.pan; gn.connect(pn); pn.connect(A.master); } else gn.connect(A.master);
    src.start(when); GUN.voices.push(when + buf.duration); return true;
  }
  function gunShot(map, it, key, Tsec, speed) {
    var A = sndA(); if (!sndOK(A) || !A.ctx || !A.master) return;
    var c = A.ctx, now = c.currentTime;
    if (!GUN.buf) GUN.buf = { fire: gunBoom(c, 'fire'), hit: gunBoom(c, 'hit') };
    if (GUN.last[key] && now - GUN.last[key] < 0.35) return; GUN.last[key] = now;
    var d = Math.max(0.4, it.period || 1.3), wk = Math.round(d * 10), real = d / Math.max(0.25, speed || 1);
    if (!GUN.whistles[wk]) GUN.whistles[wk] = gunWhistle(c, d);
    var from = gunPlace(map, L.latLng(it.from)), to = gunPlace(map, L.latLng(it.to));
    if (gunPlay(A, GUN.buf.fire, now, from, GUN_VAR === 'A' ? 0.5 : 1.05)) {
      GUN.shots++;
      gunPlay(A, GUN.whistles[wk], now + 0.12, { gain: Math.max(from.gain, to.gain) * 0.8, pan: (from.pan + to.pan) / 2 }, 0.45);
      gunPlay(A, GUN.buf.hit, now + real, to, GUN_VAR === 'A' ? 1.0 : 2.1);
    }
  }


  // ---- schematic enemy at a tank fight (the owner 10-21: "when the tanks are fighting, show also the enemy; if there is no record of other tanks, put foot soldiers on position; keep this rule for the next days").
  // GENERAL RULE, one place, every battle page: a GROUND-FIRE impact (boom item whose sfx is 'cannon', the owner 10-22: not air strikes, not other events) with one of OUR drawn tanks within INF_R of it, in the window t-0.5 .. t+9 s, is a tank fight. If the page already draws
  // enemy (opposite side) armour within INF_R of that impact, nothing is added (the record is the symbol). If it does NOT, three foot soldiers of the other side are drawn at the impact position
  // for 9 s, with a DASHED ring and a tooltip saying it is schematic: no unit record exists, so the absence of one must not look like data. The decision is made once per impact per run-through.
  var INF = {}, INF_D = {}, INF_R = 8000, INF_SHOWN = 0;
  // the owner 10-22: the schematic enemy is for GROUND fire only. An impact is ground fire when the scene's sound track marks it 'cannon' (guns, tank guns) at its time; 'boom' (air strike) and 'thud' (bombing) never get one.
  function groundFire(it) { var A = sndA(), sf = A && A.sfx; if (!sf) return false; for (var i = 0; i < sf.length; i++) if (sf[i][1] === 'cannon' && Math.abs(sf[i][0] - it.t) < 0.05) return true; return false; }
  function unitSide(it) { return (it.color === '#b3261e' || it.cls === 'syr' || it.cls === 'ar') ? 'red' : 'blue'; }
  function inferEnemy(map, markers, items, T) {
    if (!markers || !items) return;
    var tanks = [], shown = 0;
    items.forEach(function (it, i) {
      if ((it.type !== 'walk' && it.type !== 'arrow') || it.trail !== 'tank') return;
      var m = markers['s' + i + (it.type === 'arrow' ? 't' : '')]; if (!m || !m.getLatLng || !m.options || !(m.options.opacity > 0.15)) return;
      var ll = m.getLatLng(); if (!ll || (!ll.lat && !ll.lng)) return; tanks.push({ ll: ll, side: unitSide(it) });
    });
    items.forEach(function (it, i) {
      if (it.type !== 'boom' || !groundFire(it)) return;
      var key = 'inf' + i, mk = INF[key];
      if (T < it.t - 0.5) { delete INF_D[key]; if (mk) mk.setOpacity(0); return; }          // before the window (or scrubbed back): forget the decision
      if (T > it.t + 9) { if (mk) mk.setOpacity(0); return; }
      var at = L.latLng(it.at);
      if (INF_D[key] === undefined) {
        var near = null, bd = INF_R; tanks.forEach(function (k) { var d = map.distance(k.ll, at); if (d < bd) { bd = d; near = k; } });
        if (!near) { if (T > it.t + 2.5) INF_D[key] = null; return; }                    // no tank of ours near: not a tank fight (decided for good once the fight window is over)
        var enemy = near.side === 'blue' ? 'red' : 'blue', armour = tanks.some(function (k) { return k.side === enemy && map.distance(k.ll, at) < INF_R; });
        INF_D[key] = armour ? null : enemy;
      }
      var side = INF_D[key]; if (!side) { if (mk) mk.setOpacity(0); return; }
      if (!mk) {
        var clr = side === 'red' ? '#b3261e' : '#1d5ea8';
        mk = INF[key] = L.marker(at, { icon: L.divIcon({ className: '', html: '<span class="dn-inf" style="color:' + clr + '">' + ICON.inf + ICON.inf + ICON.inf + '</span>', iconSize: [34, 34], iconAnchor: [17, 17] }), interactive: true, keyboard: false, zIndexOffset: 600, opacity: 0 }).addTo(map);
        mk.bindTooltip('מיקום סכמטי של חיילי רגלים של הצד השני - אין רישום יחידה', { className: 'tt' });
      }
      mk.setOpacity(T <= it.t + 7 ? 0.9 : Math.max(0, (it.t + 9 - T) / 2 * 0.9)); shown++;
    });
    INF_SHOWN = shown;
    var lg = document.getElementById('dnInfLeg'); if (lg) lg.hidden = !shown;
  }

  // land mask (Natural Earth 10 m land, public domain, clipped to lat 27-35 / lon 31-37.5, 0.002 deg simplified): used only to keep unit icons off the water
  var LAND = null;
  function loadLand() {
    var sc = document.currentScript || [].slice.call(document.scripts).filter(function (x) { return /daynight\.js/.test(x.src); })[0];
    if (!sc || !window.fetch) return;
    fetch(sc.src.replace(/daynight\.js.*$/, 'land-mask.json')).then(function (r) { return r.json(); }).then(function (j) { LAND = j; }).catch(function () {});
  }
  function onLand(ll) {
    var y = ll.lat, x = ll.lng; if (y < 27 || y > 35 || x < 31 || x > 37.5) return true;
    for (var r = 0; r < LAND.length; r++) {
      var ring = LAND[r], c = false;
      for (var i = 0, n = ring.length; i < n; i++) { var a = ring[i ? i - 1 : n - 1], b = ring[i]; if ((a[1] > x) !== (b[1] > x) && y < (b[0] - a[0]) * (x - a[1]) / (b[1] - a[1]) + a[0]) c = !c; }
      if (c) return true;
    }
    return false;
  }
  loadLand();
  function tankForm(map, markers, items, T, reduce) {
    if (!markers || !items) return;
    items.forEach(function (it, i) {
      if ((it.type !== 'walk' && it.type !== 'arrow') || it.trail !== 'tank') return;
      var m = markers['s' + i + (it.type === 'arrow' ? 't' : '')]; if (!m || !m.getElement) return;
      var e = m.getElement(); if (!e) return; var tk = e.querySelectorAll('.dn-tank'); if (tk.length !== 2) return;
      var moving = it.type === 'walk' ? (it.legs || []).some(function (l) { return T >= l.t0 && T <= l.t1; }) : (T >= it.t0 && T <= it.t1);
      var h = headingOf(map, it, T, items, m);
      var col = !reduce && moving, g = col0(!reduce && moving), ux = Math.cos(h), uy = Math.sin(h), px = -uy, py = ux;      // column: along the heading; abreast: across it
      var dx = col ? ux * g : px * g, dy = col ? uy * g : py * g, deg = (h * 180 / Math.PI).toFixed(0);
      if (LAND) {                                                              // both icons must be on land: shrink the gap toward the true position (never into the sea)
        var cp = map.latLngToContainerPoint(m.getLatLng()), sc = [1, 0.6, 0.3, 0];
        for (var q = 0; q < sc.length; q++) {
          if (onLand(map.containerPointToLatLng([cp.x + dx * sc[q], cp.y + dy * sc[q]])) && onLand(map.containerPointToLatLng([cp.x - dx * sc[q], cp.y - dy * sc[q]]))) break;
        }
        q = Math.min(q, 3); dx *= sc[q]; dy *= sc[q];
      }
      tk[0].classList.toggle('dn-mv', moving); tk[1].classList.toggle('dn-mv', moving);
      tk[0].style.transform = 'translate(' + (-dx).toFixed(1) + 'px,' + (-dy).toFixed(1) + 'px) rotate(' + deg + 'deg)';
      tk[1].style.transform = 'translate(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px) rotate(' + deg + 'deg)';
    });
  }
  function breathe(markers, items, T, reduce) {
    if (reduce || !markers || !items) return;
    items.forEach(function (it, i) {
      var m = markers['s' + i + (it.type === 'arrow' ? 't' : '')]; if (!m || !m.getElement) return;
      var e = m.getElement(); if (!e || !e.getAttribute('data-dn')) return;
      if (it.trail === 'tank' && it.type !== 'fly') return;
      var moving = false, k = Math.sin(T * 1.9 + i * 1.3);                                // ~3.3 s cycle
      if (it.type === 'fly') moving = (it.legs || []).some(function (l) { return T >= l.t0 && T <= l.t1; });
      else if (it.type === 'walk') moving = (it.legs || []).some(function (l) { return T >= l.t0 && T <= l.t1; });
      else if (it.type === 'arrow') moving = T >= it.t0 && T <= it.t1;
      var f = e.querySelectorAll('.dn-form');
      if (f.length) {
        var sp = moving ? 3 * k : 0, d = [[-13, 9], [13, 9], [0, 17]];
        for (var j = 0; j < f.length && j < 3; j++) f[j].style.transform = 'translate(' + (d[j][0] * (1 + sp / 13)).toFixed(1) + 'px,' + (d[j][1] + sp * (j === 2 ? 1 : 0.5)).toFixed(1) + 'px) scale(.8)';
      } else {
        var h = e.querySelector('.ap') || e.querySelector('.ic'); if (h) h.style.transform = moving ? 'scale(' + (1 + 0.07 * k).toFixed(3) + ',' + (1 - 0.04 * k).toFixed(3) + ')' : '';
      }
    });
  }
  function decorate(markers, items) {
    if (!markers || !items) return;
    items.forEach(function (it, i) {
      if (it.type !== 'walk' && it.type !== 'fly' && it.type !== 'arrow') return;          // never touch impact (boom) / quiet-mark markers: position:relative on a marker element drags it out of place
      var m = markers['s' + i + (it.type === 'arrow' ? 't' : '')];
      if (!m || !m.getElement) return;
      var e = m.getElement(); if (!e || e.getAttribute('data-dn')) return;
      e.setAttribute('data-dn', '1');
      var holder = e.querySelector('.ap') || e.querySelector('.ic') || e;
      if (holder !== e) holder.style.position = holder.style.position || 'relative';
      if (it.type === 'fly') {
        var rot = e.querySelector('.rot'), svg = rot && rot.firstElementChild, n = wingCount(it.label), drawn = Math.min(4, Math.max(1, n));
        // the owner 10-21: up to 4 aircraft are drawn as they are; a bigger flight is a 4-aircraft wing with a visible multiplier N/4 (12 -> x3, 8 -> x2; a non-multiple is rounded, minimum x2) and the real number in the tooltip
        if (rot && svg) {
          [[-13, 9], [13, 9], [0, 17]].slice(0, drawn - 1).forEach(function (d) {
            var c = el('span', 'dn-form'); c.innerHTML = svg.outerHTML; c.style.transform = 'translate(' + d[0] + 'px,' + d[1] + 'px) scale(.8)'; rot.appendChild(c);
          });
        }
        if (isSorties(it.label)) { holder.setAttribute('title', 'כ-' + n + ' תקיפות (גיחות) בסך הכול; מצוירת כנף אחת של 4 מטוסים'); e.setAttribute('data-wing', 'sorties:' + n); }
        else if (n > 4) {
          var mult = Math.max(2, Math.round(n / 4)), cn = el('span', 'dn-cnt', '×' + mult); cn.setAttribute('dir', 'ltr');
          cn.setAttribute('title', n + ' מטוסים, מצוירים 4 (' + (n % 4 ? 'כ-' : '') + '×' + mult + ')'); cn.setAttribute('aria-label', n + ' מטוסים, מצוירים 4'); holder.appendChild(cn);
          e.setAttribute('data-wing', n + ':' + mult);
        }
      } else if ((it.type === 'walk' || it.type === 'arrow') && it.trail === 'tank') {
        // armoured unit: the template symbol is hidden and exactly two tank icons are drawn (the owner 10-21); echelon text stays in the tooltip
        var rt = e.querySelector('.rot'); if (rt) rt.style.display = 'none';
        var clr = (it.color === '#b3261e' || it.cls === 'syr' || it.cls === 'ar') ? '#b3261e' : '#1d5ea8';
        var box = el('span', 'dn-tk', '<span class="dn-tank">' + TANKSVG.replace(/CLR/g, clr) + '</span><span class="dn-tank">' + TANKSVG.replace(/CLR/g, clr) + '</span>');
        var gph = (i * 0.53) % 2.6; box.children[0].style.setProperty('--gp', '-' + gph.toFixed(2) + 's'); box.children[1].style.setProperty('--gp', '-' + ((gph + 1.1) % 2.6).toFixed(2) + 's');     // the barrels are never in step
        e.appendChild(box);                                                   // centred on the marker element = the true position (the holder collapses once the template symbol is hidden)
      } else if (it.type === 'walk' || it.type === 'arrow') {
        var ech = echelon(it.label);
        if (ech) {
          var kind = /תותח|ארטיל|מרגמ|סוללה/.test(it.label || '') ? 'art' : (it.trail === 'tank' ? 'tank' : 'inf');
          if (kind === 'inf') return;                                                // the owner 10-22: no black soldier badge over foot soldiers (the unit's own icon and label say what it is)
          var cnt = ech === 'XX' ? 2 : 1, eb = el('span', 'dn-ech', '');
          for (var q = 0; q < cnt; q++) eb.innerHTML += ICON[kind];
          eb.setAttribute('title', ECHNAME[ech] + ' (גודל הסמל מרמז על הדרגה, לא על מספר כלים)'); holder.appendChild(eb);
        }
      }
    });
  }

  // ---- the page
  var CSS = '' +
    '.dn-tint{position:absolute;inset:0;pointer-events:none;z-index:450;transition:background .4s}' +
    '.dn-night .leaflet-tile-pane{filter:brightness(var(--dn-b,1)) saturate(var(--dn-s,1))}' +
    /* forces on the dark-blue base: brighter fill, light outline, stronger label */
    '.dn-lit .ic,.dn-lit .ap{filter:brightness(var(--dn-ub,1)) saturate(var(--dn-us,1)) drop-shadow(0 0 var(--dn-ur,0px) #fff)}' +
    '.dn-night .tt.unt,.dn-night .leaflet-tooltip{background:#0e1b3d;color:#fff;border-color:#9db4ff}' +
    '.dn-night .leaflet-control-attribution{background:rgba(14,27,61,.8);color:#cdd9ff}' +
    /* unit symbols (mockup): echelon mark over ground units (XX division, X brigade, II battalion, I company), a four-aircraft formation per wing (כנף) with a count */
    /* armoured units: two tanks, column when moving, abreast when stopped or attacking (positions set per frame; short eased transition) */
    '.dn-tk{position:absolute;left:50%;top:50%;width:0;height:0;pointer-events:none}.dn-tank{position:absolute;left:-12px;top:-6.5px;display:block;line-height:0;filter:drop-shadow(0 0 1px #fff)}' +
    // gun traverse (the owner 10-21): the turret + barrel swing +-16 deg about the turret centre, ~2.6 s a swing, ONLY while the unit moves (class dn-mv, set in tankForm); a parked or firing tank
    // keeps the barrel along its facing (the symbol already turns to the target). Pure CSS transform on one SVG group: no layout, no per-frame JS; static for reduced motion.
    '.dn-gun{transform-origin:12px 7px}.dn-mv .dn-gun{animation:dngun 2.6s ease-in-out infinite;animation-delay:var(--gp,0s)}@keyframes dngun{0%,100%{transform:rotate(-16deg)}50%{transform:rotate(16deg)}}' +
    '@media (prefers-reduced-motion:reduce){.dn-mv .dn-gun{animation:none}}' +
    '.dn-inf{display:flex;align-items:center;justify-content:center;gap:1px;width:34px;height:34px;box-sizing:border-box;border:1.5px dashed currentColor;border-radius:50%;background:rgba(255,255,255,.5)}.dn-inf svg{width:9px;height:11px}' +
    '.dn-lit .dn-tank{filter:brightness(var(--dn-ub,1)) drop-shadow(0 0 var(--dn-ur,1px) #fff)}' +
    '@media (prefers-reduced-motion:reduce){.dn-tank{transition:none}}' +
    '.dn-ech{position:absolute;left:50%;top:-14px;transform:translateX(-50%);display:flex;gap:1px;color:#111;background:rgba(255,255,255,.9);border:1px solid #333;border-radius:3px;padding:1px 2px;pointer-events:none}.dn-ech svg{display:block}' +
    '.dn-lit .dn-ech{background:#0e1b3d;color:#fff;border-color:#9db4ff}' +
    '.dn-form{position:absolute;left:0;top:0;width:30px;height:30px;pointer-events:none}.dn-form svg{width:100%;height:100%}' +
    '.dn-cnt{position:absolute;left:50%;top:27px;transform:translateX(-50%);font:700 10px/10px system-ui,sans-serif;color:#111;background:rgba(255,255,255,.9);border:1px solid #333;border-radius:3px;padding:1px 3px;white-space:nowrap;pointer-events:none}' +
    '.dn-night .dn-cnt{background:#0e1b3d;color:#fff;border-color:#9db4ff}' +
    /* sun-position shadow, subtle, from the same solar function (vars set per frame) */
    '.dn-sh .ic,.dn-sh .ap{filter:drop-shadow(var(--dn-sx,0px) var(--dn-sy,0px) 1.2px rgba(0,0,0,var(--dn-so,0)))}' +
    '.dn-lit.dn-sh .ic,.dn-lit.dn-sh .ap{filter:brightness(var(--dn-ub,1)) saturate(var(--dn-us,1)) drop-shadow(0 0 var(--dn-ur,0px) #fff)}' +
    /* aircraft: a detached, softer, lighter shadow well below the plane (it is high above the ground); gone at night */
    '.dn-sh .ap:not(.gu){filter:drop-shadow(var(--dn-ax,0px) var(--dn-ay,0px) 3px rgba(0,0,0,var(--dn-ao,0)))}' +
    '.dn-lit.dn-sh .ap:not(.gu){filter:brightness(var(--dn-ub,1)) saturate(var(--dn-us,1)) drop-shadow(0 0 var(--dn-ur,0px) #fff) drop-shadow(var(--dn-ax,0px) var(--dn-ay,0px) 3px rgba(0,0,0,var(--dn-ao,0)))}' +
    '.dn-flash{display:block;width:26px;height:26px;border-radius:50%;background:radial-gradient(circle,#fff 0%,#ffe9a8 28%,rgba(255,170,40,.75) 55%,rgba(255,120,0,0) 72%);animation:dnf .24s ease-out forwards}' +
    '.dn-night .dn-flash{background:radial-gradient(circle,#fff 0%,#fff3b0 30%,rgba(255,200,60,.9) 58%,rgba(255,150,0,0) 75%);width:32px;height:32px}' +
    '@keyframes dnf{0%{transform:scale(.3);opacity:1}60%{transform:scale(1);opacity:.95}100%{transform:scale(1.25);opacity:0}}' +
    '@media (prefers-reduced-motion:reduce){.dn-flash{display:none}}' +
    '.dn-panel{position:absolute;inset-inline-start:8px;bottom:64px;z-index:1200;max-width:min(330px,calc(100% - 16px));background:rgba(255,255,255,.95);color:#111;border:1px solid #888;border-radius:10px;padding:8px 10px;font:12px/1.45 system-ui,sans-serif;direction:rtl}' +
    '.dn-panel[hidden]{display:none}.dn-panel .dn-x{position:absolute;top:4px;inset-inline-end:6px;border:0;background:transparent;font-size:15px;line-height:1;padding:2px 5px}.dn-panel h4{margin:0 0 4px;padding-inline-end:22px;font-size:13px}.dn-panel .row{display:flex;flex-wrap:wrap;gap:4px;margin:4px 0}.dn-panel button{font:inherit;border:1px solid #555;border-radius:7px;background:#f4f4f4;padding:2px 7px;cursor:pointer}' +
    '.dn-panel button[aria-pressed=true]{background:#1d5ea8;color:#fff}.dn-panel small{color:#444}.dn-panel details summary{cursor:pointer;font-weight:700}';

  function el(t, c, h) { var e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; }

  // whole-war page (o.whole): the minute runs on across days (day*1440 + minute of day), so the date, the sun and the panel follow it
  function addDays(date, k) { var p = date.split('-'), d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2] + k)); return d.getUTCFullYear() + '-' + ('0' + (d.getUTCMonth() + 1)).slice(-2) + '-' + ('0' + d.getUTCDate()).slice(-2); }
  window.GoinfoDayNight = {
    sun: { sunAt: sunAt, phaseOf: phaseOf, times: times, addDays: addDays },
    init: function (o) {
      // o: {map, date, lat, lon, tz, tzName, place, getMin: function -> minute or null}
      var map = o.map, root = map.getContainer(), st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
      var tint = el('div', 'dn-tint'); root.appendChild(tint);
      var curDate = o.date, T = times(o.date, o.lat, o.lon, o.tz), force = null, lastMin = null, flashes = {}, reduce = false;
      try { reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
      root.classList.add('dn-sh');
      var panel = el('div', 'dn-panel');
      panel.innerHTML = '<h4>אור יום, לילה, הבזקים וצללים</h4>' +   // the owner 10-22: the six-days page is no mockup
        
        '<div id="dnDate"><b>' + o.date.split('-').reverse().join('.') + '</b> · ' + o.place + ' · שעון: ' + o.tzName + '</div>' +
        '<div id="dnTimes">זריחה <b dir="ltr">' + hhmm(T.sunrise) + '</b> · שקיעה <b dir="ltr">' + hhmm(T.sunset) + '</b> · שחר אזרחי <span dir="ltr">' + hhmm(T.dawn) + '</span> · חשיכה אזרחית <span dir="ltr">' + hhmm(T.dusk) + '</span></div>' +
        '<div class="row" id="dnNow"></div><div class="row" id="dnBtns"></div>' +
        '<div id="dnInfLeg" hidden><small>◌ טבעת מקווקווה = מיקום סכמטי של כוח (חיילי רגלים) במקום קרב קרקעי (ירי) שבו אין רישום יחידה של הצד השני; לא נתון מהמקור.</small></div>' +
        '<details><summary>סמלי הכוחות</summary><small>קיצור סכמטי: כנף מצוירת ב-4 מטוסים לכל היותר; בטיסה גדולה יותר מופיע מכפיל ליד הכנף (12 מטוסים = ×3; הערך המדויק בחלונית מעל הסמל). כוח שריון מצויר תמיד בשני טנקים. מעל סוללת תותחים: שני סמלים = אוגדה, סמל אחד = חטיבה, גדוד או פלוגה, לפי מה שכתוב בשם הכוח בנתונים (כוח שהשם לא מציין דרגה אינו מסומן). זה רמז לגודל ולא ספירת כלים; הדרגה המלאה בטולטיפ. מטוסים: סמל אחד לכל כנף, ארבעה מטוסים (×4); כשהכותרת מציינת כמות (למשל 12 מיגים) מופיעה הכמות. ההנחה היא סמלית: הנתונים אינם מפרטים כמה מטוסים הוזנקו בכל גיחה, ולא מפורטים גדודים בתוך חטיבה.</small></details><details><summary>איך חושב</summary><small>מיקום השמש לפי נוסחת NOAA (נטייה, משוואת הזמן, זווית שעה) לתאריך ולמקום הסצנה; השעות לפי שעון ישראל (UTC+2, ללא שעון קיץ ב-1967); במצרים ובסוריה נהג אז שעון קיץ (UTC+3), והזמנים במאמר הם שעון ישראל. הצל נוטה הרחק מהשמש, ארוך בשחר ובשקיעה, קצר בצהריים, ונעלם כשהשמש מתחת לאופק.</small></details>';
      root.appendChild(panel);
      // the owner 10-23: the panel closes (x) and lives in the page's big menu ("אור וצללים"); closed by default, the choice is remembered per browser. The sun tint, flashes and shadows keep running when it is closed.
      var xb = el('button', 'dn-x', '✕'); xb.type = 'button'; xb.setAttribute('aria-label', 'סגירת הלוח'); panel.insertBefore(xb, panel.firstChild);
      var menuBtn = null, tm = document.getElementById('topMenu');
      function setOpen(on, keep) {
        panel.hidden = !on; if (menuBtn) menuBtn.setAttribute('aria-pressed', String(on));
        if (!keep) { try { localStorage.setItem('goinfo.dn.open', on ? '1' : '0'); } catch (e) {} }
      }
      if (tm) {
        menuBtn = el('button', 'btn', 'אור וצללים'); menuBtn.type = 'button'; menuBtn.id = 'bSun';
        menuBtn.title = 'לוח אור יום, לילה, הבזקים וצללים'; menuBtn.addEventListener('click', function () { setOpen(panel.hidden); });
        var anchor = document.getElementById('bLeg'); if (anchor && anchor.parentNode === tm) tm.insertBefore(menuBtn, anchor.nextSibling); else tm.appendChild(menuBtn);
      }
      xb.addEventListener('click', function () { setOpen(false); });
      var wasOpen = false; try { wasOpen = localStorage.getItem('goinfo.dn.open') === '1'; } catch (e) {}
      setOpen(wasOpen, true);
      var btns = panel.querySelector('#dnBtns'), nowEl = panel.querySelector('#dnNow');
      var presets = [['אוטומטי', null], ['שחר', function () { return T.sunrise + 5; }], ['צהריים', function () { return (T.sunrise + T.sunset) / 2; }], ['שקיעה', function () { return T.sunset - 8; }], ['ערב', function () { return T.sunset + 30; }], ['לילה', function () { return T.sunset + 150; }]];
      presets.forEach(function (p) {
        var b = el('button', '', p[0]); b.type = 'button'; b.setAttribute('aria-pressed', String(p[1] === null));
        b.addEventListener('click', function () { force = p[1] === null ? null : p[1]() + (o.whole ? 1440 * Math.floor((lastMin || 0) / 1440) : 0); [].forEach.call(btns.children, function (x) { x.setAttribute('aria-pressed', String(x === b)); }); apply(force != null ? force : lastMin); });
        btns.appendChild(b);
      });
      function apply(min) {
        if (min == null) min = lastMin == null ? 12 * 60 : lastMin;
        var dm = min, dd = o.date;
        if (o.whole) { var k = Math.floor(min / 1440); dm = min - 1440 * k; dd = addDays(o.date, k);
          if (dd !== curDate) { curDate = dd; T = times(dd, o.lat, o.lon, o.tz); var de = panel.querySelector('#dnDate'), te = panel.querySelector('#dnTimes');
            if (de) de.innerHTML = '<b>' + dd.split('-').reverse().join('.') + '</b> · ' + o.place + ' · שעון: ' + o.tzName;
            if (te) te.innerHTML = 'זריחה <b dir="ltr">' + hhmm(T.sunrise) + '</b> · שקיעה <b dir="ltr">' + hhmm(T.sunset) + '</b> · שחר אזרחי <span dir="ltr">' + hhmm(T.dawn) + '</span> · חשיכה אזרחית <span dir="ltr">' + hhmm(T.dusk) + '</span>'; } }
        var s = sunAt(dd, dm, o.lat, o.lon, o.tz), ph = phaseOf(s.elev);
        root.classList.toggle('dn-night', ph.n > 0.35);
        root.classList.toggle('dn-lit', ph.n > 0.02);
        // map base: lighter than before (evening and night +25%), night still a dark blue; units ramp up smoothly from dusk
        root.style.setProperty('--dn-b', String(1 - 0.36 * ph.n)); root.style.setProperty('--dn-s', String(1 - 0.15 * ph.n));
        root.style.setProperty('--dn-ub', (1 + 1.0 * ph.n).toFixed(3)); root.style.setProperty('--dn-us', (1 + 0.15 * ph.n).toFixed(3)); root.style.setProperty('--dn-ur', (2 * ph.n).toFixed(2) + 'px');
        // dark BLUE base (not black) at night; warm wash when the sun is low
        // evening (dusk after sunset, sun 0 to -9 deg): a reddish sunset tint on a lighter base, clearly brighter than the night that follows
        var ev = s.elev < 1 && s.elev > -9 ? Math.max(0, 1 - Math.abs(s.elev + 5) / 6) : 0;
        var night = 'rgba(' + Math.round(26 - 12 * ph.n) + ',' + Math.round(58 - 20 * ph.n) + ',' + Math.round(140 - 30 * ph.n) + ',' + (0.5 * ph.n * (1 - 0.5 * ev)).toFixed(3) + ')';
        var warm = 'rgba(' + Math.round(255 - 15 * ev) + ',' + Math.round(150 - 80 * ev) + ',' + Math.round(60 + 10 * ev) + ',' + (0.2 * ph.w + 0.36 * ev).toFixed(3) + ')';
        tint.style.background = 'linear-gradient(' + warm + ',' + warm + '),' + night;
        tint.style.mixBlendMode = ph.n > 0.05 ? 'multiply' : 'normal';
        // shadow: away from the sun, length ~ 3/tan(elev) px capped at 7, hidden below the horizon
        var len = s.elev > 1 ? Math.min(7, 3 / Math.tan(s.elev * RAD)) : 0, a = (s.az + 180) * RAD;
        root.style.setProperty('--dn-sx', (Math.sin(a) * len).toFixed(2) + 'px'); root.style.setProperty('--dn-sy', (-Math.cos(a) * len).toFixed(2) + 'px');
        root.style.setProperty('--dn-so', s.elev > 1 ? (0.42 * Math.min(1, s.elev / 6)).toFixed(2) : '0');
        var al = s.elev > 1 ? Math.min(22, 40 / Math.tan(Math.max(s.elev, 4) * RAD)) : 0;                 // aircraft shadow: well detached, 3x the ground-unit offset
        root.style.setProperty('--dn-ax', (Math.sin(a) * al).toFixed(1) + 'px'); root.style.setProperty('--dn-ay', (-Math.cos(a) * al + 6).toFixed(1) + 'px');
        root.style.setProperty('--dn-ao', s.elev > 1 ? (0.26 * Math.min(1, s.elev / 6)).toFixed(2) : '0');
        nowEl.innerHTML = '<span>שעה <b dir="ltr">' + hhmm(dm) + '</b></span><span>גובה השמש <b dir="ltr">' + s.elev.toFixed(1) + '°</b></span><span>אזימוט <b dir="ltr">' + s.az.toFixed(0) + '°</b></span><span>שלב: <b>' + ph.name + '</b></span>';
        return ph;
      }
      // flashes: one shared function, small, <= 3 per second per unit, none for reduced-motion users
      function flash(key, ll) {
        if (reduce) return;
        var now = performance.now(), f = flashes[key] || (flashes[key] = []);
        while (f.length && now - f[0] > 1000) f.shift();
        if (f.length >= 3) return;
        f.push(now);
        var m = L.marker(ll, { icon: L.divIcon({ className: '', html: '<span class="dn-flash"></span>', iconSize: [30, 30], iconAnchor: [15, 15] }), interactive: false, keyboard: false, zIndexOffset: 900 }).addTo(map);
        setTimeout(function () { map.removeLayer(m); }, 320);
      }
      // an impact (boom) is drawn as a glow only if a unit symbol (tank / flight / foot / gun) is DRAWN within 15 km of it AND on screen at that moment; otherwise a quiet mark.
      // The rule reads what is drawn (marker opacity, screen position), never the data: no shell-target or last-leg exemption (the owner 10-21)
      var curItems = null, curT = 0;
      function drawnUnits() {
        var M = o.markers && o.markers(), out = [], sz = map.getSize(); if (!M || !curItems) return null;
        for (var i = 0; i < curItems.length; i++) {
          var u = curItems[i], keys = u.type === 'arrow' ? ['s' + i + 't'] : u.type === 'shell' ? ['s' + i + 'g'] : (u.type === 'walk' || u.type === 'fly') ? ['s' + i] : [];
          keys.forEach(function (k) {
            var m = M[k]; if (!m || !m.getLatLng || !m.options || !(m.options.opacity > 0.15)) return;
            var ll = m.getLatLng(); if (!ll || (!ll.lat && !ll.lng)) return;
            var pt = map.latLngToContainerPoint(ll); if (pt.x < -10 || pt.y < -10 || pt.x > sz.x + 10 || pt.y > sz.y + 10) return;
            out.push(ll);
          });
        }
        return out;
      }
      function nearUnit(at) {
        var D = drawnUnits(); if (!D) return true;
        for (var i = 0; i < D.length; i++) if (map.distance(D[i], at) <= 15000) return true;
        return false;
      }
      var inst = {
        pre: function (Tsec, items) { curItems = items; curT = Tsec; },
        wings: function () { return (curItems || []).map(function (it, i) { return it.type === 'fly' ? { i: i, label: it.label || '', n: wingCount(it.label) } : null; }).filter(Boolean); },
        inferState: function () { return { shown: INF_SHOWN, decided: Object.keys(INF_D).map(function (k) { return [k, INF_D[k]]; }) }; },
        sndState: function () { var o = {}; if (SND.g) Object.keys(SND.g).forEach(function (k) { o[k] = +SND.g[k].gain.value.toFixed(2); }); return { moving: SND.n, gain: o, loaded: !!SND.g, gunShots: GUN.shots }; },
        landReady: function () { return !!LAND; }, onLand: function (ll) { return LAND ? onLand(ll) : true; },
        flash: flash, panel: panel, orphan: function (at) { return !nearUnit(at); },
        onTime: function (Tsec, items, playing) {
          var min = o.getMin ? o.getMin() : null; if (min != null) lastMin = min;
          apply(force != null ? force : (min != null ? min : lastMin));
          curItems = items; curT = Tsec; decorate(o.markers && o.markers(), items); if (o.markers && o.markers() && items) { sndCount(map, o.markers(), items, Tsec); inferEnemy(map, o.markers(), items, Tsec); } tankForm(map, o.markers && o.markers(), items, Tsec, reduce); breathe(o.markers && o.markers(), items, Tsec, reduce);
          if (!playing || !items) return;
          var prev = inst._prev; inst._prev = Tsec;
          if (prev == null || Tsec <= prev || Tsec - prev > 1.5) return;                  // forward play only, no burst after a seek
          items.forEach(function (it, i) {
            if (it.type === 'shell' && Tsec >= it.t0 && Tsec <= it.t1 && it.period > 0 && Math.floor((Tsec - it.t0) / it.period) !== Math.floor((prev - it.t0) / it.period)) { flash('sh' + i, it.from); gunShot(map, it, 'sh' + i, Tsec, A_speed()); }
            if (it.type === 'boom' && prev < it.t && Tsec >= it.t && nearUnit(it.at)) flash('bm' + i, it.at);
          });
        }
      };
      apply(12 * 60);
      window.__dn = inst;
      return inst;
    }
  };
})();
