---
name: Bug report / tech support
about: Report a DMR, AllStar, notification, installation, or service problem
title: "[Support] "
labels: ""
assignees: ""
---

## Watcher type

Check one:

- [ ] DMR
- [ ] AllStar
- [ ] Both
- [ ] Installation / service setup
- [ ] ntfy / phone notification
- [ ] Other

## What happened?

Describe what you expected to happen and what actually happened.

## Basic information

**Operating system / platform:**  
Examples: ASL3 Raspberry Pi, Raspberry Pi OS, Windows

**AllStar node number (if applicable):**

**DMR talkgroup (if applicable):**

**Did this work previously?**
- [ ] Yes
- [ ] No
- [ ] Not sure

## Service status

For AllStar:

```bash
systemctl status allstar-watcher --no-pager
```

Paste output here:

```text

```

For DMR:

```bash
systemctl status dmr-watcher --no-pager
```

Paste output here:

```text

```

## Recent logs

AllStar:

```bash
journalctl -u allstar-watcher -n 50 --no-pager
```

DMR:

```bash
journalctl -u dmr-watcher -n 50 --no-pager
```

Paste the relevant output here:

```text

```

## AllStar detection information

If this is an AllStar activity-detection problem, run this **while the remote station is actively talking**:

```bash
sudo asterisk -rx "rpt show variables YOUR_NODE"
```

Paste output here:

```text

```

## Configuration values

Please provide only the relevant non-secret settings:

```ini
CALLSIGN=
DMR_TALKGROUP=
ALLSTAR_NODE=
QUIET_RESET_SECONDS=
QUIET_HOURS_START=
QUIET_HOURS_END=
```

**Do not post your private `NTFY_TOPIC`.**

## Anything else?

Add any other details that might help reproduce the problem.
