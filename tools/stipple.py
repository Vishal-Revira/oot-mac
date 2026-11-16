#!/usr/bin/python3
# Pixel-level checker noise in a picture: the mean 2x2 checkerboard response of the luma, C = |L00 - L10 - L01 + L11|, against the mean gradient G = |dx| + |dy|,
# over the middle of the picture (x 0.30-0.70, y 0.45-0.90). Smooth edges give C/G near 0.1-0.2; a dither or stipple pattern pushes it up.
# Usage: stipple.py <png>[:<fraction of the image the picture fills, from the top left, default 1>] ...   (needs numpy: the system python3 has it)
import subprocess, sys, tempfile, os, struct
import numpy as np; np.seterr(all="ignore")
def load(png):
    with tempfile.TemporaryDirectory() as d:
        b = os.path.join(d, 'a.bmp'); subprocess.run(['sips', '-s', 'format', 'bmp', png, '--out', b], capture_output=True, check=True)
        raw = open(b, 'rb').read()
    off, = struct.unpack_from('<I', raw, 10); w, h = struct.unpack_from('<ii', raw, 18); bpp, = struct.unpack_from('<H', raw, 28)
    n = bpp // 8; row = (w * n + 3) & ~3
    a = np.frombuffer(raw, np.uint8, count=row * abs(h), offset=off).reshape(abs(h), row)[:, :w * n].reshape(abs(h), w, n)[:, :, :3].astype(np.float32)
    return a[::-1] if h > 0 else a
for arg in sys.argv[1:]:
    png, _, frac = arg.partition(':'); frac = float(frac or 1)
    a = load(png); H, W = int(a.shape[0] * frac), int(a.shape[1] * frac)
    L = (a[:H, :W] @ np.array([0.114, 0.587, 0.299], np.float32))[int(.45 * H):int(.90 * H), int(.30 * W):int(.70 * W)]
    C = np.abs(L[:-1, :-1] - L[:-1, 1:] - L[1:, :-1] + L[1:, 1:]).mean()
    G = (np.abs(L[:-1, :-1] - L[:-1, 1:]) + np.abs(L[:-1, :-1] - L[1:, :-1])).mean()
    print('%-28s checker %.2f  gradient %.2f  ratio %.3f  mean luma %.1f' % (os.path.basename(png), C, G, C / max(G, 1e-6), L.mean()))
