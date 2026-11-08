# Development history

These are development milestones, not claims of stable hardware releases.

## 0.3 — unreleased

- Documented native builds, the application entry/link checks and a fixed migration image extent.
- Changed USER to 405,504 bytes with matching application descriptor, VM and BTIF regions.
- Tested V15/V16 boot-area variants against the local emulator and a simulated migration core.
- Physical migration still refused at the boot-area verification stage; Tessera 3.2.2 remained responsive.
- Prepared the public source repository, Portuguese/English documentation and portable regression workflow.

## 0.2 — development

- Embedded the full 65,036-byte Tamborzão bank in the application. No separate `.fm1s` transfer is required by the instrument design.
- Verified portable operation with empty and unrelated writable sample storage.
- Generated a self-contained native package. Native emulator execution required ALNK RX and mixer-instruction corrections in a separate emulator copy.
- Re-encoded the outer M-UPGRADE version as three digits to fix file-selection rejection. Physical verification still timed out.

## 0.1 — laboratory prototype

- Introduced BAILE's four-kit selection and per-session pattern memory.
- Kept Tamborzão as the default, with 130 BPM, two bars and four supplied samples.
- Added provisional Voltmix, Beat Bolha and Mandelão patterns with 808 synthesis.
- Added the supplied startup and kit artwork, Saturator and Reverb controls, and the portable browser preview.
