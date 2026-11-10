# BAILE web panel

The GitHub Pages app is served from `docs/`. Run `python3 -m http.server 8768 --directory docs` from the repository root to preview it locally. No build step or third-party JavaScript dependency is required.

## Controls

The panel follows the [Felucca hardware diagram](https://github.com/hugelton/Felucca/blob/main/docs/controls.jpg) and the [fm1-emu panel mapping](https://github.com/joakimeriksson/fm1-emu/blob/master/crates/fm1-live/src/panel.rs). Its controls send the same input indices consumed by BAILE 0.7 in `app/screen.c` and `app/baile.c`:

| Physical control | BAILE behavior |
| --- | --- |
| MASTER | Master volume |
| PRESETS | Tamborzão, Voltmix, Beat Bolha; change at the next bar while playing |
| ALGORITHM | Select one of four tracks |
| KNOB1–4 | Saturation, reverb, tempo, swing |
| PLAY / STOP | Start or stop the sequencer |
| 16 lower keys | Toggle the selected track's 16 steps |
| SELECT, upper keys, other buttons | Same inactive behavior as the current firmware |
| OCT− / OCT+ | One bar in this version; no second page |

Drag knobs up/right to increase, down/left to decrease. Tapping either half changes one increment; keyboard arrows and the mouse wheel also work. The LCD is display-only. LEDs come from the engine's 41 LED outputs, including startup, transport and the selected pattern. Multiple held pointers are tracked separately and released on cancellation, rotation, loss of focus or hiding the page.

## Phone layout

Portrait shows a rotation prompt, a firmware download link and an **Abrir em tela cheia** button. Landscape fills the available viewport, respects safe-area insets and hides the site header, download link and footer. Device proportions adapt to wide screens while the LCD remains square and knobs remain round.

The portrait button requests fullscreen from the click gesture, then attempts to lock landscape orientation when supported. If fullscreen or orientation locking is unavailable, the rotation prompt remains usable and explains the next step. Exiting fullscreen releases an orientation lock acquired by the page. The first instrument control gesture also requests fullscreen when supported and activates audio. Rotation alone is not a user activation and cannot guarantee fullscreen. Browsers that reject the request continue using the full available webpage area. Phone/browser system bars cannot be forcibly hidden. No extra button appears over the landscape instrument panel.

## Engine and verification

`baile.wasm` is byte-identical to the BAILE 0.7 engine previously embedded in the HTML. The first audio gesture transfers the current engine memory and queued inputs to the AudioWorklet, preserving edits and the three-second startup screen. Output is converted from 44.1 kHz to the browser's actual audio rate. Edits last for the current page session.

Run `node tests/web-panel.mjs` for the shipped engine and worklet checks: three kits, four tracks, all 16 steps and LED mappings, splash interval, knob limits, bar-boundary switching, release behavior, memory handoff, finite audio at 44.1/48 kHz and master mute.

Browser validation: portrait 390×844; landscape 844×390 and 667×375 with no control outside the viewport or page overflow; knob dragging, transport, kit/track selection, step editing and orientation changes preserving edits. Desktop layout also checked at 1200×850. These are browser viewport tests, not a physical smartphone or mobile fullscreen compatibility certification. The hardware firmware and its download remain BAILE 0.7 unchanged.
