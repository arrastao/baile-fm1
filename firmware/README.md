# BAILE 0.6 firmware

`BAILE-0.6-MAC.fwsc` contains the app, all three sample banks, patterns and art. No separate asset import is needed. The splash stays visible for three seconds after rendering, and all kits use one 16-step bar.

Built on macOS via JieLi Linux + Blink, preserving the SDK boot and loader. Native emulator playback and SDK package verification passed. Installation/verification by M-UPGRADE and physical FM-1 behavior remain untested for this build. The original long identity format is retained, as in Tamborzão 0.1. Check SHA256SUMS.txt before comparing copies.

Do not confuse `sdk/firmware/FM-1_015.fwsc` (the upstream vendor resource) with BAILE.
