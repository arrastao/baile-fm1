/* Offline asset preparation; uses the pinned upstream SEA encoder/decoder. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#define FM1_DSP_DATA
#define SAMPLE_DRUM_PADS 8
#include "sample_metadata.inc"
#include "sea_encode.h"
int main(int argc,char **argv){
 if(argc!=4)return 1;
 FILE *f=fopen(argv[1],"rb");if(!f)return 2;
 fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);
 if(size<=0||size%2)return 3;
 int16_t *pcm=malloc(size);if(!pcm)return 4;
 if(fread(pcm,1,size,f)!=(size_t)size)return 5;fclose(f);
 uint8_t *encoded=fm1_sea_encode(pcm,size/2,sample_dqt);if(!encoded)return 6;
 unsigned bytes=((size/2+319)/320)*228;
 f=fopen(argv[2],"wb");if(!f)return 7;
 if(fwrite(encoded,1,bytes,f)!=bytes)return 8;fclose(f);
 f=fopen(argv[3],"wb");if(!f)return 9;
 for(unsigned i=0;i<bytes;i+=228){int16_t out[320];
  if(fm1_sea_decode(encoded+i,228,5,sample_dqt,out))return 10;
  unsigned left=size/2-(i/228)*320,n=left<320?left:320;
  if(fwrite(out,2,n,f)!=n)return 11;
 }
 fclose(f);free(encoded);free(pcm);return 0;
}
