"""
notifier.py — Sends Telegram Bot messages for check-in / check-out events.
Uses plain requests (no python-telegram-bot library needed).
"""
import logging
from datetime import datetime

import requests

import config
import db

log = logging.getLogger(__name__)

_API_URL = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"


def _send_message(text: str) -> None:
    """POST a message to the Telegram Bot API. Logs but never raises."""
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(_API_URL, json=payload, timeout=5)
        if not resp.ok:
            log.error("Telegram API error %s: %s", resp.status_code, resp.text)
    except Exception as e:
        log.error("Telegram send failed: %s", e)


def _fmt_now() -> str:
    """Return current time formatted as '09:03 AM | Wednesday, 30 Apr 2025'."""
    return datetime.now().strftime("%I:%M %p | %A, %d %b %Y")


def _calc_duration(employee_id: int) -> str | None:
    """
    Look up the most recent checkin for this employee and return
    a human-readable duration string like '9h 11m', or None if not found.
    """
    last_checkin = db.get_last_checkin(employee_id)
    if not last_checkin:
        return None
    try:
        checkin_dt = datetime.fromisoformat(last_checkin)
        delta = datetime.now() - checkin_dt
        total_minutes = int(delta.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes}m"
    except Exception as e:
        log.warning("Could not calculate duration: %s", e)
        return None


def send_checkin(employee: dict) -> None:
    """
    Send a check-in notification.
    employee dict must have: id, name, role
    """
    name = employee.get("name", "Unknown")
    role = employee.get("role", "") or "—"
    text = (
        f"✅ <b>{name} checked in</b>\n"
        f"🕐 {_fmt_now()}\n"
        f"👤 Role: {role}"
    )
    log.info("Check-in notification: %s", name)
    _send_message(text)


def send_checkout(employee: dict) -> None:
    """
    Send a check-out notification with duration.
    employee dict must have: id, name
    """
    name = employee.get("name", "Unknown")
    employee_id = employee.get("id")
    duration = _calc_duration(employee_id) if employee_id else None

    text = (
        f"🔴 <b>{name} checked out</b>\n"
        f"🕐 {_fmt_now()}"
    )
    if duration:
        text += f"\n⏱ Duration: {duration}"

    log.info("Check-out notification: %s (duration=%s)", name, duration)
    _send_message(text)
