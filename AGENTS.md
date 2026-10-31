<!-- projekt: ha-unifi-mcp -->
# AGENTS.md — ha-unifi-mcp

Denna mapp är ett **projekt** i den delade träden `~/AgentWorkspace/Project`.

- Samarbete/presence/lås/logg: `.agents/README.md` (`agent-presence`)
- Git-hooks (commit-logg + hemlighetsskydd) kommer från `AgentWorkspace/Agents/config/hooks` via `core.hooksPath`.
- Delade skills: `.skills/` (symlänk till `AgentWorkspace/Agents/skills`)

Arbeta direkt i denna mapp (inga privata kloner). Allt projektmaterial, analys och data stannar här —
även resultat från Windows 910, MacBook Pro och MacBook Air skrivs tillbaka hit.

<!-- städpolicy:genererad ur Agents/catalog/agent-policy.md sha256:c8f723ff58bb -->
Skapande lämnar inget efter sig. En agent glömmer — därför finns också
`~/bin/agent-cleanup.sh`, som körs vid varje sessionsslut och en gång per dygn.

- Skapa inga `*.bak*`/`*.backup`-kopior bredvid originalet. Använd git, eller en
  kopia i `~/.agent-scratch/<uppgift>/`.
- När uppgiften är klar: ta bort temporära filer, worktrees, scratch och
  testresurser som du själv har skapat.
- Gammalt material som ska sparas flyttas till Archive-sharen:
  `Archive/<site>/<sökväg>/<fil>`. Det raderas aldrig direkt.
- Flytta bara: kopiera först, verifiera (storlek + checksumma) och radera källan sist.
- Arkivera aldrig filer som kan innehålla hemligheter (`.claude.json*`, `.env`,
  tokens). Radera dem efter retention i stället.
- Home Assistant: ta en HA-backup före ändringen, inga `.bak` i `/config`. Ta bort
  helpers, scripts och automationer som du har skapat för test. Allt agenten skapar
  får `st_review` tills en människa tar bort etiketten; ren testskaffållning får
  `st_test` och tas bort inom 3 dagar.
- Avsluta varje uppgift med en lista "Städat / Kvar och varför".
