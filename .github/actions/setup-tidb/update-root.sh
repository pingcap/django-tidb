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

# Update root.json, the TiUP trusted root pinned next to this script, to the
# latest version published on the TiUP mirror.
#
# Usage: update-root.sh
#
# TiUP itself does the verification: starting from the pinned root.json, it
# downloads each newer root (N+1.root.json, N+2.root.json, ...) and checks that
# it is signed by the threshold of keys of the previous one. Only a root that
# passed this chain of checks is written back. Review and commit the change.

set -euo pipefail

TIUP_MIRROR="https://tiup-mirrors.pingcap.com"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_JSON="$SCRIPT_DIR/root.json"

root_info() {
  python3 -c '
import json, sys
signed = json.load(open(sys.argv[1]))["signed"]
print(signed["version"], signed["expires"])
' "$1"
}

case "$(uname -s)" in
  Linux) os=linux ;;
  Darwin) os=darwin ;;
  *) echo "Unsupported OS: $(uname -s)" >&2; exit 1 ;;
esac
case "$(uname -m)" in
  x86_64 | amd64) arch=amd64 ;;
  aarch64 | arm64) arch=arm64 ;;
  *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

# Use a fresh TiUP home, so neither an existing TiUP installation nor its
# cached metadata is involved.
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin"
curl --proto '=https' --tlsv1.2 -fsSL --retry 3 \
  "$TIUP_MIRROR/tiup-$os-$arch.tar.gz" | tar -xz -C "$work/bin"
cp "$ROOT_JSON" "$work/bin/root.json"

# Any command that reads the mirror makes TiUP update its root first. Without
# a mirror configured, TiUP uses the official one ($TIUP_MIRROR).
TIUP_HOME="$work" "$work/bin/tiup" list tidb > /dev/null

read -r old_version old_expires < <(root_info "$ROOT_JSON")
if [[ ! -f "$work/manifests/root.json" ]]; then
  echo "root.json is already the latest: version $old_version, expires $old_expires."
  exit 0
fi

read -r new_version new_expires < <(root_info "$work/manifests/root.json")
if ((new_version <= old_version)); then
  echo "root.json is already the latest: version $old_version, expires $old_expires."
  exit 0
fi

cp "$work/manifests/root.json" "$ROOT_JSON"
echo "Updated root.json from version $old_version (expires $old_expires)"
echo "to version $new_version (expires $new_expires)."
