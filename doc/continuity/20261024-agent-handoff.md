# Handoff para o próximo agente — 24/10/2026

## Primeiro contexto

Você retoma o SMSForge, fábrica SDCC/devkitSMS para Master System. O checkout
é relocável: descubra a raiz com `git rev-parse --show-toplevel`, sem assumir
`/mnt/sdcard` ou `/home/misael`. Diga `[Contexto SMS Carregado]`. Leia AGENTS.md,
arquitetura e SMS_GLOBAL centrais. Use RTK se disponível; não dependa da
memória privada do host antigo nem da existência de credenciais/skills globais.

Primeiro execute `20261024-new-host.md`: instalar, ativar ambiente, doctor,
restaurar snapshot em diretório novo e buildar isoladamente. Confira o SHA e
o estado real antes de promover qualquer eixo. Este handoff e os pareceres
são mapas; memory/GDD/spec/TDD e dados reais continuam autoridades.

## Estado técnico preservado

| Área | Fato observado / implicação |
|---|---|
| MUGEN produção nominal | `087df676…`, 851.968 B; P2 fragmentado e fundo com padrão repetido na captura de 24/10. Não aprovado |
| Candidata residente | `698e58ed…`, 458.752 B; dois corpos completos em um quadro. Bloqueia dez papéis/25 poses e reprova budget: `vline_min=4`, `vovf_delta=1740` |
| Identidade | Manifesto seleciona `ryu_ken_cross` de 49 bancos; contrato/TDD/perfil e build records não convergem. Rebuild isolado recente `6de8c451…` difere da nominal, causa não atribuída |
| Telemetria | Frame VDP não é contador do jogo. `present` é política do consumidor; probe desativado/zero não aprova SAT. Stepping não mede FPS |
| Gerador experimental | `display_fit` tem default `pose_budget` nas mudanças preservadas. Regenerar exige perfil explícito e comparação com o baseline; preservar código não aprova corte 5+3 ou os movimentos omitidos |
| Semântica | `common1.cns` ausente nos dois ZIPs; `common_forge` é adaptação não equivalente. FSM por papéis não é CNS completo; golpes bloqueados são dívida |
| Visual e input | Fundo sólido em todas as telas. Não reduzir escala/apagar golpe/FX/perigo para obter PASS. Pose lógica/residente/submetida/apresentada precisam convergir no contato |
| Áudio | Rev2 ativo sem PSG integrado; inventário SND não significa conversão ou audição aprovada |
| Ferramentas novas | Composição e sola permanecem diagnóstico limitado, fora dos gates globais. Self-check não é homologação humana |
| OpenBOR | Cap5 `701379cc…` tem medições históricas; contato da espada aponta para o lado oposto do alvo. Direção, apresentação, PAL e oráculo full-frame abertos |
| Armazenamento legado | `luta_mugen/doc` antigo com EIO/ausências no host de origem. As 25 exclusões não foram publicadas como correção. Clone contém os últimos bytes versionados, sem provar recuperação do material nunca salvo |

Detalhamento: `doc/curation/2026-10-24_mugenesis_rev2.md`, pacote PB-01–PB-18,
`2026-10-24_luta_mugem_rev2_pendencias.md` e JSON do backlog. Preserve seus IDs.
A curadoria de 21/10 também integra esta branch; não reintroduzir HAMOOPIG.

## Próximo lote: identidade → residência → um golpe completo

1. **ID01/ID02:** conferir Git/dirty tree, fontes, gerador, dados selecionados,
   toolchain, build e SHA. Gerar recibo e conciliar os documentos sem alterar
   booleans para herdar evidência. Manter histórico dos três binários distintos.
2. **R01/R11:** dumps VRAM/PNT/SAT para verificar fundo sólido/residência do
   tile BG. Sobreposição com tile 255 é hipótese concreta, não causa exclusiva
   provada. Diagnosticar em sessão privada antes de mudar backend.
3. **R02–R06/R09/IN05:** composições reais dos dois lados, ambos os facings,
   upload com deadlines/gerações, sem starvation/publicação parcial e contato
   coerente. Um golpe até os dois terminais: controle livre e pose exibida.
4. **Depois:** semântica alcançável, quatro pares pelo mesmo core, objetos,
   rounds/HUD/PSG e front-end. Seguir dependências dos 55 itens; não redesenhar
   o escopo para declarar encerramento. Projeto não contém cenário por decisão.

Ken/Ken → Ryu/Ryu → Ken/Ryu → Ryu/Ken, IA pelo canal normal de input e testes
negativos. Não usar dano/estado injetado como demonstração de IA jogando.
Mesmo core por configuração/dados; subconjunto MUGEN explícito e admissão
de incompatíveis antes do runtime. SGDK fornece método e casos, sem importar
DMA, ABI M68K, seis botões ou resultados de BlastEm MD como capacidade SMS.

## Método de execução

Use o prompt de conclusão já registrado, com caminhos resolvidos pela raiz
atual. Lote vertical com foco no blocker dominante; testes focados durante
o lote, integrais uma vez ao fechar. Um push por lote autorizado. Cada decisão
atualiza o memory bank e o backlog com ROM, caso, custo e limite, não apenas
uma narrativa ou mais um prompt.

Antes de QA, ler `emulator-isolated-session.md` e `subagent-emulator-qa.md`.
Emulicious principal, BlastEm complementar. Se delegar, reviewers nativos
distintos, pedidos V2/contexto legível/ROM congelada/sessão própria/cleanup e
recibo real. Os relatórios antigos mantêm caminhos e identidade históricos;
não os rehashar para o host novo. Coletar nova prova de input→ação→pixels,
áudio e pacing, mantendo os casos negativos e o terminal completo.

Não encerrar só depois de um diagnóstico quando houver ramo causal seguro.
Decisão humana sobre arte/escopo/controle precisa de opções concretas e prova;
tempo sem resposta não aprova corte. Continue o trabalho independente.

## Conclusão exigida

Sete eixos na mesma ROM, orçamento representativo, época delivery, binding
asset→ROM, regressão independente e memória atual. Instalação/build/screenshot
não certificam AAA, ausência universal de flicker ou aceitação comercial.
Qualidade visual, sonora e jogabilidade precisam de mídia e revisão próprias.
