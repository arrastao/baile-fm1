/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
#ifndef BAILE_H
#define BAILE_H
#include "instrument.h"
void baile_start(void);
void baile_poll(void);
int baile_select(unsigned kit);
void baile_encoder(unsigned encoder, int delta);
void baile_step(unsigned step);
void baile_page(unsigned page);
unsigned baile_state(unsigned field);
const char *baile_name(unsigned kit);
const char *baile_part(unsigned part);
extern volatile unsigned baile_drive;
void baile_saturate(int32_t *pcm);
#endif
