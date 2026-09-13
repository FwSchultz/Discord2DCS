#!/usr/bin/env python3
"""Discord2DCS v0.10.0-beta - Windows PC client.

Local side:
    DCS GameGUI overlay (TCP server on 127.0.0.1:8765)
        <-> this client
        <-> outbound WebSocket/WSS
        <-> Discord2DCS service on the VPS

No incoming port is required on the gaming PC.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import ssl
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed

APP = "Discord2DCS-Client"
VERSION = "0.10.0-beta"
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
LOG_PATH = BASE_DIR / "Discord2DCS-Client.log"
PID_PATH = BASE_DIR / "client.pid"
_SINGLE_INSTANCE_HANDLE = None


def acquire_single_instance() -> None:
    """Prevent duplicate background/desktop client instances on Windows."""
    global _SINGLE_INSTANCE_HANDLE
    if os.name != "nt":
        return
    import ctypes

    ERROR_ALREADY_EXISTS = 183
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, "Local\\Discord2DCS-PC-Client")
    if not handle:
        raise RuntimeError("Discord2DCS single-instance lock failed")
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        raise RuntimeError("Discord2DCS is already running / läuft bereits")
    _SINGLE_INSTANCE_HANDLE = handle


def write_pid_file() -> None:
    try:
        PID_PATH.write_text(str(os.getpid()), encoding="ascii")
    except Exception:
        pass


def remove_pid_file() -> None:
    try:
        PID_PATH.unlink(missing_ok=True)
    except Exception:
        pass


def clean_field(value: Any, limit: int = 1800) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = " ".join(text.split())
    return text[:limit]


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise RuntimeError(
            f"{CONFIG_PATH.name} missing / fehlt. Run INSTALL.bat / INSTALL.bat ausführen."
        )
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    defaults = {
        "vps_url": "wss://discord2dcs.example.com/ws",
        "pairing_code": "",
        "access_token": "",
        "bridge_secret": "",
        "client_name": "DCS-PC",
        "dcs_host": "127.0.0.1",
        "dcs_port": 8765,
        "reconnect_seconds": 3.0,
        "tls_ca_file": "",
        "queue_size": 50,
        "log_level": "INFO",
        "language": "de",
    }
    for key, value in defaults.items():
        cfg.setdefault(key, value)

    cfg["vps_url"] = str(cfg["vps_url"]).strip()
    cfg["pairing_code"] = str(cfg.get("pairing_code", "")).strip()
    cfg["access_token"] = str(cfg.get("access_token", "")).strip()
    cfg["bridge_secret"] = str(cfg.get("bridge_secret", "")).strip()
    cfg["client_name"] = clean_field(cfg["client_name"], 80) or "DCS-PC"
    cfg["dcs_host"] = str(cfg["dcs_host"]).strip() or "127.0.0.1"
    cfg["dcs_port"] = int(cfg["dcs_port"])
    cfg["reconnect_seconds"] = max(0.5, float(cfg["reconnect_seconds"]))
    cfg["queue_size"] = max(1, min(500, int(cfg["queue_size"])))
    cfg["language"] = str(cfg.get("language", "de")).strip().lower()
    if cfg["language"] not in {"de", "en"}:
        cfg["language"] = "en"

    if not cfg["vps_url"].startswith(("ws://", "wss://")):
        raise RuntimeError("vps_url must start / muss beginnen mit ws:// oder wss://")
    if not (cfg["access_token"] or cfg["pairing_code"] or cfg["bridge_secret"]):
        raise RuntimeError("No access_token/pairing_code configured / nicht konfiguriert")
    return cfg


def save_credentials(access_token: str, display_name: str = "", expires_at: Any = None) -> None:
    """Persist the long-lived token received after one-time pairing."""
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        raw["access_token"] = str(access_token or "").strip()
        raw["pairing_code"] = ""
        if display_name:
            raw["paired_display_name"] = clean_field(display_name, 80)
        raw["access_expires_at"] = expires_at
        tmp = CONFIG_PATH.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(raw, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        tmp.replace(CONFIG_PATH)
        CFG["access_token"] = raw["access_token"]
        CFG["pairing_code"] = ""
        LOG.info(tr("pair_saved"))
    except Exception:
        LOG.exception(tr("pair_save_failed"))


CFG = load_config()


def load_locale(language: str) -> dict[str, str]:
    path = BASE_DIR / "locales" / f"{language}.json"
    fallback = BASE_DIR / "locales" / "en.json"
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        try:
            with fallback.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}


LOCALE = load_locale(CFG.get("language", "en"))

def tr(key: str, **values: Any) -> str:
    template = str(LOCALE.get(key, key))
    try:
        return template.format(**values)
    except Exception:
        return template


logging.basicConfig(
    level=getattr(logging, str(CFG["log_level"]).upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
LOG = logging.getLogger(APP)


def build_ssl_context() -> ssl.SSLContext | None:
    if not CFG["vps_url"].startswith("wss://"):
        return None

    ca_file = str(CFG.get("tls_ca_file", "")).strip()
    if ca_file:
        path = Path(ca_file)
        if not path.is_absolute():
            path = BASE_DIR / path
        if not path.exists():
            raise RuntimeError(tr("tls_cert_missing", path=path))
        return ssl.create_default_context(cafile=str(path))

    return ssl.create_default_context()


SSL_CONTEXT = build_ssl_context()


@dataclass
class State:
    dcs_writer: asyncio.StreamWriter | None = None
    dcs_send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    ws: Any | None = None
    ws_send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    vps_connected: bool = False
    discord_ready: bool = False
    discord_user: str = ""
    auth_problem: str = ""
    dcs_module_enabled: bool | None = None
    pending_to_dcs: deque[tuple[str, ...]] = field(
        default_factory=lambda: deque(maxlen=CFG["queue_size"])
    )
    pending_to_vps: deque[dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=CFG["queue_size"])
    )

    @property
    def dcs_connected(self) -> bool:
        return self.dcs_writer is not None and not self.dcs_writer.is_closing()


state = State()


async def send_dcs(*fields: str, queue_if_offline: bool = True) -> bool:
    clean = tuple(clean_field(field) for field in fields)
    line = "\t".join(clean) + "\n"

    async with state.dcs_send_lock:
        if not state.dcs_connected:
            if queue_if_offline:
                state.pending_to_dcs.append(clean)
            return False

        assert state.dcs_writer is not None
        try:
            state.dcs_writer.write(line.encode("utf-8", errors="replace"))
            await state.dcs_writer.drain()
            return True
        except (ConnectionError, OSError, RuntimeError):
            if queue_if_offline:
                state.pending_to_dcs.append(clean)
            return False


async def flush_dcs_queue() -> None:
    while state.pending_to_dcs and state.dcs_connected:
        fields = state.pending_to_dcs[0]
        if not await send_dcs(*fields, queue_if_offline=False):
            return
        state.pending_to_dcs.popleft()


async def notify_dcs_status() -> None:
    if state.auth_problem:
        await send_dcs("OFFLINE", state.auth_problem, queue_if_offline=True)
    elif state.vps_connected and state.discord_ready:
        suffix = tr("suffix_as", user=state.discord_user) if state.discord_user else ""
        await send_dcs("STATUS", tr("dcs_status_connected", suffix=suffix), queue_if_offline=True)
    elif state.vps_connected:
        await send_dcs("OFFLINE", tr("dcs_status_waiting"), queue_if_offline=True)
    else:
        await send_dcs("OFFLINE", tr("dcs_status_offline"), queue_if_offline=True)


async def send_vps(payload: dict[str, Any], queue_if_offline: bool = True) -> bool:
    async with state.ws_send_lock:
        if state.ws is None or not state.vps_connected:
            if queue_if_offline:
                state.pending_to_vps.append(payload)
            return False
        try:
            await state.ws.send(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
            return True
        except (ConnectionClosed, ConnectionError, OSError, RuntimeError):
            if queue_if_offline:
                state.pending_to_vps.append(payload)
            return False


async def flush_vps_queue() -> None:
    while state.pending_to_vps and state.vps_connected:
        payload = state.pending_to_vps[0]
        if not await send_vps(payload, queue_if_offline=False):
            return
        state.pending_to_vps.popleft()


async def handle_dcs_line(line: str) -> None:
    if not line:
        return
    parts = line.split("\t", 1)
    command = parts[0]
    payload = parts[1] if len(parts) > 1 else ""

    if command == "HELLO":
        LOG.info(tr("dcs_hello", payload=payload))
        await notify_dcs_status()
    elif command == "DCSSTATE":
        mode = clean_field(payload, 40).upper()
        if mode == "DISABLED":
            state.dcs_module_enabled = False
            state.pending_to_dcs.clear()
            LOG.info(tr("dcs_module_disabled"))
        elif mode == "ENABLED":
            state.dcs_module_enabled = True
            LOG.info(tr("dcs_module_enabled"))
        else:
            LOG.warning(tr("dcs_unknown_state", state=mode or "?"))
    elif command == "SEND":
        content = clean_field(payload, 1700)
        if not content:
            return
        sent = await send_vps({"type": "send_discord", "content": content}, queue_if_offline=True)
        if sent:
            LOG.info("DCS -> VPS | %s", content)
        else:
            LOG.warning("DCS -> VPS vorgemerkt | VPS offline | %s", content)
    else:
        LOG.warning(tr("dcs_unknown", command=command))


async def dcs_loop() -> None:
    host = CFG["dcs_host"]
    port = CFG["dcs_port"]
    delay = CFG["reconnect_seconds"]
    waiting_announced = False

    while True:
        writer: asyncio.StreamWriter | None = None
        connected_this_attempt = False
        try:
            reader, writer = await asyncio.open_connection(host, port)
            connected_this_attempt = True
            waiting_announced = False
            state.dcs_module_enabled = None
            state.dcs_writer = writer
            LOG.info(tr("dcs_connected"))

            await send_dcs("HELLO", "PC_CLIENT", VERSION, queue_if_offline=False)
            await notify_dcs_status()
            await flush_dcs_queue()

            while True:
                raw = await reader.readline()
                if not raw:
                    raise ConnectionError(tr("dcs_closed"))
                if len(raw) > 8192:
                    LOG.warning(tr("dcs_line_long"))
                    continue
                await handle_dcs_line(raw.decode("utf-8", errors="replace").rstrip("\r\n"))

        except asyncio.CancelledError:
            raise
        except ConnectionRefusedError:
            # This is the normal idle state when DCS is not running yet.
            # Tell the user once, then keep retrying quietly in the background.
            if not waiting_announced:
                LOG.info(tr("dcs_waiting"))
                waiting_announced = True
        except (ConnectionError, OSError) as exc:
            if connected_this_attempt:
                LOG.info(tr("dcs_disconnected_waiting"))
                waiting_announced = True
            else:
                LOG.warning(tr("dcs_connect_error", error=exc))
        except Exception:
            LOG.exception(tr("dcs_unexpected"))
        finally:
            if state.dcs_writer is writer:
                state.dcs_writer = None
                state.dcs_module_enabled = None
            if writer is not None:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
        await asyncio.sleep(delay)


async def handle_vps_message(raw: str) -> None:
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        LOG.warning(tr("invalid_json"))
        return

    kind = msg.get("type")
    if kind in {"auth_ok", "pair_ok"}:
        state.discord_ready = bool(msg.get("discord_ready"))
        state.discord_user = clean_field(msg.get("discord_user", ""), 80)
        LOG.info(tr("auth_ok", ready=state.discord_ready))
        await notify_dcs_status()
    elif kind == "status":
        state.discord_ready = bool(msg.get("discord_ready"))
        state.discord_user = clean_field(msg.get("discord_user", ""), 80)
        LOG.info("VPS STATUS | Discord ready=%s | %s", state.discord_ready, state.discord_user)
        await notify_dcs_status()
    elif kind == "discord_message":
        author = clean_field(msg.get("author", "Discord"), 80) or "Discord"
        content = clean_field(msg.get("content", ""), 1400)
        if content:
            if state.dcs_module_enabled is False:
                LOG.debug(tr("discord_drop_disabled", author=author))
                return
            await send_dcs("MSG", author, content, queue_if_offline=True)
            LOG.info("Discord -> DCS | %s: %s", author, content)
    elif kind == "ack":
        content = clean_field(msg.get("content", ""), 200)
        await send_dcs("ACK", content or tr("discord_sent"), queue_if_offline=False)
    elif kind == "error":
        message = clean_field(msg.get("message", tr("vps_unknown_error")), 500)
        await send_dcs("ERR", message, queue_if_offline=True)
        LOG.error(tr("vps_error", message=message))
    else:
        LOG.warning(tr("vps_unknown_type", kind=kind))


async def vps_loop() -> None:
    delay = CFG["reconnect_seconds"]
    url = CFG["vps_url"]

    while True:
        ws = None
        try:
            LOG.info(tr("vps_connecting", url=url))
            async with websockets.connect(
                url,
                ssl=SSL_CONTEXT,
                ping_interval=20,
                ping_timeout=20,
                open_timeout=10,
                close_timeout=5,
                max_size=64 * 1024,
            ) as ws:
                state.ws = ws

                if CFG["access_token"]:
                    hello = {
                        "type": "auth",
                        "token": CFG["access_token"],
                        "client_name": CFG["client_name"],
                        "version": VERSION,
                        "language": CFG["language"],
                    }
                elif CFG["pairing_code"]:
                    hello = {
                        "type": "pair",
                        "code": CFG["pairing_code"],
                        "client_name": CFG["client_name"],
                        "version": VERSION,
                        "language": CFG["language"],
                    }
                    LOG.info(tr("pairing_start"))
                else:
                    # Legacy compatibility for v0.3.x server installations.
                    hello = {
                        "type": "auth",
                        "secret": CFG["bridge_secret"],
                        "client_name": CFG["client_name"],
                        "version": VERSION,
                        "language": CFG["language"],
                    }

                await ws.send(json.dumps(hello, ensure_ascii=False, separators=(",", ":")))

                # First reply must authenticate or complete pairing.
                first_raw = await asyncio.wait_for(ws.recv(), timeout=10)
                first = json.loads(first_raw)
                if first.get("type") not in {"auth_ok", "pair_ok"}:
                    raise ConnectionError(tr("auth_failed", reply=first))

                if first.get("type") == "pair_ok":
                    token = str(first.get("access_token", "")).strip()
                    if not token:
                        raise ConnectionError(tr("pair_no_token"))
                    save_credentials(
                        token,
                        str(first.get("display_name", "")),
                        first.get("access_expires_at"),
                    )

                state.auth_problem = ""
                state.vps_connected = True
                state.discord_ready = bool(first.get("discord_ready"))
                state.discord_user = clean_field(first.get("discord_user", ""), 80)
                expiry = first.get("access_expires_at")
                expiry_text = "LIFETIME" if expiry in (None, "") else str(expiry)
                LOG.info(tr("vps_connected", expiry=expiry_text))
                await notify_dcs_status()
                await flush_vps_queue()

                # Handle the already consumed auth reply exactly once for logging/status.
                await handle_vps_message(json.dumps(first, ensure_ascii=False))

                async for raw in ws:
                    await handle_vps_message(raw)

        except asyncio.CancelledError:
            raise
        except ConnectionClosed as exc:
            reason = clean_field(getattr(exc, "reason", ""), 160).lower()
            if reason == "token_expired" or "token expired" in reason:
                state.auth_problem = tr("token_expired")
            elif reason == "client_disabled" or "client disabled" in reason:
                state.auth_problem = tr("client_disabled")
            elif reason in {"pair_invalid", "pair_required"} or "invalid pairing code" in reason or "pairing-code ungueltig" in reason:
                state.auth_problem = tr("pair_invalid")
            elif reason == "token_invalid" or "forbidden" in reason:
                state.auth_problem = tr("token_invalid")
            else:
                state.auth_problem = ""
            LOG.warning(tr("vps_closed", code=getattr(exc, "code", "?"), reason=getattr(exc, "reason", "")))
            if state.auth_problem:
                await notify_dcs_status()
        except (ConnectionError, OSError, asyncio.TimeoutError, json.JSONDecodeError) as exc:
            LOG.warning(tr("vps_not_connected", error=exc))
        except ssl.SSLError as exc:
            LOG.error(tr("tls_error", error=exc))
        except Exception:
            LOG.exception(tr("vps_unexpected"))
        finally:
            if state.ws is ws:
                state.ws = None
            was_connected = state.vps_connected
            state.vps_connected = False
            state.discord_ready = False
            state.discord_user = ""
            if was_connected:
                await notify_dcs_status()

        await asyncio.sleep(delay)


async def main() -> None:
    LOG.info(tr("client_start", app=APP, version=VERSION))
    LOG.info(tr("local_endpoint", host=CFG["dcs_host"], port=CFG["dcs_port"]))
    LOG.info(tr("vps_endpoint", url=CFG["vps_url"]))
    if CFG["vps_url"].startswith("wss://"):
        LOG.info(tr("transport_tls"))
    else:
        LOG.warning(tr("transport_plain"))
    await asyncio.gather(dcs_loop(), vps_loop())


if __name__ == "__main__":
    try:
        acquire_single_instance()
        write_pid_file()
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except RuntimeError as exc:
        print(f"Discord2DCS: {exc}")
    finally:
        remove_pid_file()
