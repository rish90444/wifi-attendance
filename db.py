"""
db.py — SQLite read/write layer for the WiFi Attendance System.
"""
import sqlite3
import os
import logging
from datetime import datetime, date

import config

log = logging.getLogger(__name__)


def _get_conn() -> sqlite3.Connection:
    """Return a connection with row_factory set for dict-like access."""
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────

def initialize() -> None:
    """Create all tables if they don't exist. Safe to call on every startup."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS employees (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                mac_address   TEXT    NOT NULL UNIQUE,
                name          TEXT    NOT NULL,
                role          TEXT    DEFAULT '',
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active     INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS attendance_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                event_type  TEXT    NOT NULL CHECK(event_type IN ('checkin', 'checkout')),
                timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
                mac_address TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS unknown_devices (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                mac_address TEXT    NOT NULL UNIQUE,
                first_seen  DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen   DATETIME DEFAULT CURRENT_TIMESTAMP,
                times_seen  INTEGER DEFAULT 1
            );
        """)
        conn.commit()
        log.info("Database initialized at %s", config.DB_PATH)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# Scanner helpers
# ─────────────────────────────────────────────

def get_active_employee_macs() -> dict:
    """Return {mac_address: {id, name, role}} for all active employees."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, mac_address, name, role FROM employees WHERE is_active = 1"
        ).fetchall()
        return {row["mac_address"]: dict(row) for row in rows}
    finally:
        conn.close()


def log_event(employee_id: int, event_type: str, mac_address: str) -> None:
    """Insert a checkin or checkout record into attendance_log."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO attendance_log (employee_id, event_type, mac_address) VALUES (?, ?, ?)",
            (employee_id, event_type, mac_address),
        )
        conn.commit()
        log.info("Logged %s for employee_id=%s mac=%s", event_type, employee_id, mac_address)
    finally:
        conn.close()


def upsert_unknown_device(mac_address: str) -> None:
    """Insert or update an unknown device record."""
    conn = _get_conn()
    try:
        conn.execute("""
            INSERT INTO unknown_devices (mac_address, first_seen, last_seen, times_seen)
            VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(mac_address) DO UPDATE SET
                last_seen  = CURRENT_TIMESTAMP,
                times_seen = times_seen + 1
        """, (mac_address,))
        conn.commit()
    finally:
        conn.close()


def get_last_checkin(employee_id: int):
    """Return the most recent checkin timestamp for an employee (or None)."""
    conn = _get_conn()
    try:
        row = conn.execute(
            """SELECT timestamp FROM attendance_log
               WHERE employee_id = ? AND event_type = 'checkin'
               ORDER BY timestamp DESC LIMIT 1""",
            (employee_id,),
        ).fetchone()
        return row["timestamp"] if row else None
    finally:
        conn.close()


# ─────────────────────────────────────────────
# Dashboard helpers
# ─────────────────────────────────────────────

def get_employees() -> list:
    """Return all active employees as a list of dicts."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, mac_address, name, role, registered_at, is_active FROM employees ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_unknown_devices() -> list:
    """Return unknown devices that have no matching employee entry."""
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT ud.id, ud.mac_address, ud.first_seen, ud.last_seen, ud.times_seen
            FROM unknown_devices ud
            WHERE ud.mac_address NOT IN (SELECT mac_address FROM employees)
            ORDER BY ud.last_seen DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_today_log() -> list:
    """Return today's attendance events with employee names."""
    conn = _get_conn()
    try:
        today = date.today().isoformat()
        rows = conn.execute("""
            SELECT al.timestamp, e.name, al.event_type
            FROM attendance_log al
            JOIN employees e ON e.id = al.employee_id
            WHERE DATE(al.timestamp) = ?
            ORDER BY al.timestamp DESC
        """, (today,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def register_device(mac_address: str, name: str, role: str) -> None:
    """Register an unknown device as a named employee.

    Uses INSERT ... ON CONFLICT DO UPDATE so the row id is preserved,
    which keeps attendance_log foreign-key references intact.
    """
    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO employees (mac_address, name, role)
               VALUES (?, ?, ?)
               ON CONFLICT(mac_address) DO UPDATE SET
                   name      = excluded.name,
                   role      = excluded.role,
                   is_active = 1""",
            (mac_address, name, role),
        )
        conn.execute(
            "DELETE FROM unknown_devices WHERE mac_address = ?",
            (mac_address,),
        )
        conn.commit()
        log.info("Registered device %s as '%s' (%s)", mac_address, name, role)
    finally:
        conn.close()


def edit_employee(employee_id: int, name: str, role: str) -> None:
    """Update an employee's name and role."""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE employees SET name = ?, role = ? WHERE id = ?",
            (name, role, employee_id),
        )
        conn.commit()
    finally:
        conn.close()


def disable_employee(employee_id: int) -> None:
    """Set is_active = 0 for an employee."""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE employees SET is_active = 0 WHERE id = ?",
            (employee_id,),
        )
        conn.commit()
        log.info("Disabled employee_id=%s", employee_id)
    finally:
        conn.close()
