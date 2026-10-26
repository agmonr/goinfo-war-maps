# War maps: movement sound loops (the owner's picks, 2026-10-21)

All three are CC0 1.0 (public domain dedication): no attribution required, modification and use on a website allowed. Taken as the 128 kbps preview mp3 of each Freesound page, cut, loudness-matched (-20 LUFS) and, for tank and jet, crossfaded (1 s) into a seamless loop with ffmpeg.

| layer | file | title / author | source | cut |
|---|---|---|---|---|
| tanks (engine) | tank.mp3 | "Military Vehicle Humming" - qubodup | https://freesound.org/people/qubodup/sounds/182793/ | 12 s from 18.0 s, 1 s crossfade |
| aircraft (jet engine) | jet.mp3 | "Jet loop 01" - MickBoere | https://freesound.org/people/MickBoere/sounds/269064/ | 12 s from 13.0 s, 1 s crossfade |
| foot soldiers (marching boots) | march.mp3 | "marching-concrete-loop" - stib | https://freesound.org/people/stib/sounds/240732/ | whole file, 8.8 s (made as a loop) |

The reference recording the owner shared for comparison is NOT in the repo and nothing here is derived from it.

## Guns / artillery (own synthesis, no files, no licence question)

Fire boom, whistle and hit boom are computed in the browser at first use by war/daynight.js (functions gunBoomFire, gunWhistle, gunBoomHit; plain noise + sine DSP written for this project). Per shell shot: boom at the gun, falling whistle for the flight (one `period`), deeper boom at the target on arrival. Nothing is downloaded, sampled or derived from any recording.
