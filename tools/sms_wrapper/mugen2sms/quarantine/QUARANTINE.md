# Quarentena — palette_contract_MD_LEGACY.py

Status: QUARENTENADO em 2026-10-15b por decisao do coordenador de
`luta_mugem_rev2` (autorizada explicitamente no pedido: "reparar como contrato
SMS ou colocar em quarentena explícita, sem alias cosmético").

Por que quarentena e nao reparo agora:
1. O modelo e do doador Mega Drive: `SLOT_MAP` PAL0–PAL3 com 15 slots por
   linha de CRAM MD, leitura de `src/mg_gen/mg_<char>.c` (arrays `u16 pals[][16]`)
   e `res/mgres_*.res` com `SPRITE` SGDK + `get_flattened_data()` — nada disso
   existe no pipeline SMS.
2. O import `from .converters.sprites import vdp_rgb` esta quebrado neste
   pacote (modulo doador nao portado): `import mugen2sms.palette_contract`
   falha com ModuleNotFoundError (reproduzido em 2026-10-15b).
3. Zero consumidores: nenhum `.py` do wrapper ou do projeto importa o modulo
   (as ocorrencias de "palette_contract" em `audit_asset_proof_sheet.py` sao a
   string de schema `mof_sms_runtime_palette_contract_v1`, do projeto
   master_of_fighters, sem ligacao com este arquivo). Mover para fora do
   caminho de import nao altera comportamento de nada — verificado:
   pacote importa ok e `python3 -m mugen2sms inventory --help` exit 0.

Verdade de cor SMS vigente (nao substituída por este arquivo):
`mugen2sms/converters/sms_palette.py` — paleta mestra 6-bit, palavra
CRAM `r | g<<2 | b<<4`, canais 0..3 (SMSlib.h secao Colors), usada por
`sms_tiles.py` (`_subpalette`, 16 palavras, [0]=transparente).

Gatilho de reparo (quando volta como contrato SMS, com numeros medidos):
- M1 decidido o renderer/escala (t3): orcar por ator as cores efetivas de
  corpo+FX na paleta de sprite SMS (P1 compartilhada, indice 0 transparente;
  P2 distinguivel por banco/palavra conforme modo SMS1/SMS2);
- escrever o contrato contra `sms_palette.py` + headers SMSlib (autoridade
  hierarquia #8), com teste diferencial e gate propio;
- os conceitos aproveitaveis do legado sao a ANALISE de classes de cor
  estaveis/variantes e a fusao sem perda (`verify_remap`), nao o SLOT_MAP.

Proibido: reativar este arquivo por alias de import, copiar PAL0–PAL3 ou
15-slots-como-lei-SMS (audit_hardware_constants bloqueia grandeza de outro
console como lei do SMS).
