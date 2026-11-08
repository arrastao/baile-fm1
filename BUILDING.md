# Building BAILE

[Home](README.md) · [Status](STATUS.md) · [Licensing](LICENSING.md)

All commands run from the repository root. The build scripts compile files locally; they never send MIDI, flash an FM-1, install packages or download toolchains automatically. Generated files go to `build/`, which is ignored by Git.

## Portable host instrument

Requires Python 3 and a C11 clang compiler on macOS or Linux. On Windows use a Linux environment such as WSL; that route has not been locally validated here.

```sh
python3 tests/check_repository.py
python3 build.py host
```

Then run the appropriate library:

```sh
# macOS
python3 tests/test_instrument.py build/host/baile.dylib
# Linux
python3 tests/test_instrument.py build/host/baile.so
```

`build/host/verification.json` records the test output. These tests cover the portable instrument, not board I/O. `tests/host_optional.c` supplies no-op optional panel callbacks in that target only. The GitHub workflow runs repository checks and the Linux host tests; a workflow file alone does not establish that CI has passed remotely.

## Browser preview

Requires [WASI SDK 27](https://github.com/WebAssembly/wasi-sdk/releases/tag/wasi-sdk-27). Use its distribution for your host architecture; the original local build used macOS ARM64.

```sh
python3 build.py web --wasi-sdk /path/to/wasi-sdk-27
python3 -m http.server 8767 --bind 127.0.0.1 --directory build
```

Open `http://127.0.0.1:8767/preview/`. Press Tocar to enable audio. `WASI_SDK_PATH` may replace the command option. Serving `preview/` from the source tree alone is insufficient: `baile.wasm` is generated in `build/preview/` and artwork is copied to `build/assets/art/`.

The web target builds portable C from `app/`, `web/` and `third_party/synth/`, excluding the hardware board sources. It uses no native `.fwsc` and is not a device updater.

## Native firmware — experimental

Requires a matching **JieLi Linux PI32v2 toolchain**, clang 4.0.1/r3. The recorded build used `jieli-linux-toolchains-20260730.1`; the compiler hash is in [docs/evidence/build-report.json](docs/evidence/build-report.json). The original vendor Windows build files are kept inside `sdk/` for provenance, but their fixed layout is not the BAILE 0.3 layout. Do not use `sdk/Build.ps1` as a replacement for this entry point.

On a compatible Linux host:

```sh
python3 build.py firmware --toolchain /path/to/jieli-linux-toolchains-20260730.1
```

The toolchain directory may contain `pi32v2/bin/clang` or `bin/clang`. Native Linux execution depends on its runtime libraries; this route is not automatically provisioned by this repository.

On macOS ARM64 the recorded approach ran the Linux x86-64 tools through [Blink](https://github.com/jart/blink) with a Linux library overlay:

```sh
python3 build.py firmware \
  --toolchain /path/to/jieli-linux-toolchains-20260730.1 \
  --runner '/path/to/blink -m -j' \
  --linux-root /path/to/linux-root
```

The overlay must contain the shared libraries required by that Linux toolchain in `lib/x86_64-linux-gnu` and `usr/lib/x86_64-linux-gnu`. No Rosetta is used. Blink, the toolchain and the overlay are external prerequisites and are not bundled in this repository. Environment equivalents: `FM1_TOOLCHAIN`, `FM1_TOOLCHAIN_RUNNER`, `FM1_LINUX_ROOT`.

The script verifies the bundled SDK manifest before compiling, uses PI32v2 r3 flags, retains the registration and BLE symbols required by the SDK, then runs `tests/check_link.py`. That check covers the entry address, heap, required SDK symbols, registration tables and SRAM placement of audio/panel callbacks.

Outputs:

- `build/dx7/sdk.elf` and `build/dx7/sdk.map`.
- `build/dx7/generated/build-report.json` and `structural-checks.json`.
- `build/BAILE-0.3-web-experimental.fwsc`: long outer identity, kept for development; not a validated web installer.
- `build/BAILE-0.3-MUPGRADE-experimental.fwsc`: three-digit outer identity `FM-1_803`, accepted by the tested M-UPGRADE file parser. Acceptance is not a successful device installation.

The application reports `FM-1_8490133`; its build hash distinguishes the code. The outer wrapper identifies the M-UPGRADE package separately. Do not confuse these identities with official M-VAVE release numbers.

### Layout and optional V16 boot input

The default package preserves the bundled original V15 boot area. An optional `--boot-stock /path/to/FM-1.fwsc` input accepts only the exact official V16 hash `d017fb65e70aca97ee29d944470c3515a74581df5c0576bf70de917c7b2b61d5`. Obtain that file from [M-VAVE](https://www.m-vave.com/download); it is not bundled here.

```sh
python3 build.py firmware --toolchain /path/to/toolchain --boot-stock /path/to/FM-1.fwsc
```

This input selects a boot area, not a proven compatibility fix. Both V15 and V16 variants were refused during the recorded Tessera migration test. Do not try variants blindly or disable comparisons.

The image extent is `0x93000`; VM is 32,768 bytes at `0x93000`; BTIF is 4,096 bytes at `0x9B000`; USER is 405,504 bytes at `0x9C000`, ending at `0xFF000`. The application's `fm1_layout` descriptor and sample-region constants match this reservation. This is a different layout from the base and earlier BAILE experiments and can invalidate existing saved data.

### Why upstream files remain

The SDK files and their manifest are unchanged. `docs/upstream/` contains the original FM1 Open README files as historical material; their instructions describe that upstream version, not a supported BAILE workflow. `tools/pack.py` and `tools/build_firmware.py` implement the BAILE-specific layout and package generation.

## Artwork and samples

Original supplied mockups and their title crops are in `assets/art/`. Compact LCD art is in `app/baile_art.h`. The application embeds the Tamborzão bank in `app/baile_bank.h`; `assets/audio/tamborzao.fm1s` is the same bank used for regression checks. Neither asset file needs to be loaded separately onto a device for this instrument design.

Rebuilding the instrument does not regenerate the supplied art or re-extract the Ableton project. Asset licensing is described in [LICENSING.md](LICENSING.md).
