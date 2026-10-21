# Curadoria visual — 2026-10-13

Auditoria somente leitura de cinco candidatos locais recentes, dos documentos operacionais, do registro central e dos workflows. Não alterei o repositório, não executei testes ou emulador e não fiz revisão estética das imagens.

## Resultado principal

Há aprendizado válido para ampliar **L124**, sem duplicar a doutrina existente. A rota de autorização evoluiu: primeiro o dono proibiu repintura automática; depois autorizou máscaras por material; por fim autorizou reclassificação entre materiais e contorno. Essas autorizações são por revisão e escopo, não uma licença geral para o algoritmo decidir a arte.

**L127** continua cobrindo revisão e promoção de model sheets. A folha de animação v08.2 possui uma decisão própria de aprovação, que não aprova runtime ou gameplay.

## Novidades aplicáveis

- **Bloco sólido 2×2:** área ≥4 e bbox ≥2×2 não bastam; um L ou diagonal pode passar essas duas métricas sem conter um quadrado sólido. Esse mínimo é requisito específico deste asset, com exceções para detalhes aprovados, não regra física universal.
- **Convergência:** o processo de um componente por vez e recálculo evita a oscilação descrita no método anterior. Registrar limite, empates, componentes sem vizinho elegível e critério de parada. Ponto fixo não prova sombreamento artístico.
- **Ownership:** preservar alpha e contorno original não significa preservar os materiais ou separações internas. A v08.2 relata 863 novos pixels com índice de contorno e 23.236 alterações de cor; medir isso separadamente.
- **Máscaras:** zero cores proibidas dentro da máscara não prova que toda a região material foi classificada corretamente. A recuperação de 1.014 pixels avermelhados da franja é evidência desse limite. Revisar máscara, franja e fronteiras junto com a imagem fonte.
- **Exceções semânticas:** óculos dourados autorizados (85 pixels) e haste branca contínua de 1 pixel (1.245 pixels) precisam de papéis e máscaras próprios; não submetê-los cegamente ao mesmo limiar de clusters do tecido.

## Integridade e estado atual

1. A cópia aprovada em `res/approved_art/...v08_2_approved.png` existe e é byte a byte idêntica à candidata. SHA: `4e557095dcafd4f11a0369e6e993ad4fa99497ab529509dedd2445f83bcf89d8`.
2. A decisão `doc/decisions/dr-social-animation-source-v08_2_owner_approval.json` aprova a fonte artística e a conversão diagnóstica. Memory bank, diretriz e método do candidato ainda dizem pendente/sem promoção; o registro central não contém v08.2 e deixa o head `animation_source/main` nulo. É necessário conciliar esses registros sem fabricar aprovação de runtime.
3. O fluxo consolidado ainda apresenta a ROM v5 e a fonte antiga como atuais. São evidências históricas, incompatíveis com a retomada pela matriz model sheet v4 e folha nova.
4. Os outputs do relatório v08.1 apontam uma pasta antiga terminada em `_masks/`, enquanto os arquivos estão em `_masks_candidate/`.
5. O `mask_manifest.json` v08.2 ainda descreve cleanup somente dentro da própria máscara, mas método/contrato vigente permite cruzar materiais e contorno. Manifesto e método precisam concordar.
6. O hash v6 no candidato de 2026-10-11 foi truncado para 63 caracteres. O arquivo presente tem SHA completo `8445a0fd47700a38a1fb1ed25ff67c8b22aa2086551d6fe7a54155321a41455f`. As demais nove referências de imagem conferidas correspondem aos bytes presentes.
7. A afirmação `independent_per_cell_audit: pass` não referencia um artefato independente preservado. Não encontrei relatório de revisão independente desta sprite sheet nas áreas inspecionadas; isso não invalida a decisão registrada do dono, mas não substitui aquele eixo.
8. A pasta diagnóstica v08.2 contém um projeto preparado, sem ROM `.sms` no momento da leitura. Não há prova de build/emulação/FPS/áudio a herdar das ROMs antigas.

## Aplicação sugerida

- `art-review.md`: autorização de edição por revisão, máscara e fronteira; dupla passagem visual, critério de cluster e exceções; deltas de material e contorno.
- `sms-pixel-translate.md`: separar conversão técnica de repintura; máscaras heurísticas como candidatas; nunca confundir legalidade da paleta com papel semântico.
- `sms-visual-excellence.md`: tratar zeros de clusters e vazamentos como métricas limitadas; manter a revisão de luz, anatomia, identidade e leitura no tamanho nativo.
- `artwork-to-rom-lifecycle.md`: distinguir fonte aprovada em `approved_art` de recurso integrado; vincular a nova folha por SHA antes da conversão e gerar nova prova de runtime.
- `artifact-organization.md`: selar máscaras, logs, relatórios e emendas por hash; conciliar decisões, heads, paths e memória antes de iniciar outro ciclo.

## Limites

As contagens de pixels e clusters vieram de relatórios existentes; não executei novamente os algoritmos. Foram lidos código e documentos e recalculados os hashes de evidência. A autenticidade da decisão humana e o julgamento artístico não são verificáveis por esta auditoria. Os 67 arquivos fonte e as dez verificações de referências estão registrados em `art-findings.json`.
