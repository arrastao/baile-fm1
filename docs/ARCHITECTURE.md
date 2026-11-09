# BAILE rebuild architecture

## Boundary with FM1 Open

Pinned upstream: `4c7496daac04a95ff10d1afdcc8f9ead2dbabc41` (main verified 2026-11-08). Fresh Git clone, not a copy of the modified BAILE checkout. No SLOOP or Felucca code.

All `sdk/` bytes are unchanged and verified against `sdk/manifest.json`. `app/board/`, `app/synth/`, existing `web/engine/`, `web/synth/` and third-party DSP code are unchanged. `web/baile_preview.c` is an added read-only preview export.

New application layers:

- `presets.c`: validated embedded bank data and factories generated from asset manifests.
- `samples.c`: read-only bank binding using the upstream sampledrum API; external sample imports fail before writing.
- `baile.c`: kit/part/page selection, session-local projects, queued changes, effects.
- `screen.c`: four-row panel and nonblocking 16-row LCD DMA transfers. Buffer is never modified during a pending transfer; identical bands are skipped.
- `audio_output.c`: one call to the SRAM saturator before the existing master/USB/Bluetooth mixer.
- `project.c`: disables saved-project/session restoration at boot so another firmware's data cannot replace the default kit.

No previous synthetic kits, Mandelão data, stock boot substitution or short-identity repacker was imported. Image RLE bytes are reused assets, while the screen/controller is rewritten. The macOS build/check scripts derive from the earlier local FM1 Open tooling and use JieLi Linux through Blink, the same route as Tamborzão 0.1. They are separate from the official Windows build.

## Storage

Flash is 1 MiB. Original user storage was 536576 bytes; BAILE reserves 405504 bytes, leaving more space for embedded application assets. The new application still keeps the official entry point, boot resources, OTA loader, VM minimum and final chip configuration region. The storage change affects USER/BTIF placement and requires migration testing.

`baile-layout.json`, the application storage enum, native diagnostic identity and generated Windows build must agree. The Windows wrapper derives its packager from the immutable official C# file; it does not splice boot bytes from another firmware. Product identity follows the upstream long-ID rule (`FM-1_8490140`). Do not assume M-UPGRADE acceptance from a file extension or static checks.

## Timing limit

The unchanged native SDK exposes transport state to the control task, not a public atomic preset/bank swap at an audio boundary. While playing, BAILE applies the queued kit when the control task observes the new bar. The first hit at that boundary can still use the previous kit, and a brief audio pause is possible during replacement. A sample-accurate transition is **not** claimed; this needs a dedicated engine-level solution and hardware measurement before a performance release.

## Asset fidelity

SEA5 banks are 32 kHz mono. Existing encoded banks are preserved byte for byte, not recompressed. `tools/assets.py` validates the header, CRC, slot bounds, frame lengths and every codec header before generating C arrays. Tamborzão uses the original two-bar events. Voltmix/Bolha use the approved ordering of notes 60–63 and nearest-sixteenth quantization, repeated across two bars. Shared event velocity is 100, as in the previous imported assets.

Art uses 160-wide, 32-color RLE sources expanded to a 240 × 240 LCD. Header art occupies 56 screen rows; track labels, patterns and values are live C-rendered elements.
