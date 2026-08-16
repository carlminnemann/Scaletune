# Third-party components bundled with ScaleTune

Both components below are MIT licensed, which permits redistribution inside a
compiled application provided the copyright notice is retained. Keep this file
in the app bundle and surface the attributions in an "About / Licenses" screen
before submitting to the App Store or Google Play.

---

## soundfont-player 0.12.0
`vendor/soundfont-player.min.js` — 22 KB

Copyright (c) 2015 Daniel Gómez Blasco (danigb)
License: MIT
Source: https://github.com/danigb/soundfont-player

## FluidR3 GM — instrument samples
`vendor/acoustic_grand_piano-mp3.js` — 2.5 MB
`vendor/cello-mp3.js` — 2.9 MB
`vendor/oboe-mp3.js` — 2.7 MB

All cover A0–C8. The cello and oboe are played looped in Drone mode: their
samples run dry after roughly three seconds, which suits a sequence note but not
a drone that has to hold indefinitely. The organ is not sampled at all — it is
synthesised from a harmonic profile measured off the FluidR3 church organ, which
is a description rather than a copy and carries no sample data.

Those loops are also pitch-corrected: both are real players with a 4–5 Hz
vibrato, which a tuning reference must not have. The sustain is tracked and read
back at a corrected rate — point by point where that measurably steadies the
pitch, at one fixed rate otherwise. Measured across the range, every loop lands
within a cent of the note.

FluidR3 GM soundfont by Frank Wen.
MP3/JS conversion by Benjamin Gleitzman — midi-js-soundfonts.
License: MIT
Source: https://github.com/gleitz/midi-js-soundfonts

---

## Why these are bundled rather than fetched

A packaged mobile app must not download executable JavaScript at runtime:
Capacitor's default Content-Security-Policy blocks external scripts, and
Apple's review guidelines restrict apps that fetch executable code. Bundling
also makes the Real piano timbre work with no network at all, which matters
for a practice tool used in rehearsal rooms and backstage.
