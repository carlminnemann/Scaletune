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

## FluidR3 GM — acoustic grand piano samples
`vendor/acoustic_grand_piano-mp3.js` — 2.5 MB, 52 samples (A0–C8, natural
notes only; the player transposes for the accidentals)

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
