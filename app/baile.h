/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
#ifndef BAILE_H
#define BAILE_H
#include "instrument.h"
void baile_init(void);
void baile_poll(void);
int baile_choose(unsigned kit);
void baile_encoder(unsigned encoder, int delta);
void baile_toggle(unsigned step);
void baile_page(unsigned page);
unsigned baile_value(unsigned index);
const char *baile_name(unsigned kit);
const char *baile_part(unsigned part);
unsigned baile_pad(unsigned part);
extern unsigned baile_saturation;
#endif
