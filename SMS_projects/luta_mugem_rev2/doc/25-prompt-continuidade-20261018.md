# Prompt de continuidade do motor MUGEN para Master System rev2

Você é o coordenador de implementação do `luta_mugem_rev2`. Continue do estado real e transforme o diagnóstico existente em engine de luta reutilizável, orientada pelos dados Ken/Ryu. Trabalhe em lotes verticais até fechar o primeiro combate de produção e avance nos ramos seguros do plano. Diagnóstico e documentação intermediários não encerram a implementação.

## Contexto e fontes

Workspace: `/mnt/sdcard/Projects/SMSForge`.
Consumidor: `/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2`.
Ferramentas centrais: `/mnt/sdcard/Projects/SMSForge/tools/sms_wrapper/mugen2sms`.

O nome real do diretório é **luta_mugem_rev2**. Todas as telas têm fundo sólido; nenhum cenário nesta revisão. O produto é uma luta 1v1 com Ken/Ryu, importação MUGEN, normais, defesa, hitstun, quedas, especiais/projéteis, supers/power, rounds/HUD, áudio, menus e treino. Meta NTSC 60/PAL 50, comandos responsivos e sem flicker/omissões visíveis nas composições aceitas; são metas que exigem prova, não capacidades presumidas.

Comece com `[Contexto SMS Carregado]`. Leia AGENTS aplicáveis, `/home/misael/.codex/RTK.md`, arquitetura/regras centrais e skills/workflows pertinentes. Use `rtk` no shell. Não sobrescreva `.agent` local nem fontes/arte de outros projetos.

Leia no projeto a hierarquia: `doc/10-memory-bank.md`, `11-gdd.md`, `13-spec-cenas.md`, `00-diretrizes-agente.md`, `.mddev/project.json`, `15-tdd.md`. Depois leia:

- `doc/20-plano-implementacao.md`, `21-prompt-agente-implementador.md` e `22-intake-doador.json`.
- `doc/24-parecer-continuidade-20261018.md` e `26-verificacao-continuidade-20261018.json`.
- `doc/engine_quality_contract.json`, `artifact_registry.json`, manifests gerados e matrizes em `out/semantics`.
- Código atual, headers SDK e fonte das ferramentas que medirão a hipótese.

A memória é longa: as seções wave-5b/5c são as últimas do snapshot revisado. Não confundir os boots chamados M3/M4 nessa memória com a conclusão integral dos lotes M3–M5 do plano 20.

## Baseline que deve ser preservado

```text
ROM: out/rom/luta_mugem_rev2.sms
SHA256: 6f4a3cf5e336c20ff1dc0fb5225345270823350eada55d4d43655cdfca0b6e9a
bytes: 851968
histórico: changelog/roms/build_v031/rom.sms (mesmo SHA)
par atual: Ryu P1 / Ken P2, out/generated/ryu_ken_cross
```

Reconfira status, fontes, dados, ROM e acesso aos destinos antes de qualquer build. O consumidor inteiro estava untracked; não presumir que HEAD contém seu código. Congele snapshot por hashes dos arquivos necessários e preserve a v031. Respeite WIP alheio e uma única autoridade por asset/perfil. Tentativas usam filhos versionados, parent e registry; não sobrescrever relatórios antigos.

O doc do `luta_mugen` antigo retorna EIO. Nenhuma dependência obrigatória do novo fluxo pode apontar para ele. Existem quatro módulos de input previamente reaproveitados por hash; conferir as cópias locais não requer reler o diretório ilegível. Novo diretório no mesmo cartão não é reparo físico; EIO/EACCES não viram ausência, stub ou PASS. Não limpar processos/arquivos alheios nem executar fsck/remount.

Não faça commit/push sem autorização vigente. Prepare mudanças concretas e revisáveis; não use aprovações rotineiras como substituto de trabalho técnico independente seguro.

## O que existe e pode ser reutilizado

