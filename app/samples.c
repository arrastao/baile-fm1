/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
/* Read-only embedded banks: no user-flash import, erase or startup dependency. */
#include "baile.h"
#include "sampledrum.h"
#include "fm1_engine_control.h"
#include <string.h>
extern const uint8_t *baile_bank(unsigned kit, unsigned *bytes);
static const uint8_t *active;
static unsigned total, ready;
static unsigned u32(const uint8_t *p) {
    return (unsigned)p[0] | (unsigned)p[1]<<8 | (unsigned)p[2]<<16 | (unsigned)p[3]<<24;
}
/* Caller holds the audio gate throughout project and bank replacement. */
int baile_bind(unsigned kit) {
    unsigned bytes = 0;
    const uint8_t *bank = baile_bank(kit, &bytes);
    if (!bank) return GROOVE_PROJECT_INVALID;
    groove_samples_stop();
    for (unsigned pad = 0; pad < SAMPLE_DRUM_PADS; ++pad) {
        const uint8_t *e = bank + 32 + pad * 28;
        unsigned offset = u32(e), frames = u32(e+4), size = u32(e+8);
        if (sampledrum_bind(pad, frames ? bank+offset : NULL, size, frames, (const char *)e+12))
            return GROOVE_PROJECT_INVALID;
    }
    active = bank; total = bytes; ready = 2;
    return 0;
}
void groove_samples_init(void) {
    ready = 0; fm1_engine_pause();
    if (baile_bind(0)) ready = 4;
    fm1_engine_resume();
}
void groove_samples_poll(void) {}
unsigned groove_samples_status(void) { return ready; }
unsigned groove_samples_size(void) { return ready == 2 ? total : 0; }
int groove_samples_read(unsigned offset, uint8_t *data, unsigned bytes) {
    if (ready != 2 || !data || offset > total || bytes > total-offset) return GROOVE_PROJECT_INVALID;
    memcpy(data, active+offset, bytes); return 0;
}
int groove_samples_begin(unsigned bytes) { (void)bytes; return GROOVE_PROJECT_INVALID; }
int groove_samples_write(unsigned offset, const uint8_t *data, unsigned bytes) {
    (void)offset; (void)data; (void)bytes; return GROOVE_PROJECT_INVALID;
}
int groove_samples_finish(void) { return GROOVE_PROJECT_INVALID; }
void groove_samples_cancel(void) {}
