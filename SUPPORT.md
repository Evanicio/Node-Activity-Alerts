# Node Activity Alerts — Support & Troubleshooting

This page is for the classic support request:

> "It was working yesterday. Now it doesn't alert me."

Before changing anything, use the checks below. Most problems can be identified from the service status, recent log lines, and the watcher configuration.

---

## Quick diagnosis

### The log says `PHONE ALERT SENT`
The watcher detected activity and successfully attempted the ntfy push.

If the phone did not notify you, check the ntfy app, phone notification permissions, battery/background restrictions, and that the phone is subscribed to the same private topic configured on the watcher.

### The log says `Phone alert suppressed — same active conversation`
The watcher is working.

It has already sent an alert for the current conversation and is waiting for the configured quiet period before re-arming.

Check:

```ini
QUIET_RESET_SECONDS=180
```

The value is in seconds.

### The log says activity was detected, but the alert was suppressed because of quiet hours
The watcher is working normally. Notifications are intentionally suppressed between:

```ini
QUIET_HOURS_START=23:00
QUIET_HOURS_END=07:00
```

Also verify that the Raspberry Pi / ASL3 node has the correct local time.

### The service says `inactive`, `failed`, or keeps restarting
Check the detailed service log:

```bash
journalctl -u allstar-watcher -n 50 --no-pager
```

or:

```bash
journalctl -u dmr-watcher -n 50 --no-pager
```

---

# AllStar troubleshooting

## Check whether the watcher is running

```bash
systemctl status allstar-watcher --no-pager
```

Look for:

```text
Active: active (running)
```

## Watch the log live

```bash
journalctl -u allstar-watcher -f
```

Press `Ctrl+C` to stop viewing the log. This does not stop the service.

## Show the latest 50 log lines

```bash
journalctl -u allstar-watcher -n 50 --no-pager
```

## Check what ASL3 is reporting

Replace `YOUR_NODE` with your local AllStar node number:

```bash
sudo asterisk -rx "rpt show variables YOUR_NODE"
```

During incoming linked-network audio, values can look similar to:

```text
RPT_TXKEYED=1
RPT_RXKEYED=0
RPT_ALINKS=1,43004TK
```

The important idea is:

- `RPT_TXKEYED=1` can indicate your node is transmitting received linked audio.
- `RPT_RXKEYED=0` means the local RF receiver is not keyed.
- a linked node ending in `K` in `RPT_ALINKS` indicates a directly linked remote node is keyed.

The watcher uses this combination to distinguish incoming AllStar activity from a local RF key-up.

## Restart the AllStar watcher

```bash
sudo systemctl restart allstar-watcher
```

Then check:

```bash
journalctl -u allstar-watcher -n 20 --no-pager
```

---

# DMR troubleshooting

## Check whether the watcher is running

```bash
systemctl status dmr-watcher --no-pager
```

## Watch the log live

```bash
journalctl -u dmr-watcher -f
```

## Show the latest 50 log lines

```bash
journalctl -u dmr-watcher -n 50 --no-pager
```

## Restart the DMR watcher

```bash
sudo systemctl restart dmr-watcher
```

## Check the configured talkgroup and callsign

Open `config.ini` and verify:

```ini
CALLSIGN=YOURCALL
DMR_TALKGROUP=3300
```

The configured callsign can be ignored by the DMR watcher so your own activity does not repeatedly notify your phone.

---

# Configuration checks

The standard configuration file contains:

```ini
[alerts]
CALLSIGN=YOURCALL
NTFY_TOPIC=change-this-to-a-private-topic
DMR_TALKGROUP=3300
ALLSTAR_NODE=12345
QUIET_RESET_SECONDS=180
QUIET_HOURS_START=23:00
QUIET_HOURS_END=07:00
```

After changing `config.ini`, restart the applicable service:

```bash
sudo systemctl restart dmr-watcher
sudo systemctl restart allstar-watcher
```

Only restart the watcher or watchers you are actually using.

---

# Common problems

## "It alerted once, but not again"

Most likely the watcher is still treating the transmissions as one conversation.

Look in the log for:

```text
Phone alert suppressed — same active conversation
```

The watcher will re-arm after `QUIET_RESET_SECONDS` of matching silence.

## "AllStar is talking but I get no alert"

Run these while the remote station is actively talking:

```bash
sudo asterisk -rx "rpt show variables YOUR_NODE"
journalctl -u allstar-watcher -n 50 --no-pager
```

If the log shows:

```text
Remote AllStar activity detected
```

then detection is working. The lines immediately after it usually explain whether an alert was sent or suppressed.

## "Local RF triggers alerts"

The AllStar watcher is designed to ignore local RF key-ups. Capture both of these while the local radio is keyed:

```bash
sudo asterisk -rx "rpt show variables YOUR_NODE"
journalctl -u allstar-watcher -n 50 --no-pager
```

Include that output in a GitHub issue.

## "The watcher stops when I close SSH"

That normally means you are running the Python script manually rather than through systemd.

Check:

```bash
systemctl status dmr-watcher --no-pager
systemctl status allstar-watcher --no-pager
```

If you followed the Raspberry Pi / ASL3 installation in `START_HERE.md`, the service should continue running after SSH is closed.

## "It stopped working after reboot"

Check whether the service is enabled:

```bash
systemctl is-enabled dmr-watcher
systemctl is-enabled allstar-watcher
```

A configured service should normally report:

```text
enabled
```

---

# Before asking for help

Please include the following information in your GitHub issue.

## For an AllStar problem

1. Your local AllStar node number.
2. What you expected to happen.
3. What actually happened.
4. Output from:

```bash
systemctl status allstar-watcher --no-pager
```

5. Recent logs:

```bash
journalctl -u allstar-watcher -n 50 --no-pager
```

6. If the problem involves detecting active linked audio, run this while the remote station is talking:

```bash
sudo asterisk -rx "rpt show variables YOUR_NODE"
```

## For a DMR problem

1. Your configured BrandMeister talkgroup.
2. What you expected to happen.
3. What actually happened.
4. Output from:

```bash
systemctl status dmr-watcher --no-pager
```

5. Recent logs:

```bash
journalctl -u dmr-watcher -n 50 --no-pager
```

---

## Privacy before posting logs

Do **not** publish your private ntfy topic.

Before posting configuration or logs, remove or replace the value of:

```ini
NTFY_TOPIC=
```

Your amateur-radio callsign and public AllStar node number may already be publicly associated with amateur-radio activity, but you should still share only what you are comfortable posting.

---

## Still stuck?

Open a GitHub issue and choose the bug report template. The template asks for the information needed to diagnose the problem without a long back-and-forth.

73
