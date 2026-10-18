# Doador OpenBOR → SMS — auditoria de 15/10/2026

Projeto: `/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/OpenBOR_Demo [VER.001] [SGDK 211] [GEN] [GAME] [BEAT_EM_UP]`
Importador: `/mnt/sdcard/Projects/Sgdk Forge/tools/openbor2sgdk_forge`

Somente leitura: nenhum asset foi copiado, nenhum PAK extraído e nenhum teste/build/emulador executado.

## Entradas reais

- **golden_axe_legend**: `/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/OpenBOR_Demo [VER.001] [SGDK 211] [GEN] [GAME] [BEAT_EM_UP]/rascunho/entrada_bruta/golden_axe_legend/GAL.pak`
  - SHA `64da17e8b60118ca9bd3a0bbbf87ef4acea705b1485ec6b4c58bf2f4f50634c4`; tamanho `39500889`; cabeçalho PACK v0; hash confere com manifesto.
- **battle_toads**: `/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/OpenBOR_Demo [VER.001] [SGDK 211] [GEN] [GAME] [BEAT_EM_UP]/rascunho/entrada_bruta/battle_toads/battle_toads.PAK`
  - SHA `f2c5319deb68da97c3a469d3cc27b0be6b05e6b840847237369e78a01146e7a6`; tamanho `36324119`; cabeçalho PACK v0; hash confere com manifesto.

A origem externa e a versão OpenBOR original dos dois módulos continuam desconhecidas. O snapshot DCurrent `787b6770409935137579715febf80cf7a529b748` é referência semântica parcial; seus seis hashes locais conferem. Ele não identifica o executável original dos PAKs.

## Estado real

Contrato 0.1 é draft e matriz `partial_slice_only`: 13 capacidades, sendo 10 parciais, scripts desconhecidos, performance sem prova e módulos integrais/generalização não implementados. Há sete perfis; GAL TOWN1 adapta 8/26 diretivas e rejeita 18. O importador central tem Python; não existe runtime C central para instalar. O runtime é de propriedade do consumidor em `src/openbor/`.

A memória abre com12out; `doc/openbor/curation_followup_20261015.md` traz contexto mais recente. O readback de15out obteve VRAM no menu, sem input A comprovado; não valida a máscara TEXT. O próximo owner semântico é ITEM linha58, sem pickup/equip/inventário/ciclo definido. Não pular esse evento para obter um verde.

## Reuso útil e reescrita

| Área | Host reaproveitável | Backend SMS |
|---|---|---|
| Container | `pak.py`: PACK32/64, paths seguros, índice/leitura | PAK fica no host; ROM recebe dados compilados/bancos |
| Modelos/níveis | `model_text.py`, `level_inventory.py`, `reference_semantics.py` | Contrato de física, relógio, profundidade e eventos explícito |
| Imagens/texto | Inventário e metadados em `images.py`, `scene_import.py`, `text_import.py` | Paleta SMS, tiles, SAT, fonte e HUD próprios |
| Eventos | `level_event_table.py` e contrato do kernel `ob_level_events.c` | Trocar ABI/genesis.h, acesso ROM banked e callbacks por owner |
| Prova | Traces, schemas, overflow, pares A/B e testes negativos | RAM probe SMS medido; sessões privadas Emulicious/BlastEm SMS |
| Cena/streaming | Método e estados de `ob_belt.c`/`ob_world_stream.c` | Renderer, VBlank sem DMA, câmera/scroll, bancos e PSG novos |

Não importar H40, 320×224, quatro paletas, WINDOW/BG_A/B, XGM2, budgets de tiles SGDK nem tabelas/assets gerados como fontes originais. Também não tratar um recorte de512px como fase completa.

## Segundo piloto e limites

Battle Toads é um PAK diferente, mas a rota MD nativa falha no budget registrado; a legacy corta1878px de2390 e permite três inimigos. A captura de61/1200quadros é smoke test, não generalização completa. Mapeamentos de velocidade, salto, ausência de attack-z e fall→death são adaptações de perfil.

Os módulos Forge são MIT; o extrato OpenBOR declara BSD-3-Clause. Preservar avisos/licenças ao reutilizar código. Essas licenças não liberam os PAKs/assets de terceiros. Importador usa stdlib Python e Pillow; versões de dependências não foram qualificadas neste parecer.

## Rota para o plano/prompt

1. Um importador SMS central, IR/contrato versionados, runtime compartilhado e consumidor separado.
2. Intake hash-bound dos dois PAKs, com origem/versão desconhecidas registradas e grafo de dependências.
3. Parsing host reutilizado com diagnóstico explícito de lacunas; emissão SMS própria.
4. Vertical slice com1P, profundidade, um inimigo, colisão, dano e progressão; depois ampliar os eventos sem saltar owners.
5. Medir orçamento SMS de sprites, paleta compartilhada, VRAM/RAM/bancos/VBlank/áudio no pior evento.
6. Validar segundo módulo pelo mesmo núcleo e suas provas próprias, sem promover métricas MD a60FPS/AAA SMS.

O JSON contém paths concretos, hashes de módulos, runtime/owners/traces, contratos, drift em relação à matriz e bloqueios detalhados.
