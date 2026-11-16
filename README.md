# Ocarina of Time on Mac: keyboard and mouse, and an M5 fix for nxnative

A small personal project: playing **The Legend of Zelda: Ocarina of Time** (Nintendo Switch 2, title `0400486024DEC000`, update v131072) natively on a base M5 MacBook Pro with [nxnative](https://github.com/seedds/nxnative).

nxnative does all the hard work: it runs the game's own ARM64 code directly on the Mac and rebuilds the Switch graphics on Metal. This repository adds two small patches on top of it, the settings I play with, and a guide to build the same app from your own copy of the game.

**No game files are here, and none ever will be.** You need your own copy of the game. This project is not affiliated with Nintendo or with nxnative.

## What this adds to nxnative

### 1. A fix for a shader that fails on the M5 (`patches/0002-m5-float-atomic-workaround.patch`)

On an M5 (GPU family `applegpu_g17g`, macOS 26.6.2), Apple's Metal compiler service crashes while building one of the game's compute pipelines (`278f48371bcf0d58`). The log says `XPC_ERROR_CONNECTION_INTERRUPTED`, and nxnative then skips that shader every frame.

The crash comes from a native float atomic add that nxnative started emitting on 14 Nov (its PR #1930). The patch performs the add only when the value is not zero. That builds on the M5, gives the same sums, and keeps the speed-up. All 33 of the game's shaders that use the add compile with it, and all 11 compute pipelines among them build. The shader chain version changes to `4936c5d925b2`, so a build recompiles every shader once (about 50 minutes on a base M5).

As of 17 Nov 2026 nxnative's main branch still emits the bare add, and it still crashes on the M5, including with the newer MSL 3.2 shader setting.

### 2. Keyboard and mouse controls (`patches/0001-keyboard-and-mouse-controls.patch`)

- A plain text keymap, `keymap.txt`, that you can edit while the game runs. The game reads it again when you click back into its window.
- A **Controls** menu: **Edit Keymap…** (⌘K), **Reload Keymap** (⌘⇧K), **Release Mouse**.
- Mouse look: click in the game to capture the mouse, and moving it turns the camera. The mouse buttons and wheel can be bound like keys.
- Upstream nxnative has fixed keys, and its mouse acts as the touchscreen. The default layout here is the Breath of the Wild / Tears of the Kingdom one from [MacNativeGames](https://github.com/ly05010419/MacNativeGames), moved where this game's buttons differ. For example, Ocarina of Time sprints on a held **A**, not B, so **Shift** presses A here.
- 307 unit checks for the keymap parser (`dm/host/tests/t_keymap.c`).

### 3. The settings I play with (`config/env.txt`)

No code here, just choices, each with the reason it was made:

| Setting | Value | Why |
|---|---|---|
| `DM_FPS_TARGET` | `60` | Aim for 60 fps. |
| `DM_FPS_HOLD` | `off` | By default a frame that misses 16.7 ms is held for a second refresh, so one slow frame drops you to 30 fps. Off shows it as soon as it is ready. This was the biggest single gain (43 → 58 fps in town). |
| `DM_OPMODE` | `0` | The game's handheld quality profile: 1440×810 internally, upscaled to 1920×1080. It costs about 13 ms of GPU a frame here, against 18 ms for docked (1920×1080 → 2560×1440), and 60 fps needs under 16.7 ms. |
| `DM_UPSCALER` | `game` | Keep the game's own upscaler. Swapping in MetalFX is about 1.3 ms faster, but the game's upscaler also smooths its dithered hair, cloth and foliage. Without it they look dotted and painterly. |
| `DM_DYNAMIC_RESOLUTION` | `0` | Fixed resolution: a sharp, steady picture. |
| `DM_PSO_MTL4`, `DM_PSO_PREBUILD` | `1` | Build the graphics pipelines ahead, so new areas stutter less. |

## What this is not

- **Not a new engine and not a speed-up.** Everything that makes the game run, and every frame-rate gain, is nxnative's. The frame rate comes from its settings.
- **Not the only way to 60 fps.** [swordboiMacNative](https://github.com/Fasen24-AI/swordboiMacNative) reports 60 fps in Castle Town on the same MacBook Pro M5, with the MetalFX upscaler.
- **Not a polished app.** There is no builder app or settings panel; you build from the command line.
- **Pinned to nxnative of 16 Nov 2026.** Upstream changes every day. The patches are small so they are easy to carry forward.

## Results on my Mac

On a MacBook Pro with a base Apple M5 (10-core GPU, 24 GB, macOS 26.6.2):

| | A 60 fps build of nxnative from 8 Nov, its default frame pacing | This recipe |
|---|---|---|
| Castle Town, first visit | 33.9 fps | 60 fps on the bridge, 50 fps in town |
| Castle Town, walking (warm) | 43 fps | 59.9 fps (95th percentile frame 17.0 ms) |
| A real 41-minute session | — | 58 fps or better 97% of the time |
| Hair, cloth, foliage | — | smooth, with the game's own upscaler (see the settings above) |
| Controls | fixed keys | Breath of the Wild-style keyboard and mouse, editable |

These numbers come from nxnative's frame-time table, on copies of a save, on an otherwise idle Mac. The Castle Town and session numbers were measured with the MetalFX upscaler; the game's own upscaler, which this recipe uses for picture quality, costs about 1.3 ms more GPU time per frame. Details are in [docs/findings.md](docs/findings.md). Your Mac, the area, and anything else using the GPU (a browser playing video, for one) all move these numbers.

## Other Ocarina of Time ports for the Mac

If you want a friendlier app or other features, look at these. Each is its own project:

- [nxnative](https://github.com/seedds/nxnative): the engine itself, with a game note for Ocarina of Time.
- [MacNativeGames](https://github.com/ly05010419/MacNativeGames): its own engine (derived from its Tears of the Kingdom port), with a settings panel, a keyboard drawing for key bindings, frame interpolation and more resolutions.
- [GreenKid-MV](https://github.com/adi0900/GreenKid-MV): a Mac builder app with resolution presets, on nxnative of 10 Nov.
- [swordboiMacNative](https://github.com/Fasen24-AI/swordboiMacNative): a Mac-focused nxnative fork with memory and pacing fixes.
- [kid-with-sword-remake](https://github.com/cheemu21/kid-with-sword-remake): the game on iPhone, with frame generation.

## Build it yourself

### Requirements

- An Apple silicon Mac with **macOS 26.6 or later**. Tested on a base M5. An M4 or newer should manage similar results. Older chips may need docked off and a 30 fps target.
- **Xcode 27.2**, selected with `sudo xcode-select -s /Applications/Xcode.app`, and its Metal toolchain.
- [Homebrew](https://brew.sh) and an arm64 **Python 3.12 or newer**.
- About **60 GB free**: the build unpacks the game (24 GB), and the app is 35 GB.
- **Your own copy of the game** as a `.nup` file ([NUP format](https://github.com/a55uka/nup)), with update v131072.

### 1. Install the tools (once)

```bash
xcodebuild -downloadComponent MetalToolchain
brew install xcodegen zstd glslang
python3 -m pip install lz4 "capstone>=5,<6" fonttools nsz zbic
```

These are nxnative's own requirements. Its [README](https://github.com/seedds/nxnative#requirements) is the reference if anything changes.

### 2. Get this repository and nxnative with the patches

```bash
git clone <this repository's URL> oot-mac && cd oot-mac
./setup.sh
```

`setup.sh` clones nxnative into `./nxnative`, checks out the commit the patches were made on (`a0cad7e0`, 16 Nov 2026) and applies both patches. To use a newer nxnative instead, check it out and run `git apply` on each patch. On 17 Nov's main, patch 0001 applies as is; patch 0002 fails only on the one-line shader chain version in `dm/gfx/nvn/dmsh_chain.h`. Apply the rest with `git apply --exclude=dm/gfx/nvn/dmsh_chain.h`, then run `python3 dm/gfx/tools/dmsh_chain.py --header`, which writes the new version.

### 3. Put your game in place

Put your `.nup` somewhere simple, such as `~/Games/oot.nup`. Never share it or the app you build: both contain the game.

### 4. Build the app

```bash
cd nxnative
caffeinate -i python3 scripts/build_ipa_from_nsp.py ~/Games/oot.nup --platform mac-app --env-file ../config/env.txt -o "../The Legend of Zelda - Ocarina of Time.app"
```

- The first build takes about **1 hour 15 minutes** on a base M5. Most of that is compiling 42,848 shaders. Later builds reuse what did not change.
- `caffeinate -i` keeps the Mac awake: a sleeping Mac pauses the build.
- `--env-file` bakes the settings from step 3 above into the app.

### 5. Play

1. Open the app. The first start prepares shaders for a minute or two. Short stutters in places you have not visited are normal the first time.
2. Click in the game to capture the mouse. Press <kbd>`</kbd> to let it go.
3. For the best frame rate, play plugged in and close GPU-heavy apps such as browser tabs playing video.

Your saves and settings live in `~/Library/Application Support/nxnative/0400486024DEC000/`. A setting in `env.txt` there overrides the one baked into the app, for every build you make.

## Controls

| Keys | Switch button | In the game |
|---|---|---|
| <kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd> | Left stick | Move (hold <kbd>Left Control</kbd> to walk) |
| Mouse (captured), arrow keys | Right stick | Camera |
| <kbd>E</kbd>, <kbd>Return</kbd>, <kbd>Left Shift</kbd> | A | Talk, open, climb; **hold to sprint** |
| <kbd>Backspace</kbd>, <kbd>X</kbd> | B | Put away, back |
| <kbd>Space</kbd> | X | Jump |
| Left click, <kbd>G</kbd> | Y | Sword |
| <kbd>Q</kbd>, middle click | ZL | Target (lock on), shield |
| Right click, <kbd>Left Option</kbd> | ZR | Use the equipped item |
| <kbd>F</kbd> / <kbd>R</kbd> | L / R | Item quick select |
| <kbd>Esc</kbd>, <kbd>I</kbd> | + | Menu |
| <kbd>Tab</kbd>, <kbd>M</kbd> | − | Map |
| <kbd>2</kbd> or <kbd>O</kbd> | D-pad left | Ocarina |
| <kbd>4</kbd> or <kbd>N</kbd> | D-pad right | Navi |
| <kbd>3</kbd> / <kbd>5</kbd> | D-pad up / down | |
| <kbd>V</kbd> / <kbd>C</kbd> | Right / left stick press | Camera reset / — |
| <kbd>H</kbd> (hold) | Shake | Motion controls |
| <kbd>`</kbd> | — | Let the mouse go, or take it back |

To change a key, open **Controls > Edit Keymap…** in the game's menu bar, edit a line such as `X = Space`, and save. [config/keymap.txt](config/keymap.txt) is the default file, with every key name you can use. A game controller works alongside the keyboard.

If you played an earlier build with keyboard controls, your old `keymap.txt` keeps its old keys. Delete it from the folder above to get this layout.

## Troubleshooting

| Problem | Cause and fix |
|---|---|
| Hair and cloth look dotted, surfaces look painted | The MetalFX upscaler is replacing the game's. Set `DM_UPSCALER=game` (the default in this recipe), or pick **Game's own** in the launcher's settings window. |
| Stuck at 30 fps, or swinging between 30 and 60 | Something else is using the GPU, or the Mac is on battery saving power. Check Activity Monitor › Window › GPU History. `DM_FPS_HOLD=off` must be set. |
| The keys are not the ones above | Delete your old `keymap.txt` (see Controls). |
| The build stopped halfway | The Mac slept. Run the same command again: it continues where it stopped. |
| `failed to create compute pipeline ... XPC_ERROR_CONNECTION_INTERRUPTED` in the log | Patch 0002 is missing. Run `./setup.sh` again. |

## Tools

[tools/](tools/) has the small scripts used to measure all this. They read the frame table that nxnative writes with `DM_NVN_TSV=<file>`, and screenshots.

- `frames.py <tsv> [first] [last]`: fps, frame-time percentiles, frames over 17 ms and 34 ms, GPU time.
- `stipple.py <png>…`: how much pixel-level checker noise (dithering) a screenshot has.
- `bands.py <png>…`: scores horizontal garbage bands, a glitch fixed upstream on 7 Nov.

## Credits and license

- [nxnative](https://github.com/seedds/nxnative) by seedds and its contributors, MIT license. Everything that makes the game run is theirs: this repository only patches it.
- The keyboard layout follows [MacNativeGames](https://github.com/ly05010419/MacNativeGames)' Breath of the Wild / Tears of the Kingdom layout.
- This repository is MIT licensed ([LICENSE](LICENSE)). The patches change MIT-licensed nxnative code; its notice is in [NOTICE](NOTICE).

The Legend of Zelda and Nintendo Switch are trademarks of Nintendo. Play only games you own.
