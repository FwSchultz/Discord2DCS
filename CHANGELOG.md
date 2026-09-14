# Changelog

## 0.11.0-beta

### Public beta – secure no-domain server mode
- Promoted the successfully tested 0.11.0-beta-rc2 release candidate to public beta.
- Fresh Ubuntu VPS setup tested successfully.
- Docker Engine / Docker Compose preflight tested.
- Secure WSS operation with a public IPv4 address and no domain tested successfully.
- Let's Encrypt short-lived IP certificate issued successfully.
- Automatic certificate-renewal timer installed and renewal service verified with exit status 0.
- HTTPS health endpoint returned HTTP/2 200.
- Pairing using only the public IPv4 address succeeded.
- Discord → DCS and DCS → Discord both verified over `wss://<public-ip>/ws`.
- Domain mode and insecure test mode remain available.
- No bridge protocol changes compared with 0.11.0-beta-rc2.

## 0.11.0-beta

### Fresh VPS setup
- Server setup now checks Docker Engine and the Docker Compose Plugin automatically.
- On fresh Debian/Ubuntu hosts, Docker is installed from Docker's official APT repository when missing.
- Docker is enabled, started and verified before Discord2DCS configuration begins.
- Existing third-party Docker installations are not silently removed.
- German and English server-admin documentation now starts from a clean VPS.
- No Discord2DCS bridge protocol changes compared with 0.11.0-beta-rc1.

## 0.11.0-beta

### Server reachability setup
- Added interactive `SETUP-SERVER.sh` with three modes: domain/hostname, secure public IPv4 without domain, and insecure test mode.
- Secure IP mode configures Nginx + Certbot 5.4+ and Let's Encrypt short-lived IP certificates with automatic renewal.
- Server setup prints the exact address that admins should give to pilots and writes `SERVER-INFO.txt`.
- Windows installer now explicitly accepts a domain, a public IP, or a full insecure test URL.
- Plain domain/public-IP input is normalized to `wss://.../ws`; insecure `ws://` still requires explicit confirmation.

## 0.11.0-beta

### First public beta
- Promoted the successfully tested 0.11.0-beta-rc2 release candidate to the first public beta.
- Complete fresh installation on a second/clean Windows PC tested successfully.
- Discord → DCS and DCS → Discord verified after fresh installation.
- DCS Special Options, branding icons, pairing and Windows client installation verified.
- No protocol or runtime behavior changes compared with 0.11.0-beta-rc2.

## 0.11.0-beta

### Licensing
- Added the MIT License.
- Copyright: `Copyright (c) 2026 FwSchultz`.
- Updated German and English README license sections.
- Updated the release checklist: licensing is complete.
- No protocol or runtime behavior changes compared with 0.11.0-beta-rc1.

## 0.11.0-beta

### Release preparation
- Documentation completely rewritten for first-time users in German and English.
- Added `SERVER-ADMIN-GUIDE.md` and `RELEASE-CHECKLIST.md`.
- Added public-repository `.gitignore` to protect `.env`, SQLite data, certificates, logs and client configuration.
- Updated Nginx example to current `http2 on;` syntax.
- Corrected historical version headings from the alpha development cycle.
- No protocol change compared with v0.9.4-alpha.

## 0.9.4-alpha
- DCS Special Options now use the official Discord2DCS icon via a registered DCS Theme/Skin.

## 0.9.3-alpha
- Fixed Windows shortcut icon update crash caused by an uninitialized `$icon` path.

## 0.9.2-alpha
- Added official Discord2DCS branding and Windows/DCS icon assets.

## 0.9.1-alpha
- Fixed the DCS Special Options tech mod not loading because of invalid leading characters in generated files.

## 0.9.0-alpha
- Added **DCS → Options → Special → Discord2DCS** with enable/disable, overlay startup, system messages and language settings.

## 0.8.1-alpha
- DCS-not-running is handled as a normal waiting state instead of repeated warnings.

## 0.8.0-alpha
- Added German/English localization for installer, PC client, DCS overlay and Discord admin responses.

## 0.7.0-alpha
- Community-focused installation under `%LOCALAPPDATA%\Discord2DCS`, shortcuts, optional autostart, update/repair/uninstall tools and Discord quick panel.

## 0.6.0-alpha
- Added WSS/TLS reverse-proxy support and secure localhost-only WebSocket publishing on the VPS.

## 0.5.1-alpha
- Fixed `/dcs-client list` single-page response handling.

## 0.5.0-alpha
- Added SQLite persistence and Discord slash-command client administration.

## 0.4.1-alpha
- Added admin-controlled token durations, expiry changes, revoke/enable and Lifetime access.

## 0.4.0-alpha
- Added one-time pairing codes and individual client access tokens.

## 0.3.0-alpha
- Moved the Discord bridge to the Contabo/VPS architecture with an outbound Windows client connection.

## 0.2.0-alpha
- Introduced the dedicated DCS GameGUI overlay and local TCP bridge.

## 0.1.0-alpha
- First native-DCS-chat prototype. This approach was abandoned in favor of the dedicated overlay architecture.
