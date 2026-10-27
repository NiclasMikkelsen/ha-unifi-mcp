#!/usr/bin/env python3
"""Vidarebefordrar UniFi-syslog till Alloy med RFC5424-header.

UniFi-konsolerna (CyberSecure → Traffic Logging → SIEM Server) skickar CEF-rader
utan PRI, t.ex.

    Oct 27 08:27:36 Taurito CEF:0|Ubiquiti|UniFi Network|11.0.97|521|VPN Client Disconnected|2|UNIFIcategory=VPN ...

`loki.source.syslog` i Alloy kräver en PRI och avvisar annars raden med
"invalid or unsupported framing. first byte: 'O'". Den här bryggan tar emot
datagrammen på UDP, lägger på en RFC5424-header och skickar vidare till Alloy.
CEF-raden lämnas orörd i MSG så inget innehåll går förlorat; den översätter
alltså inte CEF-severity till PRI, den lägger bara på en fast
facility/severity så att raden accepteras.

DEN HÄR FILEN ÄR KANONISK. Samma byte-for-byte-kopia ligger i
`observability/alloy/unifi-syslog-relay.py` och installeras som systemd-tjänst
på Proxmox-hostarna. Redigera den bara härifrån och kopiera sedan över —
observability-repots CI hämtar den här filen från main och fäller varje
avvikelse i kopian.

Konfigurationen är miljövariabler eftersom båda förpackningarna kan sätta dem:
HA-appen via /data/options.json, systemd via Environment=. Endast stdlib
används, så imagen behöver inget utöver python3.
"""

from __future__ import annotations

import os
import signal
import socket
import sys
import time

# <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA + mellanslag
# Alla fält NIL eftersom originalraden redan bär tidsstämpel och värdnamn i MSG.
PREFIX_TEMPLATE = "<{pri}>1 - - - - - - "

STATS_INTERVAL = 300  # sekunder mellan statistikrader i apploggen


def log(message: str) -> None:
    print(f"unifi-syslog-relay: {message}", flush=True)


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        log(f"FATAL: {name}={raw!r} är inte ett heltal")
        raise SystemExit(1)


def main() -> int:
    listen_host = os.environ.get("LISTEN_HOST", "0.0.0.0").strip() or "0.0.0.0"
    listen_port = env_int("LISTEN_PORT", 1514)
    forward_host = os.environ.get("FORWARD_HOST", "").strip()
    forward_port = env_int("FORWARD_PORT", 1517)
    facility = env_int("SYSLOG_FACILITY", 1)
    severity = env_int("SYSLOG_SEVERITY", 6)

    if not forward_host:
        log("FATAL: forward_host är inte satt")
        return 1

    pri = facility * 8 + severity
    prefix = PREFIX_TEMPLATE.format(pri=pri).encode()

    try:
        forward_addr = socket.getaddrinfo(
            forward_host, forward_port, socket.AF_INET, socket.SOCK_DGRAM
        )[0][4]
    except socket.gaierror as exc:
        log(f"FATAL: kan inte slå upp {forward_host}:{forward_port}: {exc}")
        return 1

    rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # UniFi skickar i skurar vid t.ex. omstart av en AP; större buffert ger
    # färre tappade datagram innan loopen hunnit läsa.
    try:
        rx.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
    except OSError:
        pass
    rx.bind((listen_host, listen_port))
    rx.settimeout(1.0)
    tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    stop = False

    def _request_stop(signum: int, _frame: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    log(
        f"lyssnar på {listen_host}:{listen_port} (PRI <{pri}>), "
        f"vidare till {forward_addr[0]}:{forward_addr[1]}"
    )

    received = forwarded = forward_errors = 0
    last_stats = time.monotonic()

    while not stop:
        try:
            data, peer = rx.recvfrom(65535)
        except TimeoutError:
            data = b""
        except OSError as exc:  # t.ex. tillfällig resursbrist
            log(f"recvfrom misslyckades: {exc}")
            data = b""

        if data:
            received += 1
            # Har avsändaren redan en PRI låter vi raden vara.
            packet = data if data.startswith(b"<") else prefix + data
            try:
                tx.sendto(packet, forward_addr)
                forwarded += 1
            except OSError as exc:
                forward_errors += 1
                # Logga första felet och sedan var hundrade — en nere länk får
                # inte fylla apploggen.
                if forward_errors == 1 or forward_errors % 100 == 0:
                    log(
                        f"kunde inte skicka vidare från {peer[0]} "
                        f"(fel nr {forward_errors}): {exc}"
                    )

        now = time.monotonic()
        if now - last_stats >= STATS_INTERVAL:
            log(f"mottagna={received} vidaresända={forwarded} fel={forward_errors}")
            last_stats = now

    log(f"avslutar: mottagna={received} vidaresända={forwarded} fel={forward_errors}")
    rx.close()
    tx.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
