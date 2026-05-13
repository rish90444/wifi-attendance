"""
main.py — Entry point for the WiFi Attendance System.

Starts two concurrent operations:
  1. Scanner thread  — ARP scan loop (background daemon)
  2. Flask dashboard — runs on main thread at localhost:47832

Must be run with administrator privileges (required by scapy for raw sockets).
"""
import logging
import os
import threading
from logging.handlers import RotatingFileHandler

import config
import db
import scanner
import dashboard


def setup_logging() -> None:
    """Configure rotating file + console logging."""
    os.makedirs(os.path.dirname(config.LOG_PATH), exist_ok=True)

    handler = RotatingFileHandler(
        config.LOG_PATH,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))

    logging.basicConfig(
        handlers=[handler, console],
        level=logging.INFO,
    )


def main() -> None:
    setup_logging()
    log = logging.getLogger("main")

    log.info("=" * 50)
    log.info("WiFi Attendance System starting up")
    log.info("=" * 50)

    # Ensure database tables exist (safe to call repeatedly)
    db.initialize()

    # Start scanner in a background daemon thread
    scanner_thread = threading.Thread(
        target=scanner.run_loop,
        name="scanner",
        daemon=True,   # dies when main thread exits
    )
    scanner_thread.start()
    log.info("Scanner thread started.")

    # Run Flask on the main thread (blocking)
    log.info(
        "Dashboard available at http://%s:%d",
        config.DASHBOARD_HOST,
        config.DASHBOARD_PORT,
    )
    dashboard.app.run(
        host=config.DASHBOARD_HOST,
        port=config.DASHBOARD_PORT,
        debug=False,
        use_reloader=False,   # must be False when running in a thread context
    )


if __name__ == "__main__":
    main()
