# Building BAILE

No command below installs firmware on a device.

## Portable application tests (macOS)

```sh
python3 tools/assets.py
python3 tools/preview.py host
python3 tests/acceptance.py
python3 tools/preview.py web --wasi-sdk /path/to/wasi-sdk-27.0-arm64-macos
python3 -m http.server 8879 --bind 127.0.0.1 --directory build/web
```

Acceptance screenshot generation needs Pillow. The C compiler and WASI SDK 27 are build-time requirements, not runtime downloads for the instrument. Open `http://127.0.0.1:8879/BAILE.html`. It runs the rebuilt C engine and embeds all WebAssembly bytes. Audio starts on the first PLAY gesture; subsequent operations are owned by one AudioWorklet.

## Firmware on macOS (verified build route)

```sh
python3 tools/build_macos.py
node tests/package.mjs
```

Uses the existing sibling JieLi Linux 20260730.1 toolchain, Blink and Linux runtime. This is the same build route as Tamborzão 0.1. It recompiles all application units, validates SDK hashes and native layout, then packages `build/BAILE-0.7-FM1.fwsc`. The Python port of the SDK packager reproduces the earlier user-confirmed Tamborzão package byte for byte; BAILE selects its explicit 405504-byte user partition. No stock boot replacement or container-identity rewrite is applied.

## Native Windows build (alternative; pending execution)

Install the [official JieLi 2.5.3 toolchain](https://jl-update.oss-cn-shenzhen.aliyuncs.com/2.5.3.exe). The pinned upstream requires the `pi32` directory and verifies 22 exact toolchain hashes, including `bin/clang.exe` = `d4bc97cf421c1ccc373dd8924ce88720ff7457b3f1478d15df4aeda6ae923bce`.

Run in a fresh Windows PowerShell process:

```powershell
./tools/Build-Baile.ps1 -Toolchain 'C:\JL\pi32'
```

This derives the build script and C# packager in `build/baile-tools`, leaving the SDK manifest and every SDK file intact. It retains the official compiler checks, DSP checks, link checks and boot resources. It changes the documented user allocation, retains required BLE APIs despite the smaller UI, and names the local candidate `build/dx7/generated/BAILE-0.7-dev.fwsc`.

Do not run upstream `build.bat` directly for BAILE: it uses the original storage allocation. Do not distribute a binary without its matching complete source and license notices. The wrapper's Windows execution and output remain unverified on this Mac.

## Local native diagnostic

`tools/native_probe.py` uses the pre-existing sibling JieLi Linux toolchain and Blink environment to generate an ELF, application bytes and a size report. `tests/native_layout.py` inspects its SDK hashes, native entry, registrations, SRAM callbacks and available heap. This lower-level command generates ELF/application bytes. `tools/build_macos.py` wraps it with checks and FWSC packaging.

A diagnostic success, host/WASM success or an emulator screen is not proof of M-UPGRADE or real-device compatibility. The remaining physical milestone is installation on the FM-1, followed by cold boot, audio, encoder and kit-change checks.
