# Node Activity Alerts

## ⬇️ DOWNLOAD LATEST VERSION

**[CLICK HERE TO DOWNLOAD NODE ACTIVITY ALERTS (.ZIP)](https://github.com/Evanicio/Node-Activity-Alerts/archive/refs/heads/main.zip)**

After downloading:

1. Open the ZIP.
2. Extract the folder.
3. Open **START_HERE.md**.
4. Follow Option A, B, or C.

No GitHub knowledge required.

---

Simple push notifications for amateur-radio activity.

**Node Activity Alerts** can watch:

- a BrandMeister DMR talkgroup
- an ASL3 / AllStar node

Notifications are delivered with the free **ntfy** app.

The goal is simple: install it once, leave it running, and get a phone alert when somebody shows up.

## Start here

Open **START_HERE.md** and follow the steps in order.

## What it does

### DMR
- Watches one BrandMeister talkgroup.
- Sends one alert when a callsign becomes active.
- Does not repeatedly alert for the same callsign during the same conversation.
- Can ignore your own callsign.
- Re-arms after a configurable quiet period.

### AllStar
- Watches one local ASL3 node.
- Alerts on incoming linked-network activity.
- Ignores local RF PTT activity.
- Re-arms after a configurable quiet period.

### Quiet hours
Both watchers can continue running while phone notifications are suppressed overnight.

## FAQ

### Will it alert me for every transmission?
No. Nearby transmissions are treated as one conversation. After the configured quiet period passes with no matching activity, the watcher re-arms for the next conversation.

### Does my computer have to stay on?
Only if you use the Windows DMR option. When installed as a systemd service on a Raspberry Pi or ASL3 node, the watcher keeps running in the background after SSH is closed.

### Does it survive a reboot?
Yes, when the included systemd services are installed and enabled.

### Will my own transmissions trigger an alert?
The DMR watcher can ignore the callsign configured in `CALLSIGN`. The AllStar watcher ignores local RF key-ups and watches incoming linked-network activity.

### What are quiet hours?
The watcher continues running, but phone notifications are suppressed between `QUIET_HOURS_START` and `QUIET_HOURS_END`.

### How do I change how long it waits before another alert?
Edit this setting in `config.ini`:

```ini
QUIET_RESET_SECONDS=180
```

For example, `60` means the watcher can re-arm after 60 seconds of matching silence.

## Troubleshooting

See **[SUPPORT.md](SUPPORT.md)** for copy/paste diagnostics, common problems, and what information to include when asking for help.

Useful quick checks:

```bash
systemctl status dmr-watcher --no-pager
systemctl status allstar-watcher --no-pager
```

Live logs:

```bash
journalctl -u dmr-watcher -f
journalctl -u allstar-watcher -f
```

## Files

- `START_HERE.md` — easiest setup instructions
- `SUPPORT.md` — FAQ, troubleshooting, and support diagnostics
- `config.ini.example` — settings template
- `dmr_watcher.py` — BrandMeister DMR watcher
- `allstar_watcher.py` — AllStar watcher
- `requirements.txt` — Python packages
- `Start_DMR_Watcher.bat` — Windows DMR launcher
- `dmr-watcher.service` — Linux/systemd DMR service
- `allstar-watcher.service` — Linux/systemd AllStar service
- `install_services.sh` — service installer

## Important privacy note

Your ntfy topic acts like an address for your notifications. Use a long, private topic name and **do not publish it**.

Example:

`kp4abc-radio-58392-x7q`

When posting logs or opening a GitHub issue, remove your private ntfy topic if it appears anywhere in the output.

## Intended use

This is a convenience notification tool for amateur-radio activity. It is not an emergency-alert system.

73