- Intake Ken/Ryu, parsers, IR, geração de cortes e dados CLSN/CMD, banking e pacotes dos quatro pares.
- Na v031: 59 arrays CLSN comparados posicionalmente, 33 aliases, zero divergências; 194 caixas do recorte corroboradas por presença no binário. Isso prova dados, não execução de todos os controllers.
- Registro histórico wave-5b 29/29: entrada humana/IA pelo matcher, HP/dano/guarda/KO. A sessão temporária não foi integralmente preservada: reproduza o núcleo dos casos no novo protocolo, sem apagar o histórico.
- 184 testes host passaram no escopo rev2; 146 foram deselected por escopo. Não são 330 testes aprovados e não certificam os kernels novos do jogo.
- Corredor auditado no `.map` atual: 77 sondas, folga 1547 B, 0xC800..0xC8FB. Refaça após o link; isso não é medida de stack restante.
- Otimização clip→plain tem análise e A/B históricos. Não repetir toda a investigação sem delta que a invalide.

## Diagnóstico que precisa orientar a implementação

1. O runtime atual é sprite-only diagnóstico. Na falta da pose residente, omite o ator; `request_pose` pode invalidar o cache adversário. `combat_step` usa frames lógicos antes dessa decisão visual: existe caminho para dano de ator invisível.
2. O streamer limita 64 B por iteração alternando lados; pedidos novos podem cancelar cópias parciais. Esse valor não é o teto do SMS.
3. O loop faz lógica, emissão e SAT depois do `waitForVBlank`. Os selos antigos reprovaram 2456–2954 de 3000 iterações, em hashes anteriores. Não existe budget de produção aprovado na v031.
4. Sprite-only sem omissões foi refutado para composições do piloto 72–88 px. Híbrido BG/sprites foi escolhido, mas ainda é candidato sem runtime validado.
5. Current+next 6016–6592 B é de um ator. Não cabe inferir residência do par comparando esse número com 8192 B. Padrões BG não podem ocupar a PNT reservada; refaça o mapa conjunto.
6. Colisão, dano e input são subconjuntos. O pacote atual tem 3 comandos por lado: especial unsupported, HP, HK; conflitos tornam parte deles inacessível. P2 é um ciclo de inputs, não IA adaptativa, e o pad P2 real não está ligado ao mesmo modo selecionável.
7. Há fronteira de espelhamento de pixels, hitstun de fonte ausente, pusher durante hitstop, common1 ausente e KO terminal sem reset. Não promover essas aproximações a compatibilidade MUGEN.

## Lote A Congelar contexto e obter um baseline causal reproduzível

Atualize o resumo operacional da memória e o TDD/spec/contrato para distinguir implementação diagnóstica, implementação de produção e orçamento aprovado. Mantenha histórico por ROM. Corrija medidas transportadas indevidamente, incluindo 60 sondas/1781 B de artefato antigo contra 77/1547 atuais.

Parametrize os testes para `--project`, `--rom` e saída exclusiva por run. SHA esperado é entrada congelada, não constante que precisa de edição a cada build. Não alterar o report antigo para fazê-lo apontar à ROM nova. Preserve parser, mapa, ihx, dados e SDK por hash.

Reproduza na v031, antes das mudanças, os casos mínimos: um HP humano, erro por distância, defesa, ataque do lado P2 e KO. Use sessão privada, journal completo, precondições e RAM bruta, vídeo quando a afirmação depende de imagem, manifests finais e cleanup. O objetivo é fixar o comportamento, não aprovar o visual do diagnóstico.

Falhas visuais e de deadline podem aparecer nessa reprodução e devem compor o baseline. Não altere a v031 congelada para fazê-la passar; registre o resultado e siga para as correções do lote B, com ROM candidata e evidência próprias.

Registre quatro relógios: frames VDP confirmados pelo ACK, contador lógico da ROM, fronteiras de animação e relógio de parede para medições em tempo real. `Rig.hold` até N ticks ROM serve ao caso funcional; adicione deadline VDP para input/ação/apresentação. Uma espera crescente até a ROM alcançar N ticks não aprova fluidez. Não interpretar valores absolutos de frame como deltas nem inventar defeito da ponte pela diferença entre contadores.

