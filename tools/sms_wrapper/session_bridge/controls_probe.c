/* Hardware/input diagnostic fixture, not game art or a delivery ROM.
 * Rows: ROM identity, P1 six bits, P2 six bits, frame low byte.
 * RAM at C700: magic SMI1, identity, frame word, key word, pause count,
 * per-button held-frame words. The ROM itself observes SMSlib input.
 */
#include "SMSlib.h"
#ifndef PROBE_ID
#define PROBE_ID 1
#endif
volatile __at(0xC700) unsigned char probe_magic[4];
volatile __at(0xC704) unsigned char probe_id;
volatile __at(0xC705) unsigned int probe_frame;
volatile __at(0xC707) unsigned int probe_keys;
volatile __at(0xC709) unsigned char probe_pause;
volatile __at(0xC70A) unsigned int probe_held[12];
volatile __at(0xC7E0) unsigned char runtime_header[5];
volatile __at(0xC7F0) unsigned int runtime_frame;
volatile __at(0xC7F2) unsigned char runtime_snapshot[10];
static const unsigned char palette[16]={0,63,3,12,48,15,51,60,0,0,0,0,0,0,0,0};
static const unsigned char tiles[64]={
 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
 255,0,0,0,255,0,0,0,255,0,0,0,255,0,0,0,255,0,0,0,255,0,0,0,255,0,0,0,255,0,0,0};
static void bits(unsigned char y,unsigned int value,unsigned char count) {
 unsigned char i;
 for(i=0;i<count;i++) SMS_setTileatXY(4+i*2,y,(value&(1u<<i))?1:0);
}
void main(void) {
 unsigned char i;
 SMS_displayOff(); SMS_loadBGPalette(palette); SMS_loadTiles(tiles,0,sizeof(tiles));
 for(i=0;i<24;i++) { unsigned char x; for(x=0;x<32;x++) SMS_setTileatXY(x,i,0); }
 probe_magic[0]='S';probe_magic[1]='M';probe_magic[2]='I';probe_magic[3]='1';
 probe_id=PROBE_ID;probe_frame=0;probe_keys=0;probe_pause=0;
 runtime_header[0]='S';runtime_header[1]='M';runtime_header[2]='R';runtime_header[3]='T';runtime_header[4]=1;
 runtime_frame=0;for(i=0;i<10;i++)runtime_snapshot[i]=0;
 SMS_enableSRAM();SMS_SRAM[0]=PROBE_ID;SMS_SRAM[1]=0;
 for(i=0;i<12;i++)probe_held[i]=0;
 SMS_displayOn();
 for(;;) {
  SMS_waitForVBlank();probe_frame++;probe_keys=SMS_getKeysStatus()&0x0FFF;
  runtime_frame=probe_frame;runtime_snapshot[6]=(unsigned char)probe_keys;runtime_snapshot[7]=(unsigned char)(probe_keys>>8);
  SMS_SRAM[1]=(unsigned char)probe_frame;
  for(i=0;i<12;i++)if(probe_keys&(1u<<i))probe_held[i]++;
  if(SMS_queryPauseRequested()){probe_pause++;SMS_resetPauseRequest();}
  bits(4,PROBE_ID,8);bits(8,probe_keys,6);bits(12,probe_keys>>6,6);bits(16,probe_frame,8);
 }
}
SMS_EMBED_SEGA_ROM_HEADER(9999,0);
SMS_EMBED_SDSC_HEADER(1,0,2026,10,5,"SMSForge","Isolated controls probe","Diagnostic fixture; no gameplay claim");
