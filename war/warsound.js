/* War maps: our own synthesised ambience (v2, the owner 10-21). Pure DSP, no samples, no files: every layer is computed into a Float32Array at start-up.
   Loops are circular (every slow modulation has a whole number of cycles in the loop, the reverb is run over two laps and the second kept), so they repeat without a seam.
   Tuned against numeric analysis of a reference ambience (band balance, engine fundamental ~50 Hz, slow 0.4-0.6 Hz swell, dense irregular clatter); nothing is taken from it.
   UMD: window.WarSound in the browser, require() in node (tools/war_sound_render.js writes WAV for listening tests). */
(function (root) {
  'use strict';
  function rng(seed) { var a = seed >>> 0; return function () { a = (a + 0x6D2B79F5) >>> 0; var t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function addRing(x, i0, sr, f, tau, amp) {            // damped sine, circular
    var n = x.length, len = Math.min(n, Math.floor(tau * sr * 6)), w = 2 * Math.PI * f / sr, d = Math.exp(-1 / (tau * sr));
    var env = amp, ph = 0;
    for (var k = 0; k < len; k++) { x[(i0 + k) % n] += env * Math.sin(ph); ph += w; env *= d; }
  }
  function addNoiseBurst(x, i0, sr, tau, amp, r, lp) {  // decaying noise through a one-pole low-pass (lp 0..1, higher = brighter)
    var n = x.length, len = Math.min(n, Math.floor(tau * sr * 5)), d = Math.exp(-1 / (tau * sr)), env = amp, y = 0;
    for (var k = 0; k < len; k++) { y += lp * ((r() * 2 - 1) - y); x[(i0 + k) % n] += env * y; env *= d; }
  }
  function onePoleLP(x, fc, sr) { var a = 1 - Math.exp(-2 * Math.PI * fc / sr), y = 0; for (var i = 0; i < x.length; i++) { y += a * (x[i] - y); x[i] = y; } return x; }
  function onePoleHP(x, fc, sr) { var a = Math.exp(-2 * Math.PI * fc / sr), px = 0, py = 0; for (var i = 0; i < x.length; i++) { var y = a * (py + x[i] - px); px = x[i]; py = y; x[i] = y; } return x; }
  function bandpass(x, f, q, sr) {                      // RBJ biquad, two passes for a steeper skirt
    var w = 2 * Math.PI * f / sr, al = Math.sin(w) / (2 * q), cw = Math.cos(w), b0 = al, b2 = -al, a0 = 1 + al, a1 = -2 * cw, a2 = 1 - al;
    for (var p = 0; p < 2; p++) { var x1 = 0, x2 = 0, y1 = 0, y2 = 0; for (var i = 0; i < x.length; i++) { var y = (b0 * x[i] + b2 * x2 - a1 * y1 - a2 * y2) / a0; x2 = x1; x1 = x[i]; y2 = y1; y1 = y; x[i] = y; } }
    return x;
  }
  function brown(n, r) { var x = new Float32Array(n), y = 0; for (var i = 0; i < n; i++) { y = (y + 0.02 * (r() * 2 - 1)) / 1.02; x[i] = y * 3.5; } return x; }
  function white(n, r) { var x = new Float32Array(n); for (var i = 0; i < n; i++) x[i] = r() * 2 - 1; return x; }
  function reverb(x, sr, wet, t60) {                    // small Schroeder room: 4 combs + 2 all-passes, run over two laps so the loop stays seamless
    var n = x.length, two = new Float32Array(2 * n); two.set(x); two.set(x, n);
    var combs = [0.0297, 0.0371, 0.0411, 0.0437].map(function (s) { return Math.round(s * sr); });
    var out = new Float32Array(2 * n);
    combs.forEach(function (d) {
      var g = Math.pow(10, -3 * d / (t60 * sr)), buf = new Float32Array(d), p = 0, lp = 0;
      for (var i = 0; i < 2 * n; i++) { var y = buf[p]; lp += 0.35 * (y - lp); buf[p] = two[i] + g * lp; p = (p + 1) % d; out[i] += y * 0.25; }
    });
    [0.005, 0.0017].forEach(function (s, k) {
      var d = Math.round(s * sr), buf = new Float32Array(d), p = 0, g = 0.7;
      for (var i = 0; i < 2 * n; i++) { var v = out[i], b = buf[p], y = -g * v + b; buf[p] = v + g * y; p = (p + 1) % d; out[i] = y; }
    });
    var res = new Float32Array(n);
    for (var i = 0; i < n; i++) res[i] = x[i] * (1 - wet * 0.5) + wet * out[n + i];
    return res;
  }
  function normalise(x, rmsDb, peakLimit) {
    var s = 0, i; for (i = 0; i < x.length; i++) s += x[i] * x[i];
    var g = Math.pow(10, rmsDb / 20) / Math.sqrt(s / x.length + 1e-12); for (i = 0; i < x.length; i++) x[i] *= g;
    var pk = 0; for (i = 0; i < x.length; i++) pk = Math.max(pk, Math.abs(x[i]));
    if (pk > (peakLimit || 0.9)) { g = (peakLimit || 0.9) / pk; for (i = 0; i < x.length; i++) x[i] *= g; }
    return x;
  }
  function softclip(x, drive) { var d = drive || 2, k = Math.tanh(d); for (var i = 0; i < x.length; i++) x[i] = Math.tanh(x[i] * d) / k; return x; }   // tame the clank peaks so the body can be loud
  function slow(n, sr, L, terms, r) {                   // periodic slow modulation, 1 + sum of sines with integer cycles per loop
    var ph = terms.map(function () { return r() * 2 * Math.PI; }), m = new Float32Array(n);
    for (var i = 0; i < n; i++) { var t = i / n, v = 0; for (var k = 0; k < terms.length; k++) v += terms[k][1] * Math.sin(2 * Math.PI * terms[k][0] * t + ph[k]); m[i] = v; }
    return m;
  }

  // ---- tank: diesel (firing chug at ~26 Hz, 50 Hz body, 100 Hz second order) with load wobble, brown rumble, per-link track clatter with ringing resonances
  function genTank(sr, secs, seed, o) {
    o = Object.assign({ eng: 0.4, body: 0.3, rumble: 0.5, growl: 0.8, clatter: 1.05 }, o || {});
    sr = sr || 32000; secs = secs || 16; var r = rng(seed || 7), n = Math.round(sr * secs), x = new Float32Array(n), i;
    var wob = slow(n, sr, secs, [[Math.round(0.4 * secs), 0.75], [Math.round(0.63 * secs), 0.45], [Math.round(0.21 * secs), 0.35]], r);   // load swell ~0.4-0.6 Hz, deep
    // engine firing pulses: irregular timing, each a damped 52 Hz sine + low noise knock
    var t = 0;
    while (t < secs) {
      var i0 = Math.floor(t * sr), a = 0.7 + 0.5 * r(), load = 1 + 0.6 * wob[i0 % n];
      addRing(x, i0, sr, 50 + 10 * r(), 0.028, o.eng * 0.9 * a * Math.max(0.35, load));
      addRing(x, i0, sr, 100 + 12 * r(), 0.014, o.eng * 0.35 * a * Math.max(0.35, load));
      addNoiseBurst(x, i0, sr, 0.012, o.eng * 0.30 * a, r, 0.12);
      var f = 26 * (1 + 0.05 * wob[i0 % n]);
      t += (1 / f) * (1 + (r() - 0.5) * 0.16);
    }
    // body: steady 48/96/144 Hz with slow frequency wander
    var ph1 = 0, ph2 = 0, ph3 = 0; for (i = 0; i < n; i++) { var fw = 48 * (1 + 0.03 * wob[i]); ph1 += 2 * Math.PI * fw / sr; ph2 += 2 * Math.PI * 75 * (1 + 0.025 * wob[i]) / sr; ph3 += 2 * Math.PI * 108 * (1 + 0.02 * wob[i]) / sr; x[i] += o.body * (0.8 * Math.sin(ph2 + 0.4) + 0.6 * Math.sin(ph3 + 1.1)) * (0.6 + 0.4 * wob[i]); x[i] += o.body * (0.35 * Math.sin(ph1) + 0.3 * Math.sin(2 * ph1 + 0.7) + 0.08 * Math.sin(3 * ph1 + 1.3)) * (0.7 + 0.3 * wob[i]); }
    // rumble
    var rb = onePoleLP(brown(n, r), 110, sr); for (i = 0; i < n; i++) x[i] += o.rumble * rb[i] * (1.5 + 1.2 * wob[i]);
    var g0 = bandpass(white(n, r), 170, 1.0, sr), g1 = bandpass(white(n, r), 260, 0.9, sr), g2 = bandpass(white(n, r), 620, 1.1, sr);                     // mechanical growl of the diesel, breathing with the load
    for (i = 0; i < n; i++) x[i] += o.growl * (g0[i] * 3.2 + g1[i] * 2.0 + g2[i] * 1.4) * Math.max(0.2, 0.7 + 0.45 * wob[i]);
    // clatter: ~30 links/s, jittered, in swells; each link rings two resonances; a few big clanks
    var cl = new Float32Array(n), swell = slow(n, sr, secs, [[Math.round(0.9 * secs), 0.5], [Math.round(0.37 * secs), 0.4]], r);
    t = 0.01;
    while (t < secs) {
      var j0 = Math.floor(t * sr), env = Math.max(0.12, 0.7 + swell[j0 % n]), q = r(), amp = env * (0.25 + 0.75 * q * q);
      var f1 = 600 + 1700 * r();
      addRing(cl, j0, sr, f1, 0.006 + 0.03 * r(), amp * 0.5);
      addRing(cl, j0, sr, f1 * (1.5 + r() * 1.1), 0.004 + 0.02 * r(), amp * 0.3);
      addNoiseBurst(cl, j0, sr, 0.0015, amp * 0.5, r, 0.7);
      if (r() < 0.045) { addRing(cl, j0, sr, 300 + 500 * r(), 0.07, amp * 1.6); addRing(cl, j0, sr, 1600 + 900 * r(), 0.04, amp * 0.9); }
      t += (1 / 30) * (0.25 + 1.5 * r());
    }
    for (i = 0; i < n; i++) x[i] += cl[i] * o.clatter;
    onePoleHP(x, 22, sr);
    x = reverb(x, sr, 0.22, 0.9);
    var lv = slow(n, sr, secs, [[Math.round(0.11 * secs), 0.5], [Math.round(0.27 * secs), 0.3]], r);       // slow level wander, about +-4 dB, like the passing of the vehicle through the mix
    for (i = 0; i < n; i++) x[i] *= Math.pow(10, 0.45 * lv[i] / 2);
    normalise(x, -24, 0.9); softclip(x, 2.4);
    return normalise(x, -17, 0.92);
  }

  // ---- jet: broadband turbine roar + a thin whine with a slow swell + low rumble
  function genJet(sr, secs, seed) {
    sr = sr || 32000; secs = secs || 12; var r = rng(seed || 11), n = Math.round(sr * secs), i;
    var sw = slow(n, sr, secs, [[Math.round(0.25 * secs), 0.45], [Math.round(0.7 * secs), 0.2]], r);
    var roar = white(n, r); onePoleHP(roar, 180, sr); onePoleLP(roar, 3200, sr); onePoleLP(roar, 3800, sr);
    var mid = bandpass(white(n, r), 1100, 0.7, sr);
    var x = new Float32Array(n), ph = 0, ph2 = 0;
    for (i = 0; i < n; i++) {
      var g = 0.8 + 0.5 * sw[i]; x[i] = roar[i] * 1.3 * g + mid[i] * 2.0 * g;
      ph += 2 * Math.PI * (820 + 60 * sw[i]) / sr; ph2 += 2 * Math.PI * (1640 + 120 * sw[i]) / sr;
      x[i] += (0.07 * Math.sin(ph) + 0.03 * Math.sin(ph2)) * (0.6 + sw[i]);
    }
    var lo = onePoleLP(brown(n, r), 140, sr); for (i = 0; i < n; i++) x[i] += lo[i] * 1.4;
    onePoleHP(x, 40, sr); x = reverb(x, sr, 0.18, 1.2);
    return normalise(x, -19, 0.92);
  }

  // ---- marching: a platoon (12 pairs of boots) on a 2 Hz beat, each boot a thump + heel click + gear rattle; the beat is slightly uneven
  function genMarch(sr, secs, seed) {
    sr = sr || 32000; secs = secs || 14; var r = rng(seed || 5), n = Math.round(sr * secs), x = new Float32Array(n), steps = Math.round(secs * 2), k, m;
    for (k = 0; k < steps; k++) {
      var tb = k * (secs / steps) + (r() - 0.5) * 0.02;
      for (m = 0; m < 12; m++) {
        var t = tb + (r() - 0.5) * 0.07, i0 = ((Math.floor(t * sr)) + n) % n, a = 0.5 + 0.7 * r();
        addRing(x, i0, sr, 70 + 30 * r(), 0.05, 0.3 * a);                  // boot thump
        addNoiseBurst(x, i0, sr, 0.035, 0.7 * a, r, 0.2);                   // heel body
        addRing(x, i0, sr, 900 + 900 * r(), 0.008, 0.45 * a);              // heel click
        if (r() < 0.6) addNoiseBurst(x, i0 + Math.floor(0.03 * sr * r()), sr, 0.07, 0.16 * a, r, 0.6);   // gear rattle
      }
    }
    onePoleHP(x, 30, sr); x = reverb(x, sr, 0.3, 0.8);
    return normalise(x, -19, 0.92);
  }

  // ---- distant thump (explosion far away): low sine drop + dull noise, long tail
  function genThump(sr, seed) {
    sr = sr || 32000; var r = rng(seed || 3), n = Math.round(sr * 2.4), x = new Float32Array(n);
    addRing(x, 0, sr, 38 + 14 * r(), 0.35, 1.0); addRing(x, 0, sr, 70 + 20 * r(), 0.2, 0.5);
    var nb = new Float32Array(n); addNoiseBurst(nb, 0, sr, 0.18, 0.9, r, 0.05); for (var i = 0; i < n; i++) x[i] += nb[i];
    onePoleHP(x, 25, sr); x = reverb(x, sr, 0.4, 1.4);
    for (i = 0; i < 40; i++) x[i] *= i / 40;
    return normalise(x, -20, 0.9);
  }

  var api = { genTank: genTank, genJet: genJet, genMarch: genMarch, genThump: genThump };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.WarSound = api;
})(typeof window !== 'undefined' ? window : this);
