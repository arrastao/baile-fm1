/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
/* BAILE factory data; engine, sequencer and sample codec remain upstream. */
#include "baile.h"
#include "sampledrum.h"
#include <string.h>
#include "baile_assets.inc"
const uint8_t *baile_bank(unsigned kit, unsigned *bytes) {
    if (kit >= 3) return NULL;
    *bytes = bank_sizes[kit]; return banks[kit];
}
const char *baile_name(unsigned kit) {
    static const char *const names[] = {"TAMBORZAO", "VOLTMIX", "BEAT BOLHA"};
    return kit < 3 ? names[kit] : "";
}
const char *groove_factory_name(unsigned kit) { return kit < 3 ? baile_name(kit) : NULL; }
int groove_factory_build(unsigned kit, struct groove_project *p) {
    if (!p || kit >= 3) return GROOVE_PROJECT_INVALID;
    memset(p, 0, sizeof *p);
    memset(p->name, ' ', sizeof p->name);
    memcpy(p->name, baile_name(kit), strlen(baile_name(kit)));
    p->tempo = 130; p->mute = 254;
    p->effects[0] = 64; p->effects[1] = 134; p->effects[2] = 48; p->effects[3] = 100;
    groove_sequence_defaults(&p->sequence);
    groove_project_arp_defaults(p);
    for (unsigned t = 0; t < GROOVE_TRACKS; ++t) {
        struct groove_preset *v = &p->preset[t];
        v->type = t ? GROOVE_PSG : GROOVE_SAMPLE;
        v->volume = 100; v->modified = 1; v->controls.envelope[2] = 100;
        v->sequence_pages = 1;
        if (!t) {
            v->sampler_pads = SAMPLE_DRUM_PADS;
            for (unsigned pad = 0; pad < SAMPLE_DRUM_PADS; ++pad) {
                uint8_t *pot = v->data + pad * SAMPLE_DRUM_PARAMS;
                for (unsigned n = 0; n < SAMPLE_DRUM_PARAMS; ++n) pot[n] = sampledrum_param(n)->def;
                pot[SAMPLE_DRUM_VARIATION] = pot[SAMPLE_DRUM_VELOCITY_LPF] = pot[SAMPLE_DRUM_CHOKE] = 0;
            }
        } else { v->data[1] = 16; v->data[2] = 24; v->data[3] = 38; }
    }
    for (unsigned part = 0; part < 4; ++part)
        for (unsigned step = 0; step < 16; ++step)
            if ((factory_steps[kit][part] >> step) & 1U) {
                p->step[0][step].drums |= 1U << part;
                p->step[0][step].velocity = 100;
            }
    return groove_project_valid(p) ? 0 : GROOVE_PROJECT_INVALID;
}
