/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
#include "baile.h"
#include "fm1_engine_control.h"
#include <string.h>
static struct groove_project sessions[4];
static unsigned valid[4], current, selected, edit_page, previous_step, initialized;
static int queued, error;
unsigned baile_saturation;
static unsigned reverb;
static int clamp(int v,int lo,int hi) {return v<lo?lo:v>hi?hi:v;}
const char *baile_name(unsigned kit) {
    static const char *const names[]={"TAMBORZAO","VOLTMIX","BEAT BOLHA","MANDELAO"};
    return names[kit%4];
}
unsigned baile_pad(unsigned part) {
    static const uint8_t pads[4][4]={{0,1,2,3},{0,1,7,10},{0,1,2,7},{0,6,5,10}};
    return pads[current][part%4];
}
const char *baile_part(unsigned part) {
    static const char *const names[4][4]={{"BUMBO","ATAQUE","CONGA SLAP","CONGA GRAVE"},
    {"BUMBO","CAIXA","COWBELL","CHIMBAL"},{"BUMBO","CAIXA","TOM BOLHA","COWBELL"},
    {"BUMBO","PALMA","ARO","CHIMBAL"}};
    return names[current][part%4];
}
void baile_init(void) {
    memset(valid,0,sizeof valid);current=selected=edit_page=previous_step=initialized=0;
    baile_saturation=reverb=0;queued=-1;error=0;
}
static void sends(void) {
    uint8_t v[2];groove_sends_get(0,v);groove_sends_edit(0,0,(int)reverb-v[0]);
}
static int apply(unsigned kit) {
    struct groove_view v;groove_get_view(0,0,&v);
    groove_project_capture(&sessions[current]);valid[current]=1;
    if (!valid[kit]) {int r=groove_factory_build(kit,&sessions[kit]);if(r)return error=r;valid[kit]=1;}
    sessions[kit].tempo=v.tempo;
    sessions[kit].sequence.swing=(uint8_t)groove_sequence_setting(0);
    fm1_engine_pause();
    if(v.playing)groove_sequence_keep_transport(0);
    int r=groove_project_apply(&sessions[kit]);
    if(v.playing)groove_sequence_keep_transport(1);
    fm1_engine_resume();
    if(r)return error=r;
    current=kit;queued=-1;error=0;sends();groove_edit_forget_history();return 0;
}
int baile_choose(unsigned kit) {
    if(kit>=4)return -1;
    if(kit==current){queued=-1;return 0;}
    struct groove_view v;groove_get_view(0,0,&v);
    if(v.playing){queued=(int)kit;return 0;}
    return apply(kit);
}
void baile_poll(void) {
    struct groove_view v;groove_get_view(0,0,&v);
    if(!initialized){initialized=1;sends();}
    if(queued>=0 && (!v.playing || (v.play_step/16 != previous_step/16)))apply((unsigned)queued);
    previous_step=v.play_step;
}
void baile_page(unsigned page){edit_page=page>0;}
void baile_encoder(unsigned e,int delta) {
    if(!delta)return;
    if(e==6){int at=queued<0?(int)current:queued;baile_choose((unsigned)((at+delta%4+4)%4));}
    if(e==1)selected=(unsigned)((selected+delta%4+4)%4);
    if(e==0)edit_page=(unsigned)clamp((int)edit_page+delta,0,1);
    if(e==2)baile_saturation=(unsigned)clamp((int)baile_saturation+delta,0,100);
    if(e==3){reverb=(unsigned)clamp((int)reverb+delta,0,15);sends();}
    if(e==4)groove_tempo_edit(delta);
    if(e==5)groove_sequence_setting_edit(0,delta);
}
void baile_toggle(unsigned step) {
    if(step>=32)return;
    unsigned pad=baile_pad(selected);uint64_t mask=groove_drum_steps(0,pad);
    groove_sequence_edit(0,step,groove_pad_note(0,pad),(mask>>step)&1?0:100);
}
unsigned baile_value(unsigned i) {
    switch(i){case 0:return current;case 1:return (unsigned)(queued+1);case 2:return selected;
    case 3:return edit_page;case 4:return baile_saturation;case 5:return reverb;
    case 6:return groove_tempo_saved();case 7:return groove_sequence_setting(0);case 8:return (unsigned)error;
    default:return 0;}
}

/* The portable adapter invokes this on its sole owner thread before rendering,
 * so loading never allocates concurrently with the renderer. */
extern unsigned groove_baile_bar_due(void) __attribute__((weak));
void baile_before_render(void) {
    if(queued>=0 && groove_baile_bar_due && groove_baile_bar_due())apply((unsigned)queued);
}
