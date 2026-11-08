/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
/* Tamborzao: the supplied Ableton two-bar pattern. 2026-11-04. */
#include "instrument.h"
#include "sampledrum.h"
#include "baile.h"
#include "baile_808.h"
#include <string.h>
const char *groove_factory_name(unsigned index) {
    return index < 4 ? baile_name(index) : 0;
}
int groove_factory_build(unsigned index, struct groove_project *p) {
    if (!p || index >= 4) return GROOVE_PROJECT_INVALID;
    memset(p,0,sizeof *p);
    memset(p->name,32,12); memcpy(p->name,baile_name(index),strlen(baile_name(index)));
    p->tempo=130; p->mute=254; p->effects[0]=80;p->effects[1]=134;p->effects[3]=100;
    groove_sequence_defaults(&p->sequence);
    groove_project_arp_defaults(p);
    for(unsigned t=0;t<GROOVE_TRACKS;++t) {
        struct groove_preset *v=&p->preset[t];
        v->type=!t ? (index ? GROOVE_808 : GROOVE_SAMPLE) : GROOVE_PSG;
        v->volume=100; v->modified=1; v->controls.envelope[2]=100;
        v->sequence_pages=2;
        if(v->type==GROOVE_SAMPLE) {
            v->sampler_pads=SAMPLE_DRUM_PADS;
            for(unsigned pad=0;pad<SAMPLE_DRUM_PADS;++pad) {
                uint8_t *pot=v->data+pad*SAMPLE_DRUM_PARAMS;
                for(unsigned i=0;i<SAMPLE_DRUM_PARAMS;++i)pot[i]=sampledrum_param(i)->def;
                pot[SAMPLE_DRUM_LEVEL]=100;
                pot[SAMPLE_DRUM_VARIATION]=pot[SAMPLE_DRUM_VELOCITY_LPF]=pot[SAMPLE_DRUM_CHOKE]=0;
            }
        } else if(v->type==GROOVE_808) {memcpy(v->data,baile_808,209);}
        else {v->data[0]=0;v->data[1]=16;v->data[2]=24;v->data[3]=38;}
    }
    if(!index) {
        p->step[0][0].drums=3;p->step[0][0].velocity=100;
        p->step[0][3].drums=4;p->step[0][3].velocity=100;
        p->step[0][4].drums=2;p->step[0][4].velocity=100;
        p->step[0][6].drums=5;p->step[0][6].velocity=100;
        p->step[0][8].drums=2;p->step[0][8].velocity=100;
        p->step[0][10].drums=1;p->step[0][10].velocity=100;
        p->step[0][12].drums=10;p->step[0][12].velocity=100;
        p->step[0][14].drums=8;p->step[0][14].velocity=100;
        p->step[0][16].drums=3;p->step[0][16].velocity=100;
        p->step[0][19].drums=4;p->step[0][19].velocity=100;
        p->step[0][20].drums=2;p->step[0][20].velocity=100;
        p->step[0][22].drums=5;p->step[0][22].velocity=100;
        p->step[0][24].drums=2;p->step[0][24].velocity=100;
        p->step[0][26].drums=1;p->step[0][26].velocity=100;
        p->step[0][28].drums=10;p->step[0][28].velocity=100;
        p->step[0][30].drums=8;p->step[0][30].velocity=100;
    }
    if(index) {
        /* Provisional original sketches for interface evaluation, not transcriptions. */
        static const uint8_t pads[3][4]={{0,1,7,10},{0,1,2,7},{0,6,5,10}};
        static const uint32_t patterns[3][4]={
          {0x05010501U,0x10101010U,0x82488248U,0x55555555U},
          {0x04210421U,0x10101010U,0x48824882U,0x02080208U},
          {0x41414141U,0x10101010U,0x08040804U,0x44444444U}};
        for(unsigned part=0;part<4;++part)for(unsigned step=0;step<32;++step)
            if((patterns[index-1][part]>>step)&1U){p->step[0][step].drums|=1U<<pads[index-1][part];p->step[0][step].velocity=100;}
    }
    return groove_project_valid(p) ? 0 : GROOVE_PROJECT_INVALID;
}
