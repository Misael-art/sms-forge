# skill: sms-host-continuity

Use ao instalar o SMSForge, trocar de host ou retomar um backup. Aplicação de
L002/L036/L125/L138: ambiente executável, custódia e limites de promoção.

- Leia `doc/continuity/20261024-new-host.md` para comandos e escopo suportado;
  `20261024-agent-handoff.md` localiza diagnóstico, ROMs e próximos blockers.
  Resolva a raiz atual; caminhos absolutos de evidência antiga são históricos.
- Instale pelo wrapper pinado, ative `host_env.sh` e consulte o recibo. Pip só
  no venv do checkout; nenhuma alteração de perfil pessoal ou SDK divergente.
  A cápsula SDCC/libs é um ABI conjunto; não trocar apenas o compilador.
- O smoke-test chama ambos os drivers e confere o header. Na migração de
  24/10, `sdcpp` falhou por `cc1` sem permissão de execução: presença de
  `sdcc --version` não prova compile/link. Dependências transitivas contam.
- Hash de archive antes de extrair; confinamento, limites de expansão e
  destino novo antes de publicar. SDK licenciado, sem ini/recentes pessoais.
  `restore_handoff.py` verifica cada arquivo e ativa só dados gerados de build
  por opção explícita. Não ativa eixos, ROM ou sessão antiga.
- Permissões POSIX são parte do contrato: acervo 0777 não é snapshot imutável.
  Cópia restaurada é declarada; não rehashar prova para parecer sessão nova.
- Doutor de ambiente, instalação, compile/link, boot, controle, pixels, FPS e
  áudio são degraus diferentes. Sandbox/servidor de áudio bloqueados exigem
  diagnóstico, sem fallback ao desktop ou mudança global de política.
- Limpeza só dos caches próprios sob lock. Conservar fontes, evidências
  registradas e sessões por ID. Medir performance sem concorrência de QA;
  limitar workers/threads e fechar cada processo próprio em erro/sucesso.

Ferramentas: `host_bootstrap.py --self-check`, `--doctor --live-checks`,
`restore_handoff.py --self-check`; resultados de ambiente não promovem jogo.
Os gates e a QA nativa continuam em `workflows/subagent-emulator-qa.md`.
