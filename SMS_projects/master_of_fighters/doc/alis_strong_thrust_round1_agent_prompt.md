# Master of Fighters — primeira rodada da estocada forte de Alis

Implemente uma estocada forte jogável de **Alis Landale** no Master System,
com sprites autorais, **botão 1 segurado** e **Hayato de Kenseiden** em guarda
na tela como oponente de referência. Entregue uma ROM candidata pronta para
inspeção e o material para o proprietário e o coordenador avaliarem escala,
alcance, fluidez e fidelidade. Feche o percurso de arte a ROM nesta rodada.

Trabalhe no checkout existente `/home/misael/Projects/SMSForge`, em
`SMS_projects/master_of_fighters`. Leia os dois `AGENTS.md`,
`doc/10-memory-bank.md` e `doc/duel_reach_reference_v2.md`.
Os demais caminhos `doc/`, `.mddev/`, `data/` e `out/` são relativos ao
consumidor. Preserve o trabalho local e o recorte aprovado de Hayato.
Use a guarda original identificada em
`.mddev/hayato_short_cut_timing_only_v7_left.json` e uma build candidata do
consumidor existente.

## 1. Desenhe e teste o gesto

- Use a concept v4 da Alis para identidade, roupa e equipamento. A prancha
  aprovada do elenco dá **75 U para Alis e Hayato**. Use a referência de
  **68 px em pé** da régua v2 para calibrar o estudo. Compare vistas
  laterais, com chão e pés de apoio marcados, e mantenha a escala entre
  poses. Registre altura corporal, silhueta equipada e dimensões de espada
  e escudo à parte. A guarda flexionada de Hayato tem 58 px até o cabelo
  e 66 px de silhueta com katana. Esses valores descrevem a pose dele.
- Compare a espada curta e a katana no mesmo ângulo e escala. Confira
  empunhadura, ponta, rotação e fixação do escudo. Use as projeções da régua
  v2 como diagnóstico. **O alcance de 36 px da v1 foi retirado.** Derive o
  alcance desta rodada do desenho lateral produzido.
- Faça a guarda e a sequência **preparação → estocada → recolha → guarda**.
  O olhar acompanha o rival, o corpo transfere o peso com apoios legíveis,
  o escudo participa do gesto e o retorno assenta sem salto de posição.
  Use SNK e CPS3 como referência de expressão, clareza de silhueta e ritmo.
  Revise primeiro as poses-chave e o tempo em 1× e 4×. Escolha quadros e
  exposições pelo que a animação pede e registre-os no contrato da ação.
  Guarde os desenhos-fonte, a procedência e os comparativos.

## 2. Implemente o comando e a cena

- Na candidata, o P1 dispara a estocada uma vez quando a pressão contínua
  do botão 1 atinge um limiar provisório em ticks. Segurar até o fim da
  recuperação deve produzir uma única execução. Soltar rearma o comando.
  Um toque breve fica abaixo do limiar do forte. Preserve o normal fraco
  onde estiver ligado na build e registre se essa ação ainda estiver
  pendente. O limiar escolhido é para este piloto. Implemente a entrada no
  loop real com guarda estável em repouso.
- Ponha Hayato em guarda e deixe um caminho simples para reproduzir **perto,
  no limite e fora do alcance** na mesma candidata. Registre como selecionar
  cada distância e conferir o espelho. Por pose, meça pivô inicial e atual,
  mão, ponta, altura e borda do tronco-alvo na mesma altura. Exponha no
  diagnóstico da ROM a janela ativa e a leitura de alcance. Se o consumidor
  já oferecer resolução de contato aplicável, exercite-a. Identifique
  separadamente projeção visual e resultado de colisão observado.
- Reutilize `prepare_authored_sprite_sample.py`, a conversão e o consumidor
  existentes conforme o TDD. Compile via wrapper SDCC + devkitSMS. Verifique
  a paleta P1 comum, limites de VRAM e SAT, o pico de até 8 objetos por
  scanline e o pior frame com os dois atores presentes. Ao fechar o
  orçamento, meça também o degrau seguinte conforme o projeto. Se a
  composição estourar, identifique a pose e a linha e corrija a causa
  preservando a escala e a leitura.

## 3. Entregue a candidata e as provas

No Emulicious em sessão privada, valide a ROM pelo SHA exato. Use entradas
em frames VDP e prove no estado da ROM o toque breve, o limiar menos um
tick, o limiar, o limiar mais um tick, a pressão longa, o retorno à guarda,
a soltura e a segunda execução. Mostre as três distâncias e as duas faces.
Verifique input, lógica e apresentação em conjunto. Use os medidores com
self-check e registre o alvo de 60 FPS, piso de 58 sem arredondar em cada
janela válida, e pior frame medido sob a carga do trecho conforme §133.
Registre a sessão e confirme o encerramento.

