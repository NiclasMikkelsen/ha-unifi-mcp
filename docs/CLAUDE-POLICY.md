# Claude-policy för ha-unifi-mcp

## Tillåtna modeller

| Modell/preset | Användning | Kostnad |
|---------------|------------|---------|
| `@preset/best-agent` | Komplex analys | Hög |
| `@preset/best-code` | Kod och granskning | Hög |
| `@preset/fast` | Snabba uppslag | Låg |

## Aktiva connectors

| Connector | Nödvändig? | Motivering |
|-----------|------------|------------|
| UniFiKarlstad | ✅ | Site-specifik UniFi-åtkomst |
| UniFiTocksfors | ✅ | Site-specifik UniFi-åtkomst |
| UniFiTaurito | ✅ | Site-specifik UniFi-åtkomst |
| UniFiSiteManager | ✅ | Översikt över alla konsoler |

## Systemprompt

- Håll systemprompts korta. Referera till README/AGENTS.md.
- Färre connectors = mindre token use. Ta bort oanvända.
- Read-only by default: agenten kan läsa men inte ändra nätverksconfig.

## Token-effektivitet

- Använd read-only-verktyg (`get_*`, `list_*`, `search_*`).
- Begränsa verktygsutdata (t.ex. `head -50`).
- tsheadroom-komprimering automatisk via Aperture.
- Kortare prompts = högre effektivitet.

## Checklista

- [ ] Endast nödvändiga connectors aktiva
- [ ] Systemprompt kort och fokuserad
- [ ] Modellrouting konfigurerad
- [ ] Inga breda grants utan motivering