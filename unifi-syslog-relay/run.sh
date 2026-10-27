#!/usr/bin/env sh
# Läser HA-appens options och kör relayen. Inga hemligheter finns i appen —
# bara adresser och portar.
set -eu

PY=python3
OPTS=/data/options.json

opt() {
    # Skriver ut värdet utan citattecken; bool som true/false.
    "$PY" -c "
import json, sys
d = json.load(open('$OPTS'))
v = d.get(sys.argv[1], '')
if isinstance(v, bool):
    sys.stdout.write('true' if v else 'false')
else:
    sys.stdout.write(str(v))
" "$1"
}

[ -r "$OPTS" ] || { echo "FATAL: $OPTS saknas"; exit 1; }

LISTEN_PORT="$(opt listen_port)"
FORWARD_HOST="$(opt forward_host)"
FORWARD_PORT="$(opt forward_port)"
SYSLOG_FACILITY="$(opt syslog_facility)"
SYSLOG_SEVERITY="$(opt syslog_severity)"

[ -n "$FORWARD_HOST" ] || {
    echo "FATAL: forward_host är tomt — ange Alloy-reläets adress, t.ex. karlstad-proxmox"
    exit 1
}

export LISTEN_HOST="0.0.0.0"
export LISTEN_PORT FORWARD_HOST FORWARD_PORT SYSLOG_FACILITY SYSLOG_SEVERITY

echo "unifi-syslog-relay: lyssnar ${LISTEN_HOST}:${LISTEN_PORT} -> ${FORWARD_HOST}:${FORWARD_PORT}"

exec "$PY" /relay.py
