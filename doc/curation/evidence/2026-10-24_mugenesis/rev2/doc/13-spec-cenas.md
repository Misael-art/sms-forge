# Spec de cenas — luta_mugem_rev2

| Cena | Conteúdo simultâneo | Budget observado | Gatepróximo |
|---|---|---|---|
| Título/menu/options | fundo sólido/texto/cursor/cue | pending | navegação/retorno/input/áudio |
| Seleção/VS |2retratos+fonte+cursor | pending | slots/cores/legibilidade/transição |
| Luta |2atores+HUD+projéteis+sparks+IA+PSG | pending | pilotoarquitetura e worst-frame |
| Treino | luta+overlay/histórico | pending | custo adicional e controles |
| Continue/final | texto/recursosautorizados | pending | timeout/retorno/limpeza |

VDPMode4/192, SMS1/SMS2 alvo declarado; compatibilidadequirks não presumida.
RAM8KiB/VRAM16KiB compartilhada; SAT64/8entradaslinha incluindohidden.
Dois bancos de16cores, P1spritescompartilhada com índice0 transparente. SemDMA.
Layout VRAM/PNT/SAT/patterns, RAM/stack/corredorprobe, ROM/bancos e cotaVBlank
precisam mapa/l​ink e medição da mesmaROM; todos ainda pendentes. 768tiles
residentes do parecer não são capacidadefísicaSMS:512patternsbrutos/16KiB
antes de descontarPNT/SAT; janelas sprite/layout podem restringir mais.

Antes do render: limiteinferior por scanline em poses idle/guard/crouch/jump/
impacto/FX e overlap real; se>8, sprite-only zeroomissões impossível nesse
corte. CompareBG/híbrido/pool/layout e reautoria autorizada. BG não érecurso
gratuito: medir flip/facing/scroll/overlap/prioridade/HUD/palette eVRAMuploads.
Não mascarar falha com P2imóvel, removerFX/IA/áudio ou reduzir poses sem decisão.

FPS:probeprivado2janelas completas NTSC60/PAL50 com tolerância explícita,
pacingdeadline da lógica e input→ação→pose→dano separados. Probesvoláteis
com endereços pós-link/canário, audit_probe_corridor e stacksafemargin.

Estado 2026-10-18 (Lote A): os "Budget observado/pending" da tabela continuam
PENDENTES por definição — trocar par por configuração não é budget. O medido
até agora é o runtime DIAGNÓSTICO v031 (`6f4a3cf5…`): corredor de sondas
77/1547 B, deadlines causais em frames da ROM, quatro relógios
(`out/logs/runs/`), teto `diagnostic_only`. Nenhuma linha da tabela herda
esses números como orçamento; o perfil de produção (Lote B) é eixo separado
seguindo doc/15-tdd.md §Estado.
