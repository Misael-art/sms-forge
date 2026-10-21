# Auditoria de cobertura canônica — 2026-10-10

Escopo somente leitura do repositório. Outputs exclusivos neste /tmp. Nenhum emulador ou teste integral executado.

## Inventário

- 64 JSONs diretos em doc/curation/ (63 registros + registry).
- 108 IDs de lição definidos, emitidos até L124, descontados 16 holes declarados.
- 77 entradas do ledger; nenhuma dedup_key duplicada. Nenhuma definição ID duplicada.
- 70 documentos canônicos em skills/workflows/rules/agents/pipelines + architecture/AGENTS, todos legíveis.
- Todas as ferramentas nomeadas resolvidas: referências L122/L124 em SMS_projects existem, porém são scripts de projeto, não ferramentas genéricas do wrapper.
- SHA-256 e bytes de cada entrada lida em coverage.json.

## Aplicação e oportunidades concretas

1. Harness tem ownership de workers; falta ownership e resolução única de artefatos por projeto/asset/papel. Não criar mais uma árvore para sanar a desorganização. Registrar extensão criativa no mesmo índice e manter versões/derivações. Reutilizar L036/L052/L108/L122/L123.
2. L004: rebuild de bibliotecas com sdcccall incompatível existe no ensure_toolchain.sh, sem ensino operacional em skill/workflow.
3. L009: marcadores volatile/mapa do linker e parse hexadecimal DAP só constam na lei/gate. Falta ensinar a aplicação nos gotchas Z80.
4. L096: comparador reprova caudas/chaves diferentes; não é ensinado no intake/comparação semântica MUGEN.
5. Duas skills de banking declaram slot0 inteiro fixo. Contradizem a restrição real de primeiro1KiB já documentada em L117. Corrigir sob L001/L069/L117, sem ID novo.
6. Budget skill descreve SAT como64×4B. Separar área reservada256B de64Y+128X/tile efetivos SMS.
7. audit_learning_capture valida caminho de skill apenas para um status específico; não mede aplicação taught por lição promovida em outros status.

## Limites e estados

O mapa proposto oferece108 entradas e11 registros de aplicação/catalogação sem novos IDs.105 IDs têm entrypoints existentes, três gaps ficam vazios de propósito (L004/L009/L096). Os entrypoints são seleção de domínio revisada, não prova de execução nem compreensão. Evidência lexical acompanha quando disponível.

Históricos/refutados são preservados explicitamente: causas TALL/SMS_loadTiles, condenação ampla de DAP, captura desktop/sink default/global kill. Rotas atuais de sessão privada prevalecem; não promover prosa original sem ler correções.

Os custos de streaming/bandas/FPS de um corte são observações locais, não teto SMS. L111 mantém review humano pendente; L113 registra exercício não renderizado; L115 é inspeção de fonte+relato MD, sem homologação GDB Z80; L124 v10 permanece candidato pendente apesar de framebuffer61/61. Catálogo49estilos e formulário de um personagem não são presets gráficos universais.

Lições sem menção literal no ledger podem ser cobertas por fonte/registro agrupado; não foi classificado isso como defeito. Não confundir ausência de ID literal em uma skill com ausência de aplicação sem revisão semântica (L073 está ensinada em recipe asset→ROM).

## Artefatos

- coverage.json: por registro e por ID, referências, ferramentas, SHA, observações, limites e findings.
- lesson_routes.proposed.json: mapa único108IDs, fontes e regra, entrypoints concretos, lacunas sem preenchimento genérico, históricos e limites abertos.

Nenhum arquivo do projeto foi alterado por esta auditoria.
