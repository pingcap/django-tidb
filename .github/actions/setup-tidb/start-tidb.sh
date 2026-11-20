#!/bin/bash
# Copyright 2026 PingCAP, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# See the License for the specific language governing permissions and
# limitations under the License.

# Start a local TiDB cluster (PD + TiKV + TiDB, optionally TiFlash) with
# `tiup playground` in the background and wait until it is ready.
#
# Usage: start-tidb.sh <tidb-version> [tiflash-count]
#
# Normally invoked through the setup-tidb action (action.yml in this directory).

set -euo pipefail

TIDB_VERSION="${1:?usage: start-tidb.sh <tidb-version> [tiflash-count]}"
TIFLASH_COUNT="${2:-0}"
TIMEOUT_SECONDS="${TIDB_START_TIMEOUT:-600}"
MAX_ATTEMPTS="${TIDB_START_ATTEMPTS:-3}"
TIUP_MIRROR="https://tiup-mirrors.pingcap.com"
LOG_FILE="${TIDB_PLAYGROUND_LOG:-${RUNNER_TEMP:-/tmp}/tiup-playground.log}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIUP_HOME="${TIUP_HOME:-$HOME/.tiup}"

# Install TiUP and trust the root.json pinned next to this script. The official
# installer instead runs `tiup mirror set` without --root, which trusts the
# mirror's root.json (version 2) and walks the whole root chain (version 3 to
# the latest) at runtime. In CI that walk intermittently failed verification
# ("no trusted root in the local manifests"). Refresh the pinned root.json
# with update-root.sh (see check_trusted_root below).
install_tiup() {
  local os arch
  case "$(uname -s)" in
    Linux) os=linux ;;
    Darwin) os=darwin ;;
    *) echo "Unsupported OS: $(uname -s)" >&2; return 1 ;;
  esac
  case "$(uname -m)" in
    x86_64 | amd64) arch=amd64 ;;
    aarch64 | arm64) arch=arm64 ;;
    *) echo "Unsupported architecture: $(uname -m)" >&2; return 1 ;;
  esac

  mkdir -p "$TIUP_HOME/bin"
  curl --proto '=https' --tlsv1.2 -fsSL --retry 3 \
    "$TIUP_MIRROR/tiup-$os-$arch.tar.gz" | tar -xz -C "$TIUP_HOME/bin"
  chmod 755 "$TIUP_HOME/bin/tiup"
  reset_trusted_root
}

# Trust the pinned root.json, dropping any cached mirror metadata.
reset_trusted_root() {
  TIUP_HOME="$TIUP_HOME" "$TIUP_HOME/bin/tiup" mirror set "$TIUP_MIRROR" \
    --root "$SCRIPT_DIR/root.json" --silent
}

# Warn when the pinned root.json should be refreshed with update-root.sh:
# - the TiUP mirror has published a newer root. TiUP then downloads and
#   verifies it on every run, the step that used to fail intermittently.
# - the pinned root expires within ROOT_EXPIRY_WARN_DAYS days. TiUP can still
#   update from an expired root, but only while the mirror has a newer one.
# Never fails the job.
check_trusted_root() {
  local message
  message="$(python3 - "$SCRIPT_DIR/root.json" "$TIUP_MIRROR/snapshot.json" \
    "${ROOT_EXPIRY_WARN_DAYS:-90}" <<'PY' 2>/dev/null
import datetime, json, sys, urllib.request

signed = json.load(open(sys.argv[1]))["signed"]
version, expires = signed["version"], signed["expires"]
messages = []
try:
    with urllib.request.urlopen(sys.argv[2], timeout=10) as response:
        latest = json.load(response)["signed"]["meta"]["/root.json"]["version"]
    if latest > version:
        messages.append(f"the TiUP mirror has root version {latest}")
except Exception:
    pass
expiry = datetime.datetime.fromisoformat(expires.replace("Z", "+00:00"))
days = (expiry - datetime.datetime.now(datetime.timezone.utc)).days
if days < int(sys.argv[3]):
    messages.append(f"it expires on {expires} ({days} days)")
if messages:
    print(f"Pinned TiUP root.json (version {version}) is outdated: "
          + "; ".join(messages)
          + ". Run .github/actions/setup-tidb/update-root.sh to refresh it.")
PY
)" || return 0
  if [[ -n "$message" ]]; then
    if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
      echo "::warning file=.github/actions/setup-tidb/root.json::$message"
    else
      echo "Warning: $message" >&2
    fi
  fi
}

# Only touch TiUP's metadata when this script installed TiUP itself, so a
# developer's existing TiUP setup is left alone when running it locally.
MANAGED_TIUP=0
if ! command -v tiup >/dev/null 2>&1; then
  if [[ ! -x "$TIUP_HOME/bin/tiup" ]]; then
    install_tiup
  fi
  MANAGED_TIUP=1
  check_trusted_root
  export PATH="$TIUP_HOME/bin:$PATH"
  if [[ -n "${GITHUB_PATH:-}" ]]; then
    echo "$TIUP_HOME/bin" >> "$GITHUB_PATH"
  fi
fi

# Start the playground once and wait for it.
# Returns 0 when ready, 1 when the playground exited or timed out.
start_once() {
  nohup tiup playground "$TIDB_VERSION" \
    --mode tidb \
    --db 1 --pd 1 --kv 1 --tiflash "$TIFLASH_COUNT" \
    --db.port 4000 \
    --db.config "$SCRIPT_DIR/tidb.toml" \
    --without-monitor \
    > "$LOG_FILE" 2>&1 &
  local pid=$!

  for ((i = 0; i < TIMEOUT_SECONDS; i += 5)); do
    if grep -q "TiDB Playground Cluster is started" "$LOG_FILE"; then
      echo "TiDB is ready after ${i}s."
      return 0
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "tiup playground exited after ${i}s."
      return 1
    fi
    sleep 5
  done

  echo "TiDB did not start within ${TIMEOUT_SECONDS}s."
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  return 1
}

# Enforce CHECK constraints (TiDB >= 7.2 only; older versions do not have
# this variable and do not support CHECK constraints at all).
enable_check_constraints() {
  local version="${TIDB_VERSION#v}"
  local major="${version%%.*}" rest="${version#*.}"
  local minor="${rest%%.*}"
  if ((major > 7 || (major == 7 && minor >= 2))); then
    mysql --host 127.0.0.1 --port 4000 --user root \
      --execute "SET GLOBAL tidb_enable_check_constraint = ON"
    echo "Enabled tidb_enable_check_constraint."
  fi
}

for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
  echo "Starting TiDB $TIDB_VERSION (tiflash=$TIFLASH_COUNT), attempt $attempt/$MAX_ATTEMPTS..."
  if start_once; then
    enable_check_constraints
    exit 0
  fi
  echo "Playground log:"
  cat "$LOG_FILE"
  if ((attempt < MAX_ATTEMPTS)); then
    if ((MANAGED_TIUP)); then
      reset_trusted_root
    fi
    sleep $((attempt * 15))
  fi
done

echo "Failed to start TiDB after $MAX_ATTEMPTS attempts."
exit 1
