# BAILE 0.7 stable firmware

`BAILE-0.7-FM1.fwsc` contains the app, all three sample banks, patterns and art. No separate asset import is needed. Version 0.7 embeds normalized sample banks with unchanged source WAVs preserved in the repository. The splash stays visible for three seconds after rendering, and all kits use one 16-step bar.

Built on macOS via JieLi Linux + Blink, preserving the SDK boot and loader. Native emulator playback and SDK package verification passed. The user confirmed successful operation of this build on their physical FM-1 on 2026-11-09. It is promoted to stable with the tested bytes unchanged. The original long identity format is retained, as in Tamborzão 0.1. Check SHA256SUMS.txt before comparing copies.

Do not confuse `sdk/firmware/FM-1_015.fwsc` (the upstream vendor resource) with BAILE.
