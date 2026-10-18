# openbor_sms_rev1 — consumidor da engine OpenBOR → SMS

Projeto consumidor da engine `tools/sms_wrapper/openbor2sms/` (infraestrutura do
wrapper — **não editar lógica de engine aqui**). O objetivo é converter módulos
OpenBOR (pilotos: Golden Axe Legend e Battletoads) em dados + runtime para o
Sega Master System, começando por um recorte jogável real e medido.

- **Estado atual:** O0 (intake) fechado em 2026-10-15 — bootstrap, pilotos
  escolhidos, PAKs/licenças/SHAs revalidados e inventário de dependências
  portado com origem; fronteira de compatibilidade v0 registrada em
  `doc/artifacts/o0_pilot_compatibility_boundary_20261015.json`.
- **Próximo lote:** O1 — front-end neutro (PAK/model/level IR, diffs, casos
  inválidos), separando a emissão MD do doador.

## Comandos (do diretório do projeto)

```sh
./build.sh   # delega ao wrapper: pre-gates -> sdcc -> makesms
./clean.sh
./run.sh     # exige ROM buildada + emulador configurado
```

Nada de lógica de build aqui. Nada de API inventada: confira
`sdk/devkitSMS/SMSlib/SMSlib.h`.

## Organização de dados (registro único: `doc/artifact_registry.json`)

| Location | O que vive aqui | Nunca |
|----------|-----------------|-------|
| `data/source_openbor/` | fontes OpenBOR sob controle explícito (subconjuntos extraídos do PAK para import/IR) | PAK completo como recurso publicável |
| `data/generated/` | intermediários gerados pelo host (intake, dependências, IR) | virar `res/` |
| `res/` | recursos integrados **só após gates de produção** | arte/proveniência não aprovada |
| `doc/artifacts/` | planilhas/contratos/registros de decisão | provar runtime sozinho |

## Fontes e licenças

- Doador SGDK-Forge: **read-only**; hashes revalidados antes de ler/copiar.
- OpenBOR pin `787b6770409935137579715febf80cf7a529b748`: referência semântica
  **condicional** (extrato parcial), não origem demonstrada dos módulos.
- PAKs: origem externa/versão original **desconhecidas**; assets **não
  publicáveis**; licença do importador não licencia redistribuição de
  personagens.

## Regra de ferro

**"Se não foi visto rodando no emulador, não existe."**
`documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget`.
