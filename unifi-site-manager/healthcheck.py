"""Hälsokontroll för HA-appen: svarar MCP-porten?

Upstream-imagens HEALTHCHECK bygger `Settings()` i ett nytt skal, utan de miljövariabler
run.sh exporterar till huvudprocessen. Den föll därför alltid på "UNIFI_API_KEY Field
required" och visade appen som unhealthy fast servern svarade 200 (mätt 2026-11-16,
alla tre sajter). Här frågar vi porten i stället. Ingen hemlighet läses eller skickas:
utan token ska servern svara 401, och det räknas som friskt.
"""
import json
import sys
import urllib.error
import urllib.request

try:
    port = int(json.load(open("/data/options.json")).get("mcp_port") or 0)
except (OSError, ValueError):
    port = 0
if not port:
    sys.exit(1)

try:
    urllib.request.urlopen(f"http://127.0.0.1:{port}/mcp", timeout=8)
    sys.exit(0)
except urllib.error.HTTPError as err:
    sys.exit(0 if err.code < 500 else 1)
except Exception:
    sys.exit(1)
