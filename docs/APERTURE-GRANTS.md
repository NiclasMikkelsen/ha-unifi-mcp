# Aperture-grants för ha-unifi-mcp

## Repo scope

**Read-only repo** — MCP:erna är read-only by default (`UNIFI_READ_ONLY=true`).

## Nödvändiga connectors

| Connector | Syfte | Access-nivå | Read/Write |
|-----------|-------|-------------|------------|
| UniFiKarlstad | UniFi site Karlstad | cap.ha | Read |
| UniFiTocksfors | UniFi site Töcksfors | cap.ha | Read |
| UniFiTaurito | UniFi site Taurito | cap.ha | Read |
| UniFiSiteManager | Alla konsoler via api.ui.com | cap.ha | Read |

## Grants per identitet

| Identitet (src) | Roll | Modeller | Connectors | Send_hooks |
|-----------------|------|----------|------------|------------|
| nvm1995@icloud.com | admin | **/** | explicit lista | headroom + observability |
| tag:agent | user | **/** | label:cap.ha | headroom + observability |
| tag:ha | user | **/** | label:cap.ha | headroom |
| tag:proxmox | admin | **/** | label:cap.infra, cap.network | headroom + observability |
| tag:mac | user | **/** | label:cap.desktop, cap.clipboard, cap.browser, cap.llm, cap.incident | headroom + observability |

## Policy

- **Least privilege:** Bara `label:cap.ha` för agentflottan — ingen skrivåtkomst.
- **Separata grants per site:** Karlstad, Töcksfors, Taurito har egna MCP-endpoints.
- **Site Manager:** Separat connector (`UniFiSiteManager`) för översikt över alla konsoler.
- **Skrivåtkomst:** Kräver `UNIFI_READ_ONLY=false` + högre roll i Aperture-grants. Kräver beslut.
- **Inga breda grants:** `UniFiAll` ersätts av de fyra smala MCP:erna.

## Hemligheter

- `unifi_api_key` och `mcp_auth_token` sätts i HA:s appkonfiguration.
- Inga hemligheter i repot.
- API-nycklar lagras i Infisical (om de behöver delas mellan agenter).

## Checklista

- [ ] Grants definierade i `aperture-identities.yaml`
- [ ] Connectors registrerade i `aperture-connectors.yaml`
- [ ] `apply-grant-model.py` kör utan fel
- [ ] Inga breda `**`-grants utan motivering
- [ ] Hemligheter i Infisical/HA-config, inte i git