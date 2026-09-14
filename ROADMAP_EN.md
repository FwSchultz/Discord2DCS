# Discord2DCS – Roadmap

> Discord ↔ DCS without Alt+Tab

This roadmap describes the planned development of Discord2DCS after `v0.11.0-beta`.

The first priority is deliberately the **DCS in-game overlay**. After that come maintenance, server administration, Discord features, multi-community support, and additional quality-of-life improvements.

[Deutsche Roadmap](ROADMAP.md)

---

## Status legend

| Status | Meaning |
|---|---|
| ✅ | Done / released |
| 🔧 | In progress / next focus |
| 📋 | Planned |
| 💡 | Idea for later |

---

# ✅ Current state – v0.11.0-beta

Already implemented and tested:

- Discord → DCS messages
- DCS → Discord replies
- dedicated DCS GameGUI overlay
- overlay toggle with `Ctrl + Shift + D`
- DCS Special Options
- German / English
- personal one-time pairing
- individual access token per pilot
- client validity periods including `Lifetime`
- Discord admin management through `/dcs-client`
- SQLite database
- WSS/TLS
- domain / hostname operation
- secure operation without a domain using a public IPv4 address
- Let's Encrypt IP certificate
- automatic certificate renewal
- insecure `ws://` test mode
- automatic Docker / Compose setup on a fresh Debian/Ubuntu server
- Windows installer
- Update / Repair / Uninstall
- optional Windows autostart
- desktop icon
- DCS Special Options icon
- GitHub release
- MIT License
- separate Community Client and Server packages

---

# 🔧 v0.12.x – DCS Overlay 2.0

**Highest priority**

Goal: Make the overlay significantly more flexible, modern, and comfortable for everyday flying.

## v0.12.0-beta-rc1 – technical foundation

### Window position and size

- [ ] persist overlay position
- [ ] persist window size
- [ ] restore position after restarting DCS
- [ ] restore size after restarting DCS
- [ ] keep the overlay inside the visible screen area after resolution changes
- [ ] support ultrawide resolutions
- [ ] support multi-monitor setups

### Dynamic resizing

When the window is resized, all controls should resize and reposition correctly.

- [ ] chat area grows horizontally and vertically
- [ ] input field grows horizontally
- [ ] `Send` stays aligned on the right
- [ ] `Clear` stays aligned on the right
- [ ] no overlapping controls
- [ ] sensible minimum window size
- [ ] sensible maximum window size

### Font size

Selectable font size for chat and input field:

- [ ] Small – 12
- [ ] Normal – 14
- [ ] Large – 16
- [ ] Very large – 18

The selection should be available under:

```text
DCS → Options → Special → Discord2DCS
```

### Transparency

Selectable overlay transparency:

- [ ] 50 %
- [ ] 70 %
- [ ] 85 %
- [ ] 100 %

Text readability should remain good regardless of background transparency.

---

## v0.12.0-beta-rc2 – usability & presentation

### Timestamps

Optional timestamp before chat messages:

```text
[20:14] Freefall: About to go airborne.
[20:15] Schultz: Copy.
```

- [ ] timestamps ON/OFF
- [ ] use local time
- [ ] compact presentation

### Status display

More modern and compact connection status.

Example:

```text
Discord2DCS                          ● ONLINE
```

or:

```text
● DCS     ● Client     ● Discord
```

Planned:

- [ ] show DCS connection state
- [ ] show Windows client connection state
- [ ] show Discord/VPS connection state
- [ ] clear OFFLINE / CONNECTING / ONLINE states

### Auto-hide

Optional automatic hiding:

- [ ] Never
- [ ] after 10 seconds
- [ ] after 30 seconds
- [ ] after 60 seconds

Behavior:

- new message → optionally show the overlay automatically
- timeout → hide the overlay again
- `Ctrl + Shift + D` always remains available

### Remember visibility state

Optional:

- [ ] save the last visible/hidden state
- [ ] make startup behavior selectable

### Lock overlay

- [ ] lock window position
- [ ] lock window size
- [ ] prevent accidental movement while flying

### Message display

- [ ] configurable number of visible messages
- [ ] improve scrolling behavior
- [ ] automatically keep new messages visible
- [ ] keep `Clear` as a local-display-only action

---

## v0.12.x – visual polish

Target concept:

