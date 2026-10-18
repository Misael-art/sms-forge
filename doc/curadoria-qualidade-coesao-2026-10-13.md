# Curadoria de qualidade e coesão — 2026-10-13

## Aplicação ao agente canônico

113 lições e 113 rotas existentes foram revisadas; esta rodada aplica lições
já registradas sem criar IDs duplicados. O checkpoint transversal
`tools/sms_wrapper/.agent/workflows/product-quality-checkpoint.md` relaciona
público/GDD, resposta de input, legibilidade/animação, mix música/SFX, IA/HUD/FX
simultâneos, alvo regional e pior frame. Foi ligado à arquitetura, produção,
slice, review de gameplay e release. Não prevê vendas, diversão ou qualidade
AAA; parecer de agente não é playtest de mercado.

## Correções de código, schema e ensino

- **Sprites:** simulador aceita somente modos físicos 8×8/8×16 e tipos inteiros
  reais, sem coerção de string/float/bool; declara limites de wrap/Y negativo.
  Schema antigo 16×16/X+32 e offset Y do packer foram corrigidos sob
  L003/L006/L128/L129. Dois atores 16×16 normais usam oito entradas SAT totais
  e quatro objetos por scanline comum, corrigindo o custo ensinado na skill.
  Quirks SMS1/zoom e overflow real continuam sem qualificação nesta rodada.
- **FPS:** probe privado compara duas janelas completas ao alvo NTSC60/PAL50,
  com tolerância explícita de até 1FPS e dispersão até 1FPS. 55FPS NTSC ou
  janela ausente reprovam; taxa média não prova cada deadline ou reação do jogo.
  O helper deixa de descartar samples ausentes. Perfil DAP histórico não vira
  aprovação regional da nova rota privada.
- **Áudio:** bit2=1 é branco e bit2=0 periódico; a doutrina/auditor anteriores
  estavam invertidos. Fontes locais PSGlib e BlastEm foram hasheadas. Gerador
  root preserva bit de branco e usa divisor32 para frequência tone; preview
  modela ruído nominal determinístico, sem prometer fidelidade de chip/mix.
  Skills e §§63–64 foram corrigidos e a interpretação antiga preservada como
  supersedida na curadoria L078/L079. Políticas de eventos não aprovam música.
- **Claims:** tetos exigem scope/autor/data/token e texto de teto não vazios;
  UTF-8 inválido não permite aprovação. Gate lexical não julga se o escopo
  realmente autoriza uma frase nem autentica o dono. Gates/eixos históricos
  não substituem checkpoint e evidência atual.

## Arte recente e organização

Os candidatos recentes ampliam L124: autorização por revisão (máscara interna,
transferência entre materiais e contorno são escopos distintos), quadrado sólido
2×2 não é área/bbox, cobertura da máscara não é ausência de cores ilegais,
ownership/material e contorno acrescentado são deltas separados de alpha.
Convergência e zeros de clusters não provam luz/anatomia. Workflows e skills
foram fortalecidos com esses limites; contagens existentes não foram reexecutadas.

Fonte v08.2 e cópia `res/approved_art` têm bytes iguais e decisão source-only
existente, enquanto memory/diretriz/método/registro estavam divergentes. A decisão
e os conflitos foram registrados como reconciliação central, sem fabricar
aprovação de runtime. Não foi encontrada ROM v08.2; a declaração de review
independente por célula não aponta um parecer preservado. Paths antigos e hash
truncado foram registrados para corrigir no lote do projeto. Imagens, PSGs,
documentos locais dos jogos e cópias `.agent` foram preservados.

## Evidência nativa e corpus

Coordenador executou duas sessões Emulicious privadas com fixture diagnóstica
preservada SHA `be21f3686aae5ac9b54c38dc936fca4c52209050b8cff58042588865580e296c`.
Primeira medição59,60/59,77FPS; após correção de robustez, coletor atual mediu
**59,52/59,72FPS**, duas janelas de8s. Sessões encerradas. Revisor nativo
conferiu os hashes atuais, identidade da sessão, payload e ausência dos quatro
processos originais; ele não executou essa captura. Essa prova valida a
medição regional da infraestrutura; não sustenta 60FPS do jogo de luta. PAL
tem controles sintéticos, sem nova execução nativa nesta rodada.

Auditoria sprite:24 casos focados e70 manifestos diagnósticos reais. Áudio:
36 streams mantidos porSHA,11 passam a falhar apenas a política M4 após corrigir
a classificação; isso não é julgamento artístico. Root geradores corrigidos,
mas geradores locais Pulso/MSSF2T ainda precisam migração no lote de projeto.
Mudança de pitch também requer rever testes locais de faixa, sem regenerar
assets automaticamente. A4 tem período254 e picoFFT440Hz no preview.

Revisão independente de áudio encontrou três falhas adicionais de decoder/SFX.
A gramática suportada agora exige tone low+high contíguos e recusa formatos não
modelados antes do WAV; SFX usa ordem temporal. Reteste25/25 passou, sem
qualificar suporte completo PSGlib/hardware.

Subagentes reais auditaram coesão, candidatos visuais, fontes/decoder de áudio e
deltas de FPS/claims. Pareceres iniciais e retestes ficam preservados, sem
transformar leitura independente da captura em execução independente de ROM.

## Fechamento e limites

Evidência em `doc/curation/evidence/2026-10-13_quality_cohesion/`; fechamento
integral no subdiretório `closure`. Curadoria de aplicação:
`doc/curation/2026-10-13_quality_cohesion_application.json`.

O ambiente dispõe de construção/conversão, contratos gráficos, análise de
SAT/patterns, captura privada, input por frames, probes/trace, worst-frame,
áudio e revisão nativa. Existência/selfcheck dessas ferramentas não paga seus
resultados para um jogo. Permanecem abertos EIO Mugen, reconciliação v08.2,
migração de áudio local, comparação musical alinhada, pacing/input da ROM de
produção, compatibilidade física e aceitação por jogadores. Nada foi commitado.

O scan inicial encontrou371arquivos recentes não registrados. Foram selados
como baseline histórico semclassificação/aprovação, incluindo cópiaapproved_art
cuja decisão existente continua no registro de reconciliação. Registroatual:
27artefatos/1176arquivos/1122legados. Isso resolve cobertura de paths, não
retroativamente a reserva de produção nem os conflitos de autoridade.

Fechamento final: **113/113 verificações**, **65/65 ferramentas com self-check**,
learningcapture e doutrina dehardware aprovados. Registryfinal passou após
adoção explícita do legado. O resultado113/113 segue a correção da fixture
válida que tinhaX=256; resultadoinicial112/113 foi preservado. Doc sync
mantém somente dez problemas documentais conhecidos doMugen. Probe opcional
de build deprojeto não foi rodado; jogos/áudio/arte não foram regenerados.
