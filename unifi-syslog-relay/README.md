# UniFi Syslog Relay

Tar emot UniFi-konsolens CEF-syslog på UDP och vidaresänder den med en
RFC5424-PRI till Alloy.

## Varför appen finns

UniFi skickar CEF-rader **utan** PRI-header:

```text
Oct 27 08:27:36 Taurito CEF:0|Ubiquiti|UniFi Network|11.0.97|521|VPN Client Disconnected|2|UNIFIcategory=VPN ...
```

Alloys `loki.source.syslog` avvisar dem: *"invalid or unsupported framing,
first byte: 'O'"*. Relayen lägger på `<14>1 - - - - - - ` (facility 1, severity 6)
och lämnar CEF-raden orörd.

Appen behövs bara på sajter som **saknar** en Proxmox-host med Alloy. På
Töcksfors och Karlstad körs samma kod som en systemd-tjänst på Proxmox
(`unifi-syslog-relay.service` i `HomeLab/observability/alloy/`). Taurito har
ingen Proxmox — Home Assistant-hårdvaran är för liten för ännu en agent — så
reläet körs som app där i stället och skickar vidare över tailnet.

**`relay.py` i den här katalogen är kanonisk.** Observability-repot har en
byte-identisk kopia som distribueras till Proxmox-hostarna, och dess CI fäller
varje avvikelse. Båda förpackningarna konfigureras med samma miljövariabler
(`LISTEN_HOST`, `LISTEN_PORT`, `FORWARD_HOST`, `FORWARD_PORT`,
`SYSLOG_FACILITY`, `SYSLOG_SEVERITY`) — appen via `/data/options.json`,
systemd via `Environment=`.

## Dataflöde (Taurito)

```text
UCG (Taurito) --udp/1514--> HA-appen --udp/1517--> karlstad-proxmox
                                                      └─ unifi-syslog-relay-taurito
                                                         --udp/1516--> Alloy
                                                         → Loki, site="taurito"
```

Mellan HA och karlstad-proxmox krävs ett tailnet-grant
(`tag:homeassistant → tag:proxmox`, `udp:1517`).

## Konfiguration

| Option | Default | Betydelse |
|---|---|---|
| `listen_port` | `1514` | UDP-port som konsolen skickar till (HA:s LAN-IP) |
| `forward_host` | — | Alloy-reläets adress; tomt värde stoppar appen |
| `forward_port` | `1517` | UDP-port hos reläet på Proxmox |
| `syslog_facility` | `1` | RFC5424-facility (1 = user) |
| `syslog_severity` | `6` | RFC5424-severity (6 = info) |

`forward_host` sätts till IP-adress om HA inte har MagicDNS: `unifi-syslog-relay`
slår upp namnet en gång vid start och loggar den adress den använder.

## Logg

Apploggen skriver en rad vid start, en statistikrad var femte minut
(`mottagna=… vidaresända=… fel=…`) och vid avslut. En nere länk loggas första
gången och sedan var hundrade gång — aldrig en rad per datagram.

## Vad appen inte gör

- **Buffrar inte.** UDP till en otillgänglig mottagare tappas, och räknas som
  `fel`. Loggkedjan är inte en kö; går Alloy ner förloras de raderna.
- **Översätter inte CEF-severity till `level`.** Det görs i `loki.process` på
  Alloy-sidan, så att alla tre sajter får samma mappning.
