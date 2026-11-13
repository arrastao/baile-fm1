# BAILE web panel

The GitHub Pages app is served from `docs/`. Run `python3 -m http.server 8768 --directory docs` from the repository root to preview it locally. No build step or third-party JavaScript dependency is required.

## Controls

The panel follows the [Felucca hardware diagram](https://github.com/hugelton/Felucca/blob/main/docs/controls.jpg) and the [fm1-emu panel mapping](https://github.com/joakimeriksson/fm1-emu/blob/master/crates/fm1-live/src/panel.rs). Its controls send the same input indices consumed by BAILE 0.8 in `app/screen.c` and `app/baile.c`:

| Physical control | BAILE behavior |
| --- | --- |
| MASTER | Master volume |
| PRESETS | Tamborzão, Voltmix, Beat Bolha; change at the next bar while playing |
| ALGORITHM | Select one of four tracks |
| KNOB1–4 | Saturation, delay dry/wet (starts at 0%), tempo, swing |
| PLAY / STOP | Start or stop the sequencer |
| 16 lower keys | Toggle the selected track's 16 steps |
| SELECT | Level of the selected track (0–127, ±4 per click) |
| Upper keys, other buttons | Same inactive behavior as the current firmware |
| OCT− / OCT+ | One bar in this version; no second page |

Drag knobs up/right to increase, down/left to decrease. Tapping either half changes one increment; keyboard arrows and the mouse wheel also work. The LCD is display-only. LEDs come from the engine's 41 LED outputs, including startup, transport and the selected pattern. Multiple held pointers are tracked separately and released on cancellation, rotation, loss of focus or hiding the page.

## Phone and desktop layout

One device, two layouts. On a phone the device fills the screen and its controls glide (about half a second) between the **landscape** layout (the FM-1 as it looks on the desk) and the **portrait** layout (knobs and LCD on top, button grid, then the keyboard). There is no rotate-your-phone screen. In portrait a slim top bar keeps the **Baixar firmware** button; the keyboard shows eight steps at a time, and the strip above it shows the 16 steps (lit = active) and lets you tap the half you want (1–8 or 9–16). Landscape hides the top bar and shows all 16 keys. Reduced-motion settings turn the animation off.

On a computer (mouse and hover) the simulator always uses the landscape layout inside the rounded FM-1 body, whatever the window size. The first control gesture in landscape also requests fullscreen where the browser allows it.

## Engine and verification

`baile.wasm` is the BAILE 0.8 engine (same C application as the 0.8 firmware, built with `tools/preview.py web`). The sequencer autoplays when the splash ends. The first audio gesture transfers the current engine memory and queued inputs to the AudioWorklet, preserving edits and the three-second startup screen. Output is converted from 44.1 kHz to the browser's actual audio rate. Edits last for the current page session.

Run `node tests/web-panel.mjs` for the shipped engine and worklet checks: three kits, four tracks, all 16 steps and LED mappings, splash interval, autoplay, SELECT level, knob limits, bar-boundary switching, release behavior, memory handoff, finite audio at 44.1/48 kHz and master mute.

Browser validation: portrait 375×812; landscape 844×390 with the animated switch between them; knob dragging, transport, kit/track selection, step editing and orientation changes preserving edits. Desktop layout also checked at 1200×850. These are browser viewport tests, not a physical smartphone or mobile fullscreen compatibility certification. The hardware firmware download is BAILE 0.8 (`firmware/BAILE-0.8-FM1.fwsc`).
