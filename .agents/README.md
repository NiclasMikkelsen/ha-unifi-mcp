# .agents — samarbetslager

Alla agenter som arbetar i denna mapp använder `.agents/`:

- **presence/** — `<host>__<agent>.json`, hjärtslag var 60 s medan man jobbar.
  Se vilka som jobbar live:  `agent-presence list <mapp>`
- **locks/** — rådgivande lås för exklusiva resurser (namngiven fil = låst).
  Ta: `agent-presence lock <mapp> <resurs> "<orsak>"`  / släpp: `... unlock <resurs>`
- **tasks.jsonl** — append-only logg: ett JSON-objekt per rad
  `{"ts":...,"agent":...,"host":...,"kind":"change|note|done","msg":"..."}`
  Logga: `agent-presence log <mapp> change "vad du gjorde"`
- **activity.jsonl** — skrivs automatiskt av git-hooken vid varje commit.

Ingen central server — allt syns via Syncthing. Konflikter undviks genom unika filnamn per host+agent.
