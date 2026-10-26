# SMSForge — começar em um host novo

Este é o ponto de entrada da continuidade de 24/10/2026. O disco do host
anterior não é necessário para retomar o recorte `luta_mugem_rev2` preservado
no Git e na release abaixo. O motor ainda está em desenvolvimento; recuperar
arquivos e instalar ferramentas não aprova gameplay, orçamento ou AAA.

## 1. Sistema e primeira instalação

Alvo preparado: **Ubuntu 24.04 LTS x86_64**, nativo ou Ubuntu em WSL2 no
Windows. Outro Linux pode usar o diagnóstico, mas instalação de pacotes e QA
precisam de qualificação própria. A arquitetura ARM/macOS não foi qualificada.

No Windows, instale WSL2/Ubuntu e mantenha o clone no filesystem Linux
(`~/Projects`), evitando cartão SD e `/mnt/c` como diretório de build. Instale
o Codex no novo computador e autentique novamente suas contas. Nenhum token,
chave SSH, cookie, banco pessoal do agente ou configuração secreta foi migrado.

Em Ubuntu vazio, abra o terminal e execute:

```sh
sudo apt-get update
sudo apt-get install -y git python3 python3-venv ca-certificates
mkdir -p ~/Projects
cd ~/Projects
git clone --branch codex/host-bootstrap-continuity-20261024 https://github.com/Misael-art/sms-forge.git
cd sms-forge
bash tools/sms_wrapper/bootstrap_host.sh --install-system
```

O bootstrap instala os pacotes básicos de compilação, Java, Xvfb, Bubblewrap,
FFmpeg, PulseAudio e ferramentas de arquivo que faltarem. Não executa upgrade
geral do sistema. Depois prepara `.venv/`, SDK por fonte verificada, emulador
original/licença, RTK local se ausente e restaura os dados/gerados do rev2.
Os assets são fixados por SHA-256 em `host_dependencies.lock.json`.

SDCC vem da distribuição e precisa ser >=4.2. SMSlib/PSGlib são reconstruídas
com esse compilador: bibliotecas de outro host não são reutilizadas como ABI
equivalente. O recibo inclui versão/hash e smoke-test real compile→link→ROM.
Mudar a toolchain pode mudar a ROM; evidência histórica não qualifica o rebuild.

`ensure_toolchain.sh` permanece como alias do bootstrap. Em máquina já
preparada, rode sem `--install-system`. Para preparar somente ferramentas sem
restaurar o snapshot do jogo, use `--skip-project-restore`.

## 2. Usar o ambiente sem poluir o host

```sh
tools/sms_wrapper/run_host.sh rtk --version
tools/sms_wrapper/run_host.sh python tools/sms_wrapper/host_bootstrap.py doctor
tools/sms_wrapper/run_host.sh python tools/sms_wrapper/reconcile_claims.py --project SMS_projects/luta_mugem_rev2
```

O wrapper ativa PATH/PYTHONPATH só no processo. Não edita `.bashrc`, não
instala Python via pip global, não copia configurações pessoais de emulador e
não altera hooks globais do agente. Use-o também para builds, testes e QA.
RTK faz parte da convenção portátil em `tools/sms_wrapper/RTK.md`.

CPU: padrão de dois jobs e dois threads NumPy/OpenBLAS; instalação aceita
`--jobs 1..4`. Downloads/cache ficam em `.runtime/`; dependências Python em
`.venv/`; SDK em `sdk/`; logs/ROMs/capturas nos `out/` do owner. O instalador
recusa iniciar com menos de 2 GiB livres. Esse piso não é estimativa do espaço
total necessário aos demais projetos ou à retenção de vídeos.

Áudio usa o servidor do usuário quando acessível. Se não existir, o wrapper
inicia um servidor privado do workspace com expiração após 60 s de inatividade.
Não encerra o servidor do desktop. Emulicious deve continuar em sessão privada
por ID/SHA, com mute/rota confirmada e cleanup, conforme os workflows centrais.

`doctor` registra ferramentas, espaço, carga e disponibilidade de user namespaces.
Se o kernel/sandbox recusar Bubblewrap, a QA fica `FAIL_AMBIENTE`. O wrapper
não muda políticas globais de segurança nem faz fallback para o desktop.

## 3. O que recuperar e como conferir

Release de recuperação:
<https://github.com/Misael-art/sms-forge/releases/tag/continuity-20261024>.
O índice com bytes/SHA/URLs está em `20261024-release-assets.json` neste
diretório. O Git preserva código, docs e a curadoria; os assets preservam os
arquivos ignorados necessários, a fonte do SDK e o emulador com licença.

O bootstrap restaura automaticamente o pacote de dados/runtime do rev2 uma
única vez em clone limpo. Um recibo em `.runtime/project_restore.json` impede
reaplicar o snapshot sobre o desenvolvimento posterior. Não apague esse recibo
para forçar sobrescrita. Uma recuperação manual deve ser feita em diretório
separado; conflitos são recusados antes da publicação:

