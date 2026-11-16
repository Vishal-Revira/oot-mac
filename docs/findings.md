# Findings

Notes from getting Ocarina of Time (Switch 2) to a steady 60 fps with a clean picture on a base M5 MacBook Pro (10-core GPU, 24 GB, macOS 26.6.2, 3024×1898 ProMotion display) with nxnative, between 6 and 17 Nov 2026.

## How things were measured

- Always on **copies** of a save, one game at a time, on an otherwise idle Mac.
- nxnative's control file (`DM_CTL`) drives the game: buttons and stick directions with hold times (`LUp~5`), waits, and screenshots. So a walk can be repeated exactly.
- `DM_NVN_TSV=<file>` writes a frame table: frame time, and the GPU span of each frame. [`tools/frames.py`](../tools/frames.py) turns it into fps, percentiles and the share of frames over 17 ms (a missed 60 fps refresh) and 34 ms (a missed 30).
- The test route: 20 s standing on the Castle Town drawbridge, then through the gate and about 48 s walking and turning in the market, the busiest place met early in the game.

## Frame rate

The 8 Nov 60 fps build lost frames for four reasons:

1. **The GPU was at its limit in busy views.** In docked mode the frame needs about 18 ms of GPU time here.
2. **Frame-step hold.** nxnative holds a frame that misses its 16.7 ms refresh for a second refresh, so it locks to 30 fps. In the town that made one slow frame cost a whole extra refresh, again and again.
3. **Graphics pipelines built mid-play**, the first time each effect appeared.
4. **Uploads when entering an area.**

What fixed them, measured on the route, walking in town:

| Change | Town fps |
|---|---|
| 8 Nov build, warm | 43.4 |
| `DM_FPS_HOLD=off` | 58.3 |
| Newer nxnative (16 Nov) with pipelines built ahead (`DM_PSO_MTL4=1`, `DM_PSO_PREBUILD=1`), docked | 59.0 |
| Same, handheld quality profile (`DM_OPMODE=0`) | 59.9, GPU 11.4 ms median, 15.1 ms 95th percentile |
| Docked with dynamic resolution instead | 59.9 |

Turning ray tracing off (`DM_RT=0`) made it far slower (9 fps in town), so the game's own lighting path is the fast one on this chip.

Handheld was kept over docked with dynamic resolution because it holds a fixed, sharp picture rather than one whose sharpness changes with the scene.

## Picture: dotted hair and the painterly look

The game ships its own upscaling network, which turns the internal picture into the output picture. It also smooths the game's dithered transparency: hair, cloth edges and foliage are drawn as fine dot patterns that this pass resolves.

nxnative can replace that pass with Apple's MetalFX spatial upscaler (`DM_UPSCALER=metalfx`). It is about 1.3 ms faster here, but MetalFX does not resolve the dither. Hair and cloth then show the dot pattern, and surfaces look painted. Same build, same spot, only that setting changed: dotted with MetalFX, smooth with the game's own upscaler.

Measured noise with [`tools/stipple.py`](../tools/stipple.py): an older and a newer build drew identical pictures at the same settings, so this is the setting, not a rendering bug.

## The compute shader that failed on the M5

Every run on the 16 Nov nxnative logged:

```
[RED] failed to create compute pipeline for 278f48371bcf0d58_b: Compilation failed due to an interrupted connection:
XPC_ERROR_CONNECTION_INTERRUPTED. This error occurred after multiple retries. (its dispatches are skipped)
```

- The shader compiles offline. What fails is building its pipeline at run time, in Apple's compiler service.
- It began with nxnative's change of 14 Nov (PR #1930), which turns a float add on storage memory from a compare-and-swap loop into Metal's native `atomic_fetch_add_explicit` on an `atomic_float`.
- A small Swift tool that builds the pipeline from the shader library reproduces it. The crash happens with the shader's border-colour function constant (216) set to true, at `-O1` and `-O2`, not at `-O0`. The old loop builds. A guarded add, `if (v != 0.0f) atomic_fetch_add_explicit(...)`, builds. Moving the add elsewhere or removing the surrounding code does not help.
- Patch 0002 applies the guard to every such add (404 adds in 33 shaders). The guard skips only adds of zero, which change nothing but the sign of a `-0.0` sum.
- All 11 compute pipelines among those shaders now build on the M5 with the constant either way. The other 22 are draw stages, which cannot be built alone.

This is a workaround for a bug in Apple's GPU compiler, not a root-cause fix. It has not been reduced to a bug report for Apple yet.

## Things that cost frames you might not expect

- **Other apps on the GPU.** With 26–50% of the GPU busy with other apps (a browser, a chat app streaming a long conversation), the same scene took 18 ms of GPU instead of 13, and the game fell from 60 to 33–46 fps. Close them before playing.
- **A sleeping Mac pauses a build.** `caffeinate -i` keeps it awake.
- **An `env.txt` in Application Support beats the app's own settings**, for every build. A setting saved there long ago (MetalFX, say) quietly overrides the recipe.