```text
┌ Discord2DCS                              ● ONLINE ┐
│                                                     │
│ [20:14] Freefall: About to go airborne.             │
│ [20:15] Schultz: Copy.                              │
│ [20:16] Balu: Rendezvous at WP2.                    │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Type a message...                  [Send] [Clear]   │
└─────────────────────────────────────────────────────┘
```

Planned:

- [ ] modern dark design
- [ ] lightly transparent surface
- [ ] subtle cyan / blue accents matching the Discord2DCS logo
- [ ] good readability in day and night missions
- [ ] compact header
- [ ] clearer visual separation between chat and input
- [ ] cleaner presentation of Discord names
- [ ] optional distinct styling for the local user's own messages

---

## DCS Special Options – planned expansion

Planned:

```text
Discord2DCS
────────────────────────────────

☑ Enable Discord2DCS
☑ Show overlay on DCS startup
☐ Show system messages

Language:
[ Auto                  ▼ ]

Font size:
[ Normal (14)           ▼ ]

Transparency:
[ 85 %                  ▼ ]

Timestamps:
[ On                    ▼ ]

Auto-hide:
[ Never                 ▼ ]
```

Position and window size should **not** be configured through the Options menu.

They should be adjusted directly in-game with the mouse and saved automatically.

---

# 📋 v0.13.x – Update & Maintenance

Goal: Make Discord2DCS easier to keep updated and maintain.

- [ ] automatic update check for the Windows client
- [ ] “New version available” notification
- [ ] optional one-click updater
- [ ] client ↔ server version comparison
- [ ] clear warning for incompatible versions
- [ ] server update script
- [ ] automatic backup of `.env`
- [ ] automatic backup of the SQLite database
- [ ] update rollback on failure
- [ ] `/dcs-client status`
- [ ] show server version
- [ ] show uptime
- [ ] show number of connected clients

---

# 📋 v0.14.x – Server Setup & Administration

Goal: A server admin should be able to operate Discord2DCS with as little Linux knowledge as possible.

## Setup assistant

- [ ] detect an existing installation
- [ ] choose Install / Update / Repair
- [ ] check Docker status
- [ ] check firewall
- [ ] check ports 80 / 443
- [ ] detect public IPv4 automatically
- [ ] verify domain resolution
- [ ] test TLS/WSS automatically
- [ ] run a health check automatically at the end
- [ ] test Discord bot connectivity
- [ ] validate Guild ID
- [ ] validate Channel ID
- [ ] verify bot permissions
- [ ] verify Admin ID / admin role

## Server tools

- [ ] `SERVER-INFO.sh`
- [ ] show the current client address again
- [ ] `STATUS-SERVER.sh`
- [ ] `REPAIR-SERVER.sh`
- [ ] `UPDATE-SERVER.sh`
- [ ] `UNINSTALL-SERVER.sh`
- [ ] create backup
- [ ] restore backup

---

# 📋 v0.15.x – Discord Features

Goal: More flexibility for squadrons and communities.

- [ ] multiple allowed Discord channels
- [ ] switch channels directly from the DCS overlay
- [ ] configurable default channel
- [ ] role-based channel permissions
- [ ] pilots only see channels they are allowed to use
- [ ] configurable message format
- [ ] cleaner Discord-name display
- [ ] optional DCS player name ↔ Discord name mapping
- [ ] expand the Discord admin panel
- [ ] channel management through Discord commands

Example:

```text
Discord2DCS

Channel:
[ #flight-training ▼ ]
```

---

# 📋 v0.16.x – Multi-Community / Multi-Instance

Goal: A single Discord2DCS server should be able to host multiple isolated communities.

Example:

```text
VPS
├── Squadron Alpha
├── Squadron Bravo
└── Squadron Charlie
```

Planned:

- [ ] multiple Discord guilds on one server instance
- [ ] separate configuration per community
- [ ] separate Discord channels
- [ ] separate admins
- [ ] separate client data
- [ ] separate pairing codes
- [ ] separate audit logs
- [ ] separate validity periods
- [ ] unique community ID
- [ ] optional separate WSS paths

Example:

```text
wss://server.example.com/alpha/ws
wss://server.example.com/bravo/ws
```

This would allow one operator to host several smaller DCS squadrons on a single VPS.

---

# 📋 v0.17.x – Windows Client GUI & Tray

Goal: The Windows client should be able to run completely in the background.

