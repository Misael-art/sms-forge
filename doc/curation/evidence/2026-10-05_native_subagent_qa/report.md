# Curadoria: testes e feedback por subagentes nativos

Data: 2026-10-05. Escopo: fábrica SMSForge e política central para qualquer
projeto trabalhado. Autorização: pedido explícito do dono desta tarefa.

## O que foi canonizado

SMS_GLOBAL §94 e `workflows/subagent-emulator-qa.md` passam a orientar cada
lote de testes, inclusive projetos com `.agent` local antiga. O ponto de
entrada AGENTS.md e o template encaminham à fonte central atual. Nenhuma
`.agent` de projeto existente foi sobrescrita nesta curadoria.

O coordenador congela ROM/pedido, define casos do GDD e dispara subagentes
pela ferramenta nativa. Até três workers, nas faixas runtime, visual e áudio,
trabalham em sessões e diretórios próprios. Cada worker inspeciona as provas
e devolve resultado, bloqueio e próxima ação. O coordenador confere a
identidade realmente retornada e conserva decisões, memória e integração.

`session_qa.py prepare/collect` prepara pedidos e coleta provas; não cria
subagentes nem julga resultados. `audit_subagent_session.py` confere pedido,
hashes, ROM/sessão, cobertura, mídias e encerramento. Relatório válido e caso
aprovado são decisões separadas: `--require-passed` recusa feedback bloqueado.
Harness e router adotam esse contrato. Checkpoints vinculam produtor,
projeto, SHA da ROM e tasks, impedindo aprovação com provas de outro jogo.

## Evidência realmente executada

Três subagentes nativos: `/root/native_runtime_qa`,
`/root/review_qa_contract` e `/root/native_audio_qa`.
Pedidos, IDs, referências e retornos: `native_dispatch.json`.

| Trabalho | Resultado e alcance |
|---|---|
| Runtime diagnóstico | 3 casos: neutro, P1 direita por 7 frames, P2 botão 1 por 11 frames; RAM da ROM confirmou controles e isolamento |
| Visual MSSF2T | 2 casos: composição do título e quadros amostrados da animação; framebuffer 256×192 |
| Áudio MSSF2T | 1 caso: sinal/duração da captura privada; 4,458 s para 4 s pedidos, pico PCM 5985 |
| Vídeo durante comandos | 1 caso: 18 frames gravados durante a sequência de 7/11 frames, com trilha de input vinculada |
| Falha parcial deliberada | Endereço RAM inválido 0xBFFF: coleta falhou; feedback `blocked/not_run` manteve identidade, provas parciais e cleanup. Gate de aprovação recusou |

Total: **7 casos atribuídos aprovados**, mais um controle negativo de falha
parcial. A falha parcial não foi contabilizada como gameplay aprovado.
Sessões usadas pelos relatórios foram fechadas; o gate verificou os processos
próprios e metadados de encerramento. Não se interveio nas janelas do dono.

## Correções aprendidas e verificadas

- Sidecars de screenshot e vídeo colidiam: agora possuem nomes distintos.
- Vídeo era coletado depois dos comandos: agora registra cada quadro do VDP
  durante o roteiro. A fixture apresenta um frame de atraso visual; roteiros
  de reação/recuperação devem incluir cauda neutra explícita.
- Coleta interrompida perdia contrato de feedback: agora conserva sessão
  parcial fechada e artefatos, permitindo relatório bloqueado válido.
- Consolidado podia usar outra ROM/projeto: vínculos obrigatórios e negativos
  registrados. O checkpoint diagnóstico foi separado do checkpoint MSSF2T.
- Revisor visual interpretou incorretamente o prompt do título como cortado:
  coordenador reabriu os quadros e o worker retratou o achado. Parecer inicial
  e `visual_correction.json` foram preservados. Nenhuma ROM foi corrigida para
  satisfazer esse falso defeito.

## Regressão da fábrica

- `selftest.py`: **74/74**; probe de build opcional não executado nesta rodada.
- `validate_measurement_tools.py`: **52** ferramentas com self-check passando.
- `audit_doc_sync.py`: aprovado.
- `audit_learning_capture.py`: aprovado.
- Relatórios nativos, checkpoints e controles de ROM/projeto divergentes:
  validações JSON preservadas neste diretório.

## Limites e continuidade

Esta curadoria valida o mecanismo e os casos atribuídos. Não aprova gameplay
completo, 60 FPS dos jogos alvo, ausência global de flicker, fidelidade da
música ou qualidade AAA. O gate mede vínculos/cobertura; não autentica sozinho
uma conversa nativa nem determina verdade artística. Observações exigem
inspeção e confronto pelo coordenador.

Integração dos scripts de projeto ocorre em tarefa própria e avançou enquanto
esta curadoria rodava. Estado atual deve ser consultado em
`doc/matriz-consumidores-sessoes-privadas.md`; não reutilizar o antigo bloqueio
de RAM C800 como estado atual da trilha Mugen. Hotplug físico e comparação
musical de trechos alinhados continuam fora dos casos pagos aqui.

Não houve commit/push nesta curadoria. Não foram alterados por esta tarefa
fontes, ROMs ou assets dos jogos. `inventory.json` registra hashes das
ferramentas/documentos no fechamento e das evidências persistidas.
