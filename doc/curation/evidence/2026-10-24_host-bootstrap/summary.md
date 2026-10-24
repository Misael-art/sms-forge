# Migração e curadoria — 24/10/2026

## Resultado

Diagnóstico PB/Mugenesis preservado e fábrica preparada para host Linux vazio,
com launcher de pacotes, cápsula ABI SDCC/devkitSMS, venv/wheels com hashes,
Emulicious e BlastEm pinados, doctor e restaurador. O contexto da engine e
os 55 itens pendentes ficam nos handoffs; nenhuma engine foi promovida.

## O que foi preservado

As alterações rastreadas e 61 arquivos não rastreados de diagnóstico do
workspace original foram copiados para uma worktree separada. A curadoria
anterior 09a15db integra a base; o ledger foi conciliado sem perder a rodada
anterior. As 25 exclusões EIO/ausências de luta_mugen não foram incorporadas.
Inventário: `source-custody.json`. O código experimental foi salvo, sem aprovar
seus defaults/cortes ou os dois instrumentos ainda limitados.

O pacote `doc/continuity/20261024-mugen-resume.tar.zst` tem 7.876.889 bytes e
3.917 arquivos/81.882.904 bytes de conteúdo; seu manifesto lista cada SHA e
205 omissões de auth efêmera/caches. Expansão/hash/conjunto exato foram
revalidados. Restauração read-only em destino novo; só generated inputs são
ativados por opção. Evidência e booleans não são ativados.

## Instalação real em Ubuntu vazio

Container Ubuntu24.04 x86_64, iniciado sem Python/SDCC/JDK, 2 CPUs/2 GiB RAM.
O launcher instalou pacotes, SDK, Python isolado, Emulicious e BlastEm.
Os recursos de instalação foram todos verificados; a prontidão de QA falhou
explicitamente por **sandbox indisponível e servidor PulseAudio ausente** no
container. Não alteramos política do kernel, sink padrão ou desktop do host.
Xvfb privado iniciou/fechou; JDK compilou a ponte; pin BlastEm foi verificado.
Um Linux com sessão de usuário precisa rodar doctor e aceitação isolada próprios.

| Experimento | Resultado |
|---|---|
| Primeira instalação | Reprovou: cc1 sem execução; log preservado |
| Segunda instalação | Compile/link passaram; fixture sem header reprovou, corrigida com macro real SMSlib |
| Terceira instalação | Smoke de 32.768 B/header aprovado; bloqueios sandbox/Pulse declarados |
| OpenBOR no container | Build0, SHA701379cc88e074f5874e161cd7e6307b04be48456c1b469172f84a58d79a6da9 |
| MUGEN após restauração | Build0, SHA6de8c451fa39ff49670d242f8a3f3946bf67fea1830566fa4fe901517493b983 |
| Reinstalação build | Exit0, preserva SDK/venv existentes equivalentes |
| Código final do instalador | Build install0; doctor build0; full preflight2 apenas sandbox/Pulse |
| Extração final Emulicious | Somente JAR, licença e ini neutra nova; sem config pessoal restaurada |
| Pacote final saneado | Restore0 e 3.917 arquivos verificados |
| Limpeza de cache | Só downloads/pip-cache próprios removidos; venv preservado |

O SHA MUGEN coincide com o rebuild diagnóstico anterior, não com a produção
nominal087df676. Não atribuída a divergência à data, código ou toolchain sem
experimento pareado. Nenhuma ROM nova foi executada no emulador nesta migração.
Os builds rebaixaram eixos sem lastro fresco, como exigido.

O código final foi exercitado em um derivado do mesmo container após instalar
as dependências; os logs iniciais não foram substituídos. A imagem derivada
e o container de teste próprios foram removidos; não foi feito prune global.
A primeira restauração descartável não saneada foi removida da worktree;
pacote final e fixture saneada permanecem. Dependências do host original
não foram reinstaladas ou alteradas por estes experimentos.

## Gates

- Selftest central: **134/134**, probe opcional não executado.
- Ferramentas de medição: **75/75** self-checks.
- Regressão focada MUGEN: **63 passed/1 skipped**; o skip era fixture de
  display_fit não ativada, conforme política de restaurar somente build inputs.
- Com fixture restaurada via `SMSFORGE_REV2_FIXTURE_ROOT`: **16/16**, sem skips.
  Esse teste mede os contratos/diagnósticos, sem qualificar jogo ou budget.
- Learning capture e doc-sync da worktree de publicação: PASS.
- Doc-sync no workspace original: FAIL com dez problemas legados. A cópia
  limpa possui os bytes já versionados; não prova recuperar a origem EIO.
- Self-checks do instalador/restaurador: válidos, traversal, links, duplicates,
  cache corrompido, divergência de instalação, conjunto/hash e limpeza própria.

## Próxima execução

`doc/continuity/20261024-new-host.md` dá instalação, ativação e restauração.
`20261024-agent-handoff.md` orienta ID01/ID02 → residência/fundo → composição
e um golpe completo. O prompt de conclusão referencia a raiz descoberta.
Quatro pares, semântica MUGEN, objetos, PSG/HUD/fluxos e QA permanecem no
backlog. Piso O3 não é lei para MUGEN; corte/sola continuam diagnósticos.
Sem promessa de portabilidade total, QA completa em container, 60 FPS,
ausência universal de flicker, entrega visual ou AAA.
