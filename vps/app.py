#!/usr/bin/env python3
"""Discord2DCS v0.10.0-beta - VPS Discord bot + WebSocket bridge.

v0.5 adds SQLite-backed client management and a Discord slash-command admin UI.
Community PC clients remain protocol-compatible with v0.4.x.
"""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os
import ssl
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import discord
from discord import app_commands
import websockets
from websockets.exceptions import ConnectionClosed

from admin_commands import AdminConfig, install_admin_group
from database import Database

APP = "discord2dcs"
VERSION = "0.10.0-beta"
LOG = logging.getLogger(APP)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "ja", "on"}


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        return int(raw.strip()) if raw and raw.strip() else default
    except ValueError:
        return default


def clean_field(value: Any, limit: int = 1800) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = " ".join(text.split())
    return text[:limit]


TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
CHANNEL_ID = env_int("DISCORD_CHANNEL_ID", 0)
GUILD_ID = env_int("DISCORD_GUILD_ID", 0)
LEGACY_DISPLAY_NAME = clean_field(os.getenv("DCS_DISPLAY_NAME", "DCS-Pilot"), 80) or "DCS-Pilot"
LEGACY_BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "").strip()
WS_BIND = os.getenv("WS_BIND", "0.0.0.0").strip() or "0.0.0.0"
WS_PORT = env_int("WS_PORT", 8766)
MIRROR_BOTS = env_bool("MIRROR_BOTS", False)
QUEUE_SIZE = max(1, min(500, env_int("QUEUE_SIZE", 50)))
TLS_ENABLED = env_bool("TLS_ENABLED", False)
TLS_CERT_FILE = os.getenv("TLS_CERT_FILE", "/certs/server.crt").strip()
TLS_KEY_FILE = os.getenv("TLS_KEY_FILE", "/certs/server.key").strip()
DATA_DIR = Path(os.getenv("DATA_DIR", "/data").strip() or "/data")
DB_FILE = Path(os.getenv("DB_FILE", str(DATA_DIR / "discord2dcs.db")).strip() or str(DATA_DIR / "discord2dcs.db"))
WS_ALLOWED_PATHS = {
    (p.strip() or "/") for p in os.getenv("WS_ALLOWED_PATHS", "/ws,/").split(",") if p.strip()
}
TRUST_PROXY_HEADERS = env_bool("TRUST_PROXY_HEADERS", False)
REQUIRE_PROXY_TLS = env_bool("REQUIRE_PROXY_TLS", False)
CLIENT_MESSAGE_LIMIT = max(1, min(100, env_int("CLIENT_MESSAGE_LIMIT", 6)))
CLIENT_MESSAGE_WINDOW_SECONDS = max(1, min(300, env_int("CLIENT_MESSAGE_WINDOW_SECONDS", 10)))

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN fehlt")
if CHANNEL_ID <= 0:
    raise RuntimeError("DISCORD_CHANNEL_ID muss gesetzt sein")
if LEGACY_BRIDGE_SECRET and len(LEGACY_BRIDGE_SECRET) < 24:
    raise RuntimeError("BRIDGE_SECRET ist gesetzt, aber zu kurz (mindestens 24 Zeichen)")

DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE.parent.mkdir(parents=True, exist_ok=True)
db = Database(DB_FILE, legacy_data_dir=DATA_DIR)

ADMIN_CONFIG = AdminConfig.from_env(
    admin_user_ids=os.getenv("ADMIN_USER_IDS", ""),
    admin_role_ids=os.getenv("ADMIN_ROLE_IDS", ""),
    admin_channel_id=env_int("ADMIN_CHANNEL_ID", 0),
    admin_log_channel_id=env_int("ADMIN_LOG_CHANNEL_ID", 0),
    allow_guild_administrators=env_bool("ALLOW_GUILD_ADMIN", False),
    public_ws_url=os.getenv("PUBLIC_WS_URL", ""),
)


def build_server_ssl() -> ssl.SSLContext | None:
    if not TLS_ENABLED:
        return None
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(TLS_CERT_FILE, TLS_KEY_FILE)
    return ctx


SSL_CONTEXT = build_server_ssl()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
channel_cache: discord.abc.Messageable | None = None
commands_synced = False


@dataclass
class ClientSession:
    lock: asyncio.Lock
    display_name: str
    client_id: str
    legacy: bool = False
    expires_at: str | None = None
    message_times: deque[float] | None = None
    language: str = "en"


