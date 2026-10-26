#!/usr/bin/env node
// Renders the war maps' synthesised ambience (war/warsound.js) to 16-bit mono WAV files for listening tests / numeric comparison.
//   node tools/war_sound_render.cjs OUTDIR [tankSecs]
const fs = require('fs'), path = require('path'), W = (function () { const m = { exports: {} }; new Function('module', 'window', fs.readFileSync(path.join(__dirname, '../war/warsound.js'), 'utf8'))(m, undefined); return m.exports; })();
const out = process.argv[2] || '.', sr = 32000;
function wav(file, x) {
  const b = Buffer.alloc(44 + x.length * 2); b.write('RIFF', 0); b.writeUInt32LE(36 + x.length * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(sr, 24); b.writeUInt32LE(sr * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(x.length * 2, 40);
  for (let i = 0; i < x.length; i++) b.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(x[i] * 32767))), 44 + i * 2);
  fs.writeFileSync(path.join(out, file), b);
}
fs.mkdirSync(out, { recursive: true });
const t0 = Date.now();
wav('v2_tank.wav', W.genTank(sr, +process.argv[3] || 30, 7));
wav('v2_jet.wav', W.genJet(sr, 12, 11));
wav('v2_march.wav', W.genMarch(sr, 14, 5));
wav('v2_thump.wav', W.genThump(sr, 3));
console.log('rendered in', Date.now() - t0, 'ms');
