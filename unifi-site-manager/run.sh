#!/usr/bin/env sh
# Site Manager-läget: läser api.ui.com-nyckeln ur appens options.
# Samma upstream-server, men cloud-läge i stället för lokal konsol.
set -eu

PY=/opt/venv/bin/python
OPTS=/data/options.json

opt() {
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

MCP_AUTH_TOKEN="$(opt mcp_auth_token)"
[ -n "$MCP_AUTH_TOKEN" ] || { echo "FATAL: mcp_auth_token är tomt"; exit 1; }

export UNIFI_API_TYPE="$(opt unifi_api_type)"
export UNIFI_API_KEY="$(opt unifi_api_key)"
export UNIFI_SITE_MANAGER_ENABLED="true"
export UNIFI_READ_ONLY="true"

export MCP_SERVER_TRANSPORT="streamable_http"
export MCP_SERVER_HOST="0.0.0.0"
export MCP_SERVER_PORT="$(opt mcp_port)"
export MCP_AUTH_TOKEN

echo "unifi-site-manager: api_type=${UNIFI_API_TYPE} port=${MCP_SERVER_PORT}"

cd /app
exec "$PY" -m src.main