ws_clients: dict[Any, ClientSession] = {}
pending_discord_to_pc: list[dict[str, Any]] = []


def is_client_online(client_id: str) -> bool:
    return any(not session.legacy and session.client_id == str(client_id) for session in ws_clients.values())


async def disconnect_client_sessions(client_id: str, reason: str, exclude_ws: Any | None = None) -> None:
    for ws, session in list(ws_clients.items()):
        if ws is exclude_ws or session.legacy or session.client_id != str(client_id):
            continue
        try:
            await ws.close(code=4003, reason=clean_field(reason, 120) or "client access changed")
        except Exception:
            pass


# Register slash commands once. Command sync itself happens after Discord is ready.
install_admin_group(
    tree=tree,
    bot=client,
    db=db,
    config=ADMIN_CONFIG,
    disconnect_cb=disconnect_client_sessions,
    online_cb=is_client_online,
)


@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    LOG.exception("Slash-Command-Fehler: %s", error)
    lang = str(getattr(interaction, "locale", "")).lower()
    message = ("❌ Discord2DCS-Adminbefehl ist fehlgeschlagen. Details stehen im VPS-Log." if lang.startswith("de") else "❌ Discord2DCS admin command failed. Details are available in the VPS log.")
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except Exception:
        pass


def request_path(ws: Any) -> str:
    req = getattr(ws, "request", None)
    path = getattr(req, "path", "/") or "/"
    return str(path).split("?", 1)[0] or "/"


def forwarded_proto(ws: Any) -> str:
    if not TRUST_PROXY_HEADERS:
        return ""
    req = getattr(ws, "request", None)
    headers = getattr(req, "headers", None)
    if not headers:
        return ""
    try:
        return str(headers.get("X-Forwarded-Proto", "")).split(",", 1)[0].strip().lower()
    except Exception:
        return ""


def remote_label(ws: Any) -> str:
    remote = getattr(ws, "remote_address", None)
    base = str(remote)
    if not TRUST_PROXY_HEADERS:
        return base
    req = getattr(ws, "request", None)
    headers = getattr(req, "headers", None)
    if not headers:
        return base
    try:
        xff = str(headers.get("X-Forwarded-For", "")).split(",", 1)[0].strip()
        return xff or base
    except Exception:
        return base


def session_text(session: ClientSession, de: str, en: str) -> str:
    return de if session.language == "de" else en


def client_rate_allowed(session: ClientSession) -> bool:
    now = time.monotonic()
    if session.message_times is None:
        session.message_times = deque()
    cutoff = now - CLIENT_MESSAGE_WINDOW_SECONDS
    while session.message_times and session.message_times[0] < cutoff:
        session.message_times.popleft()
    if len(session.message_times) >= CLIENT_MESSAGE_LIMIT:
        return False
    session.message_times.append(now)
    return True


def discord_status_payload() -> dict[str, Any]:
    return {
        "type": "status",
        "discord_ready": client.is_ready(),
        "discord_user": clean_field(getattr(client.user, "display_name", client.user), 80) if client.user else "",
        "version": VERSION,
    }


