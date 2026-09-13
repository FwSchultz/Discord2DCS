#!/usr/bin/env python3
"""Emergency CLI administration for Discord2DCS v0.10.0-beta-rc2.

Normal community administration should happen through Discord slash commands.
This CLI remains available if Discord administration is unavailable.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from database import Database, client_status, display_expiry

DATA_DIR = Path(os.getenv("DATA_DIR", "/data").strip() or "/data")
DB_FILE = Path(os.getenv("DB_FILE", str(DATA_DIR / "discord2dcs.db")).strip() or str(DATA_DIR / "discord2dcs.db"))
db = Database(DB_FILE, legacy_data_dir=DATA_DIR)


def find_client(client_id: str):
    exact = db.get_client_by_id(client_id)
    if exact:
        return exact
    matches = [c for c in db.list_clients() if str(c.get("id", "")).startswith(client_id)]
    return matches[0] if len(matches) == 1 else None


def cmd_create(args):
    try:
        pairing = db.create_pairing(
            display_name=args.display_name,
            token_validity=args.token_validity,
            pair_hours=args.pair_hours,
        )
    except ValueError as exc:
        print(f"Fehler: {exc}")
        return 2
    print("Pairing-Code erstellt")
    print(f"Pairing-ID:        {pairing['id']}")
    print(f"Name:              {pairing['display_name']}")
    print(f"Pairing-Ablauf:    {pairing['expires_at']}")
    print(f"Client-Token:      {pairing['token_validity']}")
    print(f"Code:              {pairing['code']}")
    return 0


def cmd_pairings(_):
    items = db.list_open_pairings()
    if not items:
        print("Keine offenen Pairing-Codes.")
        return 0
    print(f"{'ID':12}  {'Name':22}  {'Token':12}  Pairing-Ablauf")
    print("-" * 90)
    for e in items:
        mode = "replace" if e.get("replacement_client_id") else str(e.get("token_validity", ""))
        print(f"{e.get('id',''):12}  {str(e.get('display_name',''))[:22]:22}  {mode[:12]:12}  {e.get('expires_at','')}")
    return 0


def cmd_clients(_):
    clients = db.list_clients()
    if not clients:
        print("Keine Clients.")
        return 0
    print(f"{'ID':16}  {'Status':8}  {'Name':22}  {'Discord-ID':20}  {'Token-Ablauf':27}")
    print("-" * 110)
    for e in clients:
        print(
            f"{e.get('id',''):16}  {client_status(e):8}  {str(e.get('display_name',''))[:22]:22}  "
            f"{str(e.get('discord_user_id') or '-')[:20]:20}  {display_expiry(e.get('expires_at'))[:27]:27}"
        )
    return 0


def cmd_info(args):
    e = find_client(args.client_id)
    if not e:
        print("Client nicht eindeutig gefunden.")
        return 1
    print(f"Client-ID:       {e.get('id','')}")
    print(f"Name:            {e.get('display_name','')}")
    print(f"Discord-ID:      {e.get('discord_user_id') or '-'}")
    print(f"Status:          {client_status(e)}")
    print(f"Erstellt:        {e.get('created_at','')}")
    print(f"Zuletzt gesehen: {e.get('last_seen_at','') or '-'}")
    print(f"Token-Ablauf:    {display_expiry(e.get('expires_at'))}")
    return 0


def cmd_revoke(args):
    e = find_client(args.client_id)
    if not e:
        print("Client nicht eindeutig gefunden.")
        return 1
    db.set_client_enabled(e["id"], False)
    print(f"Client gesperrt: {e['id']} ({e['display_name']})")
    return 0


def cmd_enable(args):
    e = find_client(args.client_id)
    if not e:
        print("Client nicht eindeutig gefunden.")
        return 1
    updated = db.set_client_enabled(e["id"], True)
    print(f"Client aktiviert: {updated['id']} ({updated['display_name']})")
    if client_status(updated) == "EXPIRED":
        print("Hinweis: Token ist weiterhin abgelaufen.")
    return 0


def cmd_extend(args):
    e = find_client(args.client_id)
    if not e:
        print("Client nicht eindeutig gefunden.")
        return 1
    try:
        updated = db.extend_client_expiry(e["id"], args.validity)
    except ValueError as exc:
        print(f"Fehler: {exc}")
        return 2
    print(f"Token-Ablauf: {display_expiry(updated.get('expires_at'))}")
    return 0


def cmd_set_expiry(args):
    e = find_client(args.client_id)
    if not e:
        print("Client nicht eindeutig gefunden.")
        return 1
    try:
        updated = db.set_client_expiry(e["id"], args.validity)
    except ValueError as exc:
        print(f"Fehler: {exc}")
        return 2
    print(f"Token-Ablauf: {display_expiry(updated.get('expires_at'))}")
    return 0


def cmd_cancel_pairing(args):
    e = db.cancel_pairing(args.pairing_id)
    if not e:
        print("Pairing nicht gefunden oder bereits beendet.")
        return 1
    print(f"Pairing storniert: {e['id']}")
    return 0


def cmd_adopt(args):
    e = find_client(args.client_id)
    if not e:
        print("Client nicht eindeutig gefunden.")
        return 1
    try:
        updated = db.adopt_client(e["id"], args.discord_user_id, args.display_name)
    except ValueError as exc:
        print(f"Fehler: {exc}")
        return 2
    print(f"Client {updated['id']} -> Discord-ID {updated['discord_user_id']}")
    return 0


def cmd_delete(args):
    e = find_client(args.client_id)
    if not e:
        print("Client nicht eindeutig gefunden.")
        return 1
    if args.yes != "JA_LOESCHEN":
        print("Abgebrochen. Fuer CLI-Loeschung --yes JA_LOESCHEN angeben.")
        return 2
    db.delete_client(e["id"])
    print(f"Client geloescht: {e['id']} ({e['display_name']})")
    return 0


def cmd_audit(args):
    for row in db.recent_audit(args.limit):
        print(f"{row['created_at']} | {row.get('admin_name') or row.get('admin_user_id') or 'system'} | {row['action']} | {row.get('target_client_id') or '-'} | {row.get('details') or {}}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Discord2DCS Notfall-CLI (Adminverwaltung normalerweise ueber Discord)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("create")
    p.add_argument("display_name")
    p.add_argument("token_validity")
    p.add_argument("--pair-hours", type=int, default=24)
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("pairings")
    p.set_defaults(func=cmd_pairings)
    p = sub.add_parser("codes")
    p.set_defaults(func=cmd_pairings)

    p = sub.add_parser("clients")
    p.set_defaults(func=cmd_clients)

    p = sub.add_parser("info")
    p.add_argument("client_id")
    p.set_defaults(func=cmd_info)

    for name, func in (("revoke", cmd_revoke), ("enable", cmd_enable)):
        p = sub.add_parser(name)
        p.add_argument("client_id")
        p.set_defaults(func=func)

    p = sub.add_parser("extend")
    p.add_argument("client_id")
    p.add_argument("validity")
    p.set_defaults(func=cmd_extend)

    p = sub.add_parser("set-expiry")
    p.add_argument("client_id")
    p.add_argument("validity")
    p.set_defaults(func=cmd_set_expiry)

    p = sub.add_parser("cancel-pairing")
    p.add_argument("pairing_id")
    p.set_defaults(func=cmd_cancel_pairing)

    p = sub.add_parser("adopt")
    p.add_argument("client_id")
    p.add_argument("discord_user_id")
    p.add_argument("--display-name", default=None)
    p.set_defaults(func=cmd_adopt)

    p = sub.add_parser("delete")
    p.add_argument("client_id")
    p.add_argument("--yes", default="")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("audit")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_audit)
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))
