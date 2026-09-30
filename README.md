# Node Activity Alerts

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

## Files

- `START_HERE.md` — easiest setup instructions
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

## Intended use

This is a convenience notification tool for amateur-radio activity. It is not an emergency-alert system.

73
