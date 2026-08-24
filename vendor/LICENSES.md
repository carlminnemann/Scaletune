# Third-party components bundled with ScaleTune

Everything below permits redistribution inside a compiled application. The two
MIT components require the copyright notice to be retained; the drum kit is
CC-BY 4.0 and requires attribution. Keep this file in the app bundle and surface
the attributions in an "About / Licenses" screen before submitting to the App
Store or Google Play.

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

## Carl Minnemann — bass drum and snare
`vendor/drums/kick.wav` · `snare.wav` — 61 KB together

Recorded by Carl Minnemann in his own room, from his own kit, and owned by him:
no third-party licence applies to these two. They replaced the borrowed kick and
snare. Each is one stroke cut from a longer take, trimmed so the transient is at
the front, tapered and normalised the same way as the rest.

## Muldjord Kit — cymbals
`vendor/drums/hhc.wav` · `hho.wav` · `ride.wav` — 261 KB together

Three hits from a recorded acoustic kit, used by the metronome's accompaniment
styles: closed hi-hat, open hi-hat, ride. The clave in the
bossa is not among them — it is synthesised, two short partials and no body,
because the kit has no rim and a soft snare hit gave a thud where a bossa wants
a piece of wood. Each is one velocity layer of the original,
trimmed to length, tapered over its last third so the cut cannot click, and
normalised to a peak of 0.95. The originals are 24-bit 44.1kHz FLAC, several
hundred kilobytes each and up to fifty velocity layers per drum; what is
bundled is a small selection at 16-bit, which is what a practice tool needs.

Recorded by Lars Muldjord. Published by the FreePats project.
License: Creative Commons Attribution 4.0 (CC-BY 4.0)
Source: https://freepats.zenvoid.org/Percussion/acoustic-drum-kit.html
        https://github.com/freepats/muldjordkit

**Attribution required.** Any distribution of the app must credit "Muldjord Kit
by Lars Muldjord (FreePats), CC-BY 4.0" where users can find it — the app's
guide, an About screen, or the store listing.

---

## Why these are bundled rather than fetched

A packaged mobile app must not download executable JavaScript at runtime:
Capacitor's default Content-Security-Policy blocks external scripts, and
Apple's review guidelines restrict apps that fetch executable code. Bundling
also makes the Real piano timbre work with no network at all, which matters
for a practice tool used in rehearsal rooms and backstage.
