#!/usr/bin/env sh
# Läser HA-appens options och mappar dem till upstream-serverns miljövariabler.
# Inga hemligheter skrivs till disk eller loggas här — de finns bara i
# /data/options.json (Supervisors konfigurationslager) och i processens miljö.
set -eu

PY=/opt/venv/bin/python
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

UNIFI_LOCAL_HOST="$(opt unifi_local_host)"
MCP_AUTH_TOKEN="$(opt mcp_auth_token)"

[ -n "$UNIFI_LOCAL_HOST" ] || { echo "FATAL: unifi_local_host är tomt"; exit 1; }
[ -n "$MCP_AUTH_TOKEN" ] || { echo "FATAL: mcp_auth_token är tomt"; exit 1; }

export UNIFI_API_TYPE="local"
export UNIFI_LOCAL_HOST
export UNIFI_LOCAL_PORT="443"
# UniFi-konsolerna använder självsignerat certifikat på LAN-segmentet.
export UNIFI_LOCAL_VERIFY_SSL="false"
export UNIFI_API_KEY="$(opt unifi_api_key)"
export UNIFI_PROFILE="$(opt unifi_profile)"
export UNIFI_READ_ONLY="$(opt unifi_read_only)"

export MCP_SERVER_TRANSPORT="streamable_http"
export MCP_SERVER_HOST="0.0.0.0"
export MCP_SERVER_PORT="$(opt mcp_port)"
export MCP_AUTH_TOKEN

echo "unifi-mcp: host=${UNIFI_LOCAL_HOST} profile=${UNIFI_PROFILE} read_only=${UNIFI_READ_ONLY} port=${MCP_SERVER_PORT}"

cd /app
exec "$PY" -m src.main