## Tray icon

- [ ] Discord2DCS icon in the Windows system tray
- [ ] start / stop client
- [ ] show status
- [ ] open logs
- [ ] open settings
- [ ] check for updates
- [ ] exit

## Small status GUI

Example:

```text
Discord2DCS

● Server connected
● DCS connected
● Pairing valid

Server:
wss://dcs.example.com/ws

[ Open logs ]
[ Settings ]
[ Check for updates ]
```

Planned:

- [ ] change server address
- [ ] change language
- [ ] change autostart setting
- [ ] renew pairing
- [ ] show client ID
- [ ] show token expiry
- [ ] manually reconnect

---

# 📋 v0.18.x – Security, Backup & Audit

Goal: Safer and more reliable long-term community operation.

- [ ] token rotation
- [ ] manually regenerate access token
- [ ] further harden pairing rate limits
- [ ] login / authentication rate limits
- [ ] automatic SQLite backups
- [ ] backup rotation
- [ ] configurable retention period
- [ ] restore function
- [ ] automatically archive expired clients
- [ ] expand audit log
- [ ] better filtering of admin actions
- [ ] warn when insecure `ws://` is used in production
- [ ] security check in server setup
- [ ] show TLS certificate status
- [ ] monitor certificate expiry

---

# 📋 v0.19.x – Release Candidate for v1.0

No major new features from this point onward.

Focus:

- [ ] bug fixes
- [ ] performance
- [ ] stability
- [ ] documentation
- [ ] migration

## Test matrix

- [ ] Windows 10
- [ ] Windows 11
- [ ] DCS World 2.9+
- [ ] single-monitor
- [ ] multi-monitor
- [ ] ultrawide
- [ ] Debian server
- [ ] Ubuntu server
- [ ] domain + WSS
- [ ] public IPv4 without domain + WSS
- [ ] insecure test mode
- [ ] upgrade from older beta versions
- [ ] fresh installation
- [ ] Repair
- [ ] Uninstall / Reinstall
- [ ] certificate renewal
- [ ] database backup / restore
- [ ] complete DE / EN review

---

# 🎯 v1.0.0 – Stable Release

Goal: Discord2DCS is stable and fully documented for normal community operation.

Planned for v1.0:

- [ ] stable DCS Overlay 2.0
- [ ] stable client installation
- [ ] stable server installer
- [ ] domain operation
- [ ] secure public IPv4 operation without a domain
- [ ] automated certificate renewal
- [ ] update system
- [ ] backup / restore
- [ ] multi-channel support
- [ ] Windows tray GUI
- [ ] complete DE / EN documentation
- [ ] Beta → Stable migration without new pairing
- [ ] GitHub release
- [ ] DCS User Files release

---

# 💡 After v1.0 – possible extensions

These items are ideas and are not firmly scheduled yet.

## Web dashboard

- web interface for server admins
- client management
- online / offline status
- token validity periods
- audit logs
- backups
- server status

## DCS server integration

Possible automatic messages:

```text
Mission started
Mission ended
Server restarted
Player connected
Player disconnected
```

## Mission-specific Discord channels

- automatic mission channel
- training channels
- event channels
- temporary channels

## SRS integration

Only if there is a clear practical benefit.

Possible ideas:

- show SRS status
- frequency information
- shared community status information

## Plugin / API system

- connect external community tools
- custom bots
- webhooks
- REST/API
- optional modules

## Statistics

Only without unnecessarily storing private message content.

Possible values:

- connected clients
- message count
- uptime
- connection quality
- server status

---

# Development principles

New features should continue to follow these goals:

1. **Easy for pilots**
2. **Easy for server admins**
3. **No unnecessary incoming port forwarding on gaming PCs**
4. **Secure WSS/TLS connections for production**
5. **No secrets in the GitHub repository**
6. **German and English**
7. **Existing installations should update without requiring new pairing whenever possible**
8. **No breaking changes without a clean migration path**
9. **Test new features as release candidates first**
10. **Stability before feature count**

---

# Next development step

## 🔧 Discord2DCS v0.12.0-beta-rc1

Next:

```text
DCS Overlay
├── save position
├── save size
├── dynamic resizing
├── font size
└── transparency
```

After that, `v0.12.0-beta-rc2` will add timestamps, status display, auto-hide, and visual polish.
