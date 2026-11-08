/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
#include "instrument.h"
#include "fm_patch.h"
#include "version.h"
#include "fm1_engine_control.h"
#include <string.h>
enum {
    BACK = 0x0000,
    PANEL = 0x18e3,
    TEXT = 0xef5d,
    ACCENT = 0x07ff,
    DIM = 0x738e,
    GREEN = 0x07e0,
    AMBER = 0xfd20
};
/* Five columns per glyph, bit 0 at the top. Digits followed by uppercase. */
static const uint8_t font[36][5] = {
    {0x3e, 0x51, 0x49, 0x45, 0x3e}, {0, 0x42, 0x7f, 0x40, 0},       {0x42, 0x61, 0x51, 0x49, 0x46},
    {0x21, 0x41, 0x45, 0x4b, 0x31}, {0x18, 0x14, 0x12, 0x7f, 0x10}, {0x27, 0x45, 0x45, 0x45, 0x39},
    {0x3c, 0x4a, 0x49, 0x49, 0x30}, {0x01, 0x71, 0x09, 0x05, 0x03}, {0x36, 0x49, 0x49, 0x49, 0x36},
    {0x06, 0x49, 0x49, 0x29, 0x1e}, {0x7e, 0x11, 0x11, 0x11, 0x7e}, {0x7f, 0x49, 0x49, 0x49, 0x36},
    {0x3e, 0x41, 0x41, 0x41, 0x22}, {0x7f, 0x41, 0x41, 0x22, 0x1c}, {0x7f, 0x49, 0x49, 0x49, 0x41},
    {0x7f, 0x09, 0x09, 0x09, 0x01}, {0x3e, 0x41, 0x49, 0x49, 0x7a}, {0x7f, 0x08, 0x08, 0x08, 0x7f},
    {0, 0x41, 0x7f, 0x41, 0},       {0x20, 0x40, 0x41, 0x3f, 0x01}, {0x7f, 0x08, 0x14, 0x22, 0x41},
    {0x7f, 0x40, 0x40, 0x40, 0x40}, {0x7f, 0x02, 0x0c, 0x02, 0x7f}, {0x7f, 0x04, 0x08, 0x10, 0x7f},
    {0x3e, 0x41, 0x41, 0x41, 0x3e}, {0x7f, 0x09, 0x09, 0x09, 0x06}, {0x3e, 0x41, 0x51, 0x21, 0x5e},
    {0x7f, 0x09, 0x19, 0x29, 0x46}, {0x46, 0x49, 0x49, 0x49, 0x31}, {0x01, 0x01, 0x7f, 0x01, 0x01},
    {0x3f, 0x40, 0x40, 0x40, 0x3f}, {0x1f, 0x20, 0x40, 0x20, 0x1f}, {0x3f, 0x40, 0x38, 0x40, 0x3f},
    {0x63, 0x14, 0x08, 0x14, 0x63}, {0x07, 0x08, 0x70, 0x08, 0x07}, {0x61, 0x51, 0x49, 0x45, 0x43}};
/* Compose the final pixels before touching the LCD. Sixteen rows cost 7,680
 * bytes; unchanged bands and unchanged horizontal margins are not transferred.
 * A page change never exposes the temporary background clear on the panel. */