Fortaleça os asserts conforme o caso declarado: contexto precisa do papel esperado, clamp precisa atingir o limite quando esse é o claim, guarda sem dano exige dano zero e pós-KO precisa de tentativa ativa de comando/contato. Exija o snapshot correto dos dois slots. Preserve o teste anterior e registre o delta; não rebatizar correlação em janela como prova de causalidade exclusiva ou de trade no mesmo tick.

## Lote B Construir o loop de produção e o primeiro híbrido

Preserve a ROM/instrumento diagnóstico e implemente um perfil de produção no mesmo sistema, com uma única autoridade de runtime. Não abrir outra engine concorrente no consumidor. O núcleo reutilizável tem owner central em `tools/sms_wrapper/mugen2sms`; o consumidor mantém configuração, assets e integração fina. Se criar um diretório runtime no wrapper, registre-o como extensão real; ele ainda não existe no snapshot revisado.

Separe preparação de lógica/input/CNS/cache/SAT/filas em CPU de commits VDP no VBlank. Escolha a ordem exata considerando o SDK, troca de SAT e latência; prove input→estado→pose→caixa→dano. Nem toda lógica precisa caber em VBlank. As escritas VDP precisam de limite mensurável, recuperação de fila e registro de overflow, inclusive o começo/fim da janela.

Faça primeiro uma cena pequena jogável com os dois atores reais e fundo sólido. Implemente híbrido de corpo BG com partes/FX na SAT, comparando uma alternativa de decomposição se o custo justificar. Prove:

- Mapa VRAM único: patterns BG/sprites, janela reg6, PNT, SAT, fonte/HUD, current/pending e espaço de FX. Regiões disjuntas; sprite e BG compartilham 16 KiB.
- Paletas por papel: P0 BG com índice 0 visível; P1 sprite compartilhada com índice 0 transparente. Cores e metadados P2 corretos e distinguíveis.
- Movimento por pixels e alinhamento sub-tile, facing, pulo, bordas, sobreposição dos corpos, prioridade e tiles ocupados simultaneamente pelos dois atores.
- Remoção da imagem anterior, atualização de tiles/PNT sujos, restauração de fundo e ausência de resíduos.
- Residência e cache por identidade exata, deltas, reuso real e pré-carga. Não reler pose inteira se puder provar mudança menor; não equiparar bytes parecidos.
- Publicação coerente de pose/facing/caixas; mantenha imagem válida nos misses. Não deixar o golpe futuro atingir com imagem antiga ou lutador omitido. Se a pose precisar esperar, medir a espera e atender o contrato de cadência, sem congelar física conforme congestionamento por conveniência.
- Probes distintos para pose desejada, residente, submetida na SAT/PNT e apresentada. O `probe_disp` atual pode indicar current sem que o ator tenha sido emitido; não usá-lo sozinho para provar contato visível.
- Upload parcial com geração/identidade do pedido, cancelamento/reuso seguros, serviço limitado por ator e nenhum desalojamento invisível do oponente como política de produção.

Compare candidatos sequencialmente: cada um com seu SHA, mesma carga/input/configuração e apenas o delta declarado. Meça bytes novos, ciclos/linhas por etapa, espera por ator, RAM/stack, VRAM/ROM/bancos, qualidade das transições e input→contato→recovery. Não presumir sucesso porque o bound residual de sprites ficou baixo. Refaça worst-frame com carga representativa e sem DAP durante a janela; contador de iterações ROM não vira quantidade de frames VDP por nome.

Não gastar outra longa série de sondas no diagnóstico sem hipótese discriminante. Use Emulicious para produção e BlastEm para localizar custo/estado quando necessário. Se o híbrido falhar, produza a comparação concreta de alternativas e a decisão de tradeoff; não reduzir arte/escala ou retirar FX silenciosamente para chamar o resultado de aprovado.

## Lote C Fechar um normal e os fundamentos do combate

Complete um normal importado por personagem, usando a interação pequena do lote B. Garanta ordem/timing AIR, offsets/pivô, espelho de pixels e CLSN nos dois facings. O SMS não oferece flip de sprite por atributo; espelhar só posições de células não espelha o interior dos tiles. Use espelhos offline ou outra solução medida, com metadados de paleta/slot corretos.

