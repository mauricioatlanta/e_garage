#!/usr/bin/env bash
set -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLENDER_BIN="${BLENDER_BIN:-/tmp/egarage_blender_5_2_2/blender-5.2.2-linux-x64/blender}"
LOG_DIR="$ROOT_DIR/logs"
MODE="${1:-final}"
export XDG_CONFIG_HOME="$ROOT_DIR/.blender_config"
export XDG_CACHE_HOME="$ROOT_DIR/.blender_cache"
mkdir -p "$LOG_DIR" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
LOG_FILE="$LOG_DIR/${MODE}_$(date +%Y%m%d_%H%M%S).log"

case "$MODE" in
  draft) export SEDAN_DRAFT=front ;;
  preview) export SEDAN_PREVIEW=1 ;;
  final) unset SEDAN_DRAFT SEDAN_PREVIEW ;;
  *) echo "Uso: $0 [draft|preview|final]" >&2; exit 2 ;;
esac

"$BLENDER_BIN" --background -noaudio --factory-startup --disable-autoexec --python "$ROOT_DIR/build_from_cc0.py" 2>&1 | tee "$LOG_FILE"
status=${PIPESTATUS[0]}
printf 'EXIT_STATUS=%s\n' "$status" | tee -a "$LOG_FILE"
exit "$status"
