#!/usr/bin/env bash
#
# reporte_cambios.sh — Genera un reporte Markdown de los commits hechos
# en un rango de fechas (pensado para "qué cambió en mis últimas N
# sesiones de Claude Code en VS Code").
#
# Uso:
#   ./reporte_cambios.sh "3 days ago"
#   ./reporte_cambios.sh "2026-06-15"
#   ./reporte_cambios.sh "1 week ago" "2026-06-20"   (desde / hasta)
#
# Si no se pasa nada, usa "7 days ago" por defecto.
# El reporte se guarda en reporte_cambios_<fecha>.md en el directorio actual.

set -euo pipefail

DESDE="${1:-7 days ago}"
HASTA="${2:-now}"

if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "Error: este script debe correrse dentro de un repositorio git." >&2
  exit 1
fi

REPO_NOMBRE=$(basename "$(git rev-parse --show-toplevel)")
RAMA=$(git rev-parse --abbrev-ref HEAD)
OUT="reporte_cambios_$(date +%Y%m%d_%H%M%S).md"

# Rango de commits según fechas
COMMITS=$(git log --since="$DESDE" --until="$HASTA" --reverse --pretty=format:"%H")

if [ -z "$COMMITS" ]; then
  echo "No se encontraron commits entre '$DESDE' y '$HASTA' en la rama '$RAMA'."
  exit 0
fi

TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')

{
  echo "# Reporte de cambios — $REPO_NOMBRE"
  echo ""
  echo "- **Rama:** \`$RAMA\`"
  echo "- **Rango:** desde \"$DESDE\" hasta \"$HASTA\""
  echo "- **Commits encontrados:** $TOTAL"
  echo "- **Generado:** $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  echo "---"
  echo ""

  while IFS= read -r hash; do
    FECHA=$(git show -s --format="%ad" --date=format:"%Y-%m-%d %H:%M" "$hash")
    AUTOR=$(git show -s --format="%an" "$hash")
    MSG=$(git show -s --format="%s" "$hash")
    HASH_CORTO=$(git rev-parse --short "$hash")

    echo "## \`$HASH_CORTO\` — $MSG"
    echo ""
    echo "- **Fecha:** $FECHA"
    echo "- **Autor:** $AUTOR"
    echo ""
    echo "**Archivos modificados:**"
    echo ""
    echo '```'
    git show --stat --format="" "$hash"
    echo '```'
    echo ""
    echo "---"
    echo ""
  done <<< "$COMMITS"

  echo ""
  echo "## Resumen acumulado de archivos tocados"
  echo ""
  echo '```'
  git diff --stat "$(echo "$COMMITS" | head -1)"^ "$(echo "$COMMITS" | tail -1)" 2>/dev/null \
    || echo "(no se pudo calcular el diff acumulado — probablemente el primer commit del rango no tiene padre)"
  echo '```'

} > "$OUT"

echo "Reporte generado: $OUT"
echo "Commits incluidos: $TOTAL"