async def send_ws(ws: Any, payload: dict[str, Any]) -> bool:
    session = ws_clients.get(ws)
    if session is None:
        return False

    if not session.legacy:
        entry = db.get_client_by_id(session.client_id)
        if entry is None:
            try:
                await ws.close(code=4003, reason="forbidden")
            except Exception:
                pass
            return False
        allowed, reason = db.client_access_state(entry)
        if not allowed:
            LOG.warning("Client-Zugriff beendet: %s | %s", session.client_id, reason)
            try:
                await ws.close(code=4003, reason=reason)
            except Exception:
                pass
            return False

    try:
        async with session.lock:
            await ws.send(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        return True
    except (ConnectionClosed, ConnectionError, OSError, RuntimeError):
        return False


async def broadcast(payload: dict[str, Any]) -> int:
    sent = 0
    for ws in list(ws_clients):
        if await send_ws(ws, payload):
            sent += 1
    return sent


async def get_channel() -> discord.abc.Messageable:
    global channel_cache
    if channel_cache is not None:
        return channel_cache
    ch = client.get_channel(CHANNEL_ID)
    if ch is None:
        ch = await client.fetch_channel(CHANNEL_ID)
    channel_cache = ch
    return ch


async def sync_commands_once() -> None:
    global commands_synced
    if commands_synced:
        return
    try:
        if GUILD_ID > 0:
            guild = discord.Object(id=GUILD_ID)
            tree.copy_global_to(guild=guild)
            synced = await tree.sync(guild=guild)
            LOG.info("Slash-Commands synchronisiert: %d | Guild %s", len(synced), GUILD_ID)
        else:
            synced = await tree.sync()
            LOG.info("Slash-Commands global synchronisiert: %d", len(synced))
            LOG.warning("DISCORD_GUILD_ID ist nicht gesetzt; globale Slash-Commands koennen bis zu etwa einer Stunde brauchen.")
        commands_synced = True
    except Exception:
        LOG.exception("Slash-Command-Synchronisierung fehlgeschlagen")


@client.event
async def on_ready() -> None:
    LOG.info("Discord verbunden als %s (%s)", client.user, getattr(client.user, "id", "?"))
    ch = await get_channel()
    LOG.info("Gekoppelter Discord-Kanal: %s (%s)", ch, CHANNEL_ID)
    if not (ADMIN_CONFIG.admin_user_ids or ADMIN_CONFIG.admin_role_ids or ADMIN_CONFIG.allow_guild_administrators):
        LOG.warning("Keine Discord2DCS-Admins konfiguriert: ADMIN_USER_IDS / ADMIN_ROLE_IDS sind leer")
    await sync_commands_once()
    await broadcast(discord_status_payload())


@client.event
async def on_message(message: discord.Message) -> None:
    if message.channel.id != CHANNEL_ID:
        return
    if client.user and message.author.id == client.user.id:
        return
    if message.author.bot and not MIRROR_BOTS:
        return

    content = clean_field(message.content, 1400)
    if message.attachments:
        names = ", ".join(clean_field(a.filename, 120) for a in message.attachments[:4])
        content = f"{content} [Attachment: {names}]".strip()
    if not content:
        return

    author = clean_field(getattr(message.author, "display_name", message.author.name), 80)
    payload = {
        "type": "discord_message",
        "author": author,
        "content": content,
        "created_at": message.created_at.isoformat(),
    }

    count = await broadcast(payload)
    if count == 0:
        pending_discord_to_pc.append(payload)
        del pending_discord_to_pc[:-QUEUE_SIZE]
        LOG.warning("Discord -> PC vorgemerkt, kein DCS-PC verbunden | %s: %s", author, content)
    else:
        LOG.info("Discord -> PC (%d Client(s)) | %s: %s", count, author, content)


async def post_to_discord(content: str, display_name: str) -> None:
    content = clean_field(content, 1700)
    if not content:
        return
    display_name = clean_field(display_name, 80) or "DCS-Pilot"
    ch = await get_channel()
    await ch.send(
        f"✈ **{display_name}:** {content}",
        allowed_mentions=discord.AllowedMentions.none(),
    )
    LOG.info("DCS -> Discord | %s: %s", display_name, content)


async def handle_authenticated_message(ws: Any, raw: str) -> None:
    session = ws_clients.get(ws)
    if session is None:
        return
    if not session.legacy:
        entry = db.get_client_by_id(session.client_id)
        if entry is None:
            await ws.close(code=4003, reason="forbidden")
            return
        allowed, reason = db.client_access_state(entry)
        if not allowed:
            await ws.close(code=4003, reason=reason)
            return

    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        await send_ws(ws, {"type": "error", "message": session_text(session, "Ungültiges JSON", "Invalid JSON")})
        return

    kind = msg.get("type")
    if kind == "send_discord":
        content = clean_field(msg.get("content", ""), 1700)
        if not content:
            return
        if not client_rate_allowed(session):
            LOG.warning(
                "Rate-Limit fuer Client %s (%s): max. %s Nachricht(en) in %ss",
                session.client_id, session.display_name, CLIENT_MESSAGE_LIMIT, CLIENT_MESSAGE_WINDOW_SECONDS,
            )
            await send_ws(
                ws,
                {
                    "type": "error",
                    "message": session_text(session, f"Zu viele Nachrichten: maximal {CLIENT_MESSAGE_LIMIT} in {CLIENT_MESSAGE_WINDOW_SECONDS}s", f"Too many messages: maximum {CLIENT_MESSAGE_LIMIT} in {CLIENT_MESSAGE_WINDOW_SECONDS}s"),
                },
            )
            return
        try:
            await post_to_discord(content, session.display_name)
            await send_ws(ws, {"type": "ack", "content": content[:200]})
        except Exception as exc:
            LOG.exception("DCS -> Discord fehlgeschlagen")
            await send_ws(ws, {"type": "error", "message": session_text(session, f"Discord-Senden fehlgeschlagen: {exc}", f"Sending to Discord failed: {exc}")})
    elif kind == "ping":
        await send_ws(ws, {"type": "pong"})
    else:
        await send_ws(ws, {"type": "error", "message": session_text(session, f"Unbekannter Nachrichtentyp: {kind}", f"Unknown message type: {kind}")})


async def websocket_handler(ws: Any) -> None:
    remote = remote_label(ws)
    path = request_path(ws)
    client_name = "unbekannt"
    LOG.info("WebSocket-Verbindung von %s | Pfad=%s", remote, path)

    try:
        if path not in WS_ALLOWED_PATHS:
            LOG.warning("WebSocket-Pfad abgelehnt: %s | %s", path, remote)
            await ws.close(code=4004, reason="invalid websocket path")
            return

        if REQUIRE_PROXY_TLS and SSL_CONTEXT is None and forwarded_proto(ws) != "https":
            LOG.warning("Unverschluesselte Proxy-Verbindung abgelehnt: %s", remote)
            await ws.close(code=4003, reason="secure websocket required")
            return
        raw = await asyncio.wait_for(ws.recv(), timeout=15)
        hello = json.loads(raw)
        kind = hello.get("type")
        client_name = clean_field(hello.get("client_name", "DCS-PC"), 80) or "DCS-PC"
        client_version = clean_field(hello.get("version", "?"), 40)
        client_language = str(hello.get("language", "en")).strip().lower()
        if client_language not in {"de", "en"}:
            client_language = "en"

        session_data: dict[str, Any] | None = None
        pair_access_token = ""
        paired_result = None

        if kind == "pair":
            code = str(hello.get("code", "")).strip()
            if not code:
                await ws.close(code=4003, reason="pair_required")
                return
            paired_result, pair_error = db.consume_pairing_code(code)
            if paired_result is None:
                LOG.warning("Pairing abgelehnt fuer %s | %s", remote, pair_error)
                await ws.close(code=4003, reason="pair_invalid")
                return
            pair_access_token = paired_result.access_token
            session_data = {
                "client_id": paired_result.client_id,
                "display_name": paired_result.display_name,
                "discord_user_id": paired_result.discord_user_id,
                "legacy": False,
                "expires_at": paired_result.expires_at,
            }
            if paired_result.replaced_existing:
                await disconnect_client_sessions(paired_result.client_id, "access token replaced", exclude_ws=ws)
                LOG.info("Client-Token rotiert: Client-ID %s | %s", paired_result.client_id, remote)
            else:
                LOG.info("Neues Pairing: %s | Client-ID %s | %s", paired_result.display_name, paired_result.client_id, remote)

        elif kind == "auth":
            token = str(hello.get("token", "")).strip()
            legacy_secret = str(hello.get("secret", "")).strip()

            auth_error = "forbidden"
            if token:
                session_data, auth_error = db.authenticate_access_token(token)
            elif LEGACY_BRIDGE_SECRET and legacy_secret and hmac.compare_digest(legacy_secret, LEGACY_BRIDGE_SECRET):
                session_data = {
                    "client_id": "legacy",
                    "display_name": LEGACY_DISPLAY_NAME,
                    "legacy": True,
                    "expires_at": None,
                }

            if session_data is None:
                LOG.warning("Authentifizierung abgelehnt fuer %s | %s", remote, auth_error)
                auth_reason = {
                    "client disabled": "client_disabled",
                    "token expired": "token_expired",
                    "forbidden": "token_invalid",
                }.get(str(auth_error or "").lower(), "token_invalid")
                await ws.close(code=4003, reason=auth_reason)
                return
        else:
            await ws.close(code=4001, reason="auth_or_pair_required")
            return

        assert session_data is not None
        ws_clients[ws] = ClientSession(
            lock=asyncio.Lock(),
            display_name=clean_field(session_data["display_name"], 80) or client_name,
            client_id=clean_field(session_data["client_id"], 64),
            legacy=bool(session_data.get("legacy")),
            expires_at=session_data.get("expires_at"),
            message_times=deque(),
            language=client_language,
        )
        session = ws_clients[ws]
        LOG.info(
            "PC-Client authentifiziert: %s | Anzeige=%s | ID=%s | Version %s | %s",
            client_name,
            session.display_name,
            session.client_id,
            client_version,
            remote,
        )

        status = discord_status_payload()
        response = {
            "type": "pair_ok" if pair_access_token else "auth_ok",
            "discord_ready": status["discord_ready"],
            "discord_user": status["discord_user"],
            "display_name": session.display_name,
            "client_id": session.client_id,
            "version": VERSION,
            "access_expires_at": session.expires_at,
        }
        if pair_access_token:
            response["access_token"] = pair_access_token
            response["access_expires_at"] = paired_result.expires_at if paired_result else None
        await send_ws(ws, response)

        while pending_discord_to_pc:
            payload = pending_discord_to_pc[0]
            if not await send_ws(ws, payload):
                break
            pending_discord_to_pc.pop(0)

        async for message in ws:
            await handle_authenticated_message(ws, message)

    except asyncio.TimeoutError:
        LOG.warning("WebSocket-Authentifizierung Timeout: %s", remote)
        try:
            await ws.close(code=4001, reason="auth timeout")
        except Exception:
            pass
    except (ConnectionClosed, ConnectionError, OSError):
        pass
    except json.JSONDecodeError:
        LOG.warning("Ungueltige Auth-JSON von %s", remote)
        try:
            await ws.close(code=4002, reason="bad json")
        except Exception:
            pass
    except Exception:
        LOG.exception("WebSocket-Clientfehler: %s", remote)
    finally:
        session = ws_clients.pop(ws, None)
        LOG.info("PC-Client getrennt: %s | %s", session.display_name if session else client_name, remote)


async def revalidate_sessions() -> None:
    while True:
        await asyncio.sleep(30)
        for ws, session in list(ws_clients.items()):
            if session.legacy:
                continue
            entry = db.get_client_by_id(session.client_id)
            if entry is None:
                allowed, reason = False, "forbidden"
            else:
                allowed, reason = db.client_access_state(entry)
            if allowed:
                continue
            LOG.warning("Trenne Client %s (%s): %s", session.client_id, session.display_name, reason)
            try:
                await ws.close(code=4003, reason=reason)
            except Exception:
                pass


async def websocket_server() -> None:
    scheme = "wss" if TLS_ENABLED else "ws"
    LOG.info("WebSocket-Bridge lauscht: %s://%s:%s", scheme, WS_BIND, WS_PORT)
    LOG.info("SQLite-Datenbank: %s", DB_FILE)
    LOG.info("Legacy-Shared-Secret: %s", "AN" if LEGACY_BRIDGE_SECRET else "AUS")
    LOG.info("WebSocket-Pfade: %s", ", ".join(sorted(WS_ALLOWED_PATHS)))
    LOG.info("Proxy-Header vertrauen: %s", "JA" if TRUST_PROXY_HEADERS else "NEIN")
    LOG.info("Proxy-TLS erzwingen: %s", "JA" if REQUIRE_PROXY_TLS else "NEIN")
    LOG.info("Client-Rate-Limit: %s Nachricht(en) / %ss", CLIENT_MESSAGE_LIMIT, CLIENT_MESSAGE_WINDOW_SECONDS)
    async with websockets.serve(
        websocket_handler,
        WS_BIND,
        WS_PORT,
        ssl=SSL_CONTEXT,
        ping_interval=20,
        ping_timeout=20,
        close_timeout=5,
        max_size=64 * 1024,
    ):
        await asyncio.Future()


async def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    LOG.info("Discord2DCS VPS %s startet", VERSION)
    LOG.info("TLS im Python-Backend: %s", "AN" if TLS_ENABLED else "AUS (Reverse Proxy moeglich)")
    LOG.info("Oeffentliche WebSocket-URL: %s", ADMIN_CONFIG.public_ws_url or "nicht gesetzt")
    LOG.info("Clients in DB: %d", db.count_clients())
    await asyncio.gather(client.start(TOKEN), websocket_server(), revalidate_sessions())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
