#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x research/.venv/bin/python ]; then
  bash scripts/setup-research.sh
fi
exec research/.venv/bin/python research/server.py
