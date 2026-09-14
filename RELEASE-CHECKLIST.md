# Discord2DCS 0.11.0-beta – Release-Checkliste

## Pflicht vor Public Beta

- [x] Frischer Ubuntu-VPS: Docker/Compose durch `SETUP-SERVER.sh` erkannt bzw. vorbereitet.
- [x] Modus `[2] Öffentliche IP ohne Domain` erfolgreich getestet.
- [x] Let's-Encrypt-IP-Zertifikat (`shortlived`) erfolgreich ausgestellt.
- [x] `https://<IP>/health` liefert HTTP/2 200.
- [x] Pairing über reine öffentliche IP erfolgreich.
- [x] Discord → DCS und DCS → Discord über `wss://<IP>/ws` erfolgreich getestet.
- [x] Certbot-Renewal-Service manuell getestet: `status=0/SUCCESS`.
- [x] Renewal-Timer aktiv und wartend.

- [x] MIT-Lizenz ausgewählt und `LICENSE` hinzugefügt.
- [x] Frische Installation auf einem zweiten/sauberen Windows-PC erfolgreich getestet.
- [ ] Test mit bereits vorhandenem Python **und** ohne Python durchführen.
- [ ] Update von v0.9.4-alpha auf 0.11.0-beta testen; Access-Token muss erhalten bleiben.
- [ ] Deutsch und English im Installer testen.
- [ ] DCS Special Options testen: Aktivieren, Overlay beim Start, Systemmeldungen, Sprache.
- [ ] Desktop-Icon und DCS-Special-Icon prüfen.
- [ ] Discord → DCS und DCS → Discord testen.
- [ ] `/dcs-client create`, `panel`, `set-expiry`, `extend`, `revoke`, `enable`, `pairing` testen.
- [ ] 30-Tage-Token und `Lifetime` testen.
- [ ] WSS/TLS-Endpunkt testen; `/health` muss HTTP 200 liefern.
- [ ] Zertifikatserneuerung prüfen (`certbot renew --dry-run` oder Caddy).
- [ ] Sicherstellen, dass Port 8766 im Produktions-Compose nur auf `127.0.0.1` gebunden ist.
- [ ] `.env`, `vps/data/`, `vps/certs/`, `config.json`, Logs und Tokens dürfen nicht im Repository landen.

## GitHub

- [ ] Neues Repository `FwSchultz/Discord2DCS` anlegen.
- [ ] Inhalt des GitHub-Repository-ZIPs hineinkopieren.
- [ ] `git status` kontrollieren – keine Secrets oder Datenbankdateien.
- [ ] README DE/EN auf GitHub prüfen.
- [ ] Release `v0.11.0-beta` erstellen.
- [ ] Als Release-Asset mindestens `Discord2DCS-Community-Client-v0.11.0-beta.zip` hochladen.
- [ ] Optional Komplettpaket für Server-Admins als zweites Asset hochladen.

## DCS User Files

- [ ] **Nur das Community-Client-ZIP** hochladen, nicht das Voll-/VPS-Paket.
- [ ] `DCS-USER-FILES-DESCRIPTION.txt` in die Beschreibung übernehmen.
- [ ] offizielles Discord2DCS-Logo als Vorschaubild verwenden.
- [ ] Kategorie/Tags passend zu DCS utility/mod wählen.
- [ ] GitHub-Projektlink nach Repo-Erstellung ergänzen.

## Nach Veröffentlichung

- [ ] Mit einem echten Community-Mitglied Neuinstallation testen.
- [ ] Support-Logs auf verständliche Fehlermeldungen prüfen.
- [ ] Bekannte Probleme als GitHub-Issues dokumentieren.
- [ ] No-Domain-WSS als eigenes Folge-Thema planen/testen.
