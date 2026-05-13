import os
import secrets

# ─────────────────────────────────────────────
# WiFi Attendance System — Configuration
# Copy this file to config.py and fill in your values.
# ─────────────────────────────────────────────

# ── Telegram ──────────────────────────────────
# Get your bot token from @BotFather on Telegram
# Get your chat ID from @userinfobot on Telegram
TELEGRAM_BOT_TOKEN = "your-bot-token-here"
TELEGRAM_CHAT_ID   = "your-chat-id-here"

# ── Scanner ───────────────────────────────────
SCAN_INTERVAL_SECONDS = 60       # How often to scan (seconds)
CHECKOUT_MISSED_SCANS = 3        # Mark checkout after N consecutive missed scans
NETWORK_RANGE         = "192.168.1.0/24"  # Your office WiFi subnet

# ── Admin Dashboard ───────────────────────────
DASHBOARD_PORT     = 47832
DASHBOARD_HOST     = "127.0.0.1"   # localhost only — never change to 0.0.0.0
DASHBOARD_PASSWORD = "change-this-password"

# ── Session Secret Key ────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# ── Paths ─────────────────────────────────────
DB_PATH  = "data/attendance.db"
LOG_PATH = "logs/app.log"
