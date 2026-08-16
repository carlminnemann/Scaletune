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
`vendor/church_organ-mp3.js` — 2.7 MB
`vendor/oboe-mp3.js` — 2.7 MB

All cover A0–C8. The cello, organ and oboe are played looped in Drone mode:
their samples run dry after roughly three seconds, which suits a sequence note
but not a drone that has to hold indefinitely.

Those loops are also pitch-corrected. Two separate faults are fixed. The cello
and oboe are real players with a 4–5 Hz vibrato, which a tuning reference must
not have; and the organ sits 4 to 9 cents sharp throughout, which matters more.
So the sustain is tracked and read back at a corrected rate — point by point
where that measurably steadies the pitch, at one fixed rate otherwise (a church
organ stop is several pipes at once, and near the top of its range there is no
single period to track). Measured across the range, every loop lands within a
cent of the note.

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
