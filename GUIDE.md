# BAILE guide — development snapshot 0.3

[Home](README.md) · [Português](README.pt-BR.md) · [Status](STATUS.md)

This guide describes implemented controls, verified in the portable instrument and/or native firmware emulation. It is not a verified physical installation guide.

## Start

BAILE shows the supplied startup portrait, then selects Tamborzão. A control gesture can skip the 2.4-second opening. The default pattern has 32 steps, two bars at 130 BPM. Press PLAY to start; in the browser press Tocar to allow audio.

Only one kit is active. Each kit is implemented as the active drum source on engine track 0; the other underlying engine tracks are muted. The four rows are drum parts, not four independently selected engine tracks.

## Choose a kit

Turn PRESETS to cycle Tamborzão → Voltmix → Beat Bolha → Mandelão. While stopped the change is immediate. While playing it is queued for a bar change. The newest queued selection replaces the previous one. Selecting the current kit cancels the pending selection.

BPM, swing, saturator and reverb stay across kit changes. Edits to a kit's pattern remain in RAM during the session. Stop with a change pending to apply it immediately.

The browser's pre-render adapter and the board's polling path have different timing: the physical SDK's first hit at the change may still use the previous kit. Hardware timing remains unverified.

## Choose a part

Turn ALGORITHM to select one of the kit's four drum parts. The highlight and step grid follow that selection. The part names differ across kits; the supplied visual mockups do not override the actual audio mapping.

| Kit | Part 1 | Part 2 | Part 3 | Part 4 |
| --- | --- | --- | --- | --- |
| Tamborzão | Bumbo | Ataque | Conga slap | Conga grave |
| Voltmix | Bumbo | Caixa | Cowbell | Chimbal |
| Beat Bolha | Bumbo | Caixa | Tom bolha | Cowbell |
| Mandelão | Bumbo | Palma | Aro | Chimbal |

## Edit steps

The sixteen white keys toggle one bar of the selected part. OCT − shows steps 1–16; OCT + shows 17–32. SELECT and SEQ also change this page. Editing one part leaves the others' steps as they are. There is no user-facing per-step velocity or micro-timing editor in this snapshot.

## Shape the sound

- K1: Saturator, 0–100.
- K2: reverb send, 0–15 internally. The web interface displays 0–100%.
- K3: BPM. The current browser range is 40–240; this is not a claim about every underlying SDK control.
- K4: swing, 0–50 in the current browser interface.

The saturator uses an integer cubic drive curve. The board processing cost has not been measured on the device. Reverb is the base engine's reverb path.

## Browser equivalents

Use PRESETS buttons or Up/Down for a kit, track buttons or Left/Right for a part, 1–16 / 17–32 for the page and the sixteen step buttons to edit. Space or Tocar starts/stops. Shortcuts defer to focused inputs and buttons.

Audio is rendered in an AudioWorklet from the portable C/WASM engine. The LCD canvas uses the C screen renderer. This preview is not the native firmware CPU emulator and cannot validate the updater, the board driver or physical performance.

## What is saved

Session edits exist only in RAM. Reloading, power cycling or restarting returns all four kits to their factory patterns. There is no BAILE project export/import or persistent-save UI in this version. The underlying SDK's project and sample facilities should not be confused with a finished BAILE save workflow.

## What the kits contain

Tamborzão uses the four samples and two-bar pattern supplied in the Ableton project. The bank is embedded in the application and chosen on boot, even if writable sample storage is blank or contains unrelated data. Ableton master effects are not included.

The other three kits use 808 synthesis and provisional patterns. They exist to exercise kit selection and editing; do not describe them as definitive recreations of those styles.

## Before testing on a device

Read [STATUS.md](STATUS.md). Installation from the tested Tessera 3.2.2 device was not completed. Back up the installed firmware's projects and sounds using its own supported tool. A successful browser preview, a clean build or an enabled Update button does not establish a safe migration path.
