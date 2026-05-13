"""
scanner.py — ARP scan loop for WiFi-based attendance detection.

Primary method : scapy ARP broadcast
Fallback method: nmap subprocess (if scapy/raw-socket fails)

Must run with administrator privileges on Windows.
"""
import logging
import subprocess
import time
from typing import Set

import config
import db
import notifier

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# In-memory state (reset on restart)
# ─────────────────────────────────────────────
missed_counts: dict[str, int] = {}   # mac → consecutive missed scans
currently_present: Set[str] = set()  # MACs considered "present" right now


# ─────────────────────────────────────────────
# MAC normalisation
# ─────────────────────────────────────────────

def normalize_mac(mac: str) -> str:
    """Normalise MAC to lowercase colon-separated format: aa:bb:cc:dd:ee:ff"""
    return mac.lower().replace("-", ":").strip()


# ─────────────────────────────────────────────
# ARP scan (scapy primary, nmap fallback)
# ─────────────────────────────────────────────

def _scan_with_scapy(network_range: str) -> Set[str]:
    """Use scapy ARP broadcast to discover active MACs."""
    from scapy.all import ARP, Ether, srp  # type: ignore
    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network_range)
    answered, _ = srp(packet, timeout=2, verbose=False)
    return {normalize_mac(rcv.hwsrc) for _, rcv in answered}


def _scan_with_nmap(network_range: str) -> Set[str]:
    """Fallback: run nmap -sn and parse MAC addresses from output."""
    macs: Set[str] = set()
    try:
        result = subprocess.run(
            ["nmap", "-sn", "--host-timeout", "2s", network_range],
            capture_output=True,
            text=True,
            timeout=30,
        )
        for line in result.stdout.splitlines():
            if "MAC Address:" in line:
                # Line format: MAC Address: AA:BB:CC:DD:EE:FF (Vendor)
                parts = line.strip().split()
                if len(parts) >= 3:
                    macs.add(normalize_mac(parts[2]))
    except FileNotFoundError:
        log.error("nmap not found. Install nmap or ensure scapy works with admin rights.")
    except subprocess.TimeoutExpired:
        log.error("nmap scan timed out.")
    except Exception as e:
        log.error("nmap scan failed: %s", e)
    return macs


def scan_network(network_range: str) -> Set[str]:
    """
    Scan the network and return a set of active (normalised) MAC addresses.
    Tries scapy first; falls back to nmap subprocess on any error.
    """
    try:
        macs = _scan_with_scapy(network_range)
        log.debug("Scapy scan found %d devices", len(macs))
        return macs
    except Exception as e:
        log.warning("Scapy scan failed (%s), falling back to nmap.", e)

    return _scan_with_nmap(network_range)


# ─────────────────────────────────────────────
# Event processing
# ─────────────────────────────────────────────

def _handle_checkin(mac: str, employee: dict) -> None:
    db.log_event(employee["id"], "checkin", mac)
    notifier.send_checkin(employee)
    currently_present.add(mac)
    missed_counts[mac] = 0
    log.info("CHECK-IN  %s (%s)", employee["name"], mac)


def _handle_checkout(mac: str, employee: dict) -> None:
    db.log_event(employee["id"], "checkout", mac)
    notifier.send_checkout(employee)
    currently_present.discard(mac)
    missed_counts[mac] = 0
    log.info("CHECK-OUT %s (%s)", employee["name"], mac)


# ─────────────────────────────────────────────
# Main scan loop
# ─────────────────────────────────────────────

def run_loop() -> None:
    """
    Infinite loop: scan → compare → fire events.
    Runs as a background daemon thread started by main.py.
    """
    log.info(
        "Scanner starting. Interval=%ds, checkout after %d missed scans, range=%s",
        config.SCAN_INTERVAL_SECONDS,
        config.CHECKOUT_MISSED_SCANS,
        config.NETWORK_RANGE,
    )

    while True:
        try:
            _run_one_scan()
        except Exception as e:
            # Never crash the loop — log and continue
            log.error("Unexpected scanner error: %s", e, exc_info=True)

        time.sleep(config.SCAN_INTERVAL_SECONDS)


def _run_one_scan() -> None:
    """Execute a single scan cycle and process all events."""
    active_macs = scan_network(config.NETWORK_RANGE)
    registered = db.get_active_employee_macs()  # {mac: employee_dict}

    # ── New MACs (appeared since last scan) ──────────────────────────────
    new_macs = active_macs - currently_present
    for mac in new_macs:
        if mac in registered:
            _handle_checkin(mac, registered[mac])
        else:
            # Unknown device — upsert to unknown_devices, no notification
            db.upsert_unknown_device(mac)
            log.debug("Unknown device seen: %s", mac)

    # ── Disappeared MACs (were present, now missing) ──────────────────────
    gone_macs = currently_present - active_macs
    for mac in gone_macs:
        if mac in registered:
            missed_counts[mac] = missed_counts.get(mac, 0) + 1
            log.debug(
                "Missed scan for %s (%s): %d/%d",
                registered[mac]["name"], mac,
                missed_counts[mac], config.CHECKOUT_MISSED_SCANS,
            )
            if missed_counts[mac] >= config.CHECKOUT_MISSED_SCANS:
                _handle_checkout(mac, registered[mac])

    # ── Still present MACs: reset miss counters ───────────────────────────
    still_present = currently_present & active_macs
    for mac in still_present:
        if missed_counts.get(mac, 0) > 0:
            log.debug("Device %s back — resetting miss counter", mac)
            missed_counts[mac] = 0

    log.debug(
        "Scan complete. Active=%d, Present=%d, Registered=%d",
        len(active_macs), len(currently_present), len(registered),
    )
