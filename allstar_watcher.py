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
POLL_SECONDS = 5


def load_config(path):
    if not os.path.exists(path):
        raise SystemExit("config.ini not found. Copy config.ini.example to config.ini and edit it.")

    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()

    # Support both the current [alerts] format and the older plain KEY=value format.
    if not re.search(r"^\s*\[alerts\]\s*$", raw, re.M | re.I):
        raw = "[alerts]\n" + raw

    parser = configparser.ConfigParser()
    parser.read_string(raw)
    return parser["alerts"]


section = load_config(CONFIG_FILE)

NTFY_TOPIC = section.get("NTFY_TOPIC", "").strip()
NODE = section.get("ALLSTAR_NODE", "").strip()
RESET_SECONDS = section.getint("QUIET_RESET_SECONDS", fallback=180)
QUIET_START = section.get("QUIET_HOURS_START", "23:00").strip()
QUIET_END = section.get("QUIET_HOURS_END", "07:00").strip()

if not NTFY_TOPIC or NTFY_TOPIC == "change-this-to-a-private-topic":
    raise SystemExit("Set NTFY_TOPIC in config.ini first.")
if not NODE or NODE == "12345":
    raise SystemExit("Set ALLSTAR_NODE in config.ini first.")


def log(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


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
        log(f"QUIET HOURS — phone alert suppressed: {body}")
        return False

    response = requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        headers={"Title": title, "Priority": "4"},
        data=body.encode("utf-8"),
        timeout=15,
    )
    response.raise_for_status()
    return True


def read_vars():
    cmd = ["sudo", "/usr/sbin/asterisk", "-rx", f"rpt show variables {NODE}"]
    text = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=10)

    values = {}
    for line in text.splitlines():
        line = line.strip()
        if "=" in line and line.startswith("RPT_"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def keyed_remote_nodes(alinks):
    nodes = []

    # Typical direct-link token: 43004TK
    # Final K means that linked node is currently keyed.
    for token in re.split(r"[,\s]+", alinks or ""):
        token = token.strip()
        match = re.match(r"(\d+).*K$", token, re.I)
        if match:
            nodes.append(match.group(1))

    return nodes


conversation_armed = True
last_remote_activity = 0.0
was_remote_active = False

log(f"AllStar node {NODE} remote-activity watcher ONLINE")
log("Local RF key-ups: ignored")
log("Remote linked activity: alerts")
log(f"Polling every {POLL_SECONDS} seconds")
log(f"Conversation re-arm: {RESET_SECONDS} seconds of complete remote silence")
log(f"Quiet hours: {QUIET_START} -> {QUIET_END}")
log("Watcher ARMED and ready")


while True:
    try:
        vars_ = read_vars()

        rx_keyed = vars_.get("RPT_RXKEYED", "0") == "1"
        tx_keyed = vars_.get("RPT_TXKEYED", "0") == "1"
        remote_nodes = keyed_remote_nodes(vars_.get("RPT_ALINKS", ""))

        # Remote AllStar audio:
        #   TX keyed
        #   local RF receiver not keyed
        #   directly linked remote node marked keyed
        remote_active = tx_keyed and not rx_keyed and bool(remote_nodes)

        now = time.time()

        if remote_active:
            last_remote_activity = now

            # Log only at the beginning of each remote transmission burst.
            if not was_remote_active:
                source = ", ".join(remote_nodes)
                log(f"Remote AllStar activity detected from node(s): {source}")

                if conversation_armed:
                    body = f"AllStar node {NODE} is active from linked node"
                    body += "s " if len(remote_nodes) > 1 else " "
                    body += f"{source}."

                    try:
                        sent = push(f"AllStar {NODE} Active", body)
                        if sent:
                            log("PHONE ALERT SENT")
                        conversation_armed = False
                        log(
                            f"Conversation alert DISARMED until {RESET_SECONDS} seconds "
                            "of complete remote silence"
                        )
                    except Exception as exc:
                        log(f"Push failed: {exc}")
                else:
                    log("Phone alert suppressed — same active conversation")

        elif conversation_armed is False and last_remote_activity:
            quiet_for = now - last_remote_activity
            if quiet_for >= RESET_SECONDS:
                conversation_armed = True
                log(
                    f"Conversation reset after {RESET_SECONDS} seconds quiet — "
                    "watcher ARMED again"
                )

        was_remote_active = remote_active
        time.sleep(POLL_SECONDS)

    except KeyboardInterrupt:
        log("Watcher stopped.")
        break
    except subprocess.CalledProcessError as exc:
        log(f"Asterisk command failed: {exc.output.strip()}")
        time.sleep(5)
    except Exception as exc:
        log(f"Watcher error: {exc}")
        time.sleep(5)
