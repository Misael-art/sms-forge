# workflow: curation-learning

Quando algo dá errado (gate furado, lição paga cara, regressão):
1. Conferir `doc/curation/id_registry.json`, o ledger e SMS_GLOBAL para achar
   duplicatas. Se a lição já existe, não emitir outro ID: ligar o workflow/skill
   usado no ponto da falha à lição existente.
2. Separar o fato observado da inferência; declarar alcance (hardware SMS,
   gênero, projeto ou ferramenta). Evidência de um motor MUGEN não vira
   capacidade universal do Master System. Bloqueio ainda aberto fica como
   hipótese/risk, não como técnica resolvida.
3. Para lição realmente nova, escrever JSON canônico em
   `doc/curation/<data>_<tema>.json` (lesson id, evidence,
   tool_that_measures, rule_section). Se o resultado só amplia a evidência de
   uma lição existente, atualizar aquela curadoria/ledger sem emitir outro ID.
4. APENDAR seção numerada em `.agent/rules/SMS_GLOBAL.md` (nunca renumerar
   antigas) quando houver regra nova. Atualizar também o workflow ou a skill
   que fará o agente aplicar o aprendizado na próxima ocorrência.
5. Se a lição é mensurável e não tem ferramenta → criar/atualizar gate +
   caso no selftest (§20). Regra vira medição, nunca só prosa.
   Para animação, `audit_animation_contract.py` mede a cobertura estrutural e
   o mínimo de sete princípios aplicados antes da arte; depois dos PNGs,
   `audit_animation_semantics.py` valida a timeline real. Nenhum dos dois julga
   física ou qualidade artística sozinho.
6. Para conceito de personagem com fontes em mídias diferentes, registre no
   `asset_contract` a autoridade do jogo de origem e o escopo de cada fonte
   suplementar; prenda os papéis a URLs e SHA-256 no lineage. Rode
   `audit_reference_boundary.py` para validar declarações e limites. O gate
   não mede semelhança visual nem substitui aprovação do dono.
7. Para pixels de recorte ligados à silhueta, registre as cores de material por
   região no contrato; `audit_sprite_cutout.py` mede componentes e cores fora
   do perfil. Registre também o limite do gate: ele não julga fidelidade visual
   total (L104).
8. Atualizar learning ledger com dedup_key. Rode `audit_learning_capture.py`
   para conferir JSON, furos, ferramentas, IDs e doutrina.
   Atualize também `doc/agent_learning/lesson_routes.json`: cada ID emitido
   aponta sua curadoria única e entrypoints concretos skills/workflows com
   SHA atual. Revise o conteúdo antes de atualizar o hash; refresh cego não
   demonstra absorção. Para refutações, apontar a aplicação corrigida e manter
   o limite histórico. O gate mede cobertura/frescor, não entendimento.
9. Curadoria só altera wrapper/doc com aprovação humana explícita.

Relatório de gate é saída, nunca o JSON da lição usado como entrada. As CLIs
`audit_learning_capture.py`, `audit_hardware_constants.py`,
`audit_header_claims.py` e `audit_debug_markers.py` aceitam `--report-out`
(`--json` é alias) e recusam destino existente, inclusive symlink/hardlink.
Usar arquivo novo por run; não apagar a fonte para contornar a recusa.
`report_output.py` implementa criação exclusiva e tem regressão no selftest.
Outras CLIs ainda podem ter semântica antiga de sobrescrita: conferir ajuda e
escolher saída nova. Não afirmar que a família inteira já foi migrada.
