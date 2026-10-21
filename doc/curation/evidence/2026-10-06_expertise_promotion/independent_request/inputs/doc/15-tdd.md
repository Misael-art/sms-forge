# 15-tdd — laboratorio_01

> Arquitetura técnica. FSM, memory pool, ownership, layout de VRAM — decidido ANTES dos assets.

## Layout de VRAM (fixo por projeto)
| Região | Endereço | Uso |
|--------|----------|-----|
| BG patterns | 0x0000 | 256 tiles máx |
| BG name table | 0x3800 | 32×28 |
| Sprite patterns | 0x2000 | 256 tiles |
| SAT | 0x3F00 | 64 entradas |

## Entidades
- Pool estático de N entidades (sem malloc).
- FSM global: BOOT → TITLE → GAME → PAUSE(NMI) …

## Orçamento de frame (contrato, não otimização)
- Janela VBlank NTSC ≈ 4.5ms. Toda transferência em massa dentro dela.
- Worst-frame medido: (pendente — primeira medição real)

## Bancos de ROM
- v1: 48KB linear. Mapper só quando necessário e medido.
