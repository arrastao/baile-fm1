/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
/* BAILE panel rebuilt on the official control and nonblocking LCD APIs. */
#include "baile.h"
#include "fm1_engine_control.h"
#include <string.h>

#include "baile_font.inc"
#include "baile_art.h"
static const uint8_t white[16] = {0,2,4,6,7,9,11,12,14,16,18,19,21,23,24,26};
static uint16_t pixels[FM1_SCREEN_WIDTH*16];
static uint32_t hashes[15], old_keys, old_buttons, started, frame_at;
static unsigned band, top, splash, dirty, frame_active, initialized;
static struct { unsigned kit, selected, page, sat, rev, swing, pending, error, splash;
    struct groove_view transport; uint32_t steps[4]; } frame;
static void fill(unsigned x,unsigned y,unsigned w,unsigned h,uint16_t color) {
    if(x>=240 || y>=240)return;
    unsigned bottom=y+h<top+16?y+h:top+16, right=x+w<240?x+w:240;
    if(y<top)y=top;
    for(unsigned row=y;row<bottom;++row)
        for(unsigned col=x;col<right;++col)pixels[(row-top)*240+col]=color;
}
static void text(unsigned x,unsigned y,const char *s,uint16_t color) {
    if(y>=top+16 || y+7<=top)return;
    for(;*s && x+5<=240;++s,x+=6){
        const uint8_t *g=0;
        char c=*s;
        if(c>='0'&&c<='9')g=font[c-'0'];
        else if(c>='A'&&c<='Z')g=font[10+c-'A'];
        static const uint8_t slash[]={96,24,6,1,0},minus[]={8,8,8,8,8},plus[]={8,8,62,8,8},arrow[]={65,34,20,8,0};
        if(c=='/')g=slash;if(c=='-')g=minus;if(c=='+')g=plus;if(c=='>')g=arrow;
        if(g)for(unsigned col=0;col<5;++col)for(unsigned row=0;row<7;++row)
            if(g[col]&(1U<<row))fill(x+col,y+row,1,1,color);
    }
}
static void art(const uint8_t *r,unsigned bytes,const uint16_t *pal,unsigned height,unsigned destination) {
    unsigned at=0;
    for(unsigned n=0;n<bytes;++n){
        unsigned count=(r[n]>>5)+1;
        for(unsigned i=0;i<count;++i,++at){
            unsigned sy=at/160,sx=at%160,y=sy*destination/height,end=(sy+1)*destination/height;
            if(y>=top+16)return;
            if(end>top)fill(sx*240/160,y,(sx+1)*240/160-sx*240/160,end-y,pal[r[n]&31]);
        }
    }
}
#define ART(n,h,d) art(art_##n,sizeof art_##n,art_##n##_palette,h,d)
static void number_label(char *out,const char *prefix,unsigned value,const char *suffix) {
    char digits[10];unsigned n=0;strcpy(out,prefix);unsigned at=(unsigned)strlen(out);
    do {digits[n++]=(char)('0'+value%10);value/=10;} while(value);
    while(n)out[at++]=digits[--n];out[at]=0;strcat(out,suffix);
}
static void draw_band(void) {
    static const uint16_t backgrounds[]={0xff00,0x601f,0x07ff};
    uint16_t bg=backgrounds[frame.kit];
    fill(0,top,240,16,bg);
    if(frame.splash){ART(boot,160,240);return;}
    if(top<56){if(frame.kit==0){ART(tamborzao,38,56);}else if(frame.kit==1){ART(voltmix,38,56);}else{ART(bolha,38,56);}}
    for(unsigned row=0;row<4;++row){
        unsigned y=65+row*24,selected=row==frame.selected;
        if(selected)fill(3,y-6,234,22,0);
        if(selected)text(6,y,">",0x07ff);
        text(18,y,baile_part(row),selected?0xffff:0);
        for(unsigned n=0;n<16;++n){
            unsigned step=frame.page*16+n;
            unsigned on=(frame.steps[row]>>step)&1U;
            fill(112+n*7,y,5,9,on?(selected?0x07ff:0xffbc):0x2124);
            if(frame.transport.playing&&frame.transport.play_step==step)fill(112+n*7,y+11,5,2,selected?0xffff:0);
        }
    }
    char s[40];
    number_label(s,"COMPASSO ",frame.page+1,"/2");text(6,161,s,0);
    text(99,161,frame.transport.playing?"TOCANDO":"PARADO",0);
    number_label(s,"",frame.transport.tempo," BPM");text(191,161,s,0);
    fill(6,179,70,19,0);fill(83,179,70,19,0);
    number_label(s,"SAT ",frame.sat,"");text(12,185,s,0x07ff);
    number_label(s,"REV ",frame.rev,"");text(89,185,s,0x07ff);
    number_label(s,"SWING ",frame.swing,"  OCT -/+ PAGINA");text(6,206,s,0);
    if(frame.error){text(6,226,"ERRO AO CARREGAR KIT",0);return;}
    if(frame.pending){strcpy(s,"PROX > ");strcat(s,baile_name(frame.pending-1));text(6,226,s,0);return;}
    fill(3,220,72,17,0x07ff);fill(77,220,48,17,0);fill(127,220,53,17,0);fill(182,220,55,17,0);
    text(8,225,"ALGORITHM",0);text(83,225,"TRILHA",0xffff);text(135,225,"TECLAS",0xffff);text(190,225,"PASSOS",0xffff);
}
static void snapshot(void) {
    frame.kit=baile_state(0);frame.pending=baile_state(1);frame.selected=baile_state(2);
    frame.page=baile_state(3);frame.sat=baile_state(4);frame.rev=baile_state(5);
    frame.swing=baile_state(7);frame.error=baile_state(8);frame.splash=splash;
    groove_get_view(0,0,&frame.transport);
    for(unsigned p=0;p<4;++p)frame.steps[p]=(uint32_t)groove_drum_steps(0,p);
}
static void paint(void) {
    if(fm1_screen_pending())return;
    if(!frame_active){
        if(!dirty && fm1_millis()-frame_at<40)return;
        snapshot();frame_active=1;band=0;dirty=0;frame_at=fm1_millis();
    }
    /* Submit at most one DMA band per poll. Never mutate a borrowed buffer. */
    while(band<15){
        top=band*16;draw_band();uint32_t hash=2166136261U;
        for(unsigned n=0;n<sizeof pixels/sizeof pixels[0];++n)hash=(hash^pixels[n])*16777619U;
        if(initialized && hashes[band]==hash){++band;continue;}
        if(fm1_screen_submit(0,top,240,16,pixels,240*16))return;
        hashes[band++]=hash;return;
    }
    initialized=1;frame_active=0;
}
void groove_screen_init(void) {
    old_keys=old_buttons=band=frame_active=initialized=0;dirty=splash=1;
    memset(hashes,0,sizeof hashes);started=frame_at=fm1_millis();
    fm1_controls_init();fm1_screen_init();
    for(unsigned i=0;i<41;++i)fm1_led_set(i,0);
    baile_start();paint();
}
void groove_screen_control(void) {
    struct fm1_controls c;fm1_controls_read(&c);
    uint32_t pressed=c.buttons&~old_buttons,keys=c.keys&~old_keys;
    unsigned moved=0;for(unsigned n=0;n<7;++n)moved|=c.encoders[n]!=0;
    if(splash&&(fm1_millis()-started>=1200||pressed||keys||moved)){splash=0;dirty=1;}
    groove_master_update(c.knob);
    for(unsigned n=0;n<7;++n)if(c.encoders[n]){baile_encoder(n,c.encoders[n]);dirty=1;}
    if(pressed&1)baile_page(0);if(pressed&2)baile_page(1);
    if(pressed&(1U<<12)){
        struct groove_view v;groove_get_view(0,0,&v);uint8_t command=v.playing?0xfc:0xfa;
        (void)fm1_midi_post(&command,1);
    }
    for(unsigned n=0;n<16;++n)if(keys&(1U<<white[n]))baile_step(baile_state(3)*16+n);
    if(pressed||keys)dirty=1;
    old_buttons=c.buttons;old_keys=c.keys;
    baile_poll();
    struct groove_view v;groove_get_view(0,0,&v);
    uint32_t mask=(uint32_t)groove_drum_steps(0,baile_state(2));
    for(unsigned n=0;n<16;++n)fm1_led_set(14+white[n],(mask>>(baile_state(3)*16+n))&1U);
    fm1_led_set(12,v.playing);fm1_led_set(0,baile_state(3)!=0);fm1_led_set(1,baile_state(3)==0);
    paint();
}
void groove_screen_mmc(unsigned command) {
    uint8_t status=command==1||command==9?0xfc:command==2||command==3?0xfb:0;
    if(status)(void)fm1_midi_post(&status,1);
}
void groove_screen_tap(uint32_t now){groove_tempo_tap(now);}
#ifdef FM1_HOST_TEST
int groove_screen_preset(unsigned slot){dirty=1;return baile_select(slot);}
unsigned groove_screen_preset_position(void){return baile_state(0)|(1U<<8)|(1U<<9);}
int groove_screen_open(unsigned target){if(target>1)return -1;splash=0;dirty=1;return 0;}
void groove_screen_web_fine(unsigned fine){(void)fine;}
unsigned groove_screen_web_first(void){return baile_state(3)*16;}
int groove_screen_web_step(unsigned step,unsigned toggle){if(step>=32||toggle>1)return -1;if(toggle)baile_step(step);baile_page(step/16);dirty=1;return 0;}
unsigned groove_screen_web_context(void){return 1+baile_state(0)*4+baile_state(2);}
unsigned groove_screen_web_mask(void){return 15;}
const void *groove_screen_web_targets(void){static const int empty;return &empty;}
unsigned groove_screen_web_target_count(void){return 0;}
int groove_screen_web_adjust(unsigned context,unsigned action,unsigned index,unsigned owner,int delta){
    if(context!=groove_screen_web_context()||action||index>=4||owner||!delta)return -1;
    return (int)index+3;
}
const char *groove_screen_web_knobs(void){
    static char knobs[4][2][16];static const char *const labels[]={"SATURATOR","REVERB","BPM","SWING"};
    for(unsigned i=0;i<4;++i){strcpy(knobs[i][0],labels[i]);number_label(knobs[i][1],"",baile_state(i+4),"");}
    return &knobs[0][0][0];
}
void groove_screen_snapshot(uint8_t state[8]){
    memset(state,0,8);state[1]=1;state[2]=baile_state(3)*16;state[3]=baile_state(2);state[7]=24;
}
#endif
