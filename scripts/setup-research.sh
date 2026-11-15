#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv research/.venv
research/.venv/bin/python -m pip install -r research/requirements.lock
mkdir -p research/upstream
if [ ! -d research/upstream/searxng/.git ]; then
  git clone --depth 1 --no-checkout https://github.com/searxng/searxng.git research/upstream/searxng
fi
git -C research/upstream/searxng fetch --depth 1 origin a7128d5d1d5af2837a68fbeaaee9c3e8391aa9cf
git -C research/upstream/searxng checkout --detach a7128d5d1d5af2837a68fbeaaee9c3e8391aa9cf
research/.venv/bin/python -m playwright install chromium
