#!/usr/bin/env python3
"""Generate ScaleTune's app icons.

No image library is installed on this machine, so the PNGs are written by hand:
raw RGBA scanlines, zlib-deflated, wrapped in the three chunks a PNG needs.
The mark is three concentric rings around a solid centre - a pitch radiating -
which stays legible down to a home-screen icon.
"""
import zlib, struct, math, os

BG      = (0x12, 0x14, 0x1a)
RING    = (0x3b, 0x82, 0xf6)   # the app's blue
CENTRE  = (0xea, 0xb3, 0x08)   # the app's yellow
SS      = 3                    # supersampling factor per axis, for smooth edges


def coverage(px, py, size):
    """Fraction of this pixel covered by the mark, and which colour it is."""
    cx = cy = size / 2.0
    ring_hits = 0
    centre_hits = 0
    total = SS * SS
    for sy in range(SS):
        for sx in range(SS):
            x = px + (sx + 0.5) / SS
            y = py + (sy + 0.5) / SS
            d = math.hypot(x - cx, y - cy) / size          # 0..~0.7
            if d <= 0.105:
                centre_hits += 1
            else:
                for r in (0.215, 0.335, 0.455):
                    if abs(d - r) <= 0.024:
                        ring_hits += 1
                        break
    return ring_hits / total, centre_hits / total


def blend(base, top, a):
    return tuple(round(b + (t - b) * a) for b, t in zip(base, top))


def make_png(size, path):
    rows = []
    for y in range(size):
        row = bytearray([0])                                # filter type 0
        for x in range(size):
            ring_a, centre_a = coverage(x, y, size)
            c = BG
            if ring_a:
                c = blend(c, RING, ring_a)
            if centre_a:
                c = blend(c, CENTRE, centre_a)
            row += bytes(c) + b'\xff'
        rows.append(bytes(row))
    raw = b''.join(rows)

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))

    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 9))
           + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, '..', 'icons')
os.makedirs(out, exist_ok=True)
for size, name in [(180, 'apple-touch-icon.png'), (192, 'icon-192.png'), (512, 'icon-512.png')]:
    n = make_png(size, os.path.join(out, name))
    print(f'{name:24} {size}x{size}  {n:,} bytes')