Preserve os acertos: aritmética Q8.8 de posição acima de 32767 precisa domínio unsigned/largura adequada no SDCC; teste clamps 16/240, push, troca de lados e limites. Testes gcc com int de 32 bits não substituem a largura Z80.

Defina hitstop/hitstun/blockstun/guardpush/knockdown/getup e invulnerabilidade segundo a fonte/perfil; HitDef ativo, dano, multi-hit, re-hit, cancel e recovery não podem ser deduzidos apenas de `S_HIT`. Teste impulso inicial versus movimentação do pusher durante hitstop. A mudança de vida precisa corresponder a contato do estado apresentado; fonte→caixa no binário não paga essa prova.

Defina coleta de contatos e aplicação de efeitos para trades e KO simultâneo. O loop atual favorece a avaliação P1 antes de P2 e pode trocar o estado do defensor antes do segundo contato. Revalide snapshots após mudança terminal e teste prioridade, empate e pós-KO; dano cruzado ao longo de três janelas não é prova de simultaneidade.

Para AIR finito, preserve IDs e N+1 fronteiras com terminal. Use `audit_import_semantics.py` somente nos perfis suportados e com self-check, sem chamar schema MUGEN algo não modelado. Não fusione elementos de imagem igual quando seu tempo/CLSN difere.

O comentário atual de `main.c:533` diz 1/100 s para AIR: confronte-o com a especificação MUGEN 1.0, que define 60 game ticks por segundo em velocidade normal. Não aplicar a unidade do OpenBOR aqui. Valide primeira exposição, elementos de duração 1, loops/holds e terminal; a FSM avança antes da emissão no calendário atual, então uma imagem de duração 1 precisa de prova de que chegou a aparecer. PAL exige política regional explícita para preservar a duração, sem simplesmente tratar 50 frames como 60 ticks.

## Autoridade CLSN e estados comuns

Consulte e registre as fontes primárias obtidas na revisão:

