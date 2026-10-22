# Projetos aposentados

## HAMOOPIG — 18/10/2026

**Estado:** obsoleto, retirado do versionamento por solicitação explícita do
proprietário. O projeto deixou de integrar o catálogo e a galeria do README.
`/SMS_projects/hamoopig/` está no `.gitignore`, preservando a cópia local e
impedindo sua reinclusão por um `git add` comum.

O último estado versionado anterior à remoção pode ser consultado no commit
[`0cac1e3`](https://github.com/Misael-art/sms-forge/tree/0cac1e369f687026375c2eafa0af019dbcb435bf/SMS_projects/hamoopig).
A remoção é um commit normal; o histórico do repositório permanece disponível.
Trabalho local nunca commitado continua apenas no host.

O roteiro `tools/sms_wrapper/session_bridge/consumer_acceptance.py`, específico
do par MUGEN/HAMOOPIG, permanece como replay histórico: exige `--legacy` e as
ROMs antigas locais. Sua execução padrão é recusada antes de iniciar sessões.
A validação ativa da infraestrutura usa `session_bridge/acceptance.py`; não
foram substituídas ROMs ou endereços de probes arbitrariamente.

Lições canônicas, registros de curadoria e medições anteriores são mantidos
como histórico técnico. Essas citações não tornam o projeto ativo nem provam
resultados nas ROMs atuais. Não houve execução de testes ou de emuladores
nesta retirada.

### Reconciliação de 21/10/2026

O snapshot de continuidade `bdb32e7` voltou a rastrear 108 arquivos do projeto
apesar do ignore. A curadoria reaplica a retirada já autorizada em commit
normal: o diretório deixa o índice da branch de curadoria; a cópia original
do workspace e o histórico permanecem. `.gitignore` não remove arquivos já
versionados. Snapshots futuros devem cotejar este registro com o índice.
