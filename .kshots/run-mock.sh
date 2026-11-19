#!/usr/bin/env bash
# Box-only launcher: mock inference server + real `hermes serve` + built Electron app.
# Runs inside an isolated omabox; HERMES_HOME and userData are throwaway temp dirs.
set -euo pipefail
export PATH="/home/meshvault3/.local/share/mise/installs/node/26.12.1/bin:$PATH"
cd "$(dirname "$0")/.."
exec node tests-js/scripts/mock-server.ts
