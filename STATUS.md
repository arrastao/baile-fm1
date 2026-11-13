# BAILE 0.8 candidate — delay, autoplay, LED playhead, part level

Status: **source and host tests only. Not built as firmware, not flashed, not hardware-validated.** 0.7 remains the stable release and `firmware/BAILE-0.7-FM1.fwsc` is untouched.

- Autoplay: the sequencer starts when the three-second splash ends (same MIDI start path as PLAY). PLAY still stops/starts.
- LED playhead: keyboard LEDs show the selected part's steps; the LED under the playhead shows the inverse, so a lit step blinks off as it passes and an empty step blinks on.
- SELECT (encoder 0) edits the sampler Level of the selected part in steps of 4 (0..127). Stored per kit for the session, like pattern edits.
- Delay replaces reverb (`app/delay.c`): mono 11.025 kHz int16 line (32 KiB RAM), 1/4 note synced to BPM (1/8 below ~40 BPM so the line fits), feedback 50%, 250 Hz high-pass + 4 kHz low-pass (a wide band centred on 1 kHz; an approximation of Ableton's Filter 1 kHz / Width 8, not an exact match), repitch smoothing when the tempo changes, no ping-pong, no L/R offset, no modulation. K2 is Dry/Wet 0–100%, initial 50% (Ableton-style: dry stays unity to 50%, wet is unity from 50%). 0% is bit-exact dry; the tail rings out after STOP. All reverb sends stay at zero and the engine reverb receives no signal. LCD shows `DLY`, and `VOL` for the selected part.
- Host acceptance (`tests/acceptance.py`, `tests/audio_levels.py`): autoplay, LED playhead, SELECT bounds, delay bypass, echo time/level, tail, click-free BPM and Dry/Wet changes. Not run here: native firmware build, WebAssembly build, `tests/native_layout.py`, `tests/web-panel.mjs`, `tests/source_contract.py` (needs the upstream git history).
- Open risks for hardware: the new 32 KiB buffer and `baile_delay` in the audio ISR need the native build's heap/SRAM checks and a listening test on the FM-1; the published web simulator still runs the 0.7 wasm until it is rebuilt.

# BAILE 0.7 — stable

Promoted on 2026-11-09 after the user reported that BAILE 0.7 was working perfectly on their physical FM-1. This is a user-reported hardware result, separate from the automated host and emulator checks. The promotion does not rebuild or modify the tested firmware.

- Firmware: `BAILE-0.7-FM1.fwsc` (590388 bytes).
- SHA-256: `ec1ac0da4085b2509fc11cec100a1870b4302da0c3ebae3e168b395289be6361`.
- Includes normalized samples for Tamborzão, Voltmix and Beat Bolha, single-bar patterns, approved Bolha BRILHANTE and the three-second splash.
- Original WAVs and earlier encoded banks are preserved.
- Existing limitations: pattern edits last for the current session; kit switching is observed by the control task rather than sample-accurate; migration from every other firmware has not been tested.

The build-time `hardware_tested` fields and older development labels are historical evidence and remain unchanged. The following records describe earlier versions at the time they were built.

# BAILE 0.6 — three-second splash

The complete boot artwork is held for three seconds after the first LCD frame is submitted. Panel controls cannot skip this interval; screen and engine servicing continue. After the hold, Tamborzão opens normally.

Includes the 0.5 single-bar update and approved Bolha BRILHANTE pattern. The user confirmed 0.4 on physical hardware; 0.6 physical-device validation is pending. Host tests verify splash hold, ignored early PLAY input, eventual transition, all three kits, single-bar loops, editing and effects. Native build/package evidence is generated under build/dx7/generated.

Previous development records follow:

# BAILE 0.5 — single-bar update

All three presets use one bar (16 steps). The first bar of each earlier pattern is retained, except Bolha BRILHANTE, which uses the user-approved browser edit: steps 4, 7, 11 and 13. Page controls are inactive; kit switching observes the 16-step wrap.

The user confirmed BAILE 0.4 worked perfectly on a physical FM-1 on 2026-11-09. That report applies to 0.4. Hardware validation of 0.5 remains pending.

Build and test evidence for 0.5 is generated under build/evidence and build/dx7/generated. SDK, native board drivers and portable engine remain pinned and unmodified.

Previous 0.4 build record follows (historical pre-device-test status):

# BAILE rebuild — 2026-11-09

Status: firmware compiled and packaged on macOS; new physical-device installation pending.

## Verified

- Latest FM1 Open main queried: `4c7496daac04a95ff10d1afdcc8f9ead2dbabc41`.
- Fresh clone; previous BAILE checkout untouched.
- Clean upstream host build/boot before application changes.
- All SDK files retain their pinned hashes; native board drivers and existing portable engine/DSP sources unchanged.
- Three real sample banks, 12 samples, original/approved quantized patterns and supplied art embedded.
- Host acceptance: bank bytes, source-derived note masks, audible finite output for every kit, independent RAM edits, both bars, queued changes, preset bounds, exact saturation bypass, finite saturation output, audible reverb, reboot defaults and no performance-time storage writes.
- WebAssembly builds. Browser PLAY/STOP and Tamborzão → Voltmix → Bolha transitions observed with the new preview.
- Native diagnostic compilation and structural checks passed: 551528 bytes of application in a 584993-byte limit; 239244 bytes of runtime heap; 143 audio/panel SRAM symbols checked.

- macOS FWSC generated: `firmware/BAILE-0.4-MAC.fwsc`, 590388 bytes. SHA-256 `a712e7750feb14e4a7973b96c6a99119e24a2c79c62e44c671e08170d045f584`.
- SDK container CRC verification passed; decoded application matches the compiled bytes; all three sample banks embedded.
- First 16 KiB of boot and OTA loader match the user-confirmed Tamborzão 0.1 exactly. The Python packager reproduces that entire earlier package byte for byte.
- Native firmware boot and audio passed in the corrected local diagnostic emulator; see `docs/evidence/native-emulator.log`.

## Not verified

- Official JieLi Windows 2.5.3 compiler execution as an alternative build route. The macOS JieLi Linux + Blink route has now generated the FWSC successfully; the Windows wrapper remains unexecuted.
- M-UPGRADE acceptance, verification, flashing, reboot and sound on the actual FM-1.
- Migration of USER/BTIF storage from the currently installed firmware.
- Sample-accurate kit changes. The unchanged SDK only exposes a control-task switch; see the timing limitation in ARCHITECTURE.md.

No new firmware was flashed and no user backup was overwritten. The compiled FWSC is provided for device testing, not represented as physically validated. The user-reported Tamborzão 0.1 hardware success remains evidence about that earlier binary only.

## Next physical milestone

Test installation of the verified macOS-built package and cold boot on the FM-1. Keep the verified Tamborzão 0.1 artifact available for comparison. Do not treat a new source base alone as a resolution of the previous verification timeout.
