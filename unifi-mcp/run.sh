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

# Profil "all" betyder "registrera allt": upstream laddar hela registret när
# UNIFI_PROFILE saknas, så vi lämnar variabeln oexportad i stället för att skicka
# ett okänt värde (som skulle logga en varning vid varje start).
PROFILE="$(opt unifi_profile)"
if [ "$PROFILE" = "all" ]; then
    unset UNIFI_PROFILE 2>/dev/null || true
else
    export UNIFI_PROFILE="$PROFILE"
fi

export UNIFI_READ_ONLY="$(opt unifi_read_only)"

# DEBUG=true lägger till debug_api_request (rå GET/DELETE mot valfri endpoint).
# Bara satt när det uttryckligen är på — strängen "false" får aldrig exporteras,
# eftersom upstream tolkar en satt variabel som sann.
DEBUG_OPT="$(opt unifi_debug)"
if [ "$DEBUG_OPT" = "true" ]; then
    export DEBUG="true"
    DEBUG_SHOWN="true"
else
    unset DEBUG 2>/dev/null || true
    DEBUG_SHOWN="false"
fi

export MCP_SERVER_TRANSPORT="streamable_http"
export MCP_SERVER_HOST="0.0.0.0"
export MCP_SERVER_PORT="$(opt mcp_port)"
export MCP_AUTH_TOKEN

echo "unifi-mcp: host=${UNIFI_LOCAL_HOST} profile=${PROFILE} read_only=${UNIFI_READ_ONLY} debug=${DEBUG_SHOWN} port=${MCP_SERVER_PORT}"

cd /app
exec "$PY" -m src.main
