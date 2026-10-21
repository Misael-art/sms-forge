# Handoff — Criação de Assets (agente de ARTE) — kage_matsuri

> Este documento é o contrato de handoff do `implementation_plan.md` §1.
> **Runtime, pipeline, contratos e gates são de outro agente — NÃO toque em
> `src/main.c`, `doc/13-spec-cenas.md`, `doc/15-tdd.md`, `tools/pack_kage.py`.**
> O seu escopo é escolher e traduzir as fontes de arte em `rascunho/`.

## Estado que você recebe

As duas poses novas JÁ estão empacotadas e na ROM a partir de fontes provisórias:

| Poses na ROM | Fonte atual (provisória) | O que se espera de você |
|---|---|---|
| `kage_slash2` (pose 4, 2º golpe do combo) | `rascunho/kage_slash2.png` (frame solto) | Selecionar o frame de clímax do golpe aberto em `rascunho/anim_kage_slash2/` (36 frames PNG 544×544; o plano cita `f015.png` como candidato) e salvá-lo **como** `rascunho/kage_slash2.png` |
| `kage_jump` (pose 5, salto ninja) | `rascunho/kage_jump.jpg` | Selecionar/traduzir a pose de salto ninja (fonte candidata: frames de `rascunho/anim_kage_combo/` ou nova passagem) e salvá-la **como** `rascunho/kage_jump.jpg` |

O pipeline já processa esses dois caminhos — você troca a FONTE, o resto é automático.

## Restrições duras da tradução (o `pack_kage.py` assume tudo isso)

1. **Uma figura por fonte**, corpo inteiro visível. O recorte automático usa
   janela 1:2 centrada na **massa do corpo** (`crop_body`), não no bbox da arma —
   a arma pode sair da janela; o tronco não.
2. **Chroma magenta** (255, 0, 255) no fundo — regra `r>180 && b>180 && g<120`.
   Magenta vira índice 0 (transparente); o gi PRETO do ninja NÃO é transparente.
3. **Resolução mínima ~64×128** (o pack faz nearest para 16×32); 544×544 é ideal.
4. Sem branding, sem texto, sem marca — gate `audit_visual_delivery --delivery`
   reprova palco/HUD com branding.
5. **Não quantize nem reduza paleta**: a conversão para a paleta mestra 6-bit é
   feita pelo `pack_kage.py`. Entregue RGB puro + chroma.

## Passo a passo depois de soltar as fontes

```bash
cd SMS_projects/kage_matsuri
./clean.sh && python3 tools/pack_kage.py   # regenera PNGs, headers, áudio e manifestos de provenância
./build.sh                                  # pré-gates + SDCC + changelog
```

Depois re-selar os contratos (o SHA da ROM muda a cada build por causa do
header SDSC com data automática):

1. Atualizar `doc/rom_asset_binding.json`: `rom_sha256`/`rom_size_bytes` da nova
   ROM e os `sha256` das entradas `res/sprites/kage_slash2_*` e `kage_jump_*`.
2. Rodar os gates analíticos (todos precisam PASS):
   ```bash
   python3 ../../tools/sms_wrapper/audit_claims.py --project .
   python3 ../../tools/sms_wrapper/audit_audio_provenance.py --project .
   python3 ../../tools/sms_wrapper/audit_visual_delivery.py --project . --delivery
   python3 ../../tools/sms_wrapper/audit_rom_asset_binding.py --project . --require
   python3 ../../tools/sms_wrapper/audit_sprite_line_sim.py doc/sprite_scene_rua_matsuri.json
   ```
3. Evidência fresca no emulador (boot, screenshot `delivery`, fps, probe de
   runtime) conforme `tools/sms_wrapper/.agent/workflows/`.

## Definition of done

- Gates acima 100% PASS com a ROM nova;
- Evidência de emulador selada como mais recente que a ROM
  (`seal_fresh_evidence_bundle.py`);
- `doc/10-memory-bank.md` atualizado com a data e a prova;
- Nenhuma alteração em runtime/contratos de HUD — se achar que precisa de
  mudança de código, PARE e devolva pelo handoff inverso.

## Fechamento do handoff pelo coordenador — 2026-09-09

As fontes provisórias foram integradas pelo coordenador de produção, sem
transferir ao papel de arte a responsabilidade por runtime ou gates:

- `rascunho/kage_slash2.png` veio do frame de clímax `anim_kage_slash2/f015.png`;
- `rascunho/kage_jump.jpg` veio da pose suspensa `anim_kage_combo/f025.png`;
- `pack_kage.py` gerou provas integrais `res/proof/*_full.png` 16×32 e o
  runtime usa as partes 8×16 correspondentes;
- `audit_rom_asset_binding --require` passou contra símbolos reais do linker,
  e não aliases `sym_*`;
- ROM final: `out/rom/kage_matsuri.sms`, SHA256
  `283e250a2df13ca87df58dd5ddcf16ff314f71e5c79aabf38c37cf12b3f7941e`;
- `full_cycle_memory.json` prova combo→duas derrotas→torii→reset. O áudio
  isolado, vídeo nativo 256×192, runtime NTSC e worst-frame foram renovados
  depois desta ROM.

O gate PAL foi executado, mas ficou fora do limite: 49.37/49.42 quadros/s contra
a faixa regional exigida. Isso permanece bloqueio reportado; não é motivo para trocar
o critério ou promover a fatia como pronta.

O budget causal de ação também foi executado: `worst_frame_cycle.json` alcançou
combo e `state=1`, mas falhou com `vline_max=244` e `vovf_delta=67`; o PASS de
`worst_frame_final6.json` é somente ROUND passivo. O ciclo jogável em si fecha
por RAM em `full_cycle_memory.json`.

Atualização final7: o coordenador renovou vídeo nativo, áudio isolado e probes
NTSC/PAL após a última build. NTSC passou em avanço; PAL ficou em 48.99/48.22
quadros/s. O budget causal permanece bloqueado por `vline_max=243` e
`vovf_delta=66`; não promover sem nova medição PASS.

## Handoff do coordenador — continuidade 2026-09-19

Slash2/jump estão integrados, as provas 16×32 existem e o binding aponta para
`_kage_ext_right_tiles`/`_kage_ext_left_tiles` realmente linkados. ROM atual:
`out/rom/kage_matsuri.sms`, SHA256
`1e6c4e9bb9e91b0b5649d8877a5a5b78bdb10c4930146f5b9bea9e5bb74a77a3`.

O ciclo jogável passou por RAM em `out/evidence/full_cycle_memory.json`; o
budget causal falhou com `vline_max=246`, `vovf_delta=66`. A fatia não é
promovida enquanto esse degrau permanecer sem PASS. A renovação NTSC/PAL,
vídeo, áudio isolado, selo e review independente do novo SHA continua
pendente: o Emulicious apresentou NPE no debugger e a porta oficial também
foi ocupada por sessão concorrente de `hamoopig`, que não foi encerrada.

Não há decisão nova de escopo: dano, projéteis e nova cena continuam fora.
Foi selado o bundle fresco parcial atual
`out/evidence/fresh_evidence_bundle_current.json` (8 artefatos, SHA
`ca07c2d8da7454bc02d226622b904d845229af33f9db80b457df8a4d13e315d2`), com
gameplay, budget, binding, vídeo nativo, áudio isolado e render fidelity; ele
não substitui o bundle de entrega sem boot/FPS NTSC-PAL e review novo.
