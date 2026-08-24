#!/usr/bin/env python3
"""Builds vendor/drums-mine/*.wav from Carl's own kit recordings.

The recordings are short takes, not one-shots: most files hold several strokes,
and the cymbals came in some forty decibels under the drums. So each one is cut
to a single hit, moved so the transient is at the front, tapered at the end
because several of them stop while the cymbal is still ringing, and normalised
on its own — the balance between drums is the mixer's job, not the file's.

Reads from the OneDrive folder; writes 16-bit mono WAV, the same shape the app
already loads. Run from the repo root:  python3 tools/build-drums-mine.py
"""
import math, os, struct, wave

SRC = ('/Users/carlminnemann/Library/CloudStorage/OneDrive-JOBRA/'
       'Carl Minnemann/Claude/bateria')
OUT = 'vendor/drums-mine'

# name    file                   which hit  how long  taper  rate
# "which hit" is 1-based, counted the way tools/look.py counts them: the files
# hold anything from one stroke to six, and the chosen one is the cleanest of
# them — loudest, and with the most room after it before the next.
SPEC = [
    ('kick',  'bombo forte.wav',     1, 0.50, 0.30, 44100),
    ('snare', 'snare forte.wav',     1, 0.40, 0.30, 44100),
    ('hhc',   'hihat fechado.wav',   3, 0.17, 0.35, 44100),
    ('hho',   'choques aberto.wav',  1, 0.34, 0.22, 44100),
    ('ride',  'ride.wav',            2, 0.33, 0.20, 44100),
    ('clave', 'clave.wav',           1, 0.15, 0.30, 44100),
]

BLOCK = 256


def read24(path):
    """Any width, any channel count, out as mono floats."""
    w = wave.open(path)
    n, sr, ch, sw = w.getnframes(), w.getframerate(), w.getnchannels(), w.getsampwidth()
    raw = w.readframes(n)
    w.close()
    out = [0.0] * n
    step = sw * ch
    for i in range(n):
        b = i * step
        acc = 0
        for c in range(ch):
            o = b + c * sw
            if sw == 3:
                v = raw[o] | (raw[o + 1] << 8) | (raw[o + 2] << 16)
                if v & 0x800000:
                    v -= 0x1000000
                acc += v / 8388608.0
            else:
                v = raw[o] | (raw[o + 1] << 8)
                if v & 0x8000:
                    v -= 0x10000
                acc += v / 32768.0
        out[i] = acc / ch
    return out, sr


def envelope(a, block=BLOCK):
    return [max(abs(v) for v in a[i:i + block]) or 0.0
            for i in range(0, len(a) - block, block)]


def hit_starts(env, peak):
    """The sample block each stroke begins at."""
    out, armed = [], True
    for i, v in enumerate(env):
        if armed and v > peak * 0.35:
            out.append(i); armed = False
        elif not armed and v < peak * 0.08:
            armed = True
    return out


def resample(d, src, dst):
    if src == dst:
        return d
    n = int(len(d) * dst / src)
    out = [0.0] * n
    for i in range(n):
        x = i * src / dst
        j = int(x)
        f = x - j
        a = d[j] if j < len(d) else 0.0
        b = d[j + 1] if j + 1 < len(d) else 0.0
        out[i] = a + (b - a) * f
    return out


def db(x):
    return -999.0 if x <= 0 else 20 * math.log10(x)


def main():
    os.makedirs(OUT, exist_ok=True)
    print(f'{"peça":7}{"origem":22}{"duração":>9}{"pico bruto":>12}{"sinal/ruído":>13}')
    for name, fn, which, dur, taper, rate in SPEC:
        d, sr = read24(os.path.join(SRC, fn))
        env = envelope(d)
        peak = max(env)
        starts = hit_starts(env, peak)
        if not starts:
            starts = [0]
        idx = starts[min(which, len(starts)) - 1] * BLOCK

        # back up to the true onset, then 2ms of air so the attack is not clipped
        local = peak
        back = idx
        while back > 0 and abs(d[back]) > local * 0.02:
            back -= 1
        start = max(0, back - int(0.002 * sr))

        cut = list(d[start:start + int(dur * sr)])
        if not cut:
            raise SystemExit('%s: nothing to cut' % name)

        # The noise is measured in the silence BEFORE the stroke, not inside the
        # cut: a cymbal sustains, so the quietest moment while it rings is the
        # cymbal, not the room, and measuring there called a clean open hat
        # noisy. Where a file begins on the hit there is no such silence and the
        # figure is left out rather than guessed.
        lead = d[:max(0, start - int(0.005 * sr))]
        if len(lead) > int(0.02 * sr):
            win = int(0.02 * sr)
            floor = min(max(abs(x) for x in lead[i:i + win]) or 1e-9
                        for i in range(0, len(lead) - win, win))
            snr = '%.1f dB' % (db(max(abs(x) for x in cut)) - db(floor))
        else:
            snr = 'sem silêncio'

        # several of these files stop while the cymbal is still ringing, so the
        # taper is doing real work: without it the cut edge is a click
        tail = int(len(cut) * taper)
        for i in range(tail):
            cut[len(cut) - tail + i] *= 0.5 * (1 + math.cos(math.pi * (i / tail)))

        cut = resample(cut, sr, rate)
        g = 0.95 / (max(abs(x) for x in cut) or 1)
        frames = [max(-32768, min(32767, int(x * g * 32767))) for x in cut]
        p = os.path.join(OUT, name + '.wav')
        f = wave.open(p, 'w')
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
        f.writeframes(struct.pack('<%dh' % len(frames), *frames))
        f.close()
        print(f'{name:7}{fn:22}{len(frames)/rate:8.3f}s{db(peak):11.1f}dB{snr:>13}')


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
