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
