# ScaleTune

A practice app for instruments you tune yourself: a drone, scales and arpeggios,
a free set of notes, a metronome with accompaniment, and a tuner. One file.

Carl Minnemann — double bass player and teacher — is the author and the only
user who matters. He writes in Portuguese; answer him in Portuguese. Everything
inside the app and every comment in the code is in English.

## Where things are

    index.html    the whole app: markup, style and script in one file
    sw.js         the service worker; CACHE must be bumped with APP_VERSION
    lang/*.json   pt es it fr de ru zh — English lives in the markup itself
    vendor/       his own recordings (strings, piano, hammond, rhodes) and the kit
    tools/        build-samples.py slices and tunes the takes; build-drums.py

Deployed to https://carlminnemann.github.io/Scaletune/ from `main`.

## The deploy ritual, every time

1. Bump `APP_VERSION` in index.html **and** `CACHE` in sw.js. They go together;
   a new page with an old cache is how a device ends up on yesterday's build.
2. Commit and push.
3. Poll the live URL until the new stamp is there. Do not report a deploy from
   the local file.

The page and the language packs are network-first; everything heavy is
cache-first. An installed app updates itself on the next launch with a
connection — verified, not assumed.

## How work is done here

**Measure before and after.** Reproduce the fault with numbers, change one
thing, measure again, and report the numbers to him. When a measurement is the
evidence, validate the meter first — a tuner checked against the same family of
meter that produced its table is not a check.

**A script's click is not a finger.** `.click()` ignores `pointer-events`, so it
passes where a tap fails. For anything a hand touches, read what is actually
under the point and click that.

**Reload the page.** Round-tripping through save and load functions in a live
page does not test what a reload does.

**Every deploy runs a sweep**: click every visible control in six modes and both
themes with an error listener attached; check nothing is clipped at 320px in
German, Russian and Chinese; report the counts.

**Say what is not done.** If something is untested — the microphone, iOS — say
so plainly. He would rather hear it than find it.

## Rules he set, which are not negotiable without him

- **Everything starts at zero.** Opening the app remembers nothing except saved
  exercises, saved patterns, and personal preferences (theme, language, note
  names). Not the last session's settings.
- **Every mode is independent** — tempo, bar, range, phrasing, accompaniment,
  silences, saved exercises and their folders. The exceptions, all deliberate:
  the timbre (the drone keeps its own), and the study list when it is grouped.
- **Scale and Arpeggio share one rotation when Group is chosen.** The run never
  leaves the panel it was started from: a chord in the list plays as an arpeggio
  inside Scale, at Scale's tempo, over Scale's octaves.
- **Nothing destructive without a second tap.** Saving over a name asks; the
  crosses in a list are behind ✕ Select; a folder goes only when empty.
- **Words name what a thing does, not the box it lives in.** Not "panel" (the
  panels are the folds), not "mode" (the modes are the modes of a scale).

## The guide (the ? in the header)

It is short on purpose — it was cut from 4,500 words to 1,200 and must not creep
back. One or two sentences per control, in the same words the buttons use.

The ? in the header is a switch: it puts a mark beside every panel, and each
mark opens **that panel's section alone**. One mark per section — no two visible
marks may open the same page.

## i18n

Every `data-t` / `data-ta` key in the markup must exist in all seven packs, and
the seven packs must hold **exactly the same key set**. Check it before every
commit that touches text:

```bash
python3 -c "
import json,re
s=open('index.html',encoding='utf-8').read()
attr=set(re.findall(r'data-t=\"([^\"]+)\"',s))|set(re.findall(r'data-ta=\"([^\"]+)\"',s))
base=None
for l in ['pt','es','it','fr','de','ru','zh']:
    k=set(json.load(open(f'lang/{l}.json')));base=base or k
    print(l,len(k),'same:',k==base,'missing:',sorted(x for x in attr if x not in k))
"
```

A select that holds words must be rebuilt when the language changes. Beware
apostrophes inside single-quoted strings — one took the whole script down.

## Saved exercises

`EX_KEYS` and `EX_DEEP` are the definition of what an exercise is: a field not
in those lists is not part of one. Adding state means deciding whether it
belongs there — and if it does, `applyExercise` must read it back. A field
written on save and ignored on load is the failure mode that has happened twice.

Volumes: the click's volume is carried, the room's is not.

## Notes on the audio

- Web Audio scheduler with 0.12 s lookahead; the grid is twelfths of a beat, so
  sixteenths and triplets share it.
- `cancelAndHoldAtTime` throws on a param under `setTargetAtTime` — read
  `.value`, cancel, set, then ramp. That was the stop-click.
- The samples are his own, one note in four, shifted by cents to the rest.
