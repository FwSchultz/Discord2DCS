#!/usr/bin/env python3
"""SQLite storage for Discord2DCS v0.10.0-beta-rc2.

The DB stores only hashes of pairing codes and access tokens. Existing v0.4.x
JSON files are imported once on first start for backwards compatibility.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

DURATION_RE = re.compile(r"^(\d+)([hdw])$", re.IGNORECASE)
PAIR_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().replace(microsecond=0).isoformat()


def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def parse_iso(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        dt = datetime.fromisoformat(str(value))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_pairing_code() -> str:
    groups = []
    for _ in range(4):
        groups.append("".join(secrets.choice(PAIR_ALPHABET) for _ in range(4)))
    return "D2DCS-" + "-".join(groups)


def parse_validity(raw: str) -> dict[str, Any]:
    value = str(raw or "").strip()
    lower = value.lower()
    if lower in {"lifetime", "life", "unlimited"}:
        return {"kind": "lifetime", "label": "lifetime"}

    match = DURATION_RE.fullmatch(lower)
    if match:
        amount = int(match.group(1))
        if amount < 1:
            raise ValueError("Dauer muss groesser als 0 sein")
        unit = match.group(2).lower()
        seconds_per_unit = {"h": 3600, "d": 86400, "w": 7 * 86400}[unit]
        return {
            "kind": "relative",
            "seconds": amount * seconds_per_unit,
            "label": f"{amount}{unit}",
        }

    if lower.startswith("until:"):
        raw_date = value.split(":", 1)[1].strip()
        if not raw_date:
            raise ValueError("Bei until: fehlt das Datum")
        try:
            if len(raw_date) == 10:
                dt = datetime.fromisoformat(raw_date + "T23:59:59+00:00")
            else:
                dt = datetime.fromisoformat(raw_date)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt = dt.astimezone(timezone.utc)
        except ValueError as exc:
            raise ValueError("Ungueltiges until-Datum; z.B. until:2027-12-31") from exc
        if dt <= utc_now():
            raise ValueError("Ablaufdatum liegt nicht in der Zukunft")
        return {"kind": "absolute", "expires_at": iso(dt), "label": f"until:{raw_date}"}

    raise ValueError("Ungueltige Dauer. Erlaubt: lifetime, 12h, 30d, 4w oder until:YYYY-MM-DD")


def expiry_from_policy(policy: dict[str, Any], *, base: datetime | None = None) -> str | None:
    base = base or utc_now()
    kind = policy["kind"]
    if kind == "lifetime":
        return None
    if kind == "relative":
        return iso(base + timedelta(seconds=int(policy["seconds"])))
    if kind == "absolute":
        return str(policy["expires_at"])
    raise ValueError(f"Unbekannte Policy: {kind}")


def display_expiry(value: Any) -> str:
    if value in (None, ""):
        return "LIFETIME"
    dt = parse_iso(value)
    return iso(dt) if dt else str(value)


def client_status(entry: dict[str, Any]) -> str:
    if not bool(entry.get("enabled", True)):
        return "DISABLED"
    expires = parse_iso(entry.get("expires_at"))
    if expires is not None and expires <= utc_now():
        return "EXPIRED"
    return "ACTIVE"


@dataclass(frozen=True)
class PairingResult:
    client_id: str
    display_name: str
    access_token: str
    expires_at: str | None
    discord_user_id: str | None
    replaced_existing: bool


class Database:
    def __init__(self, db_path: Path, *, legacy_data_dir: Path | None = None) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.legacy_data_dir = Path(legacy_data_dir) if legacy_data_dir else self.db_path.parent
        self._init_schema()
        self._migrate_legacy_json_once()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS clients (
                    id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    discord_user_id TEXT,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    expires_at TEXT,
                    updated_at TEXT,
                    disabled_at TEXT
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_discord_user
                ON clients(discord_user_id)
                WHERE discord_user_id IS NOT NULL AND discord_user_id <> '';

                CREATE TABLE IF NOT EXISTS pairing_codes (
                    id TEXT PRIMARY KEY,
                    code_hash TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    discord_user_id TEXT,
                    created_by_user_id TEXT,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    token_lifetime INTEGER NOT NULL DEFAULT 0,
                    token_duration_seconds INTEGER,
                    token_expires_at TEXT,
                    token_validity TEXT NOT NULL,
                    replacement_client_id TEXT,
                    used_at TEXT,
                    used_client_id TEXT,
                    cancelled_at TEXT,
                    FOREIGN KEY(replacement_client_id) REFERENCES clients(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_pairing_active
                ON pairing_codes(code_hash, used_at, cancelled_at, expires_at);

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    admin_user_id TEXT,
                    admin_name TEXT,
                    action TEXT NOT NULL,
                    target_client_id TEXT,
                    target_discord_user_id TEXT,
                    details_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log(created_at DESC);
                """
            )

    def _meta_get(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
            return str(row["value"]) if row else None

    def _meta_set(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def _migrate_legacy_json_once(self) -> None:
        if self._meta_get("legacy_json_migrated") == "1":
            return

        clients_path = self.legacy_data_dir / "clients.json"
        pairings_path = self.legacy_data_dir / "pairing_codes.json"
        imported_clients = 0
        imported_pairings = 0

        try:
            clients_data: dict[str, Any] = {"clients": []}
            pairings_data: dict[str, Any] = {"codes": []}
            if clients_path.exists():
                loaded = json.loads(clients_path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError("clients.json enthaelt kein JSON-Objekt")
                clients_data = loaded
            if pairings_path.exists():
                loaded = json.loads(pairings_path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError("pairing_codes.json enthaelt kein JSON-Objekt")
                pairings_data = loaded

            with self._connect() as conn:
                for entry in clients_data.get("clients", []):
                    if not isinstance(entry, dict):
                        continue
                    cid = str(entry.get("id", "")).strip()
                    token_hash = str(entry.get("token_hash", "")).strip()
                    if not cid or not token_hash:
                        continue
                    try:
                        cur = conn.execute(
                            """
                            INSERT OR IGNORE INTO clients
                            (id, token_hash, display_name, discord_user_id, created_at, last_seen_at,
                             enabled, expires_at, updated_at, disabled_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                cid,
                                token_hash,
                                str(entry.get("display_name", "DCS-Pilot"))[:80],
                                str(entry.get("discord_user_id")) if entry.get("discord_user_id") else None,
                                str(entry.get("created_at") or utc_now_iso()),
                                str(entry.get("last_seen_at") or "") or None,
                                1 if entry.get("enabled", True) else 0,
                                entry.get("expires_at"),  # missing/None intentionally means LIFETIME
                                entry.get("updated_at"),
                                entry.get("disabled_at"),
                            ),
                        )
                        imported_clients += max(0, int(cur.rowcount))
                    except sqlite3.IntegrityError:
                        # Keep the already-present DB record if unique ownership conflicts.
                        pass

                for entry in pairings_data.get("codes", []):
                    if not isinstance(entry, dict):
                        continue
                    pid = str(entry.get("id", "")).strip() or secrets.token_hex(6)
                    code_hash = str(entry.get("hash", "")).strip()
                    if not code_hash:
                        continue
                    token_lifetime = bool(entry.get("token_lifetime", False))
                    token_duration = entry.get("token_duration_seconds")
                    token_exp = entry.get("token_expires_at")
                    token_validity = str(entry.get("token_validity") or "lifetime")
                    if "token_lifetime" not in entry and "token_duration_seconds" not in entry and "token_expires_at" not in entry:
                        token_lifetime = True
                        token_validity = "lifetime"
                    try:
                        cur = conn.execute(
                            """
                            INSERT OR IGNORE INTO pairing_codes
                            (id, code_hash, display_name, discord_user_id, created_by_user_id,
                             created_at, expires_at, token_lifetime, token_duration_seconds,
                             token_expires_at, token_validity, replacement_client_id,
                             used_at, used_client_id, cancelled_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)
                            """,
                            (
                                pid,
                                code_hash,
                                str(entry.get("display_name", "DCS-Pilot"))[:80],
                                str(entry.get("discord_user_id")) if entry.get("discord_user_id") else None,
                                str(entry.get("created_by_user_id")) if entry.get("created_by_user_id") else None,
                                str(entry.get("created_at") or utc_now_iso()),
                                str(entry.get("expires_at") or iso(utc_now() + timedelta(hours=24))),
                                1 if token_lifetime else 0,
                                int(token_duration) if token_duration not in (None, "") else None,
                                token_exp,
                                token_validity,
                                entry.get("replacement_client_id"),
                            ),
                        )
                        imported_pairings += max(0, int(cur.rowcount))
                    except sqlite3.IntegrityError:
                        pass
        except Exception as exc:
            raise RuntimeError(f"Migration der v0.4.x-JSON-Daten fehlgeschlagen: {exc}") from exc

        self._meta_set("legacy_json_migrated", "1")
        self.audit(
            admin_user_id=None,
            admin_name="system",
            action="legacy_json_migration",
            details={"clients": imported_clients, "pairings": imported_pairings},
        )

    @staticmethod
    def _row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def audit(
        self,
        *,
        admin_user_id: str | None,
        admin_name: str | None,
        action: str,
        target_client_id: str | None = None,
        target_discord_user_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_log
                (created_at, admin_user_id, admin_name, action, target_client_id,
                 target_discord_user_id, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    utc_now_iso(),
                    admin_user_id,
                    admin_name,
                    action,
                    target_client_id,
                    target_discord_user_id,
                    json.dumps(details or {}, ensure_ascii=False, separators=(",", ":")),
                ),
            )

    def recent_audit(self, limit: int = 20) -> list[dict[str, Any]]:
        limit = max(1, min(100, int(limit)))
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            try:
                item["details"] = json.loads(item.pop("details_json") or "{}")
            except Exception:
                item["details"] = {}
            result.append(item)
        return result

    def get_client_by_id(self, client_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (str(client_id),)).fetchone()
        return self._row_dict(row)

    def get_client_by_discord_user(self, discord_user_id: str | int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM clients WHERE discord_user_id = ?",
                (str(discord_user_id),),
            ).fetchone()
        return self._row_dict(row)

    def list_clients(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM clients
                ORDER BY CASE WHEN discord_user_id IS NULL THEN 1 ELSE 0 END,
                         lower(display_name), created_at
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def client_access_state(self, entry: dict[str, Any]) -> tuple[bool, str]:
        if not bool(entry.get("enabled", True)):
            return False, "client disabled"
        expires = parse_iso(entry.get("expires_at"))
        if expires is not None and expires <= utc_now():
            return False, "token expired"
        return True, ""

    def authenticate_access_token(self, token: str) -> tuple[dict[str, Any] | None, str]:
        supplied_hash = hash_secret(str(token).strip())
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM clients").fetchall()
            for row in rows:
                entry = dict(row)
                if hmac.compare_digest(str(entry.get("token_hash", "")), supplied_hash):
                    allowed, reason = self.client_access_state(entry)
                    if not allowed:
                        return None, reason
                    now_iso = utc_now_iso()
                    conn.execute("UPDATE clients SET last_seen_at = ? WHERE id = ?", (now_iso, entry["id"]))
                    entry["last_seen_at"] = now_iso
                    return {
                        "client_id": entry["id"],
                        "display_name": entry["display_name"],
                        "discord_user_id": entry.get("discord_user_id"),
                        "legacy": False,
                        "expires_at": entry.get("expires_at"),
                    }, ""
        return None, "forbidden"

    def _pairing_token_expiry(self, entry: dict[str, Any], created_at: datetime) -> str | None:
        if bool(entry.get("token_lifetime")):
            return None
        duration = entry.get("token_duration_seconds")
        if duration not in (None, ""):
            seconds = int(duration)
            if seconds > 0:
                return iso(created_at + timedelta(seconds=seconds))
        fixed = parse_iso(entry.get("token_expires_at"))
        return iso(fixed) if fixed else None

    def create_pairing(
        self,
        *,
        display_name: str,
        token_validity: str,
        pair_hours: int = 24,
        discord_user_id: str | int | None = None,
        created_by_user_id: str | int | None = None,
        replacement_client_id: str | None = None,
    ) -> dict[str, Any]:
        pair_hours = max(1, min(168, int(pair_hours)))
        if replacement_client_id:
            policy = {"kind": "preserve", "label": "preserve"}
            client = self.get_client_by_id(replacement_client_id)
            if client is None:
                raise ValueError("Client fuer Ersatz-Pairing nicht gefunden")
            display_name = client["display_name"]
            if discord_user_id is None:
                discord_user_id = client.get("discord_user_id")
        else:
            policy = parse_validity(token_validity)

        code = make_pairing_code()
        created = utc_now()
        pair_expires = created + timedelta(hours=pair_hours)
        pid = secrets.token_hex(6)

        token_lifetime = 0
        token_duration_seconds = None
        token_expires_at = None
        if policy["kind"] == "lifetime":
            token_lifetime = 1
        elif policy["kind"] == "relative":
            token_duration_seconds = int(policy["seconds"])
        elif policy["kind"] == "absolute":
            token_expires_at = str(policy["expires_at"])

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pairing_codes
                (id, code_hash, display_name, discord_user_id, created_by_user_id,
                 created_at, expires_at, token_lifetime, token_duration_seconds,
                 token_expires_at, token_validity, replacement_client_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid,
                    hash_secret(code),
                    str(display_name)[:80] or "DCS-Pilot",
                    str(discord_user_id) if discord_user_id is not None else None,
                    str(created_by_user_id) if created_by_user_id is not None else None,
                    iso(created),
                    iso(pair_expires),
                    token_lifetime,
                    token_duration_seconds,
                    token_expires_at,
                    policy["label"],
                    replacement_client_id,
                ),
            )

        return {
            "id": pid,
            "code": code,
            "display_name": str(display_name)[:80] or "DCS-Pilot",
            "discord_user_id": str(discord_user_id) if discord_user_id is not None else None,
            "created_at": iso(created),
            "expires_at": iso(pair_expires),
            "token_validity": policy["label"],
            "replacement_client_id": replacement_client_id,
        }

    def consume_pairing_code(self, code: str) -> tuple[PairingResult | None, str]:
        supplied_hash = hash_secret(str(code).strip())
        now = utc_now()
        now_iso = iso(now)

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            rows = conn.execute(
                """
                SELECT * FROM pairing_codes
                WHERE used_at IS NULL AND cancelled_at IS NULL
                """
            ).fetchall()
            matched: dict[str, Any] | None = None
            for row in rows:
                entry = dict(row)
                if not hmac.compare_digest(str(entry.get("code_hash", "")), supplied_hash):
                    continue
                pair_exp = parse_iso(entry.get("expires_at"))
                if pair_exp is not None and pair_exp <= now:
                    return None, "Pairing-Code ungueltig oder abgelaufen"
                matched = entry
                break

            if matched is None:
                return None, "Pairing-Code ungueltig oder abgelaufen"

            replacement_client_id = matched.get("replacement_client_id")
            access_token = secrets.token_urlsafe(32)
            token_hash = hash_secret(access_token)
            replaced = bool(replacement_client_id)

            if replacement_client_id:
                client_row = conn.execute("SELECT * FROM clients WHERE id = ?", (replacement_client_id,)).fetchone()
                if client_row is None:
                    return None, "Ziel-Client fuer Ersatz-Pairing existiert nicht mehr"
                existing = dict(client_row)
                conn.execute(
                    """
                    UPDATE clients
                    SET token_hash = ?, last_seen_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (token_hash, now_iso, now_iso, replacement_client_id),
                )
                client_id = str(replacement_client_id)
                display_name = str(existing["display_name"])
                expires_at = existing.get("expires_at")
                discord_user_id = existing.get("discord_user_id")
            else:
                discord_user_id = matched.get("discord_user_id")
                if discord_user_id:
                    existing_row = conn.execute(
                        "SELECT id FROM clients WHERE discord_user_id = ?",
                        (str(discord_user_id),),
                    ).fetchone()
                    if existing_row is not None:
                        return None, "Fuer diesen Discord-Benutzer existiert bereits ein Client"

                expires_at = self._pairing_token_expiry(matched, now)
                parsed_expiry = parse_iso(expires_at)
                if parsed_expiry is not None and parsed_expiry <= now:
                    return None, "Die festgelegte Token-Laufzeit ist bereits abgelaufen"
                client_id = secrets.token_hex(8)
                display_name = str(matched.get("display_name") or "DCS-Pilot")[:80]
                conn.execute(
                    """
                    INSERT INTO clients
                    (id, token_hash, display_name, discord_user_id, created_at,
                     last_seen_at, enabled, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        client_id,
                        token_hash,
                        display_name,
                        str(discord_user_id) if discord_user_id else None,
                        now_iso,
                        now_iso,
                        expires_at,
                    ),
                )

            conn.execute(
                """
                UPDATE pairing_codes
                SET used_at = ?, used_client_id = ?
                WHERE id = ?
                """,
                (now_iso, client_id, matched["id"]),
            )

        return PairingResult(
            client_id=client_id,
            display_name=display_name,
            access_token=access_token,
            expires_at=expires_at,
            discord_user_id=str(discord_user_id) if discord_user_id else None,
            replaced_existing=replaced,
        ), ""

    def list_open_pairings(self) -> list[dict[str, Any]]:
        current = utc_now()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM pairing_codes
                WHERE used_at IS NULL AND cancelled_at IS NULL
                ORDER BY created_at DESC
                """
            ).fetchall()
        result = []
        for row in rows:
            entry = dict(row)
            exp = parse_iso(entry.get("expires_at"))
            if exp is None or exp > current:
                result.append(entry)
        return result

    def cancel_pairing(self, pairing_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM pairing_codes WHERE id = ? AND used_at IS NULL AND cancelled_at IS NULL",
                (str(pairing_id),),
            ).fetchone()
            if row is None:
                return None
            conn.execute("UPDATE pairing_codes SET cancelled_at = ? WHERE id = ?", (utc_now_iso(), str(pairing_id)))
            return dict(row)

    def set_client_enabled(self, client_id: str, enabled: bool) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (str(client_id),)).fetchone()
            if row is None:
                return None
            now_iso = utc_now_iso()
            conn.execute(
                "UPDATE clients SET enabled = ?, disabled_at = ?, updated_at = ? WHERE id = ?",
                (1 if enabled else 0, None if enabled else now_iso, now_iso, str(client_id)),
            )
        return self.get_client_by_id(client_id)

    def set_client_expiry(self, client_id: str, validity: str) -> dict[str, Any]:
        policy = parse_validity(validity)
        expires_at = expiry_from_policy(policy)
        with self._connect() as conn:
            row = conn.execute("SELECT id FROM clients WHERE id = ?", (str(client_id),)).fetchone()
            if row is None:
                raise KeyError(client_id)
            conn.execute(
                "UPDATE clients SET expires_at = ?, updated_at = ? WHERE id = ?",
                (expires_at, utc_now_iso(), str(client_id)),
            )
        result = self.get_client_by_id(client_id)
        assert result is not None
        return result

    def extend_client_expiry(self, client_id: str, validity: str) -> dict[str, Any]:
        policy = parse_validity(validity)
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (str(client_id),)).fetchone()
            if row is None:
                raise KeyError(client_id)
            entry = dict(row)
            if policy["kind"] == "lifetime":
                expires_at = None
            elif policy["kind"] == "absolute":
                expires_at = str(policy["expires_at"])
            else:
                current_expiry = parse_iso(entry.get("expires_at"))
                if current_expiry is None:
                    raise ValueError("Client ist bereits LIFETIME; fuer endliche Laufzeit 'set-expiry' verwenden")
                base = max(current_expiry, utc_now())
                expires_at = iso(base + timedelta(seconds=int(policy["seconds"])))
            conn.execute(
                "UPDATE clients SET expires_at = ?, updated_at = ? WHERE id = ?",
                (expires_at, utc_now_iso(), str(client_id)),
            )
        result = self.get_client_by_id(client_id)
        assert result is not None
        return result

    def adopt_client(self, client_id: str, discord_user_id: str | int, display_name: str | None = None) -> dict[str, Any]:
        uid = str(discord_user_id)
        with self._connect() as conn:
            target = conn.execute("SELECT * FROM clients WHERE id = ?", (str(client_id),)).fetchone()
            if target is None:
                raise KeyError(client_id)
            other = conn.execute("SELECT id FROM clients WHERE discord_user_id = ?", (uid,)).fetchone()
            if other is not None and str(other["id"]) != str(client_id):
                raise ValueError("Discord-Benutzer ist bereits mit einem anderen Client verknuepft")
            target_dict = dict(target)
            current_uid = target_dict.get("discord_user_id")
            if current_uid and str(current_uid) != uid:
                raise ValueError("Client ist bereits mit einem anderen Discord-Benutzer verknuepft")
            conn.execute(
                "UPDATE clients SET discord_user_id = ?, display_name = ?, updated_at = ? WHERE id = ?",
                (
                    uid,
                    (str(display_name)[:80] if display_name else target_dict["display_name"]),
                    utc_now_iso(),
                    str(client_id),
                ),
            )
        result = self.get_client_by_id(client_id)
        assert result is not None
        return result

    def delete_client(self, client_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (str(client_id),)).fetchone()
            if row is None:
                return None
            entry = dict(row)
            # Audit rows intentionally survive; pending pairings linked to this client are deleted by FK cascade.
            conn.execute("DELETE FROM clients WHERE id = ?", (str(client_id),))
            return entry

    def count_clients(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM clients").fetchone()
        return int(row["n"] if row else 0)
