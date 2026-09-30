#!/usr/bin/env python3
import configparser
import os
import re
import subprocess
import time
from datetime import datetime

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")

cfg = configparser.ConfigParser()
if not cfg.read(CONFIG_FILE):
    raise SystemExit("config.ini not found. Copy config.ini.example to config.ini and edit it.")

section = cfg["alerts"]
NTFY_TOPIC = section.get("NTFY_TOPIC", "").strip()
NODE = section.get("ALLSTAR_NODE", "").strip()
RESET_SECONDS = section.getint("QUIET_RESET_SECONDS", fallback=180)
QUIET_START = section.get("QUIET_HOURS_START", "23:00").strip()
QUIET_END = section.get("QUIET_HOURS_END", "07:00").strip()
POLL_SECONDS = 5

if not NTFY_TOPIC or NTFY_TOPIC == "change-this-to-a-private-topic":
    raise SystemExit("Set NTFY_TOPIC in config.ini first.")
if not NODE or NODE == "12345":
    raise SystemExit("Set ALLSTAR_NODE in config.ini first.")

def hm(value):
    h, m = value.split(":", 1)
    return int(h) * 60 + int(m)

def in_quiet_hours():
    now = datetime.now()
    cur = now.hour * 60 + now.minute
    start = hm(QUIET_START)
    end = hm(QUIET_END)
    if start == end:
        return False
    if start < end:
        return start <= cur < end
    return cur >= start or cur < end

def push(title, body):
    if in_quiet_hours():
        print(f"[quiet hours] {title}: {body}", flush=True)
        return
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            headers={"Title": title},
            data=body.encode("utf-8"),
            timeout=10,
        ).raise_for_status()
    except Exception as exc:
        print(f"Push failed: {exc}", flush=True)

def read_vars():
    cmd = ["sudo", "/usr/sbin/asterisk", "-rx", f"rpt show variables {NODE}"]
    text = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=10)
    values = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return values

def keyed_remote_nodes(alinks):
    nodes = []
    # Typical direct-link tokens look like 43004TK.
    for token in re.split(r"[,\s]+", alinks or ""):
        token = token.strip()
        m = re.match(r"(\d+).*K$", token, re.I)
        if m:
            nodes.append(m.group(1))
    return nodes

active = False
last_remote = 0.0

print(f"AllStar node {NODE} remote-activity watcher ONLINE", flush=True)
print("Local RF key-ups: ignored", flush=True)
print("Remote linked activity: alerts", flush=True)
print(f"Polling every {POLL_SECONDS} seconds", flush=True)
print(f"Quiet hours: {QUIET_START} -> {QUIET_END}", flush=True)
print("-" * 46, flush=True)

while True:
    now = time.time()
    try:
        v = read_vars()
        tx = v.get("RPT_TXKEYED", "0") == "1"
        rx = v.get("RPT_RXKEYED", "0") == "1"
        remotes = keyed_remote_nodes(v.get("RPT_ALINKS", ""))
        remote_active = tx and not rx and bool(remotes)

        if remote_active:
            last_remote = now
            if not active:
                source = ", ".join(remotes)
                print(f"Incoming AllStar activity from {source}", flush=True)
                push(f"AllStar {NODE}", f"Incoming linked activity from node {source}")
                active = True
        elif active and now - last_remote >= RESET_SECONDS:
            active = False
            print("--- activity reset ---", flush=True)

    except subprocess.CalledProcessError as exc:
        print(f"Asterisk command failed: {exc.output.strip()}", flush=True)
    except Exception as exc:
        print(f"Watcher error: {exc}", flush=True)

    time.sleep(POLL_SECONDS)
