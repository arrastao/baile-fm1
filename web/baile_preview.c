/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
#include "baile.h"
#ifdef __wasm__
#define EXPORTED(name) __attribute__((export_name(name)))
#else
#define EXPORTED(name)
#endif
EXPORTED("baile_inspect") const uint32_t *baile_inspect(void) {
    static uint32_t values[16];
    for(unsigned i=0;i<9;++i)values[i]=baile_state(i);
    values[15]=baile_state(9);
    for(unsigned i=0;i<4;++i)values[i+9]=(uint32_t)groove_drum_steps(0,i);
    struct groove_view v;groove_get_view(0,0,&v);values[13]=v.playing;values[14]=v.play_step;
    return values;
}
