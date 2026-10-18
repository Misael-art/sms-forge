"""`.snd` MUGEN (PCM) -> PSG: nada e portavel direto; o que sai e esboco de evento PSGlib.

O VDP do SMS nao tem PCM nem DMA de audio (so o PSG YM2413 interno, 3 tones + ruido;
PSGlib.h e a autoridade do formato de eventos). Classificacao honesta medida na S3:
33/33 sons PCM -> `manual` com esboco, ou `unsupported` quando nem uso ha.
"""
from __future__ import annotations

SFX_MAX_SECONDS = 0.35        # acima disso vira música/BGM (outra decisão de reautoria)


def classify(sounds) -> list[dict]:
    """Linhas de relatório: um registro por som do pacote, com esboço PSGlib quando útil."""
    rows = []
    for s in sounds:
        if s.error:
            rows.append({"id": f"{s.group},{s.sample}", "classe": "unsupported",
                         "motivo": f"snd-invalido:{s.error}"})
            continue
        dur = s.seconds
        if dur > SFX_MAX_SECONDS:
            rows.append({"id": f"{s.group},{s.sample}", "classe": "unsupported",
                         "motivo": f"pcm-longo>{SFX_MAX_SECONDS}s (candidato a BGM autoral, nao a porta)"})
        else:
            rows.append({"id": f"{s.group},{s.sample}", "classe": "manual",
                         "motivo": "pcm>psg",
                         "esboco": f"PSGSFX de ruido/ton {round(dur * 50)} frames; canal A ou B; "
                                   f"declarar no manifest de audio antes de gerar"})
    return rows