Entregue **ROM `.sms` com SHA-256 e instruções de teste manual**, fontes e
configuração reproduzível, prancha lateral do par em 1× e 4×, vídeo do
framebuffer à velocidade normal e relatório com medidas por pose, entrada,
resultado de alcance e desempenho. Inclua, para curadoria, as tentativas
que falharam, o ajuste que resolveu cada falha e a evidência comparativa.
Indique separadamente o que passou, o que falhou e o que ficou pendente de
validação. Atualize o handoff do projeto com os caminhos da candidata e das
provas. O julgamento artístico cabe ao coordenador e ao proprietário.

## Continuação após a quarta revisão

Retome a mesma rodada até uma ROM candidata com provas vinculadas ao mesmo
SHA. Leia `AGENTS.md` da raiz e do projeto, memória, GDD/TDD, a régua v2,
o parecer de coordenação atualizado e o roteiro de QA. Preserve o checkout e
o trabalho local; use a concept v4 e a guarda v7 aprovada de Hayato.

1. **Feche as chaves.** Reaproveite a direção da guarda e da extensão. Calibre
   o corpo pela referência neutra de 68 px e pela relação 75 U : 75 U,
   comparando segmentos, postura e chão; use um fator por lutador em todas
   as poses. A prancha com fator 1/10 é só hipótese. Compare em 1× e 4×
   as duas chaves com Hayato, marcando apoios, pivô, mão, base e ponta da
   lâmina. Compare as duas armas no mesmo ângulo e escala; registre corpo,
   espada e escudo separadamente. A construção interna do escudo é hipótese
   e a mão pode ficar oculta naturalmente.
2. **Corrija o que chega à conversão.** A máscara atual preservou o exterior,
   mas não mudou a máscara binária para limiares ≥25. Determine onde o defeito
   sobrevive na extração e na paleta escolhidas; corrija as regiões necessárias
   com máscara verificável ou redesenho autoral delimitado. Registre hashes,
   alterações fora da máscara, tentativas e comparativos sobre fundos claro
   e escuro, antes e depois da conversão. Não trate zero alterações externas
   como prova de melhora visual. Preserve as tentativas anteriores.
3. **Faça o gesto funcionar em movimento.** Registre por pose a âncora de
   apoio, pivô e avanço corporal separadamente; reavalie a hipótese de avanço
   zero. Use a mesma guarda para fechar o ciclo. Assista primeiro ao esboço
   normal e use o lento para localizar antecipação, saída, trajetória da
   mão/base/ponta, apoio e recolha; refine desenho e duração conforme o que
   observar. Mantenha escala corporal, comprimento da espada e construção do
   escudo coerentes. Escolha a quantidade de desenhos pelo gesto e registre
   as exposições; valide o resultado novamente no framebuffer.
4. **Integre e prove o comando e o alcance.** Reutilize o conversor e o
   consumidor oficiais. Ligue a arte da Alis e Hayato em guarda à mesma
   candidata; não use o seletor com um par histórico como substituto. Mantenha
   o limiar provisório de 12 leituras, ação única por pressão e rearme na
   soltura. Preserve o normal fraco onde já estiver ligado e documente seu
   estado. Audite `C7F9` pose, `C7FC` pressão, latch/contador e corredor.
   Na ROM, teste toque, 11/12/13 leituras, pressão longa, soltura, retorno e
   segunda execução, além do limiar na última leitura da recuperação; meça
   aperto→disparo→primeira pose visível→extensão e registre a resposta.
   Implemente seleção de perto/no limite/fora e duas faces. Por pose, meça
   avanço, mão, ponta, altura e borda do tronco-alvo na mesma altura. Derive
   o alcance do desenho; os 36 px antigos foram retirados. Mostre janela
   ativa e leitura de alcance. Se houver resolução de contato aplicável,
   exercite-a e separe colisão observada de projeção visual.
5. **Valide e entregue.** Reavalie carga, memória, I/O, temperatura e
   concorrentes antes de operações pesadas; preserve outras tarefas. O
   wrapper anteriormente falhou na rota de áudio, que precisa de diagnóstico
   e correção pela infraestrutura oficial sem alterar a sessão pessoal. Com
   margem, compile via wrapper SDCC/devkitSMS, confira P1, VRAM, SAT e ≤8
   objetos por scanline, pior frame e degrau seguinte. No Emulicious privado,
   use instrumentos com self-check, SHA e sessão, valide controles, distâncias,
   faces e desempenho real: alvo 60 FPS, cada janela válida ≥58 sem arredondar,
   conforme §133. Confirme cleanup. Entregue ROM `.sms` e SHA-256, instruções
   manuais, fontes/configuração reproduzíveis, pranchas 1×/4×, vídeo normal do
   framebuffer e relatório de entrada, alcance, desempenho e retrabalho.
   Atualize o handoff e indique o que passou, falhou ou permanece pendente.

Continue o trabalho leve independente enquanto aguarda margem; não encerre
após um relatório ou uma única etapa se houver trabalho seguro restante.
Se o ambiente realmente impedir a candidata, preserve evidências e registre
o bloqueio exato, sem alegar desempenho, qualidade ou colisão não observados.
