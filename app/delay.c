/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
/* BAILE delay: BPM-synced 1/4 note, feedback 50%, 250 Hz-4 kHz band filter
 * (centre 1 kHz, wide), repitch smoothing, no ping-pong, no modulation.
 *
 * One mono int16 line at 11.025 kHz (44.1 kHz / 4) shared by both channels:
 * 32 KiB of RAM for any tempo down to ~40 BPM (slower tempos use 1/8 note).
 * The reverb is not used: BAILE keeps every reverb send at zero.
 * Audio ISR only; control publishes baile_delay_mix and baile_delay_length. */
#include "baile.h"
#include "fm1_engine_control.h"

enum { LINE = 16384, MASK = LINE - 1, DECIM = 4, STEPS = FM1_BLOCK_FRAMES / DECIM,
       Q = 8, SLEW = 1 << 6 /* delay-time change per sample, Q8: repitch ~1.5% */ };
static int16_t line[LINE];
static unsigned write_at;
static int32_t length_now, hp_x, hp_y, lp_y, gain_dry = 32768, gain_wet, previous_wet;

/* Control side: samples of a 1/4 note at 11.025 kHz, Q8. 1/8 below ~40 BPM. */
unsigned baile_delay_quarter(unsigned bpm) {
    if (bpm < 30) bpm = 30;
    if (bpm > 300) bpm = 300;
    unsigned length = (11025U * 60U * 256U) / bpm;
    if (length > (LINE - 8U) * 256U) length /= 2U;
    return length;
}
void baile_delay_reset(void) {
    for (unsigned i = 0; i < LINE; ++i) line[i] = 0;
    write_at = 0; hp_x = hp_y = lp_y = previous_wet = 0;
    gain_dry = 32768; gain_wet = 0;
    length_now = 0; /* adopt the first published length without a glide */
}
static inline int32_t clip24(int32_t v) { return v > 8388607 ? 8388607 : v < -8388607 ? -8388607 : v; }
static inline int32_t approach(int32_t now, int32_t target, int32_t step) {
    int32_t d = target - now;
    return d > step ? now + step : d < -step ? now - step : target;
}
FM1_AUDIO_CODE void baile_delay(int32_t *pcm) {
    unsigned mix = baile_delay_mix;
    int32_t target_length = (int32_t)baile_delay_length;
    /* Ableton-style Dry/Wet: dry stays unity to 50%, wet reaches unity at 50%. */
    int32_t want_dry = mix <= 50 ? 32768 : (int32_t)((100U - mix) * 32768U / 50U);
    int32_t want_wet = mix >= 50 ? 32768 : (int32_t)(mix * 32768U / 50U);
    if (target_length < 2 * 256) target_length = 2 * 256;
    if (!length_now) length_now = target_length;
    for (unsigned i = 0; i < STEPS; ++i) {
        int32_t *f = pcm + i * DECIM * 2;
        int32_t input = (f[0]+f[1]+f[2]+f[3]+f[4]+f[5]+f[6]+f[7]) >> 3;
        /* Repitch: the read point glides, so tempo changes bend the echo. */
        length_now = approach(length_now, target_length, SLEW);
        int32_t read = ((int32_t)write_at << Q) - length_now;
        unsigned at = (unsigned)(read >> Q) & MASK, frac = (unsigned)read & 255U;
        int32_t a = (int32_t)line[at] * 256, b = (int32_t)line[(at + 1U) & MASK] * 256;
        int32_t wet = a + (int32_t)(((int64_t)(b - a) * (int32_t)frac) >> Q);
        /* Feedback 50%, then band limit: 250 Hz high-pass, 4 kHz low-pass. */
        int32_t x = clip24(input + (wet >> 1));
        hp_y = (int32_t)(((int64_t)(hp_y + x - hp_x) * 28418) >> 15); hp_x = x;
        lp_y += (int32_t)(((int64_t)(hp_y - lp_y) * 29409) >> 15);
        int32_t stored = clip24(lp_y) >> 8;
        line[write_at] = (int16_t)stored;
        write_at = (write_at + 1U) & MASK;
        gain_dry = approach(gain_dry, want_dry, 256);
        gain_wet = approach(gain_wet, want_wet, 256);
        for (unsigned j = 0; j < DECIM; ++j) {
            int32_t w = previous_wet + (int32_t)(((int64_t)(wet - previous_wet) * (int32_t)(j + 1U)) >> 2);
            for (unsigned c = 0; c < 2; ++c) {
                int32_t *s = f + j * 2 + c;
                *s = clip24((int32_t)(((int64_t)*s * gain_dry + (int64_t)w * gain_wet) >> 15));
            }
        }
        previous_wet = wet;
    }
}
