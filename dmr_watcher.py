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
FRESH_SESSION_WINDOW = 30


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

MY_CALL = section.get("CALLSIGN", "").strip().upper()
NTFY_TOPIC = section.get("NTFY_TOPIC", "").strip()
TG = str(section.get("DMR_TALKGROUP", "3300")).strip()
RESET_SECONDS = section.getint("QUIET_RESET_SECONDS", fallback=180)
QUIET_START = section.get("QUIET_HOURS_START", "23:00").strip()
QUIET_END = section.get("QUIET_HOURS_END", "07:00").strip()

if not NTFY_TOPIC or NTFY_TOPIC == "change-this-to-a-private-topic":
    raise SystemExit("Set NTFY_TOPIC in config.ini first.")


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
    # BrandMeister commonly wraps the JSON call data inside data["payload"].
    if isinstance(data, dict) and "payload" in data:
        payload = data["payload"]
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except Exception:
                pass
        if isinstance(payload, (dict, list)):
            return payload

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
    value = find_value(
        obj,
        [
            "DestinationID",
            "destination",
            "dst",
            "dstid",
            "destinationid",
            "talkgroup",
            "tg",
            "group",
        ],
    )

    if value is None:
        raw = json.dumps(obj)
        match = re.search(
            r'"(?:DestinationID|Destination|DstId|Talkgroup|TG)"\s*:\s*"?([0-9]+)',
            raw,
            re.I,
        )
        return match.group(1) if match else None

    if isinstance(value, dict):
        value = find_value(value, ["id", "dmrid", "number"])

    return str(value).strip() if value is not None else None


def get_call(obj):
    value = find_value(obj, ["SourceCall", "callsign", "call", "sourcecallsign"])
    return str(value).strip().upper() if value else ""


def get_name(obj):
    value = find_value(obj, ["SourceName", "name", "firstname", "displayname"])
    return str(value).strip() if value else ""


def get_event(obj):
    value = find_value(obj, ["Event", "event", "eventtype", "type", "status"])
    if value:
        return str(value)

    raw = json.dumps(obj)
    for candidate in ("Session-Start", "Session-Update", "Session-Stop"):
        if candidate.lower() in raw.lower():
            return candidate

    return ""


sio = socketio.Client(reconnection=True, logger=False, engineio_logger=False)

fresh_sessions = {}
notified_calls = set()
last_tg_activity = 0.0


def reset_if_quiet(now):
    global last_tg_activity

    if last_tg_activity and now - last_tg_activity >= RESET_SECONDS:
        fresh_sessions.clear()
        notified_calls.clear()
        last_tg_activity = 0.0
        log(
            f"Conversation reset after {RESET_SECONDS} seconds quiet — "
            "watcher ARMED again"
        )


@sio.event
def connect():
    log("Connected to BrandMeister")
    sio.emit("join", "everything")
    log(f"DMR TG {TG} watcher ONLINE")
    log(f"{MY_CALL or 'Own callsign'}: ignored for phone alerts")
    log(f"Conversation re-arm: {RESET_SECONDS} seconds of TG silence")
    log(f"Quiet hours: {QUIET_START} -> {QUIET_END}")
    log("Watcher ARMED and ready")


@sio.event
def disconnect():
    log("BrandMeister disconnected; reconnecting...")


@sio.on("mqtt")
def on_mqtt(data):
    global last_tg_activity

    now = time.time()
    reset_if_quiet(now)

    obj = normalize_payload(data)

    if get_tg(obj) != TG:
        return

    event = get_event(obj).lower()
    callsign = get_call(obj)
    name = get_name(obj)

    if "start" in event or "update" in event:
        last_tg_activity = now

        if not callsign:
            return

        fresh_sessions[callsign] = now
        label = f"{callsign} {name}".strip()

        if MY_CALL and callsign == MY_CALL:
            log(f"{label} — local only")
            return

        if callsign in notified_calls:
            log(f"{label} — already alerted in this conversation")
            return

        body = f"{callsign}"
        if name:
            body += f" ({name})"
        body += f" is active on BrandMeister TG {TG}."

        try:
            sent = push(f"DMR TG {TG} Active", body)
            notified_calls.add(callsign)

            if sent:
                log(f"{label} — PHONE ALERT SENT")
            else:
                log(f"{label} — quiet hours, no phone alert")

        except Exception as exc:
            log(f"{label} — push failed: {exc}")

        return

    if "stop" in event:
        if not callsign:
            return

        # BrandMeister can generate delayed/orphan Session-Stop packets.
        # Only let a stop extend conversation activity when tied to a recent
        # Start/Update for the same callsign.
        last_live = fresh_sessions.get(callsign, 0)
        if last_live and now - last_live <= FRESH_SESSION_WINDOW:
            last_tg_activity = now
            fresh_sessions.pop(callsign, None)


log(f"Starting DMR TG {TG} watcher")

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
        log("Watcher stopped.")
        break

    except Exception as exc:
        log(f"Connection error: {exc}; retrying in 10 seconds")
        time.sleep(10)
