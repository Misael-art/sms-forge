#!/usr/bin/env bash
# new_project.sh <nome> — instancia o modelo em SMS_projects/<nome>/
#
# Contrato: um projeto recem-criado nasce com a HIERARQUIA DE VERDADE completa
# (AGENTS.md niveis 1-7) e capaz de buildar. Este script FALHA se o modelo nao
# materializar isso — regra vira medicao, nunca so prosa (SMS_GLOBAL §21).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE/../.."
NAME="${1:-}"
[ -n "$NAME" ] || { echo "uso: new_project.sh <nome-slug>"; exit 3; }
[[ "$NAME" =~ ^[a-z0-9_]+$ ]] || { echo "[FAIL] nome deve ser slug [a-z0-9_]"; exit 3; }
DEST="$ROOT/SMS_projects/$NAME"
[ -e "$DEST" ] && { echo "[FAIL] $DEST ja existe"; exit 1; }

cp -r "$HERE/modelo" "$DEST"
find "$DEST" -name "*.sh" -exec chmod +x {} \;
# substitui o placeholder em TODO arquivo (inclui .mddev/project.json e doc/)
grep -rl "__PROJECT_NAME__" "$DEST" | while read -r f; do
  sed -i "s/__PROJECT_NAME__/$NAME/g" "$f"
done
mkdir -p "$DEST/rascunho" "$DEST/data" "$DEST/inc" "$DEST/res" "$DEST/out" "$DEST/.agent"
cat > "$DEST/.agent/README.md" <<EOF
.agent local de $NAME — MATERIALIZACAO.
Fonte canonica: tools/sms_wrapper/.agent/ (regras sempre ativas).
Politica: arquivo local existente NAO e sobrescrito pelo bootstrap.
EOF

# --- verificacao de materializacao (o gate do proprio bootstrap) ---
REQUIRED=(
  ".mddev/project.json"
  "doc/00-diretrizes-agente.md"
  "doc/10-memory-bank.md"
  "doc/11-gdd.md"
  "doc/12-roteiro.md"
  "doc/13-spec-cenas.md"
  "doc/15-tdd.md"
  "doc/artifact_registry.json"
  "src/main.c"
  "build.sh"
)
missing=()
for f in "${REQUIRED[@]}"; do
  [ -s "$DEST/$f" ] || missing+=("$f")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "[FAIL] modelo incompleto — projeto nasceria sem hierarquia de verdade:"
  for f in "${missing[@]}"; do echo "         falta (ou vazio): $f"; done
  echo "       corrija tools/sms_wrapper/modelo/ antes de criar projetos."
  rm -rf "$DEST"
  exit 1
fi
if grep -rq "__PROJECT_NAME__" "$DEST"; then
  echo "[FAIL] placeholder __PROJECT_NAME__ sobrou apos substituicao:"
  grep -rl "__PROJECT_NAME__" "$DEST" | sed 's/^/         /'
  rm -rf "$DEST"
  exit 1
fi

echo "[OK] projeto instanciado: $DEST"
echo "     hierarquia de verdade materializada (${#REQUIRED[@]} arquivos)"
echo "proximo passo: preencher $DEST/doc/11-gdd.md e rodar $NAME/build.sh"
