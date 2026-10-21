/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */
/* politica de corte D9-a revisada (contagem exata por scanline):
   o runtime mantem ec[O3_ROWS] (celulas incluidas por linha do
   inimigo) e consulta a tabela estatica do jogador por indice de
   pose (frame*2 + lado); linhas do mesmo ator nao se sobrepoem
   (passo 16 px), entao line_count = o3_ax_rows[pose][rp] + ec[r]
   nas regioes sobrepostas. Sobreposicao: linhas cujos topos
   dividem scanlines visiveis (1..191). */
#define O3_ROWS 6
#define O3_ROW_PITCH 16
#define O3_DY0P (-80)
#define O3_DY0E (-72)
const unsigned char o3_ax_rows[32][6] = {{1,5,5,4,5,3},{1,5,5,4,5,3},{0,4,4,4,3,2},{0,4,4,4,3,2},{0,4,4,4,3,2},{0,4,4,4,3,2},{2,4,4,4,5,4},{2,4,4,4,5,4},{0,5,5,4,6,4},{0,5,5,4,6,4},{0,3,5,6,5,4},{0,3,5,6,5,4},{0,3,5,4,6,4},{0,3,5,4,6,4},{0,3,5,3,6,4},{0,3,5,3,6,4},{3,5,4,4,4,2},{3,5,4,4,4,2},{3,4,5,4,3,0},{3,4,5,4,3,0},{0,4,5,4,6,4},{0,4,5,4,6,4},{0,3,4,4,5,4},{0,3,4,4,5,4},{0,3,6,8,2,2},{0,3,6,8,2,2},{0,0,5,8,7,0},{0,0,5,8,7,0},{0,0,0,3,8,8},{0,0,0,3,8,8},{0,0,3,5,5,5},{0,0,3,5,5,5}};
