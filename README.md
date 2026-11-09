# BAILE by MULÚ

BAILE is a three-kit rhythm instrument for the M-VAVE FM-1: **Tamborzão**, **Voltmix** and **Beat Bolha**. It starts with Tamborzão, displays four sound parts, and lets the player edit a one-bar pattern with the white keys.

This is a reconstruction on [FM1 Open](https://github.com/m-vave/fm1_open), pinned to [`4c7496d`](https://github.com/m-vave/fm1_open/commit/4c7496daac04a95ff10d1afdcc8f9ead2dbabc41). 

**0.7 change:** the 12 samples use a common attack-energy reference with peak headroom; originals are preserved. See [audio preparation](docs/AUDIO.md).


**Status: stable (0.7).** Promoted after the user reported successful operation on their FM-1. The firmware bytes are unchanged from the tested build. Container integrity, original boot, embedded banks and native emulator playback were also verified. See [STATUS](STATUS.md).

[Download BAILE 0.7 firmware](firmware/BAILE-0.7-FM1.fwsc) · [SHA-256](firmware/SHA256SUMS.txt)

[Português](README.pt-BR.md) · [Build](docs/BUILDING.md) · [Architecture](docs/ARCHITECTURE.md) · [Asset rights](assets/README.md)

## Controls

| Control | Function |
|---|---|
| PRESETS | Tamborzão / Voltmix / Beat Bolha |
| ALGORITHM | Select one of the four sound parts |
| 16 white keys | Toggle the selected part's steps in the visible bar |
| OCT −/+ | Unused (single bar) |
| PLAY | Start / stop |
| K1 | Saturator |
| K2 | Reverb |
| K3 | Tempo |
| K4 | Swing |

One kit plays at a time. Stopped preset changes are immediate; playing changes are queued to the next bar observed by the control task. Changes are retained separately for each kit during the current session. Reboot restores the factory Tamborzão pattern. Mandelão is excluded.

## Assets and firmware

The application embeds all 12 samples, source-derived patterns, boot art and three title images. It does not require a sample download or import after installation. Banks are read-only in this MVP; editing changes patterns in RAM.

The SDK's original 524 KiB user partition leaves insufficient application space for these embedded assets. BAILE explicitly reserves 396 KiB for user storage, retaining the original boot resources and at least 32 KiB for VM. This partition change is documented and **not yet validated for migration from other firmware**.

The SDK files, engine library, board drivers and portable DSP/sequence engine remain pinned and unmodified. `tools/Build-Baile.ps1` derives a build driver and packager from the checked official sources, adapting only the storage size, package name and retained API symbols. It preserves compiler/SDK hash checks and does not flash a device.

## Preview

Build with `python3 tools/preview.py web --wasi-sdk /path/to/wasi-sdk-27`, serve `build/web` locally and open `BAILE.html`. The preview includes its WebAssembly bytes and uses the same C application. It is not a hardware emulator or a flashable firmware file.

## License

Application code follows [GPLv3 with the inherited linking exception](LICENSE.md). The binary SDK retains its original terms and [third-party notices](THIRD_PARTY.md). User-supplied audio and artwork have separate rights; see [assets/README.md](assets/README.md).
