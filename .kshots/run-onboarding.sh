#!/usr/bin/env bash
# Box-only launcher: built Electron app with an empty throwaway HERMES_HOME (first-run onboarding).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
sandbox="$(mktemp -d /tmp/kodros-onboard-XXXXXX)"
mkdir -p "$sandbox/hermes-home" "$sandbox/user-data"
electron="$(readlink -f "$root/apps/desktop/node_modules/electron")/dist/electron"
export HERMES_HOME="$sandbox/hermes-home"
export HERMES_DESKTOP_USER_DATA_DIR="$sandbox/user-data"
export HERMES_DESKTOP_IGNORE_EXISTING=1
export HERMES_DESKTOP_HERMES_ROOT="$root"
export HERMES_DESKTOP_APP_NAME="KodrosOnboard-$$"
cd "$root/apps/desktop"
exec "$electron" "$root/apps/desktop" --disable-gpu --no-sandbox