- [Formato AIR e unidade de tempo](https://www.elecbyte.com/mugendocs/air.html)
- [Tutorial oficial de colisões](https://www.elecbyte.com/mugendocs-11b1/tutorial2.html)
- [Formato CNS e estados](https://www.elecbyte.com/mugendocs/cns.html)

A documentação distingue caixa por elemento de Default persistente. Ela sustenta o reset por frame com fallback Default atual; não acrescente 27 hitboxes por carry-forward com base em intenção presumida do autor. Adicione fixtures discriminantes e preserve a comparação anterior. Separe conformidade documental de replay no executável MUGEN/versionamento do pacote.

`common1.cns` ausente não autoriza inventar equivalência. Escolha fonte autorizada/versionada ou perfil de adaptação próprio explícito para estados comuns, com testes diferenciais e limitações. Faça proposta concreta para os comportamentos que dependem de aceite de fidelidade; enquanto isso, prossiga com mecanismos e testes independentes. Uma dúvida documental pesquisável não deve virar bloqueio humano indefinido.

Mapeie actions reais: action 170 de Ryu é LOSE na convenção, não prova de cadeia completa de KO; resolver hit/queda/morte/resultado pela fonte/perfil e consumo. Walk com idle é apenas aproximação do piloto; fonte, estado e ação precisam ser conferidos antes de aceitar animação de caminhada.

## Lote D Completar movimentos por lowering e perfis de controle

Amplie o subconjunto CNS AOT por alcance real dos dois pacotes: ChangeState/ChangeAnim, triggers/time/AnimElem/ctrl, pos/vel/physics, HitDef/HitPause/guard, Life/Power/Var, Projectile/Explod/Pause/SuperPause e Target/Helper quando alcançáveis. Preserve ordem e predicados. Não exigir VM universal antes de implementar um movimento completo nem ampliar uma tabela de papéis como se já executasse controllers.

Cada capacidade registra fonte/section/state/action/controller/trigger/SHA, lowering, consumidor, teste e ROM observada. Estados parsed/generated/consumed/observed/budget_validated separados; fidelidade exact/approximate/blocked/dropped_by_owner com justificativa. Feature essencial unsupported bloqueia aquele movimento; não vira noop.

Use `out/semantics/cmd_2button_audit.json` e a matriz de alcance para criar perfis de 2 botões separados Ken/Ryu. Resolva em proposta concreta os conflitos de fraco/forte/especial, botões ausentes/acordes e supers. Compare gestos/contextos/tier por latência, falsos positivos, prioridade e facilidade humana; não copiar mapa do personagem anterior. Não sacrificar 9 supers ou deixar só HP funcionando como conclusão do remapeamento. Conserve comandos não mapeados com diagnóstico específico.

Uma família precisa de comando→predicado→estado→animação→objeto/hit→power/dano→recovery funcionando. Implemente projétil com pool estático, lifetime, colisão, ownership de banco/tiles, hitlimit e despawn no KO/reset. Specials/supers precisam custo/recurso/pausas/FX reais e prioridades, não apenas rótulo ou CMD reconhecido.

Resolva o warning 110 de `fight_input.c` confrontando fonte e ASM com testes discriminantes de todos os 300 ticks do ciclo 12 × 25. Não chamar aviso do otimizador de defeito sem evidência. Integre os testes de input/CLSN do consumidor à suíte ou a runner explícito; não esconder cobertura sob 146 deseleções do legado.

## Lote E Fechar os pares na ordem de produto

1. **Ken/Ken:** conjunto suportado de movimentos, paleta P2, ambos os facings, defesa/queda/KO, especiais/supers/power, IA×IA / humano×IA / humano×humano.
2. **Ryu/Ryu:** mesma engine, perfis próprios, features de fonte adicionais com testes; nenhuma edição por nome no núcleo.
3. **Ken/Ryu e Ryu/Ken:** capacidades equivalentes, alvo móvel, troca de lados, cantos, guard/cancel, projéteis e FX simultâneos.

O núcleo precisa aceitar seleção de controlador por slot: pad P1, pad P2, IA e dummy de treino. Leia a porta P2 real; o ciclo atual de beats é driver de regressão, não substituto de IA com dificuldade. A IA deve usar o mesmo caminho de comandos e restrições, sem aplicar dano/estado privilegiado.

Trocar par por configuração/DEF não pode exigir editar `main.c`, includes por nome de personagem ou ABI central. Gere bindings neutros por seleção do build; prove hashes do núcleo inalterados na troca, além de metadados e bankmap válidos. Boots antigos dos quatro pares não provam essa matriz de combate na versão atual.

## Lote F Match HUD áudio e front end

Integre por fatias, com fundo sólido em todas as telas:

- Life/power/timer/rounds/hits, abertura Round/Fight, KO/timeout/empate, win/result e reset/revanche. Shake/slowdown leves, finitos e medidos, distintos de stall.
- Música/SFX PSG com fontes/manifests, prioridades/preempção/restauração, sons de eventos e captura/escuta. SND não é PSG pronto. Voz Fight é experimento opcional de abertura com custo/restauração medidos; não colocar PCM/FM como dependência do combate.
- Título identificador + Press Start piscante, Arcade/Versus/Treino/Options, seleção com retratos rastreados, VS, pause, continue e final.
- Options: dificuldade, rounds, timer, controles P1/P2, música/SFX, sound test/music player. Treino: input history/command list, reset, dummy/guard/IA, power infinito.

Uma FSM de cenas define owners e teardown de objetos, VRAM/paletas, bancos, input edges, áudio e contadores. Teste começo→luta→resultado/continue→restart→menu. Reset precisa funcionar na mesma sessão; KO terminal da v031 não é lifecycle completo.

## Harness e QA obrigatórios

Use até 3 especialistas nativos com writepaths exclusivos: semântica/lowering; VDP/runtime; QA/áudio/gamefeel. Sem delegação recursiva nem dois compiladores no mesmo diretório. Coordenador integra, promove e atualiza memória. Produtor não aprova a própria faixa.

Leia os workflows centrais atuais de sessão isolada e QA por subagentes, SMS_GLOBAL §§93–100. Prepare pedidos V2 com snapshot de contexto legível, ROM congelada, precondições reais e `independent`/`chained` correto. Dispare pela ferramenta nativa, um ID real e sessão privada por worker; valide o retorno e a cobertura com `audit_subagent_session.py`. Coleta automática não é julgamento; reviewer inspeciona imagens/vídeos/probes e áudio conforme capacidade.

Emulicious é produção/QA. BlastEm complementa diagnósticos Z80/VDP/mapper/dumps; suporte GDB M68K não prova Z80. Nenhum fallback ao teclado/foco/janela do dono ou execução global por título. Cada sessão tem SHA/PID/controles e sink privados, manifests finais e cleanup em finally. FPS em tempo real usa reserva cooperativa e carga registrada; stepped só prova sequência.

Matriz mínima de regressão por nova ROM: ambos os facings/paletas/slots, input press/release/tier/gestos negativos, alvo móvel e bordas de CLSN, guard e hitstop, contato visível e recuperação, morte/reset, pool cheio/cancel/stale upload, cruzamento/overlap/subtile, dois atores + projéteis + sparks + HUD + PSG. Regiões de VRAM/RAM/stack e frame worst-case incluídas. PAL sobe somente após perfil regional e execução próprios.

Crie oráculo de render independente e validado para `audit_render_glitch`: fixtures known-good/known-bad, identidade de pose, tiles residuais/slot errado/omissão. Não copiar screenshots como expected nem ajustar a legalidade para ocultar flicker. SAT/VRAM/CRAM e fonte indexada servem ao cross-check; revisão visual em tamanho nativo mede o acabamento.

Testes conhecidos a partir do workspace:

```sh
rtk proxy env PYTHONPATH=tools/sms_wrapper python3 -m pytest tools/sms_wrapper/mugen2sms/tests --project rev2 -q
rtk proxy python3 SMS_projects/luta_mugem_rev2/tests/input_wave5b_rom_causal.py --self-check
rtk proxy python3 SMS_projects/luta_mugem_rev2/tests/clsn_source_to_rom_diff.py --self-check
rtk proxy python3 tools/sms_wrapper/audit_mugen_engine_contract.py --project SMS_projects/luta_mugem_rev2
```

Confira `--help` antes de rodar os testes de integração: scripts atuais podem sobrescrever outputs fixos. Acrescente testes positivos/negativos e self-check a qualquer ferramenta nova; não enfraquecer gates compartilhados. Testes focados por lote; integrais uma vez no fechamento. Reprovação de delivery atual é esperada, não autorização para marcar capacidades true.

## Entrega e aprendizado

Mantenha resumo operacional atual no topo da memória; TDD implementado, spec com budgets medidos, contrato/matriz de capacidades, registry/proveniência e bindings asset→ROM atualizados. Arte final tem fonte autorizada; sprites gerados por código servem apenas como fixture diagnóstica identificada.

Ao fechar cada lote, entregue antes/depois por SHA: controles, latência/cadência, integridade visual, serviço/cache/transferências, RAM/stack/VRAM/ROM/bancos, pior frame com PSG e resultados regionais. Promoção exige evidências da mesma ROM e cobertura exata; áudio, sinal, música certa e gamefeel são julgamentos diferentes.

Curadoria só promove lição reproduzida, corrigida e medida. Candidatos úteis: Q8.8 assinado, contador loop ≠ VDP, cancelamento/expulsão de cache, contato sem apresentação, reports sobrescritos e vínculo CLSN. Não canonizar 64 B como limite SMS, não culpar o host pelo pacing sem controle, não transformar candidato BG em viabilidade já provada.

Durante o trabalho: **Resultado / Bloqueio / Próxima ação**. Na entrega: mudança concreta, motivo, ROM vista executando, testes/evidências, limites e próximo ramo. Persistir nas correções seguras; decisões humanas necessárias recebem alternativas concretas com custo/benefício e impacto, sem impedir trabalho independente já autorizado.