```sh
python3 tools/sms_wrapper/recovery_bundle.py verify \
  --archive /caminho/luta_mugem_rev2-runtime-20261024.tar.gz \
  --manifest /caminho/luta_mugem_rev2-runtime-20261024.json
python3 tools/sms_wrapper/recovery_bundle.py restore \
  --archive /caminho/luta_mugem_rev2-runtime-20261024.tar.gz \
  --manifest /caminho/luta_mugem_rev2-runtime-20261024.json \
  --into /caminho/clone-limpo
```

O pacote completo de continuidade contém wrapper, fontes/dados/gerados e
histórico local do rev2, diagnóstico atual e documentos de retomada. Um
manifesto por arquivo verifica composição exata, bytes e SHA; extração recusa
traversal, links e dispositivos. Isso é recuperação cooperativa de arquivos,
sem promessa de atomicidade do filesystem inteiro ou resistência a queda de energia.

O arquivo completo também tem sua cópia de recuperação na
[Page privada de continuidade](https://chatgpt.com/space/page_d9ac1918a4d4819195db59a18b76d316),
com anexos cuja confirmação consta no índice. Se dividido, a ordem e o SHA do arquivo reunido
constam no índice. Guarde o link de recuperação entregue ao fim desta tarefa.
Não trate o diretório local desta tarefa no Codex como cópia remota garantida.
A documentação oficial descreve worktrees como arquivos no computador/ambiente
onde o projeto está; veja [Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees).

Outros projetos conservam a release histórica `continuity-20261021` e seus
manifestos. Não foi criado um backup integral atualizado de todo o disco.
`luta_mugen/doc` tinha EIO: versões já commitadas permanecem no Git, mas
alterações ilegíveis do working tree não puderam ser preservadas. Um clone
limpo recupera o último estado commitado; não repara nem autentica o cartão.

## 4. Estado e prioridade do motor

Leia nesta ordem:

1. `AGENTS.md` e regras/workflows centrais atuais;
2. `SMS_projects/luta_mugem_rev2/doc/10-memory-bank.md`, GDD, spec e TDD;
3. `doc/curation/2026-10-24_mugenesis_rev2.md`;
4. `doc/curation/2026-10-24_luta_mugem_rev2_pendencias.md` e o JSON com 55 itens;
5. `doc/curation/2026-10-24_prompt_concluir_engine_sms.md`;
6. `doc/continuity/20261024-next-agent.md` e validação desta migração.

Baseline nominal: `087df676…` (851968 B). Prova de composição limitada:
`698e58ed…` (458752 B). A prova bloqueia dez papéis/25 poses e seu selo
histórico continua `derramou` (`vline_min=4`, `vovf_delta=1740`). A produção
mostrou P2 fragmentado/fundo repetido na QA de 24/10. Não promover por boot.

Primeira prioridade: identidade da build/documentos e apresentação completa,
composição legal, streaming com prazo, coerência pose/contato e VBlank. Depois
fechar o subconjunto CNS, os quatro pares, objetos/rounds/HUD/PSG/front-end e
reuso autoral em consumidor separado. Não ampliar para cenários ou elenco novo.

Os 55 itens são um backlog de desenvolvimento, não 55 tarefas já concluídas.
As ferramentas de composição e sola continuam diagnósticos não promovidos.
O kernel, toolchain e ambiente novos exigem QA nova antes de qualquer claim.

## 5. Rotina de trabalho e retenção

Comece por `git status`, valide a fonte/ROM selecionadas e trabalhe em branch
`codex/…`. Escolha um lote vertical ligado ao blocker dominante. Durante o lote,
testes focados; no fechamento, gates integrais uma vez, memória e um push do
lote completo. Não faça polling de CI. Se houver subagentes, seguir pedidos
nativos, owners disjuntos e sessões exclusivas dos workflows atuais.

Não rebuildar na pasta da baseline preservada para depois chamar a captura
antiga de fresca. Copie o consumidor ou use destino isolado, registre SHA e
refaça a QA afetada. Dados gerados precisam de receita e fonte identificadas.
Qualidade de código inclui erros explícitos, tipos/limites Z80, módulos com
owners, testes negativos e ausência de hardcode por personagem no core.

Preserve inputs imutáveis, contratos, recibos, ROMs aprovadas/controle e mídia
que sustenta claims. Caches e builds descartáveis podem ser removidos somente
por caminho/owner conhecido e sem apagar a única cópia de fonte/evidência.
Antes de deixar outro host, publique mudanças e confira os assets remotos.

## Recuperação organizada — 2026-10-26

Raiz única neste host: `/home/misael/Projects/SMSForge`, base `8dfb8ea7be950b91c0dc4e41af995865a7537775`. Arquivos/runtime do rev2 restaurados pelo bootstrap com recibo; Python 3.11 selecionado para manter o lock numpy 2.2.6 sem compilação incompatível no Python 3.14. SDCC 4.6.0 do pacote oficial Manjaro foi verificado por assinatura e instalado somente em `.runtime/sdcc/`, com launcher em `.runtime/bin/` e recibo de hash/origem. SMSlib/PSGlib recompiladas e smoke compile→link→ROM de 16 KiB passou. Não é prova de gameplay/FPS/áudio. O doctor passou com Java/Javac 21 fixados, namespaces e áudio disponíveis. O JDK já provisionado pelo host-manager é compartilhado por referência, com dependência registrada no inventário central; não há outra cópia do JDK. Retomar pelos 55 itens preservados, sem novos clones/worktrees.
