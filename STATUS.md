# Test status and known limits

Development snapshot: **BAILE 0.3**, documented 2026-11-08. The underlying physical installation attempts were recorded on 2026-11-07.

## Evidence by target

| Target | Observed result | What it does not prove |
| --- | --- | --- |
| Portable C host | Four-kit audio, pattern editing, pending selection and effects tested; embedded Tamborzão works with blank writable flash | Native CPU instructions, board I/O or physical timing |
| WebAssembly | The portable instrument boots and renders audio in the browser | Execution of the native firmware package |
| Native `.fwsc` emulation | Boot and PLAY produce audio with the local emulator corrections | Physical installation, physical audio or full-speed DSP |
| M-UPGRADE file selection | Three-digit wrappers accepted as versions 802/803; long version wrapper rejected | Successful verification or programming of the FM-1 |
| Physical migration from Tessera 3.2.2 | Verification timed out; application-write phase was not reached in logs; Tessera still answered after the attempts | A successful BAILE installation |

Recorded technical results are in [docs/evidence/](docs/evidence/). Public evidence is restricted to technical results and emulator output; no personal backup or full updater history is included.

## What failed during installation

1. BAILE 0.2's long outer version was rejected by the installed M-UPGRADE parser. A three-digit wrapper fixed file selection, not installation.
2. Its `flash.bin` extent was `0x7F000`. The examined Tessera migration code accepts `0x93000` or `0x89000` and refuses other extents. The physical attempt stopped after header reads.
3. BAILE 0.3 used the accepted extent and coherent USER/VM/BTIF regions. Physical V15 and V16 boot-area variants both stopped at the first boot-area comparison. The exact physical-screen failure code was not captured, so boot mismatch versus a boot-read failure remains unresolved.
4. The physical instrument subsequently responded through its editor protocol as **TESSERA v3.2.2**. BAILE was not verified installed.

The tests using Tessera's portable migration core initialized the simulated boot region to the package's boot region. They verify that the model accepts that matching case; they do not establish a match with the physical instrument.

Relevant upstream investigation: [Tessera 3.2.2 OTA verification](https://github.com/Rastapopolix/tessera/blob/v3.2.2/firmware/src/ota.c). That code's safety checks were not disabled.

## Known behavior limits

- Voltmix, Bolha and Mandelão sounds/patterns are provisional.
- Edits live in RAM only; reboot/reload restores factory patterns.
- The board's panel-polling kit transition can leave the first hit on the old kit.
- Physical Saturator DSP cost and audio deadlines have not been measured.
- The browser's pre-render synchronization differs from the board SDK.
- The native emulator needed local RX-DMA and instruction implementations and ran below real time.
- The FM1 Open binary SDK remains a device-specific dependency with separate licensing.

## Required before a hardware release

- Identify the exact boot-area refusal on the physical device without bypassing protection.
- Establish and verify the migration/recovery route and actual storage layout.
- Confirm BAILE's physical boot, LCD, keys, encoders and audio output.
- Measure effects CPU budget, audio underruns, kit transitions and USB/MIDI behavior used by the product.
- Test power cycles, session-reset behavior and the effects of migration on prior saved data.

No stable firmware release is published as part of this source snapshot. CI and emulator checks are not substitutes for these device checks.
