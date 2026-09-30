# START HERE — Easy Setup Guide

This guide assumes you know ham radio, but you do **not** need to know Python or Linux.

## STEP 1 — Download the project

On the GitHub page, click:

**Code → Download ZIP**

Unzip the downloaded folder.

## STEP 2 — Install ntfy on your phone

Install the **ntfy** app on your phone.

Create/subscribe to a private topic name.

Example:

`kp4abc-radio-58392-x7q`

Use something difficult to guess.

Write the topic down. You will need it in Step 3.

## STEP 3 — Make your config.ini file

Inside the unzipped project folder you will see:

`config.ini.example`

Make a copy of it and rename the copy:

`config.ini`

Open `config.ini` with Notepad.

Change these values:

```ini
CALLSIGN=YOURCALL
NTFY_TOPIC=your-private-topic
DMR_TALKGROUP=3300
ALLSTAR_NODE=12345
QUIET_RESET_SECONDS=180
QUIET_HOURS_START=23:00
QUIET_HOURS_END=07:00
```

Example:

```ini
CALLSIGN=KP4ABC
NTFY_TOPIC=kp4abc-radio-58392-x7q
DMR_TALKGROUP=3300
ALLSTAR_NODE=12345
QUIET_RESET_SECONDS=180
QUIET_HOURS_START=23:00
QUIET_HOURS_END=07:00
```

Save the file.

---

# OPTION A — DMR ONLY ON WINDOWS

## STEP 4 — Install Python

Install Python 3 from python.org if it is not already installed.

During installation, check:

**Add Python to PATH**

## STEP 5 — Install the required packages

Open the unzipped Node Activity Alerts folder in File Explorer.

Click the File Explorer address bar.

Type:

`powershell`

Press Enter.

Then run:

```powershell
py -m pip install -r requirements.txt
```

## STEP 6 — Start the DMR watcher

Double-click:

`Start_DMR_Watcher.bat`

Leave that window open.

Your PC must remain on for the Windows watcher to work.

---

# OPTION B — DMR + ALLSTAR ON AN ASL3 / RASPBERRY PI

This is the better option if your node stays on 24/7.

## STEP 4 — Copy the files to the Pi

Copy these files to the home folder of your ASL3 user:

- `dmr_watcher.py`
- `allstar_watcher.py`
- `config.ini`
- `requirements.txt`
- `dmr-watcher.service`
- `allstar-watcher.service`
- `install_services.sh`

If your ASL3 username is not `admin`, read the note near the bottom before installing the services.

## STEP 5 — Create the Python environment

SSH into the Pi and run:

```bash
sudo apt install -y python3-venv
python3 -m venv ~/hamalerts-venv
source ~/hamalerts-venv/bin/activate
pip install -r ~/requirements.txt
```

## STEP 6 — Test DMR

Run:

```bash
source ~/hamalerts-venv/bin/activate
python ~/dmr_watcher.py
```

Press `Ctrl+C` after the test.

## STEP 7 — Test AllStar

Run:

```bash
source ~/hamalerts-venv/bin/activate
python ~/allstar_watcher.py
```

Have someone come into your node through AllStar.

Local RF PTT should not trigger an alert.

Press `Ctrl+C` after the test.

## STEP 8 — Make the watchers automatic

If your ASL3 username is `admin`, run:

```bash
cd ~
chmod +x install_services.sh
./install_services.sh
```

Check them:

```bash
systemctl status dmr-watcher --no-pager
systemctl status allstar-watcher --no-pager
```

Look for:

`Active: active (running)`

Once both are running, you can close SSH.

They will continue in the background and start again after a reboot.

---

# LIVE LOGS

DMR:

```bash
journalctl -u dmr-watcher -f
```

AllStar:

```bash
journalctl -u allstar-watcher -f
```

Press `Ctrl+C` to stop watching the log. This does **not** stop the service.

---

# QUIET HOURS

Default:

```ini
QUIET_HOURS_START=23:00
QUIET_HOURS_END=07:00
```

That means no phone notifications from 11 PM through 7 AM.

The watcher itself can keep running.

Make sure the computer/Pi has the correct local time.

---

# IF YOUR ASL3 USERNAME IS NOT admin

The included systemd service files assume:

`/home/admin/`

If your username is different, edit both `.service` files before running `install_services.sh`.

Replace every occurrence of:

`/home/admin`

with your actual home directory.

Example:

`/home/kp4abc`

---

# VERY IMPORTANT

Every operator should create their **own private ntfy topic**.

Do not copy somebody else's topic into your config.

And now your watch begins.
