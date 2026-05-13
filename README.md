# WiFi Attendance System
**S.P. Timber Industries, Lucknow**

Automatically detects when registered employees connect to or disconnect from the office WiFi, sends real-time Telegram notifications, and logs all events to a local SQLite database. Runs silently on the always-on office PC — no extra hardware needed.

---

## ⚩ Quick Start (Recommended — for most users)

**Prerequisites:** Python 3.10+ must be installed. Download from [python.org](https://www.python.org/downloads/) — tick **"Add Python to PATH"** during install.

```
# 1. Clone the repo
git clone https://github.com/rish90444/wifi-attendance.git
cd wifi-attendance

# 2. Copy config template and fill in your details
copy config.example.py config.py
notepad config.py

# 3. Right-click START_HERE.bat → Run as administrator
```

`START_HERE.bat` will automatically:
- Install all Python dependencies
- Register the system to start on every Windows boot
- Launch the dashboard at http://localhost:47832

That's it. No other steps needed.

---

## Setup (Manual / Advanced)
Download from https://python.org and install. During setup, tick **"Add Python to PATH"**.

### Step 2 — Install dependencies
Open Command Prompt in the `wifi-attendance` folder and run:
```
pip install -r requirements.txt
```

### Step 3 — Configure the system
Open `config.py` in Notepad and fill in:

| Setting | What to enter |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | Your Telegram chat/group ID |
| `NETWORK_RANGE` | Your office WiFi subnet, e.g. `192.168.1.0/24` |
| `DASHBOARD_PASSWORD` | A strong password for the admin dashboard |

> **How to get your Telegram bot token:**
> Message @BotFather on Telegram → `/newbot` → follow instructions → copy the token.
>
> **How to get your Chat ID:**
> Add @userinfobot to your group, or message it directly — it will reply with your chat ID.

### Step 4 — Register as a startup task (run once as Administrator)
Right-click `setup_task.bat` → **Run as administrator**.
This registers the system to start automatically every time Windows boots.

### Step 5 — Reboot
Restart the PC. The system starts automatically in the background.

### Step 6 — Register employees
1. Open **http://localhost:47832** in the browser on the office PC
2. Log in with the password you set in `config.py`
3. Ask each employee to connect their phone to the office WiFi
4. Within 60 seconds their device appears in the **Unknown Devices** section
5. Click **Register**, type their name and role, click **Save**

> ⚠️ **Important — tell every employee:**
> Go to phone **Settings → WiFi → tap the office network name → Privacy / MAC Address → set to "Use Device MAC"** (not Random).
> This must be done once per network. Without it, the phone changes its MAC address and cannot be tracked.

---

## Admin Dashboard

URL: **http://localhost:47832** (only accessible from the office PC itself)

| Section | What it shows |
|---|---|
| Unknown Devices | MACs seen on network but not yet registered |
| Registered Employees | All employees with current Present/Absent status |
| Today's Attendance Log | Chronological check-in/check-out events for today |

---

## Telegram Notifications

**Check-in:**
```
✅ Ramesh Kumar checked in
🕐 09:03 AM | Wednesday, 30 Apr 2025
👤 Role: Warehouse
```

**Check-out:**
```
🔴 Ramesh Kumar checked out
🕐 06:14 PM | Wednesday, 30 Apr 2025
⏱ Duration: 9h 11m
```

---

## How It Works

1. Every 60 seconds the system scans the office WiFi network using ARP
2. When a registered employee's phone joins the network → **Check-in** event
3. When the phone disappears for 3 consecutive scans (≈ 3 min) → **Check-out** event
4. All events are logged to `data/attendance.db` and sent to Telegram

---

## Known Limitations

- If an employee's phone is off or disconnected from WiFi, they will not be detected as present (even if they are physically in the office). This is a fundamental limitation of WiFi-based tracking.
- Each device (phone, laptop) is tracked independently. If an employee registers both devices, each will trigger its own notifications.

---

## File Structure

```
wifi-attendance/
├── main.py           ← Entry point
├── scanner.py        ← ARP scan loop
├── notifier.py       ← Telegram notifications
├── db.py             ← SQLite database layer
├── dashboard.py      ← Flask admin web UI
├── config.py         ← All settings (edit this)
├── setup_task.bat    ← Windows startup registration
├── requirements.txt
├── data/
│   └── attendance.db ← Created automatically
└── logs/
    └── app.log       ← Created automatically
```

---

## Logs

Logs are written to `logs/app.log` (rotates at 5 MB, keeps 3 backups).
Check this file if something isn't working.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| No devices detected | Make sure the script is running as Administrator (required for ARP scanning) |
| Telegram not sending | Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `config.py` |
| Dashboard not opening | Ensure the system is running; check `logs/app.log` for errors |
| Employee not detected | Confirm their phone's MAC Privacy is set to "Use Device MAC" for the office WiFi |
