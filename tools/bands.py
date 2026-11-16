#!/usr/bin/env python3
# Score a shot for horizontal garbage bands: rows whose change from the row above is far above the picture's typical row change.
# Usage: bands.py <png> [...]   (converts each through sips to a 24-bit BMP; no numpy needed)
import os, struct, subprocess, sys, tempfile, statistics as S

def load(png):
    fd, bmp = tempfile.mkstemp(suffix='.bmp'); os.close(fd)
    subprocess.run(['sips', '-s', 'format', 'bmp', png, '--out', bmp], check=True, capture_output=True)
    b = open(bmp, 'rb').read(); os.unlink(bmp)
    off, = struct.unpack_from('<I', b, 10); w, h = struct.unpack_from('<ii', b, 18); bpp, = struct.unpack_from('<H', b, 28)
    px = bpp // 8; stride = (w * px + 3) & ~3; rows = []
    for y in range(abs(h)):
        r = b[off + y * stride: off + y * stride + w * px]
        rows.append([(r[i + 2] + 2 * r[i + 1] + r[i]) >> 2 for i in range(0, w * px, px)])   # BGR(A) → luma-ish
    if h > 0: rows.reverse()   # bottom-up BMP
    return rows

def score(rows):
    w = len(rows[0])
    d = [sum(abs(a - b) for a, b in zip(rows[y], rows[y - 1])) / w for y in range(1, len(rows))]
    med = S.median(d)
    spikes = [y + 1 for y, v in enumerate(d) if v > 3 * med]
    return med, spikes

def line(what, med, sp):
    gaps = [b - a for a, b in zip(sp, sp[1:]) if b - a > 3]
    return f'{what} over 3x median {len(sp)} (median change {med:.1f}' + (f', spacing {S.mode(gaps)} px)' if len(gaps) >= 3 else ')')

for p in sys.argv[1:]:
    rows = load(p); cols = [list(c) for c in zip(*rows)]
    print(f'{os.path.basename(p)}: ' + line('rows', *score(rows)) + '; ' + line('columns', *score(cols)))
