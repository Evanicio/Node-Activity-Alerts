#!/usr/bin/env python3
import configparser
import json
import os
import re
import time
from datetime import datetime

import requests
import socketio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")

cfg = configparser.ConfigParser()
if not cfg.read(CONFIG_FILE):
    raise SystemExit("config.ini not found. Copy config.ini.example to config.ini and edit it.")

section = cfg["alerts"]
MY_CALL = section.get("CALLSIGN", "").strip().upper()
NTFY_TOPIC = section.get("NTFY_TOPIC", "").strip()
TG = str(section.get("DMR_TALKGROUP", "3300")).strip()
RESET_SECONDS = section.getint("QUIET_RESET_SECONDS", fallback=180)
QUIET_START = section.get("QUIET_HOURS_START", "23:00").strip()
QUIET_END = section.get("QUIET_HOURS_END", "07:00").strip()

if not NTFY_TOPIC or NTFY_TOPIC == "change-this-to-a-private-topic":
    raise SystemExit("Set NTFY_TOPIC in config.ini first.")

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

def find_value(obj, keys):
    wanted = {k.lower() for k in keys}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in wanted and v not in (None, ""):
                return v
        for v in obj.values():
            found = find_value(v, keys)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_value(item, keys)
            if found not in (None, ""):
                return found
    return None

def normalize_payload(data):
    if isinstance(data, (dict, list)):
        return data
    if isinstance(data, bytes):
        data = data.decode("utf-8", "ignore")
    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception:
            return {"raw": data}
    return {"raw": str(data)}

def get_tg(obj):
    value = find_value(obj, ["destination", "dst", "dstid", "destinationid", "talkgroup", "tg", "group"])
    if value is None:
        raw = json.dumps(obj)
        m = re.search(r'"(?:Destination|DstId|Talkgroup|TG)"\s*:\s*"?([0-9]+)', raw, re.I)
        return m.group(1) if m else None
    if isinstance(value, dict):
        value = find_value(value, ["id", "dmrid", "number"])
    return str(value).strip() if value is not None else None

def get_call(obj):
    value = find_value(obj, ["callsign", "call", "sourcecallsign"])
    if value:
        return str(value).strip().upper()
    return ""

def get_name(obj):
    value = find_value(obj, ["name", "firstname", "displayname"])
    return str(value).strip() if value else ""

def get_event(obj):
    value = find_value(obj, ["event", "eventtype", "type", "status"])
    if value:
        return str(value)
    raw = json.dumps(obj)
    for candidate in ("Session-Start", "Session-Update", "Session-Stop"):
        if candidate.lower() in raw.lower():
            return candidate
    return ""

sio = socketio.Client(reconnection=True, logger=False, engineio_logger=False)
fresh = {}
notified = {}
last_any_activity = 0.0

def expire_conversation(now):
    global last_any_activity
    if last_any_activity and now - last_any_activity >= RESET_SECONDS:
        fresh.clear()
        notified.clear()
        last_any_activity = 0.0
        print("--- conversation reset ---", flush=True)

@sio.event
def connect():
    print("Connected to BrandMeister", flush=True)
    sio.emit("join", "everything")

@sio.event
def disconnect():
    print("BrandMeister disconnected; reconnecting...", flush=True)

@sio.on("mqtt")
def on_mqtt(data):
    global last_any_activity
    now = time.time()
    expire_conversation(now)

    obj = normalize_payload(data)
    target = get_tg(obj)
    if target != TG:
        return

    event = get_event(obj)
    call = get_call(obj)
    name = get_name(obj)

    event_l = event.lower()
    if "start" in event_l or "update" in event_l:
        last_any_activity = now
        if call:
            fresh[call] = now
            label = f"{call} {name}".strip()
            if call == MY_CALL:
                print(f"{label} — local only", flush=True)
                return
            if call not in notified:
                print(f"{label} — activity", flush=True)
                push(f"DMR TG {TG}", f"{label} is active")
                notified[call] = now
        return

    if "stop" in event_l:
        if not call:
            return
        # BrandMeister can produce late/orphan stop events. Accept only a stop
        # tied to very recent activity for that callsign.
        if now - fresh.get(call, 0) > 30:
            return
        last_any_activity = now

print(f"DMR TG {TG} watcher ONLINE", flush=True)
print(f"{MY_CALL or 'Own callsign'}: ignored for phone alerts", flush=True)
print(f"Quiet hours: {QUIET_START} -> {QUIET_END}", flush=True)
print("-" * 46, flush=True)

while True:
    try:
        sio.connect(
            "https://api.brandmeister.network",
            socketio_path="/lh/socket.io",
            transports=["websocket"],
            wait_timeout=20,
        )
        sio.wait()
    except KeyboardInterrupt:
        break
    except Exception as exc:
        print(f"Connection error: {exc}; retrying in 10 seconds", flush=True)
        time.sleep(10)
