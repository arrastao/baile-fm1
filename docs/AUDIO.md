# Audio normalization (0.7)

Run `python3 tools/normalize_audio.py` before `python3 tools/assets.py` to regenerate normalized banks from the unchanged source WAVs. The helper compiles the pinned SEA encoder/decoder locally with clang; it is not linked into the firmware.

Each sample receives constant gain toward -16 dBFS RMS in its strongest 50 ms window. Peak ceiling: -3 dBFS. Maximum boost: 18 dB. The script decodes the encoded output, checks peaks, and reduces gain if the codec overshoots. No compression, EQ, trimming or duration change is applied. This energy measurement is a repeatable level reference, not an exact perceptual-loudness measure. Peak-limited transients may remain below the RMS target.

Original WAVs remain unchanged. Original banks are stored in assets/audio/original-banks; prepared WAVs in assets/audio/normalized. Normalization metadata records input hashes, gain and measurements before and after decoding. Active .fm1s banks and generated C arrays contain the normalized sound.

`tests/audio_levels.py` checks the rendered factory beats, a stress pattern with all four parts on every step, and original WAV hashes. Hardware listening and artistic balance remain for the musician to assess.
