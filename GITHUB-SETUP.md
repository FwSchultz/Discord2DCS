# GitHub mit GitHub Desktop vorbereiten

Das Repository `FwSchultz/Discord2DCS` existiert aktuell noch nicht.

## Einfacher Weg

1. GitHub Desktop öffnen.
2. **File → New repository…**
3. Name: `Discord2DCS`
4. Owner: `FwSchultz`
5. Lokalen Pfad auswählen.
6. Repository erstellen und auf GitHub veröffentlichen.
7. Den Inhalt des Pakets `Discord2DCS-GitHub-Repository-v0.11.0-beta.zip` **in den Repository-Ordner** kopieren.
8. In GitHub Desktop kontrollieren, welche Dateien geändert/neu sind.
9. Besonders prüfen, dass **keine** `.env`, `discord2dcs.db`, Zertifikate, `config.json` oder Logs auftauchen.
10. Commit-Vorschlag: `Prepare Discord2DCS 0.11.0-beta`
11. Push origin.

Danach kann das Repository direkt weiter gepflegt werden. Release-ZIPs gehören später besser in **GitHub Releases** und nicht dauerhaft als Binärdateien in den Source-Tree.
