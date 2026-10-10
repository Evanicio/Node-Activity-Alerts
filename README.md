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
- `install_allstar_permissions.sh` — installs and verifies the narrowly scoped Asterisk sudo permission for ASL3

## AllStar permission requirement

On ASL3, the AllStar watcher reads Asterisk link state using
`sudo /usr/sbin/asterisk -rx "rpt show variables NODE"`.
Because the watcher runs unattended, the Linux user needs a passwordless
sudo rule restricted to that **exact command and node**. Otherwise the
service may stay active while detection fails with `sudo: a terminal is required`.

For example, on a Pi running node 46651 as user `admin`, the rule is:

```sudoers
admin ALL=(root) NOPASSWD: /usr/sbin/asterisk -rx rpt show variables 46651
```

Use `bash ~/install_allstar_permissions.sh 46651` on that Pi after copying
the script to the home directory. For other stations, substitute their own
node number. The installer uses the current Linux username, validates the
sudoers rule, and tests it without cached credentials. See `START_HERE.md`
for full setup instructions. This is an installation requirement, **not a
change to either watcher's detection logic**.

## Important privacy note

Your ntfy topic acts like an address for your notifications. Use a long, private topic name and **do not publish it**.

Example:

`kp4abc-radio-58392-x7q`

## Intended use

This is a convenience notification tool for amateur-radio activity. It is not an emergency-alert system.

73
