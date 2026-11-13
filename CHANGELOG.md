# Changelog

## 0.8 — 2026-11-13

Hardware: the user reported that this build works on their physical FM-1. Firmware: `firmware/BAILE-0.8-FM1.fwsc` (594484 bytes, SHA-256 `813390703a715913188b486d157d0f81b2d697b12559ac29c25eace5dae9b763`). The build label inside the binary still reads `BAILE 0.8-dev`; the tested bytes were not rebuilt.

### Added
- **Autoplay:** the sequencer starts when the three-second splash ends. PLAY still stops and starts it.
- **LED playhead:** the keyboard LEDs show the selected part's steps; the LED under the playhead shows the inverse (a lit step blinks off as it passes, an empty step blinks on).
- **SELECT encoder:** sets the level of the selected part (0–127, ±4 per click), kept per kit for the session. The LCD shows `VOL`.
- **BPM-synced delay** (`app/delay.c`): 1/4 note, feedback 50%, 250 Hz–4 kHz band filter centred on 1 kHz (an approximation of Ableton's 1 kHz / Width 8 filter), repitch smoothing on tempo changes, no ping-pong, no L/R offset, no modulation. One mono 11.025 kHz line (32 KiB RAM) shared by both channels; below ~40 BPM it uses 1/8 note so the line fits.

### Changed
- **K2 is Delay Dry/Wet** (0–100%, starts at **0%**), replacing Reverb. Dry is exact at 0%; the tail rings out after STOP. The LCD shows `DLY`. The delay is global (master), not per part.
- The engine reverb is no longer used: every reverb send stays at zero.

### Checks
- Host tests (`tests/acceptance.py`, `tests/audio_levels.py`): autoplay, LED playhead, SELECT bounds, exact dry at 0%, echo time and level, tail after STOP, click-free BPM and Dry/Wet changes.
- Native build on macOS (JieLi Linux + Blink): application 553096 of 584993 bytes (0.7: 551528); runtime heap 205516 bytes (0.7: 239244, minimum 49152); 144 audio/panel SRAM symbols checked, including `baile_delay`; SDK hashes, layout and package verification passed.
- Native FM-1 emulator: boot, autoplay, VOL 100→80, DLY 0→50→100, tail after STOP, kit change, finite audio.

### Website
- The GitHub Pages simulator now runs the 0.8 engine (autoplay, delay, SELECT level), labels K2 as Delay, shows SELECT's level, and its download links to `firmware/BAILE-0.8-FM1.fwsc`. `tests/web-panel.mjs` passes.

### Known limits
- Delay amount is global; per-part delay is not possible without separating the parts inside the engine.
- Edits still last for the current session only; kit switching is not sample-accurate (unchanged from 0.7).

## 0.7 — 2026-11-09
Normalized samples for Tamborzão, Voltmix and Beat Bolha; stable after hardware confirmation. See [STATUS](STATUS.md).
