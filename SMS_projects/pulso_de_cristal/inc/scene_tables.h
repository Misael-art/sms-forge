/* gerado por tools/gen_scene_tables.py — NAO EDITAR. Edite a
 * partitura JSON e regenere. Composicao mora na partitura;
 * isto so expoe o QUANDO (frames) que a cena consome. */
/* fontes (sha256): */
/*   music_title.json 28c8a8314284944262a1da0d33db48659c2382c3dc13cb7151fb9e8ff7a2c42a */
/*   music_dawn.json c18ed26da42bfc16d0e0f15b59fb171488acb18232acfc662e49f3f1140ba540 */
/*   music_storm.json 26da6d767df7b28949718d4120cc3427eb70c5f20e970d7235f2796f776d9602 */
/*   music_eco.json 5e4b75a5a0f95f7cbe42f82e15ff7fbebe62199f9ab48a232ebd3d30c899e651 */
#define LOOP_TITLE 1536    /* compasso=48 f */
#define LOOP_DAWN 1920    /* compasso=60 f */
#define LOOP_STORM 896    /* compasso=28 f */
#define LOOP_ECO 1728    /* compasso=72 f */

/* cena 02 — ataques do lead de dawn (ressonancia em ordem) */
#define DAWN_ATTACKS_N 20
static const unsigned int dawn_attacks[DAWN_ATTACKS_N] = {
0,120,240,330,420,480,540,600,690,720,840,960,1140,1200,1290,1350,1440,1560,1680,1770
};

/* cena 03 — hits de ch3 (flash de paleta sinc; ruido branco) */
#define STORM_HITS_N 59
static const unsigned int storm_hits[STORM_HITS_N] = {
0,28,42,56,70,84,98,112,133,140,168,182,196,210,224,252,266,280,294,308,322,336,357,364,378,392,413,420,434,441,448,462,476,490,504,518,532,546,560,588,609,616,630,644,658,672,693,700,728,742,756,770,784,798,812,840,861,868,882
};

