# ha-unifi-mcp

Home Assistant-appar som kör en **läs-only** UniFi-MCP-server per site, plus en
för UniFi Site Manager. Syftet är att ersätta den enda breda `UniFiAll`-
connectorn i Aperture med fyra smala, separata MCP:er.

| App | Slug | Port | Vad den täcker |
|---|---|---|---|
| UniFi MCP (site) | `unifi_mcp` | 8765 | En lokal UniFi-konsol (UCG) via Integration API |
| UniFi MCP (Site Manager) | `unifi_site_manager` | 8766 | Alla konsoler via `api.ui.com` |

## Arkitektur

- Upstream-server: [enuno/unifi-mcp-server](https://github.com/enuno/unifi-mcp-server)
  (Apache-2.0). Valt för att `UNIFI_READ_ONLY=true` **tar bort** muterande
  verktyg ur verktygslistan helt, och för att `UNIFI_PROFILE` håller nere både
  verktygsantal och minnesbruk.
- Appen bygger vidare på upstreams publicerade image
  `ghcr.io/enuno/unifi-mcp-server:latest` (multi-arch amd64 + aarch64). Endast
  `run.sh` läggs till — den mappar HA-appens options till upstreams
  miljövariabler.
- `host_network: true`, samma mönster som `81f33d0f_ha_mcp`, så att Aperture
  kan nå servern på `<site>-homeassistant.tailb6ed4a.ts.net:<port>/mcp` utan
  proxy i något CT.
- Varje instans kräver `mcp_auth_token`; servern svarar bara med
  `Authorization: Bearer <token>`.

## Installation

1. HA → Inställningar → Appar → Appbutik → ⋮ → Repositories → lägg till
   `https://github.com/nvm1995/ha-unifi-mcp`.
2. Installera **UniFi MCP (site)**.
3. Fyll i konfigurationen:
   - `unifi_local_host` — konsolens LAN-IP (t.ex. `192.168.50.1`)
   - `unifi_api_key` — Integration API-nyckel för **den siten**
   - `unifi_profile` — `network` (48 verktyg) eller `minimal` (19) vid minnesbrist
   - `mcp_auth_token` — `openssl rand -hex 32`
4. Starta appen. Loggen ska sluta med `unifi-mcp: host=… profile=… port=…`.

## Säkerhet

- `unifi_read_only: true` är default. Sätt den bara till `false` efter beslut,
  och då med högre roll i Aperture-grants.
- `UNIFI_LOCAL_VERIFY_SSL=false` eftersom konsolerna använder självsignerat
  certifikat på LAN-segmentet. Trafiken går bara inom det lokala nätet.
- Inga hemligheter finns i det här repot. API-nycklar och tokens sätts i HA:s
  appkonfiguration och loggas aldrig av `run.sh`.
- Servern lyssnar på `0.0.0.0` eftersom `host_network` krävs för tailnet-åtkomst.
  Skyddet är bearer-token, inte nätverksisolering.

## Kända gränser

- Karlstad och Töcksfors har bara ~550 MB ledigt RAM. Börja på `network`;
  går minnet i taket, byt till `minimal`.
- Taurito är `aarch64` — imagen är multi-arch, men verifiera första starten där.
