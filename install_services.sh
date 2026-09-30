#!/bin/bash
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"

if [ "$(basename "$HOME")" != "admin" ]; then
  echo "STOP: The included service files currently expect /home/admin."
  echo "Edit dmr-watcher.service and allstar-watcher.service for your username first."
  exit 1
fi

sudo cp "$HERE/dmr-watcher.service" /etc/systemd/system/
sudo cp "$HERE/allstar-watcher.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dmr-watcher.service allstar-watcher.service
sudo systemctl restart dmr-watcher.service allstar-watcher.service

echo
echo "Installed and started."
echo
systemctl --no-pager --full status dmr-watcher.service || true
echo
systemctl --no-pager --full status allstar-watcher.service || true
