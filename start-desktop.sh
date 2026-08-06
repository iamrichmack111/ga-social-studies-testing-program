#!/usr/bin/env bash
set -euo pipefail
D="$(cd "$(dirname "${BASH_SOURCE[0]}")"&&pwd)"; P="$D/.venv/bin/python"; U="http://127.0.0.1:5085"; L="$HOME/.local/state/ga-social-studies-testing-program/app.log"
mkdir -p "$(dirname "$L")" "$HOME/KIDS-HW/grades"
if ! curl -fsS "$U/health" >/dev/null 2>&1;then cd "$D";nohup "$P" app.py >>"$L" 2>&1 &;for _ in $(seq 1 40);do curl -fsS "$U/health" >/dev/null 2>&1&&break;sleep .25;done;fi
xdg-open "$U" >/dev/null 2>&1 &
