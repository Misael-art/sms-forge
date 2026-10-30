# Pendências da engine luta_mugem_rev2 — 2026-10-24

55 itens identificados; nenhum fechado por esta análise. O detalhamento e as dependências estão no JSON de mesmo nome.

Atualização de execução em 27/10: ID01, R01, R05, R06, R09 e S04 foram
reexaminados; todos permanecem abertos. O rebuild isolado identifica seus
insumos, foram corrigidos o tile de fundo e duas falhas do cache de pose, e a
ordem lógica AIR passou em teste C. Dumps de PNT/VRAM/SAT cobrem cinco
fronteiras de uma ROM diagnóstica, não todas as ações. Ainda faltam a
conciliação da ROM nominal, identidade AIR em ROM, coerência de contato e
budget com carga completa. Evidências e SHAs estão no
memory bank do consumidor; a tabela abaixo preserva os critérios de 24/10.

No lote seguinte, a seleção de faces foi exercitada em uma travessia real e o
alias observado de 28 bancos foi eliminado nas fronteiras testadas ao preencher
a imagem para 32 bancos. O manifesto nominal seleciona o corte de 24 bancos
do GDD; o header antigo de 49 bancos é recusado pelo runtime atual.
Nenhum ID foi encerrado: permanecem abertos mapper físico, composição, contato,
cadência e pior quadro sob carga completa. No roteiro medido de ataque, 13 de
30 fronteiras da SAT ultrapassaram 8 sprites por scanline; esse resultado não
generaliza a todas as ações nem identifica por si só o ator omitido.

P0: impede concluir o núcleo/entrega. P1: necessário ao escopo ou à robustez. P2: distribuição e ergonomia secundárias.

