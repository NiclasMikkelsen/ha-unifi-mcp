# Hooks och automation för ha-unifi-mcp

## Git hooks

| Hook | Vad den gör | Vem ansvarar |
|------|-------------|--------------|
| pre-commit | secrets-scan, lint | CI |
| pre-push | validate | CI |

## CI-workflows

| Workflow | Fil | Vad den gör |
|----------|-----|-------------|
| validate | `.github/workflows/validate.yml` | Validering av kod/config |
| secrets-scan | `.github/workflows/secrets-scan.yml` | Söker efter läckta hemligheter |

## Automatiska kontroller

- **Secrets-scan:** körs vid varje commit/PR.
- **Validate:** kör projektets validering.
- **Docs validation:** kontrollerar att README och docs är uppdaterade.

## Underhåll

- Hooks uppdateras via `.github/workflows/`.
- Agent-aktivitet loggas i `.agents/activity.jsonl`.
- Tasks och handoff i `.agents/tasks.jsonl`.

## Checklista

- [ ] pre-commit hook konfigurerad (secrets-scan)
- [ ] validate-workflow finns
- [ ] secrets-scan-workflow finns
- [ ] .agents/README.md uppdaterad