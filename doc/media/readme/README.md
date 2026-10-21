# Galeria de desenvolvimento — SMSForge

Seleção editorial de capturas de emulador para o README público, preparada
em **18/10/2026**. Todos os projetos permanecem em desenvolvimento.

Esta pasta concentra as mídias da página. Ela não altera os assets dos jogos,
não substitui os registros de produção e não promove evidências históricas
para o build atual. O [manifesto](manifest.json) registra caminhos de origem,
hashes, recortes de tempo, transformações e limites de cada arquivo.

## Capturas de execução

| Mídia | Origem | Apresentação |
|---|---|---|
| [MSSF2T](mssf2t.gif) | `MSSF2T/out/evidence/recipe_combate.mp4` | Trecho 10–18 s, combate no cais. |
| [Kage Matsuri](kage-matsuri.gif) | `kage_matsuri/out/evidence/recipe_combate.mp4` | Trecho 13–21 s, movimento e combate. |
| [Arena Nocturna](arena-nocturna.gif) | `arena_nocturna/out/evidence/arena_transition_final_v1.mp4` | Trecho a partir de 2,3 s da atração automática; não prova controle humano. |
| [OpenBOR SMS](openbor-sms.gif) | `openbor_sms_rev1/out/evidence/m6/sessions/05030d2243d64962b6a1773278be8e29/m6_jump.mp4` | Pulo do piloto M6; vídeo original produzido por stepping. |

Os caminhos da tabela são relativos a `SMS_projects/`. Os quatro registros
originais de captura foram copiados sem alterações para `records/`.
Os vídeos originais permanecem nos seus diretórios de evidência locais;
o repositório publica os derivados leves e os registros de origem.

### Como os GIFs foram produzidos

- Fonte: somente o framebuffer gravado pelo Emulicious, com canvas de 256×192.
- Trechos consecutivos do vídeo; sem montagem de poses ou geração de pixels.
- Exportação em 512×384 por nearest-neighbor, taxa de 15 FPS e paleta GIF.
- Sem áudio. O loop volta ao início do trecho e não representa uma transição do jogo.
- Filtro FFmpeg e hashes dos arquivos de entrada/saída constam no manifesto.

Os GIFs são previews editoriais: a redução temporal e a conversão de paleta
não servem para auditar flicker, fidelidade de cor, latência ou FPS. Os registros
legados de MSSF2T, Kage Matsuri e Arena Nocturna não possuem hash
de ROM no próprio JSON de vídeo; o manifesto mantém esse campo nulo. Não foi
deduzida identidade de ROM a partir do binário que existe hoje no diretório.

## Capturas diagnósticas

### MUGEN rev2

[PNG](mugen-rev2.png), copiado byte a byte de
`SMS_projects/luta_mugem_rev2/out/evidence/m4_ryu_ken/det120_v025_r1.png`.
ROM v025, SHA-256 `bd144ee613c0ed1469f933ee255d06a435ee5045b3b10f60266e06e903d71f3f`.
O mesmo hash de PNG aparece na repetição A/B preservada em
[records/mugen-rev2.log](records/mugen-rev2.log).

A imagem mostra apenas um ator renderizado sobre fundo preto. É evidência
diagnóstica de framebuffer, não de uma luta completa ou de render simultâneo
resolvido. Não houve nova execução do emulador para preparar esta página.

### Master of Fighters

[PNG](master-of-fighters.png), copiado byte a byte da pose `render_ID01.png`
da revisão diagnóstica v10. O [registro original](records/master-of-fighters.json)
vincula a captura à ROM
`41879e38c8a83caec07bd97e9208ca08f00fe35ec1e927ff31feab4eb7a3c8cc`.

A ROM compara uma pose de Dr. Social com uma fonte artística histórica,
posteriormente substituída. A imagem comprova aquele exercício de conversão;
não representa arte final aprovada, combate jogável ou a direção artística atual.

## Medição separada da apresentação

OpenBOR M6: ROM
`76cdbee3f10a58a07199b9012ff6dbe53df372d7532d6a8aa324089824425e73`.

- [Runtime](records/openbor-runtime.json): três janelas de execução contínua,
  59,48 / 59,66 / 59,78 FPS.
- [Worst-frame](records/openbor-worst-frame.json): janela de 3.000 quadros,
  `vovf_delta=0` no cenário medido.
- [Índice M6](records/openbor-m6.json): declara os casos, os artefatos e as
  pendências de áudio, PAL e detecção integral de glitches. Seus caminhos
  internos continuam relativos ao diretório de evidência original do projeto;
  os demais artefatos desse índice não são republicados nesta galeria.

Esses registros foram preservados como evidência histórica. O vídeo por
stepping e o GIF derivado não medem velocidade em tempo real. Não se herdam
essas medidas para outras ROMs ou projetos.

## Manutenção

Para trocar uma imagem, selecione uma captura real, confira o escopo e a
origem, mantenha o registro da versão e atualize o manifesto desta pasta.
Não use mockups, concepts, poses recompostas ou screenshots de outro jogo
como se fossem execução do consumidor. Preserve as evidências originais nos
projetos e descreva o estágio mostrado na legenda pública.
