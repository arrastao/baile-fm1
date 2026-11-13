/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
#include "baile.h"
#include "fm1_engine_control.h"
#include <string.h>
extern int baile_bind(unsigned kit);
static struct groove_project session[3];
static unsigned kit, part, page, last_step, delay_mix, valid[3];
static int pending, fault;
volatile unsigned baile_drive;
/* Published to the audio ISR: dry/wet 0..100 and 1/4-note length (see delay.c). */
volatile unsigned baile_delay_mix, baile_delay_length;
static int clamp(int n, int lo, int hi) { return n < lo ? lo : n > hi ? hi : n; }
const char *baile_part(unsigned p) {
    static const char *const names[3][4] = {
        {"BUMBO","ATAQUE","CONGA SLAP","CONGA GRAVE"},
        {"BUMBO","CAIXA","CHIMBAL","ARO"},
        {"BUMBO","CAIXA","BRILHANTE","RITMADA"}};
    return p < 4 ? names[kit][p] : "";
}
static int activate(unsigned next, int capture) {
    if (!valid[next]) {
        int r = groove_factory_build(next, &session[next]);
        if (r) return fault = r;
        valid[next] = 1;
    }
    fm1_engine_pause();
    struct groove_view v; groove_get_view(0, 0, &v);
    if (capture) {
        groove_project_capture(&session[kit]);
        session[next].tempo = v.tempo;
        session[next].sequence.swing = (uint8_t)groove_sequence_setting(0);
    }
    if (v.playing) groove_sequence_keep_transport(0);
    int r = groove_project_apply(&session[next]);
    if (!r) r = baile_bind(next);
    if (v.playing) groove_sequence_keep_transport(1);
    if (!r) { kit = next; pending = -1; groove_edit_forget_history(); }
    fm1_engine_resume();
    return fault = r;
}
void baile_start(void) {
    kit = part = page = last_step = baile_drive = 0;
    delay_mix = 0; baile_delay_mix = 0; baile_delay_length = baile_delay_quarter(130);
    pending = -1; fault = 0; memset(valid, 0, sizeof valid);
    (void)activate(0, 0);
}
int baile_select(unsigned next) {
    if (next >= 3) return GROOVE_PROJECT_INVALID;
    if (next == kit) { pending = -1; return 0; }
    struct groove_view v; groove_get_view(0, 0, &v);
    if (v.playing) { pending = (int)next; return 0; }
    return activate(next, 1);
}
void baile_poll(void) {
    struct groove_view v; groove_get_view(0, 0, &v);
    unsigned step = v.play_step;
    unsigned bpm = groove_tempo_current();
    if (!bpm) bpm = groove_tempo_saved();
    baile_delay_length = baile_delay_quarter(bpm);
    if (pending >= 0 && (!v.playing || step < last_step)) (void)activate((unsigned)pending, 1);
    last_step = step;
}
void baile_page(unsigned value) { (void)value; page = 0; }
void baile_encoder(unsigned e, int delta) {
    if (!delta) return;
    switch (e) {
    case 0: /* SELECT: level of the selected part */
        groove_tone_edit(0, part, 0, delta * 4); break;
    case 1: part = (unsigned)((int)part+delta%4+4)%4; break;
    case 2: baile_drive = (unsigned)clamp((int)baile_drive+delta,0,100); break;
    case 3: delay_mix = (unsigned)clamp((int)delay_mix+delta*5,0,100); baile_delay_mix = delay_mix; break;
    case 4: groove_tempo_edit(delta); break;
    case 5: groove_sequence_setting_edit(0,delta); break;
    case 6: (void)baile_select((unsigned)((pending < 0 ? (int)kit : pending)+delta%3+3)%3); break;
    }
}
void baile_step(unsigned step) {
    if (step >= 16) return;
    uint64_t mask = groove_drum_steps(0,part);
    groove_sequence_edit(0,step,groove_pad_note(0,part),(mask>>step)&1U ? 0 : 100);
}
unsigned baile_state(unsigned field) {
    switch (field) {
    case 0:return kit; case 1:return (unsigned)(pending+1); case 2:return part;
    case 3:return page; case 4:return baile_drive; case 5:return delay_mix;
    case 6:return groove_tempo_saved(); case 7:return groove_sequence_setting(0);
    case 8:return (unsigned)fault;
    case 9: { uint8_t v[GROOVE_TONE_PARAMS] = {0}; return groove_tone_copy(0, part, v) >= 0 ? v[0] : 0; }
    default:return 0;
    }
}
/* Bounded integer soft clip before the upstream master/USB/Bluetooth mixer.
 * Audio ISR and all callees reside in SRAM; zero drive is exact bypass. */
FM1_AUDIO_CODE void baile_saturate(int32_t *pcm) {
    unsigned amount = baile_drive;
    if (!amount) return;
    for (unsigned i = 0; i < FM1_BLOCK_WORDS; ++i) {
        int32_t x = pcm[i];
        int64_t driven = (int64_t)x * (128U + amount * 8U) >> 7;
        if (driven > 8388607) driven = 8388607;
        if (driven < -8388607) driven = -8388607;
        int32_t v = (int32_t)driven;
        int64_t cube = ((((int64_t)v*v)>>23)*v)>>23;
        pcm[i] = (int32_t)(v - (cube >> 2));
    }
}
