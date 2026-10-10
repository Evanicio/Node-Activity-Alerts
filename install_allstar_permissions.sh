#!/usr/bin/env bash
# Install a narrowly scoped sudoers rule for the AllStar watcher.
set -euo pipefail
if [[ $# -ne 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "Usage: $0 ALLSTAR_NODE (numeric node ID)" >&2
  exit 2
fi
NODE="$1"
USER_NAME="$(id -un)"
if [[ ! "$USER_NAME" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
  echo "Unsupported Linux username: $USER_NAME" >&2
  exit 2
fi
if [[ ! -x /usr/sbin/asterisk ]]; then
  echo "/usr/sbin/asterisk not found" >&2
  exit 1
fi
TEMP="$(mktemp)"
trap 'rm -f "$TEMP"' EXIT
printf '%s ALL=(root) NOPASSWD: /usr/sbin/asterisk -rx rpt show variables %s\n' "$USER_NAME" "$NODE" > "$TEMP"
sudo visudo -cf "$TEMP"
echo "Installing /etc/sudoers.d/allstar-watcher for user $USER_NAME, node $NODE"
sudo install -o root -g root -m 0440 "$TEMP" /etc/sudoers.d/allstar-watcher
sudo visudo -cf /etc/sudoers.d/allstar-watcher
sudo -k
sudo -n /usr/sbin/asterisk -rx "rpt show variables $NODE" | grep -E 'RPT_(ALINKS|NUMLINKS)='
echo "AllStar watcher sudo permission verified."
