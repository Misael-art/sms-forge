# Auditoria do doador SGDK — SMS luta_mugem_rev2

**Somente leitura:** nenhum byte foi copiado para o SMS, nenhum ZIP foi extraído, nenhum teste/build/emulador foi executado e nenhum arquivo do doador foi alterado.

## Fonte correta

Projeto: `/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/Mugenesis_Demo [VER.001] [SGDK 211] [GEN] [GAME] [FIGHTING]`

Pacotes originais escolhidos pelo manifesto:

- **ken**: `/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/Mugenesis_Demo [VER.001] [SGDK 211] [GEN] [GAME] [FIGHTING]/rascunho/inputs/mugen_authorized_20260929/characters/street-fighter-zero/Ken_Majik_.zip`
  - SHA-256 `b244ec9a105fa0131b37c075dc06b032a87cf0f839f46ec7054ac60d9bd6f14c`; manifesto e bytes conferem.
  - DEF `ken8/ken8.def`; SHA `fdbe2fb2498be72078232ca68f2cc74fd8347aac2c8304c626d5f15dc68f5fc8`.
- **ryu**: `/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/Mugenesis_Demo [VER.001] [SGDK 211] [GEN] [GAME] [FIGHTING]/rascunho/inputs/mugen_authorized_20260929/characters/street-fighter-zero/ryu.zip`
  - SHA-256 `6db7e29d82fff1034e8c2ddab600e500fe8377ebdeef9b626fd6b580b812300d`; manifesto e bytes conferem.
  - DEF `ryu/ryu.def`; SHA `edb3db7714b5fc47f34f702eb06c166bfec039cc96a270288a3f8050b40a01e8`.

Os ZIPs são as entradas canônicas. Não usar `res/mugen` (já convertido) nem `ken_masters_adv.zip`/`ssf2_01_ryu.zip` da entrada antiga como se fossem esses pilotos. Todos os membros relevantes e seus hashes estão no JSON; leitura foi feita em memória, sem extração.

## Estados comuns

Ambos os DEF exigem `common1.cns`, ausente nos dois ZIPs. O loader usa `/mnt/sdcard/Projects/Sgdk Forge/tools/mugen2sgdk_forge/mugen2sgdk_forge/data/common_forge.cns`, que contém 34 StateDefs originais do Forge. Essa adaptação não comprova equivalência com o common1 original e não fornece FightFX/fight.snd. Falta suporte/estado Ken51/105/300 e Ryu5040/5200/5210 conforme mapa estático recente.

## Estado e bloqueios

A memória de15out prevalece sobre a matriz atualizada11out: engine reutilizável em technical_demo, novas opções/treino implementadas mas sem build desta fonte; bloqueios de host e evidência preservados. `best_proven=null`; ROM principal histórica não é comprovação da fonte nova.

- **missing_common — source_dependency_unresolved:** Both selected DEF name common1.cns; absent in both selected ZIPs. common_forge has34 statedefs and is adaptation, not recovered original.
- **strict_source — blocked_recorded_2026-10-12:** Ken170findings;Ryu157(154blocked+3supported_evidence_insufficient), source_preflight_blocked/review_required_before_pilot. These are donor strict findings, not newly executed tests or proof source corrupt.
- **ryu_missing_sff — 8_static_refs_unresolved:** AIR refs(6000,0..5),(8400,5..6) absent selectedSFF; 8400frames referencedExplod3900; six6000literalreachabilityunknown.
- **global_fx_audio — unresolved:** Ken spark0/1,guard40 and common hitsounds5*/guardsound6,0 lack global FightFX/fight.snd. Ryu localS8060 supplied but exactFX8060fallback alias is explicitconsumeradaptation, not fullglobalfx support.
- **palette_SMS — needs_new_SMS_contract:** Donor historical exactbody+FX20Ken29Ryu exceed15perMDfighter; SMS hasone15usefulspritepalette sharedP1/P2+FX. Quantization/scale/overlap must be redesigned and reviewed, noinheritMDPAL1/PAL2/PAL3.
- **donor_hardware_budget — measured_overage_diagnostic_only:** FX8060H40fivecheckpoints linepixels504/552/512/608/376;3/5spriteoverage. A/Bspawnpath contributes, isolatedcostunknown. SMS8spritesline/64SATbudget must be measured fromnewSMSscene.
- **latest_frontend — implemented_unbuilt_2026-10-15:** Options/training/navigationcode updatedsource+installedcopy; runtimefull /run/user/1000 and projectoutlogsEIOpreventbuild. Donor memory says noROMnewerforlatestsource; notcurrenthoststatuschecked.
- **delivery — technical_demo_partial_best_proven_null:** MainROMhistorical1b66cd1d7d3117f7fec0e487e1d4a7473357b5fa0693c24d21cf333eada1c7a8; current gameplay/FPS/audio/physicalcontrols/visualmotionunvalidated; no SMSruntimeproof.

## Reuso apropriado

Adotar contratos de parsing, proveniência e testes diferenciais, preservando os diagnósticos arquivo/linha, os IDs AIR/Clsn/commands e separando origem, IR, dados, runtime, consumidor e evidência. Source/INI/AIR/CMD/CNS/SFFv1/SND e os métodos de strict/exploratory são os primeiros doadores úteis. Os caminhos e hashes exatos estão no JSON.

A VM host serve de oráculo semântico. Runtime Z80, renderer, paletas, SAT, banking, áudio e budgets precisam de backend SMS próprio. Não transplantar SPR/DMA/XGM2, H40, quatro linhas PAL ou o custo do runtime68000. O header sharedMgSound foi alterado recentemente; não copiar tabelasC antigas como ABI estável.

O repositório declara MIT para software Forge; preservar o aviso ao copiar código substancial. Isso não licencia os assets MUGEN de terceiros, cujo manifesto registra uso local e redistribuição não verificada.

## Sequência recomendada

1. Criar intake SMS único dos dois ZIPs por hash, com seleção de DEF e manifesto de membros.
2. Resolver/registrar common1 e FightFX/fight.snd; common_forge é adaptação explícita, nunca o original recuperado.
3. Projetar perfil SMS e converter sem importar tabelasSGDK, mantendo eixos, timing, IDs e caixas.
4. Medir uma cena SMS nova com os dois lutadores, paleta compartilhada, FX e HUD; validar inputs, combate e orçamento com ROM e sessão próprias.

## Limites

Nenhum parser foi executado como teste ou conversão. Os ZIPs e arquivos fonte foram somente lidos para nomes, cabeçalhos, refs e hashes. Os números de compatibilidade e hardware são registros históricos do doador, não medições novas nem garantias para Master System. Não houve varredura recursiva do enorme rascunho: fontes foram localizadas pelo contexto, matriz e manifesto.
