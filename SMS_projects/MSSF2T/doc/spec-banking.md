# Spec — Banking no MSSF2T (48 KB Sega mapper)

> Preparada em 2026-09-08. **Fora da execução do ciclo atual** — entra só com
> aprovação humana explícita (cerimônia de curadoria: `curation-mode.md`).
> Gatilho: ROM v085 tem **484 B livres** (fim da `_CODE` em 0x7E1C); o teto
> real do `makesms` é 0x7F80 (reserva 0x7F80–0x7FFF). Arte autoral nova +
> trilha completa + frames de animação extra não cabem sem banking.

## Objetivo
Abrir ~32 KB de espaço para dados (tiles de lutadores/palco, streams PSG)
sem tocar na lógica de jogo, usando o **Sega mapper** padrão (slots: 0x0000
não-bancado, 0x4000 slot 1, 0x8000 slot 2).

## Decisões de projeto propostas
1. **Dados em banco, código linear.** Tiles e música movem para páginas
   `BANK1+`; código e `data` quente (P[], g_*, probe) ficam nos primeiros
   32 KB. Nenhuma função bancada no primeiro passo — `__banked` só se o
   código crescer acima de ~30 KB (não é o caso: `_CODE` termina em 0x7E1C
   com dados dentro; movendo os dados, o código sobra < 20 KB).
2. **O que vai para banco (por ordem de ganho):**
   - `inc/*.h` de tiles dos lutadores (12 folhas × ~832-1024 B ≈ 11 KB);
   - `stage_ken_dock_tiles` (2.976 B);
   - streams de música (917 + 145 + 49 + SFX ≈ 1,2 KB);
   - fonte (1.376 B) fica linear (HUD toca todo frame).
3. **Leitura em runtime:** `SMS_mapROMBank(n)` (SMSlib.h:65+, autoridade #8)
   antes do stream de troca de pose e antes do `PSGPlay`; restaurar o banco
   após o stream (padrão `SMS_saveROMBank`/`SMS_restoreROMBank`).
4. **Build:** `build_inner.py` ganha `-Wl-b_BANK1=0x8400` (…`BANKn`), flags
   `--constseg BANK1` nos objetos de dados e um inventário declarado de qual
   segmento mora em qual banco — **mudança no wrapper é zona de curadoria**
   (bateria completa + aprovação + memory bank). O `crt0_sms` já inicializa
   os registradores de mapper ([0xFFFD]=0, [0xFFFE]=1, [0xFFFF]=2).
5. **Probe e probe-map intocados** (0xC7xx é RAM — banking não afeta).

## Efeitos colaterais aceitos
- Rebuild muda o SHA → **re-selagem completa** (cadeia única: capturas →
  selo, L064) e re-atualização do `rom_asset_binding.json`.
- `measure_worst_frame` re-medido depois (mapROMBank consome ciclos do
  VBlank; o streaming bancado troca banco + dados no mesmo VBlank).

## Estimativa honesta
1 ciclo de curadoria (build_inner + bateria) + 1 ciclo de projeto (mover
dados, gates de runtime) + re-selagem. Risco médio: o makesms/linker do SDK
documenta o fluxo (`sdk/README.md`, seção "Comandos canônicos"), mas o
caminho não tem precedente neste workspace — primeiro projeto bancado.
