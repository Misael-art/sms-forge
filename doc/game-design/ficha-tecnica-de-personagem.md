# Ficha técnica de construção de personagens de luta

Use o [modelo editável de personagem](../../SMS_projects/master_of_fighters/doc/ficha_tecnica_personagem_modelo_v1.docx) para abrir a ficha de cada lutador. A primeira página reúne identidade, recursos e repertório. Duplique a segunda para cada ação ou variante que tenha comando, exposição, colisão ou efeito próprio.

A [ficha ilustrada de Alis Landale](../../SMS_projects/master_of_fighters/doc/ficha_tecnica_alis_g6e_v1.docx) preenche o modelo para o capítulo Guardiões de Algol de *Master of Fighters*. A lista rápida reúne os comandos. Nas fichas individuais, cada tira identifica a pose e sua duração. Acerto, defesa e erro têm resultados próprios. As ações com efeitos independentes incluem a trilha do projétil, da invocação ou da vítima.

Em outro jogo, preencha as unidades, os controles, o medidor e os estados definidos pelo respectivo GDD. Registre a arte daquele personagem e associe os resultados medidos à ROM correspondente. O [registro de repertório de Master of Fighters](../../SMS_projects/master_of_fighters/doc/repertorio_alis_hayato.md#ficha-que-acompanha-cada-ação-até-a-rom) descreve a passagem da ficha à prova de cada golpe.

## Publicar uma edição da ficha

Mantenha um Word editável e um PDF exportado dele para cada personagem em produção. Registre no handoff os dois caminhos canônicos e a edição impressa na capa. Na mesma mudança que alterar o contrato de arte ou de jogo, atualize o Word, exporte o PDF e confira o par. O [PDF de Alis](../../SMS_projects/master_of_fighters/out/qa/alis_ficha_r6b/ficha_alis_r6b.pdf) preserva o nome histórico. A capa identifica a edição R8 usada na calibração.

Vincule a identidade, os materiais e a escala ao model sheet aprovado. Para cada ação de um lutador, mostre comando, poses do atlas com exposição e transições, alcance, caixas, contato, guarda, erro e recuperação. Registre custo, dano, pausa de impacto, reação, recuo, queda, sinais de áudio e vídeo, recursos ou ligações de combo conforme o GDD. Distinga o especificado, o exercitado em bancada e o visto no emulador com o SHA da ROM. Em outros gêneros, descreva as ações que o jogador deve reconhecer e suas consequências.

Use o [contrato de Alis R8](../curation/evidence/2026-11-27_ficha/alis-r8.json) como exemplo. Os caminhos são relativos à raiz do jogo. Registre os SHA-256 das duas vias e das imagens aprovadas em **cada ocorrência editada** no corpo do Word. A chave da figura é o ID de desenho em `wp:docPr`. `blip` identifica os bytes da imagem principal e `svgBlip` identifica a alternativa SVG ativa, quando prevista. Confirme a ilustração contra a fonte aprovada antes de registrar o hash. Uma alternativa vetorial intencional precisa representar o mesmo desenho que a imagem principal.

Execute com o LibreOffice e as fontes usados na edição, Poppler no PATH e temporário privado em disco. Aponte para as vias já publicadas. O auditor exporta uma cópia privada e compara a quantidade de páginas, o texto extraído com layout e todos os quadros a 100 dpi. Se divergir, localize a primeira página apontada, confira o exportador e as fontes, corrija o par e repita.

```sh
tools/sms_wrapper/run_host.sh rtk proxy python3 tools/sms_wrapper/audit_character_sheet.py \
  --project SMS_projects/master_of_fighters \
  --contract doc/curation/evidence/2026-11-27_ficha/alis-r8.json
```

Abra o Word e revise as páginas do PDF em tamanho de leitura. Confira cortes de texto, legibilidade das legendas, alinhamento dos pés, ordem das poses e a correspondência entre o gesto ilustrado e a ação descrita. Registre páginas, edição, hashes e decisão. A comparação automática também passa se o mesmo erro artístico estiver presente nas duas vias.