enum { PAINT_ROWS = 16, PAINT_BANDS = FM1_SCREEN_HEIGHT / PAINT_ROWS };
_Static_assert(FM1_SCREEN_WIDTH * PAINT_ROWS <= FM1_SCREEN_DMA_PIXELS, "LCD band capacity");
static uint16_t paint_pixels[FM1_SCREEN_WIDTH * PAINT_ROWS];
static uint8_t paint_left[PAINT_BANDS], paint_right[PAINT_BANDS];
static unsigned paint_rendering, paint_top, paint_next, paint_x, paint_end;
static uint32_t paint_priority;
static void paint_mark(unsigned x, unsigned y, unsigned w, unsigned h)
{
    for (unsigned b = y / PAINT_ROWS; b <= (y + h - 1) / PAINT_ROWS; ++b) {
        paint_priority |= 1U << b;
        if (x < paint_left[b]) paint_left[b] = (uint8_t)x;
        if (x + w > paint_right[b]) paint_right[b] = (uint8_t)(x + w);
    }
}
/* Many LCD pages share this bounded fill; keep a single native copy. */
static __attribute__((noinline)) void paint_fill(unsigned x, unsigned y, unsigned w, unsigned h, uint16_t color)
{
    if (!w || !h || x >= FM1_SCREEN_WIDTH || y >= FM1_SCREEN_HEIGHT) return;
    if (w > FM1_SCREEN_WIDTH - x) w = FM1_SCREEN_WIDTH - x;
    if (h > FM1_SCREEN_HEIGHT - y) h = FM1_SCREEN_HEIGHT - y;
    if (!paint_rendering) { paint_mark(x, y, w, h); return; }
    if (x >= paint_end || x + w <= paint_x) return;
    unsigned right = x + w < paint_end ? x + w : paint_end;
    if (x < paint_x) x = paint_x;
    unsigned first = y < paint_top ? paint_top : y;
    unsigned end = y + h < paint_top + PAINT_ROWS ? y + h : paint_top + PAINT_ROWS;
    for (unsigned row = first; row < end; ++row)
        for (unsigned col = x; col < right; ++col)
            paint_pixels[(row - paint_top) * (paint_end - paint_x) + col - paint_x] = color;
}
static const uint8_t punctuation[][6] = {
    {45,8,8,8,8,8}, {47,0x60,0x18,6,1,0}, {43,8,8,0x3e,8,8},
    {35,0x14,0x7f,0x14,0x7f,0x14}, {37,0x63,0x13,8,0x64,0x63},
    {62,0x41,0x22,0x14,8,0}, {63,2,1,0x51,9,6},
    {33,0,0,0x5f,0,0}, {34,0,7,0,7,0}, {36,0x24,0x2a,0x7f,0x2a,0x12},
    {38,0x36,0x49,0x55,0x22,0x50}, {39,0,5,3,0,0}, {40,0,0x1c,0x22,0x41,0},
    {41,0,0x41,0x22,0x1c,0}, {42,0x14,8,0x3e,8,0x14}, {44,0,0x50,0x30,0,0},
    {46,0,0x60,0x60,0,0}, {58,0,0x36,0x36,0,0}, {59,0,0x56,0x36,0,0},
    {60,8,0x14,0x22,0x41,0}, {61,0x14,0x14,0x14,0x14,0x14},
    {64,0x32,0x49,0x79,0x41,0x3e}, {91,0,0x7f,0x41,0x41,0},
    {92,1,6,0x18,0x60,0}, {93,0,0x41,0x41,0x7f,0}, {94,4,2,1,2,4},
    {95,0x40,0x40,0x40,0x40,0x40}, {96,0,1,2,4,0}, {123,0,8,0x36,0x41,0},
    {124,0,0,0x7f,0,0}, {125,0,0x41,0x36,8,0}, {126,8,4,8,0x10,8}
};
static void text(unsigned x, unsigned y, const char *s, unsigned scale, uint16_t color,
                 uint16_t background)
{
    if (!s || !scale || scale > 4 || x >= FM1_SCREEN_WIDTH ||
        y >= FM1_SCREEN_HEIGHT || 7U * scale > FM1_SCREEN_HEIGHT - y) return;
    unsigned w = 6U * scale, h = 7U * scale;
    if (paint_rendering && (y >= paint_top + PAINT_ROWS || y + h <= paint_top)) return;
    if (!paint_rendering) {
        unsigned n = (unsigned)strlen(s), available = (FM1_SCREEN_WIDTH - x) / w;
        if (n > available) n = available;
        if (n) paint_mark(x, y, n * w, h);
        return;
    }
    for (; *s && x + w <= FM1_SCREEN_WIDTH; ++s, x += w) {
        if (x >= paint_end) break;
        if (x + w <= paint_x) continue;
        char letter = *s >= 'a' && *s <= 'z' ? (char)(*s - 'a' + 'A') : *s;
        static const uint8_t blank[5] = {0};
        const uint8_t *shape = blank;
        if (*s >= '0' && *s <= '9')
            shape = font[*s - '0'];
        else if (letter >= 'A' && letter <= 'Z')
            shape = font[10 + letter - 'A'];
        else if (*s != ' ')
            for (unsigned i = 0; i < sizeof punctuation / sizeof punctuation[0]; ++i)
                if ((uint8_t)*s == punctuation[i][0]) {
                    shape = punctuation[i] + 1;
                    break;
                }
        unsigned first_row = y < paint_top ? paint_top : y;
        unsigned end_row = y + h < paint_top + PAINT_ROWS ? y + h : paint_top + PAINT_ROWS;
        unsigned first_col = x < paint_x ? paint_x : x;
        unsigned end_col = x + w < paint_end ? x + w : paint_end;
        unsigned stride = paint_end - paint_x;
        for (unsigned row = first_row; row < end_row; ++row) {
            unsigned mask = 1U << ((row - y) / scale);
            uint16_t *pixel = paint_pixels + (row - paint_top) * stride + first_col - paint_x;
            for (unsigned col = first_col; col < end_col; ++col) {
                unsigned column = (col - x) / scale;
                *pixel++ = column < 5U && (shape[column] & mask) ? color : background;
            }
        }
    }
}
#include "baile.h"
#include <stdarg.h>
static void label(char *out,unsigned capacity,const char *fmt,...) {
    va_list args;va_start(args,fmt);unsigned n=0;
    while(*fmt && n+1<capacity){
        if(*fmt!='%'){out[n++]=*fmt++;continue;}
        ++fmt;
        if(*fmt=='s'){const char *value=va_arg(args,const char *);while(*value&&n+1<capacity)out[n++]=*value++;}
        else if(*fmt=='u'){unsigned value=va_arg(args,unsigned),count=0;char digits[10];do{digits[count++]=(char)('0'+value%10);value/=10;}while(value&&count<10);while(count&&n+1<capacity)out[n++]=digits[--count];}
        if(*fmt)++fmt;
    }out[n]=0;va_end(args);
}
static const uint8_t white_keys[16]={0,2,4,6,7,9,11,12,14,16,18,19,21,23,24,26};
static uint32_t old_keys, old_buttons, started, last_frame;
static unsigned boot;
#include "baile_art.h"
static void artwork(const uint8_t *runs,unsigned bytes,const uint16_t *palette,unsigned height,unsigned dest_height) {
    if(!paint_rendering){paint_mark(0,0,240,dest_height);return;}
    unsigned at=0;
    for(unsigned i=0;i<bytes;++i){unsigned count=(runs[i]>>5)+1;uint16_t color=palette[runs[i]&31];
        for(unsigned j=0;j<count;++j,++at){unsigned sy=at/160,sx=at%160;
            unsigned y=sy*dest_height/height,ey=(sy+1)*dest_height/height;
            if(y>=paint_top+16)return;if(ey<=paint_top)continue;
            unsigned x=sx*240/160,ex=(sx+1)*240/160;paint_fill(x,y,ex-x,ey-y,color);
        }
    }
}
#define ART(name,h,dh) artwork(art_##name,sizeof art_##name,art_##name##_palette,h,dh)
static void draw(void) {
    char buf[40];struct groove_view v;groove_get_view(0,0,&v);
    unsigned kit=baile_value(0);static const uint16_t backgrounds[]={0xff00,0x601f,0x07ff,0xf8b0};
    uint16_t bg=backgrounds[kit],ink=0x0000,cyan=0x07ff;
    paint_fill(0,0,240,240,bg);
    if(boot){ART(boot,160,240);return;}
    if(kit==0){ART(tamborzao,38,56);}else if(kit==1){ART(voltmix,38,56);}else if(kit==2){ART(bolha,38,56);}else{ART(mandelao,38,56);}
    unsigned selected=baile_value(2),first=16*baile_value(3);
    for(unsigned row=0;row<4;++row){unsigned y=65+row*24;uint16_t rb=row==selected?0:bg;
        if(row==selected)paint_fill(3,y-6,234,22,0);
        text(6,y,row==selected?">":" ",1,cyan,rb);text(18,y,baile_part(row),1,row==selected?0xffff:ink,rb);
        uint64_t mask=groove_drum_steps(0,baile_pad(row));
        for(unsigned i=0;i<16;++i){unsigned on=(mask>>(first+i))&1;unsigned x=112+i*7;
            paint_fill(x,y,5,9,on?(row==selected?cyan:0xffbc):0x2124);
            if(v.playing && v.play_step==first+i)paint_fill(x,y+11,5,2,row==selected?0xffff:0);}
    }
    label(buf,sizeof buf,"COMPASSO %u/2",baile_value(3)+1);text(6,161,buf,1,ink,bg);
    text(99,161,v.playing?"TOCANDO":"PARADO",1,ink,bg);label(buf,sizeof buf,"%u BPM",v.tempo);text(191,161,buf,1,ink,bg);
    paint_fill(6,179,70,19,0);paint_fill(83,179,70,19,0);
    label(buf,sizeof buf,"SAT %u",baile_value(4));text(12,185,buf,1,cyan,0);
    label(buf,sizeof buf,"REV %u",baile_value(5));text(89,185,buf,1,cyan,0);
    label(buf,sizeof buf,"SWING %u  OCT -/+ PAGINA",baile_value(7));text(6,206,buf,1,ink,bg);
    if(baile_value(1)){label(buf,sizeof buf,"PROX: %s",baile_name(baile_value(1)-1));text(6,226,buf,1,ink,bg);}
    else {paint_fill(3,220,72,17,cyan);paint_fill(77,220,48,17,0);paint_fill(127,220,53,17,0);paint_fill(182,220,55,17,0);
        text(8,225,"ALGORITHM",1,0,cyan);text(83,225,"TRILHA",1,0xffff,0);text(135,225,"TECLAS",1,0xffff,0);text(190,225,"PASSOS",1,0xffff,0);}
}
static void flush(void) {
    uint32_t at=fm1_millis();paint_rendering=1;
    for(unsigned n=0;n<PAINT_BANDS;++n){if(fm1_screen_pending())break;
        unsigned band=paint_next;paint_next=(band+1)%PAINT_BANDS;
        if(paint_left[band]>=paint_right[band])continue;
        paint_top=band*16;paint_x=0;paint_end=240;draw();
        if(fm1_screen_submit(0,paint_top,240,16,paint_pixels,3840))break;
        paint_left[band]=240;paint_right[band]=0;
        if(fm1_millis()-at>=4)break;
    }paint_rendering=0;
}
void groove_screen_init(void) {
    baile_init();old_keys=old_buttons=0;boot=1;started=last_frame=fm1_millis();
    paint_next=paint_rendering=0;memset(paint_left,240,sizeof paint_left);memset(paint_right,0,sizeof paint_right);
    fm1_controls_init();fm1_screen_init();draw();flush();
}
static void transport(unsigned command){uint8_t c=(uint8_t)command;fm1_midi_post(&c,1);}
void groove_screen_control(void) {
    struct fm1_controls c;fm1_controls_read(&c);groove_master_update(c.knob);
    uint32_t down=c.keys&~old_keys,buttons=c.buttons&~old_buttons;
    unsigned changed=down||buttons;
    for(unsigned e=0;e<7;++e)if(c.encoders[e]){baile_encoder(e,c.encoders[e]);changed=1;}
    if(buttons&1)baile_page(0);if(buttons&2)baile_page(1);
    if(buttons&(1U<<11))baile_page(!baile_value(3));
    if(buttons&(1U<<12)){struct groove_view v;groove_get_view(0,0,&v);transport(v.playing?0xfc:0xfa);}
    for(unsigned i=0;i<16;++i)if(down&(1U<<white_keys[i]))baile_toggle(baile_value(3)*16+i);
    old_keys=c.keys;old_buttons=c.buttons;baile_poll();
    uint32_t now=fm1_millis();if(boot&&(changed||now-started>=2400)){boot=0;changed=1;}
    if(changed||now-last_frame>=33){last_frame=now;draw();}
    flush();
    struct groove_view v;groove_get_view(0,0,&v);uint64_t mask=groove_drum_steps(0,baile_pad(baile_value(2)));
    for(unsigned i=0;i<16;++i){unsigned step=baile_value(3)*16+i;fm1_led_set(14+white_keys[i],((mask>>step)&1)||(v.playing&&v.play_step==step));}
    fm1_led_set(12,v.playing);
}
void groove_screen_tap(uint32_t now){groove_tempo_tap(now);}
void groove_screen_mmc(unsigned command){if(command==1)transport(0xfc);else if(command==2||command==3)transport(0xfa);}
#ifdef FM1_HOST_TEST
int groove_screen_preset(unsigned slot){return baile_choose(slot);}
unsigned groove_screen_preset_position(void){return baile_value(0)|768;}
int groove_screen_open(unsigned target){(void)target;boot=0;draw();flush();return 0;}
unsigned groove_screen_web_context(void){return baile_value(0)*8+baile_value(2)*2+baile_value(3);}
unsigned groove_screen_web_mask(void){return 15;}
const void *groove_screen_web_targets(void){return 0;}
unsigned groove_screen_web_target_count(void){return 0;}
void groove_screen_web_fine(unsigned fine){(void)fine;}
int groove_screen_web_adjust(unsigned context,unsigned action,unsigned index,unsigned owner,int delta){(void)action;(void)owner;if(context==groove_screen_web_context()&&index<4)baile_encoder(index+2,delta);return 0;}
const char *groove_screen_web_knobs(void){static char values[4][2][24];const char *labels[]={"SATURATOR","REVERB","BPM","SWING"};for(unsigned i=0;i<4;++i){strcpy(values[i][0],labels[i]);label(values[i][1],24,"%u",baile_value(i+4));}return &values[0][0][0];}
unsigned groove_screen_web_first(void){return baile_value(3)*16;}
int groove_screen_web_step(unsigned step,unsigned toggle){if(step>=32)return -1;baile_page(step/16);if(toggle)baile_toggle(step);return 0;}
void groove_screen_snapshot(uint8_t s[8]){memset(s,0,8);s[1]=1;s[2]=(uint8_t)(baile_value(3)*16);s[3]=(uint8_t)baile_pad(baile_value(2));s[7]=24;}
#endif
