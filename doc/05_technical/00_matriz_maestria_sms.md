# 05_technical — Matriz de maestria Master System

Técnicas por domínio. Cada técnica listada aqui é CANDIDATA até ter sido paga com
build + evidência de emulador em algum projeto (`doc/curation/` promove).

> **Versão machine-readable:** `01_registry_maestria_sms.json` (escada por técnica).
> Toda técnica citada aqui PRECISA existir no registry — `audit_mastery_registry.py`
> cruza os dois. Nota dura sem entrada no registry é fato não pago passando por lei
> (foi assim que S05/S06 carregaram números do Mega Drive por semanas).
> **Roadmap:** `02_roadmap_waves.md`. A matriz abaixo é a leitura humana.
> Escada de proficiência: `mapped → incorporada → reproduzível → emulador_provado → default_senior`.
> O nível real de cada técnica está no registry JSON; aqui ficam o conteúdo e a nota dura.

## 1. VDP / tiles BG
| # | Técnica | Nota dura |
|---|---------|-----------|
| V01 | Grid 8×8, pattern table 32 bytes/tile | name table = entrada 16-bit com flags flip/paleta/prioridade (probe `pnt_16bit`, L069) |
| V02 | Metatile 16×16 via camada de índices | economiza name table e lógica de colisão |
| V03 | Scroll global X/Y (regs) + trava 1ª coluna | sem scroll fino por linha nativo |
| V04 | Line interrupt para split de scroll/raster | jitter de Z80: medir estabilidade em evidência |
| V05 | Modos estendidos 224/240 linhas | PAL/alguns SMS2; contrato por projeto |
| V06 | Backdrop color como "índice 0 global" | fade = recarga de paleta |
| V07 | Padrão de tilemap comprimido (STM/ZX7) | descompressão custa CPU fora do frame |

## 2. Sprites
| S01 | SAT 64 entradas; terminador Y=0xD0 | escrever 0xD0 cedo corta processamento |
| S02 | Máximo 8 sprites/scanline | excesso descartado; SMS1 corrompe display |
| S03 | Tamanho global **8×8 ou 8×16** (+ zoom ×2 → 16×16 / 16×32) | misturar tamanhos é impossível. **Correção 2026-08-31 (L006):** esta linha dizia "8×8 ou 16×16" e induziu o erro; `SPRITEMODE_TALL` é **8×16**, e o zoom dobra o PIXEL, não a arte. Arte 16×16 exige metasprite. Gate: `audit_sprite_mode.py` |
| S04 | Metasprites (SMS_addMetaSprite) | composição de tiles por entidade |
| S05 | X é armazenado **sem offset**: X=0 desenha na borda esquerda | **Corrigido 2026-09-01 (L003):** dizia "X+32 / X<32 esconde" — herança do Mega Drive, REFUTADA em emulador (probe `_laboratorio/early_clock`) |
| S06 | `VDPFEATURE_SHIFTSPRITES` (reg 0, bit 3) desloca **8px** à esquerda | **Corrigido 2026-09-01 (L003):** dizia 32px — REFUTADO em emulador (114→106 medido). Sprite em X<8 sai da tela com o bit ligado |
| S07 | Rotação de buffer de sprites p/ reduzir flicker | ordenar prioridades na SAT |

## 3. Paleta / cor
| P01 | 2 subpaletas ×16; BG índice 0 visível, sprite índice 0 transparente | até 16 entradas BG + 15 entradas opacas de sprite; cores distintas dependem da paleta da cena |
| P02 | Cor = código 6-bit (canais 0–3); paleta mestra fixa | sem gradiente suave; fade = troca de paleta |
| P03 | Contraste medido em degraus (luma derivada dos códigos) | gate audit_luma_floor.py |
| P04 | Half-brightness / color add/sub do SMSlib | efeitos sem alpha (não existe alpha) |
| P05 | Ciclos de paleta sincronizados ao VBlank | senão meia paleta velha numa scanline |

## 4. VRAM / orçamento de frame (sem DMA!)
| M01 | Toda transferência em massa DENTRO do VBlank | janela ~4.5ms NTSC; medir, não estimar |
| M02 | Orçamento worst-frame por cena = contrato | doc/13-spec-cenas.md |
| M03 | VRAM layout fixo por projeto (patterns/names/SAT) | decidido no TDD antes de assets |
| M04 | Streaming de tiles entre frames com cota | degrau seguinte sempre medido |
| M05 | Compressão ZX7/aPLib/PSG paged | descompressão compete com gameplay |

## 5. Z80 / SDCC
| Z01 | int = 16-bit signed; char default unsigned (SDCC z80) | armadilha clássica |
| Z02 | Multiplicação/divisão caras (sem HW mul) | tabelas lookup/Q8.8 |
| Z03 | float = software float → PROIBIDO em runtime quente | Q8.8/int16 |
| Z04 | Sem malloc: buffers estáticos, pools por entidade | RAM 8KB total |
| Z05 | fastcall/callee (__z88dk_fastcall etc.) | convenções do header mandam |
| Z06 | Banked code __banked (--codeseg BANKn) | trampolino automático do crt0 |
| Z07 | ISR/NMI: handler curto; trabalho pesado no loop principal | pause = NMI |

## 6. Banking / ROM
| B01 | 48KB linear máximo sem mapper | primeiro alvo de qualquer jogo |
| B02 | Mapper Sega: páginas 16KB, slots 0x4000/0x8000 (FFFE/FFFF) | slot 0x0000 fixo pág 0 |
| B03 | Header SEGA em 0x7FF0 ("TMR SEGA"+checksum+região) | makesms calcula checksum |
| B04 | Código restrito a 32KB; dados bancados desde bank2 | convenção devkitSMS |
| B05 | SRAM via registro 0xFFFC (frame reg) | saves: provar em cartucho/emulador |

## 7. Áudio PSG
| A01 | SN76489: 3 tone + noise; volume/latch por canal | driver padrão PSGlib |
| A02 | SFX vs música: arbitração de canais explícita no TDD | 4 canais só |
| A03 | Samples PSG comprimidos | custo de ROM e timing |
| A04 | YM2413 (FM unit/JP) opcional — nunca obrigatório | jogo tem que funcionar sem FM |
| A05 | Atualização de áudio dentro do frame com budget próprio | medir junto com VRAM |

## 8. Input / timing
| I01 | Joypad portas 0xDC/0xDD; 2 botões + d-pad | leitura direta ou via SMSlib |
| I02 | Pause button = NMI | tratar reset de estado com cuidado |
| I03 | Normalização NTSC(60)/PAL(50) | velocidade de jogo independente de região |
| I04 | Frame counter como relógio mestre | nada de delay loops |

## 9. Estética / produção
| E01 | Pixel art autoral obrigatória; proveniência por asset | audit_provenance.py |
| E02 | Silhueta legível em tela 256×192 com ≤15 cores úteis | model sheet antes do sprite final |
| E03 | Storyboard = planta baixa em pixel ANTES da arte cara | ordem de trabalho de cena |
| E04 | Coreografia medida antes do orçamento fechar | lição curadoria SGDKForge 2026-08-17 |
| E05 | Dark Deco adaptado: contraste alto, luz como recurso escasso | bible artística vincula |

## 10. Verificação
| Q01 | Gates executáveis em TODA transição | tabela em AGENTS.md |
| Q02 | Evidência = boot + gameplay + fps + áudio | 7 eixos simultâneos |
| Q03 | Claims com teto aprovado | audit_claims.py |
| Q04 | Self-check em toda ferramenta de medição | §19 |
| Q05 | Learning loop: JSON + lei numerada + ferramenta | curation-learning.md |
