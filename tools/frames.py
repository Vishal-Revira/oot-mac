#!/usr/bin/env python3
# Frame-time distribution from a DM_NVN_TSV table: per frame @frame_ms (and the GPU span), over frames [first, last].
# Usage: frames.py <tsv> [first frame] [last frame]
import sys, collections
path = sys.argv[1]; lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0; hi = int(sys.argv[3]) if len(sys.argv) > 3 else 1 << 62
rows = collections.defaultdict(dict)
for ln in open(path):
    p = ln.rstrip('\n').split('\t')
    if len(p) < 3 or not p[0].isdigit(): continue
    f = int(p[0])
    if lo <= f <= hi and p[1] in ('@frame_ms', '@gpu_beg_ms', '@gpu_end_ms'):
        try: rows[f][p[1]] = float(p[2])
        except ValueError: pass
ft = sorted(r['@frame_ms'] for r in rows.values() if '@frame_ms' in r)
gs = sorted(r['@gpu_end_ms'] - r['@gpu_beg_ms'] for r in rows.values() if '@gpu_end_ms' in r and '@gpu_beg_ms' in r)
if not ft: sys.exit('no frames in range')
q = lambda a, x: a[min(len(a) - 1, int(x * len(a)))]
n = len(ft); total = sum(ft) / 1000
print(f'frames {n} over {total:.1f} s: {n / total:.1f} fps; frame p50 {q(ft, .5):.2f} p95 {q(ft, .95):.2f} p99 {q(ft, .99):.2f} max {ft[-1]:.1f} ms')
print('  over 17 ms (missed 60): %d (%.1f%%), over 34 ms (missed 30): %d, over 50 ms: %d' % (sum(t > 17 for t in ft), 100 * sum(t > 17 for t in ft) / n, sum(t > 34 for t in ft), sum(t > 50 for t in ft)))
if gs: print(f'  GPU span p50 {q(gs, .5):.2f} p95 {q(gs, .95):.2f} max {gs[-1]:.1f} ms')