| ID | Prioridade | Pendência | Critério de fechamento |
|---|---|---|---|
| ID01 | P0 | Identidade de build e documentos | Recibo do rebuild identifica exatamente o binário e os dados; os documentos descrevem o perfil selecionado. |
| ID02 | P1 | Saúde de armazenamento e reprodução | Fontes obrigatórias legíveis e build/QA reproduzíveis; erro de armazenamento permanece reportado. |
| R01 | P0 | Fundo sólido e residência do tile de BG | Boot e ações mantêm fundo sólido; dumps demonstram ausência de sobreposição indevida. |
| R02 | P0 | Todas as composições reais | Manifests e SAT viva respeitam 8 entradas por linha e 64 totais, com todos os papéis exigidos cobertos. |
| R03 | P0 | Recuperar os movimentos bloqueados | Normais, especial e KO exigidos executam integralmente; qualquer tradeoff tem decisão explícita. |
| R04 | P0 | Facing e dados corretos em ambas as orientações | Vídeo e comparação fonte/pattern/SAT cobrem faces, troca de lado e bordas sem deslocamento indevido. |
| R05 | P0 | Streaming com deadlines e sem starvation | Serviço aos dois lados, prazo máximo medido, sem publicação parcial, starvation ou perda de elementos de um tick. |
| R06 | P0 | Publicação coerente de pose e colisão | Trace e vídeo do mesmo frame explicam o contato visível; nenhuma pose futura causa dano invisível. |
| R07 | P1 | Slots e namespaces neutros | Os quatro pares são gerados por configuração, com fonte, símbolos e hashes corretos e núcleo C idêntico. |
| R08 | P1 | Paleta compartilhada e cor por material | Readback da paleta confere com cada pool/META; cores e silhuetas permanecem legíveis em movimento. |
| R09 | P0 | Worst-frame com carga representativa | Janela contínua completa sem DAP, done=1 e zero overflow, incluindo HUD, FX e PSG na mesma ROM. |
| R10 | P0 | Cadência e pacing regional | Duas janelas SMRT por região suportada, tolerância declarada e AIR/input/pose dentro dos prazos aceitos. |
| R11 | P0 | Mapa VRAM/PNT/SAT e backend | Plano confere com dumps; nenhuma região se sobrepõe indevidamente; movimento e overlap funcionam. |
| R12 | P1 | RAM, stack, probes e canários | Corredor válido e margem de stack medida sob stress, sem corrupção de sondas ou dados. |
| R13 | P1 | Capacidade e ownership do mapper | Bancos-limite têm dados distintos acessíveis; referências permanecem válidas e não há overflow do banco fixo. |
| S01 | P0 | Dependências common e FightFX | Nenhuma dependência obrigatória é tratada como suporte por proxy não validado. |
| S02 | P0 | Matriz de alcance e capacidades | Matriz fonte/IR/gerado/consumidor/teste/ROM sem unsupported obrigatório oculto. |
| S03 | P0 | Lowering CNS AOT para C/Z80 | Um golpe completo executa predicado, estado, animação, contato e recovery por dados, sem hardcode de personagem. |
| S04 | P1 | Ordem e temporalidade CNS/AIR | Positivos e negativos nos limiares; AIR com identidade em N+1 fronteiras e execução observada na ROM. |
| S05 | P1 | HitDef e vulnerabilidade completos no perfil | Casos por campo demonstram dano, guarda, imunidade, juggle e repetição coerentes no perfil aceito. |
| S06 | P1 | Hitstun, blockstun, queda, getup, win | Ciclos de dano, defesa, ar/chão e KO recuperam estados válidos e não deixam ataques ou controle presos. |
| S07 | P1 | Hitstop, slowdowns e shake finitos | Duração observada em frames, encerramento correto em round/cena e ausência de congelamento residual. |
| S08 | P1 | Projéteis e especiais | Spawn CNS, velocidade, lifetime, colisão, guarda, dano e despawn funcionam, incluindo concorrência medida. |
| S09 | P1 | Explod, spark e Helper alcançável | Eventos corretos, overflow explícito, expiração e reset seguros; custo incluído no orçamento. |
| S10 | P1 | Power, supers, cancels e combos | Limiares de recurso e janelas passam em testes fonte/ROM, com efeitos e custos corretos. |
| S11 | P1 | CLSN e distância dinâmica | Comparação fonte/gerado/ROM nos dois lados dos limiares, sem caixas de pose futura ou ajuste cego da sola. |
| S12 | P1 | Física e limites numéricos Z80 | Bordas, landing e push não causam teleporte, suspensão ou perda de pivô. |
| IN01 | P1 | Mapeamento de dois botões por personagem | Todos os movimentos exigidos são acessíveis ou têm tradeoff aceito; thresholds da fonte, gerador e C coincidem. |
| IN02 | P1 | CMD, prioridade e onepulse | Testes diferenciais e de mutação cobrem buffers/soltura; acorde não mapeado não dispara normal indevido. |
| IN03 | P1 | Humano×humano e seleção de modos | Humano×humano, humano×IA e IA×IA funcionam nos quatro pares sem chamadas diretas de dano ou estado. |
| IN04 | P1 | IA responsiva e dificuldade | Mudança de dificuldade é observável; defesa, canto e projéteis não geram loops sem saída. |
| IN05 | P0 | Input→ação→pose→contato | Prazos por ação são rederiváveis de trace e vídeo; ACK da ponte não é usado como prova de consumo. |
| G01 | P1 | Round, match, timeout e empate | Todos os caminhos e bordas do timer funcionam com resets consistentes de HUD, áudio e objetos. |
| G02 | P1 | Pausa e transições com owners | Cada aresta é exercitada e repetida; retorno sem tecla presa, cache stale ou recurso abandonado. |
| G03 | P1 | HUD e mensagens | HUD acompanha combate, recupera redraw após recusa e cabe no pior quadro com legibilidade nativa. |
| G04 | P1 | Título, menus, seleção, VS e finais | Matriz de entrada/retorno completa por input real; retratos e demais recursos rastreáveis. |
| G05 | P1 | Ferramentas de treino | Opções atuam na ROM e a lista usa os mesmos dados do matcher; reset limpa combate e objetos. |
| G06 | P1 | Configuração em RAM da sessão | Configuração sobrevive à reentrada; captura/soltura não vaza para combate; categorias vazias são explícitas. |
| A01 | P1 | Transcrição/autoria PSG | Cada evento integrado tem asset PSG, hash, canal e função identificada no perfil aceito. |
| A02 | P1 | Driver e arbitragem integrada | Mix sob carga medido e ouvido; mute, pausa, stop e reentrada não deixam canal preso. |
| A03 | P2 | Fila e catálogo de eventos | Canal ocupado, wrap, mute, pausa e expiração testados; nenhuma classificação de voz universal indevida. |
| A04 | P1 | Música e identidade auditiva | Captura privada alinhada, proveniência, gates de sinal/PSG e revisão auditiva; pico positivo sozinho não aprova música. |
| RE01 | P1 | Core canônico compartilhado | Mesmo core atende quatro pares e outro consumidor; mudanças de dados não exigem editar C do núcleo. |
| RE02 | P1 | Contrato intermediário neutro | Admissão antes do runtime rejeita contagens, índices e referências inválidos, sem truncamento ou malloc. |
| RE03 | P1 | Adaptador e consumidor autorais | Interação jogável por dados sem editar o core; arte final tem proveniência e fixture de debug não vira entrega artística. |
| RE04 | P1 | Schema, ABI, features e limites | C compatível compila; ABI, feature ou contagem incompatíveis falham antes de publicar ou executar. |
| RE05 | P1 | Receita reproduzível e publicação | Rebuild limpo reproduz dados/ROM; on/off/repeat/recusa e falha injetada preservam a geração anterior. |
| RE06 | P2 | Instalação, upgrade e handoff | Instalar fora do checkout, gerar/buildar/QA em consumidor limpo; upgrade e rollback preservam customizações. |
| Q01 | P1 | Regressão independente do acervo legado | Contagem e escopo da suíte são publicados; dependência ilegível continua registrada e não qualifica rev2. |
| Q02 | P1 | Matriz de pares, modos e bordas | Pedidos V2 nativos com baseline, ROM exata, mídia e cobertura do domínio suportado. |
| Q03 | P1 | Admissão e recuperação sob falha | Negativos rejeitados com diagnóstico e preservação do estado; recuperação sem omissão silenciosa. |
| Q04 | P1 | Soak e stress prolongados | Janelas registradas sem corrupção, deadlock, starvation ou glitch observado no domínio testado. |
| Q05 | P1 | Revisão visual, animação e gamefeel | Review independente e conferência do coordenador em mídia fresca; decisão humana de arte e fidelidade. |
| Q06 | P0 | Sete eixos e época delivery na mesma ROM | Todos os gates aplicáveis passam, com vínculo asset→ROM, frescor e revisão; AAA não é veredito automático. |
| Q07 | P1 | Limites dos instrumentos de medição | Self-checks negativos e calibração real; SHA explícito; nomes distintos e snapshot isolado não aprovam conteúdo ou mínimo. |
