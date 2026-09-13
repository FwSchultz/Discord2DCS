#!/usr/bin/env python3
"""Discord slash-command administration for Discord2DCS v0.10.0-beta-rc2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable

import discord
from discord import app_commands

from database import Database, client_status, display_expiry, parse_iso

DisconnectCallback = Callable[[str, str], Awaitable[None]]
OnlineCallback = Callable[[str], bool]


def _language_from_locale(value: Any) -> str:
    raw = str(value or "").lower()
    return "de" if raw.startswith("de") else "en"


def _interaction_language(interaction: discord.Interaction) -> str:
    return _language_from_locale(getattr(interaction, "locale", None))


def _text(language: str, de: str, en: str) -> str:
    return de if language == "de" else en


def _tx(interaction: discord.Interaction, de: str, en: str) -> str:
    return _text(_interaction_language(interaction), de, en)

VALIDITY_CHOICES = [
    app_commands.Choice(name="1 Tag / day", value="1d"),
    app_commands.Choice(name="7 Tage / days", value="7d"),
    app_commands.Choice(name="30 Tage / days", value="30d"),
    app_commands.Choice(name="90 Tage / days", value="90d"),
    app_commands.Choice(name="180 Tage / days", value="180d"),
    app_commands.Choice(name="365 Tage / days", value="365d"),
    app_commands.Choice(name="Lifetime", value="lifetime"),
    app_commands.Choice(name="Benutzerdefiniert / custom", value="custom"),
]


def _ids_csv(raw: str) -> set[str]:
    return {part.strip() for part in str(raw or "").replace(";", ",").split(",") if part.strip()}


def _discord_timestamp(value: Any, style: str = "f") -> str:
    dt = parse_iso(value)
    if dt is None:
        return "LIFETIME" if value in (None, "") else str(value)
    return f"<t:{int(dt.timestamp())}:{style}>"


def _status_label(entry: dict[str, Any], online: bool, language: str = "en") -> str:
    access = client_status(entry)
    if access == "DISABLED":
        return _text(language, "⛔ GESPERRT", "⛔ DISABLED")
    if access == "EXPIRED":
        return _text(language, "⌛ ABGELAUFEN", "⌛ EXPIRED")
    return "🟢 ONLINE" if online else "⚪ OFFLINE"


def _validity_from_choice(choice: app_commands.Choice[str], custom: str | None) -> str:
    if choice.value != "custom":
        return choice.value
    value = str(custom or "").strip()
    if not value:
        raise ValueError("Custom / Benutzerdefiniert: use / nutze e.g. `45d`, `8w`, `12h` or / oder `until:2027-12-31`.")
    return value


@dataclass(frozen=True)
class AdminConfig:
    admin_user_ids: set[str]
    admin_role_ids: set[str]
    admin_channel_id: int = 0
    admin_log_channel_id: int = 0
    allow_guild_administrators: bool = False
    public_ws_url: str = ""

    @classmethod
    def from_env(
        cls,
        *,
        admin_user_ids: str = "",
        admin_role_ids: str = "",
        admin_channel_id: int = 0,
        admin_log_channel_id: int = 0,
        allow_guild_administrators: bool = False,
        public_ws_url: str = "",
    ) -> "AdminConfig":
        return cls(
            admin_user_ids=_ids_csv(admin_user_ids),
            admin_role_ids=_ids_csv(admin_role_ids),
            admin_channel_id=int(admin_channel_id or 0),
            admin_log_channel_id=int(admin_log_channel_id or 0),
            allow_guild_administrators=bool(allow_guild_administrators),
            public_ws_url=str(public_ws_url or "").strip(),
        )


class ClientListView(discord.ui.View):
    def __init__(self, owner_id: int, clients: list[dict[str, Any]], online_cb: OnlineCallback, language: str = "en") -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.clients = clients
        self.online_cb = online_cb
        self.language = language
        self.page = 0
        self.per_page = 8
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "d2dcs_clients_prev":
                item.label = _text(self.language, "Zurück", "Previous")
            elif isinstance(item, discord.ui.Button) and item.custom_id == "d2dcs_clients_next":
                item.label = _text(self.language, "Weiter", "Next")
        self._update_buttons()

    @property
    def pages(self) -> int:
        return max(1, (len(self.clients) + self.per_page - 1) // self.per_page)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(_text(self.language, "Diese Ansicht gehört zu einem anderen Admin.", "This view belongs to another admin."), ephemeral=True)
            return False
        return True

    def _update_buttons(self) -> None:
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            if item.custom_id == "d2dcs_clients_prev":
                item.disabled = self.page <= 0
            elif item.custom_id == "d2dcs_clients_next":
                item.disabled = self.page >= self.pages - 1

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Discord2DCS • Clients",
            description=_text(self.language, f"{len(self.clients)} Client(s) • Seite {self.page + 1}/{self.pages}", f"{len(self.clients)} client(s) • Page {self.page + 1}/{self.pages}"),
        )
        start = self.page * self.per_page
        for entry in self.clients[start : start + self.per_page]:
            cid = str(entry.get("id", ""))
            uid = str(entry.get("discord_user_id") or "")
            linked = f"<@{uid}>" if uid else _text(self.language, "nicht mit Discord verknüpft", "not linked to Discord")
            status = _status_label(entry, self.online_cb(cid), self.language)
            expiry = _discord_timestamp(entry.get("expires_at"), "f")
            embed.add_field(
                name=f"{status} • {entry.get('display_name', 'DCS-Pilot')}",
                value=f"{linked}\n`{cid}`\n" + _text(self.language, f"Ablauf: {expiry}", f"Expiry: {expiry}"),
                inline=False,
            )
        return embed

    @discord.ui.button(label="Zurück", style=discord.ButtonStyle.secondary, custom_id="d2dcs_clients_prev")
    async def previous(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.page = max(0, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Weiter", style=discord.ButtonStyle.secondary, custom_id="d2dcs_clients_next")
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.page = min(self.pages - 1, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


class DeleteClientView(discord.ui.View):
    def __init__(
        self,
        *,
        owner_id: int,
        client_entry: dict[str, Any],
        db: Database,
        disconnect_cb: DisconnectCallback,
        audit_cb: Callable[..., Awaitable[None]],
        language: str = "en",
    ) -> None:
        super().__init__(timeout=60)
        self.owner_id = owner_id
        self.entry = client_entry
        self.db = db
        self.disconnect_cb = disconnect_cb
        self.audit_cb = audit_cb
        self.language = language
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.style == discord.ButtonStyle.danger:
                    item.label = _text(language, "Endgültig löschen", "Delete permanently")
                elif item.style == discord.ButtonStyle.secondary:
                    item.label = _text(language, "Abbrechen", "Cancel")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(_text(self.language, "Nur der Admin, der den Löschvorgang gestartet hat, kann ihn bestätigen.", "Only the admin who started the delete operation can confirm it."), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Endgültig löschen", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.defer()
        cid = str(self.entry["id"])
        deleted = self.db.delete_client(cid)
        if deleted is None:
            await interaction.edit_original_response(content=_text(self.language, "Client existiert bereits nicht mehr.", "Client no longer exists."), embed=None, view=None)
            return
        await self.disconnect_cb(cid, "client deleted by admin")
        await self.audit_cb(
            interaction,
            "client_delete",
            client_entry=deleted,
            details={"display_name": deleted.get("display_name", "")},
        )
        await interaction.edit_original_response(
            content=_text(self.language, f"✅ Client **{deleted.get('display_name', 'DCS-Pilot')}** wurde endgültig gelöscht.", f"✅ Client **{deleted.get('display_name', 'DCS-Pilot')}** was permanently deleted."),
            embed=None,
            view=None,
        )
        self.stop()

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(content=_text(self.language, "Löschen abgebrochen.", "Deletion cancelled."), embed=None, view=None)
        self.stop()


class ClientAdminPanelView(discord.ui.View):
    """Compact, ephemeral admin panel for one linked Discord2DCS client."""

    def __init__(
        self,
        *,
        owner_id: int,
        member: discord.Member,
        db: Database,
        disconnect_cb: DisconnectCallback,
        online_cb: OnlineCallback,
        audit_cb: Callable[..., Awaitable[None]],
        public_ws_url: str = "",
        language: str = "en",
    ) -> None:
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.member = member
        self.db = db
        self.disconnect_cb = disconnect_cb
        self.online_cb = online_cb
        self.audit_cb = audit_cb
        self.public_ws_url = public_ws_url
        self.language = language
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                labels = {
                    "d2dcs_panel_refresh": ("Aktualisieren", "Refresh"),
                    "d2dcs_panel_30d": ("+30 Tage", "+30 days"),
                    "d2dcs_panel_lifetime": ("Lifetime", "Lifetime"),
                    "d2dcs_panel_pairing": ("Neues Pairing", "New pairing"),
                }
                if item.custom_id in labels:
                    item.label = _text(language, *labels[item.custom_id])
        self._sync_toggle_button()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(_text(self.language, "Dieses Adminpanel gehört zu einem anderen Admin.", "This admin panel belongs to another admin."), ephemeral=True)
            return False
        return True

    def _entry(self) -> dict[str, Any] | None:
        return self.db.get_client_by_discord_user(self.member.id)

    def _sync_toggle_button(self) -> None:
        entry = self._entry()
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "d2dcs_panel_toggle":
                if entry and bool(entry.get("enabled", True)):
                    item.label = _text(self.language, "Sperren", "Disable")
                    item.style = discord.ButtonStyle.danger
                else:
                    item.label = _text(self.language, "Freischalten", "Enable")
                    item.style = discord.ButtonStyle.success

    def build_embed(self) -> discord.Embed:
        entry = self._entry()
        if not entry:
            return discord.Embed(
                title=f"Discord2DCS • {self.member.display_name}",
                description=_text(self.language, "Dieser Client existiert nicht mehr.", "This client no longer exists."),
            )
        cid = str(entry["id"])
        embed = discord.Embed(title=f"Discord2DCS • {entry.get('display_name', self.member.display_name)}")
        embed.add_field(name="Discord", value=self.member.mention, inline=True)
        embed.add_field(name="Status", value=_status_label(entry, self.online_cb(cid), self.language), inline=True)
        embed.add_field(name="Client-ID", value=f"`{cid}`", inline=False)
        embed.add_field(name=_text(self.language, "Token-Ablauf", "Token expiry"), value=_discord_timestamp(entry.get("expires_at"), "F"), inline=True)
        embed.add_field(
            name=_text(self.language, "Zuletzt gesehen", "Last seen"),
            value=_discord_timestamp(entry.get("last_seen_at"), "R") if entry.get("last_seen_at") else _text(self.language, "nie", "never"),
            inline=True,
        )
        embed.set_footer(text=_text(self.language, "Schnellverwaltung • weitere Optionen über /dcs-client", "Quick controls • more options via /dcs-client"))
        return embed

    async def _refresh_message(self, interaction: discord.Interaction) -> None:
        self._sync_toggle_button()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Aktualisieren", style=discord.ButtonStyle.secondary, custom_id="d2dcs_panel_refresh", row=0)
    async def refresh(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._refresh_message(interaction)

    @discord.ui.button(label="+30 Tage", style=discord.ButtonStyle.primary, custom_id="d2dcs_panel_30d", row=0)
    async def extend_30(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        entry = self._entry()
        if not entry:
            await interaction.response.send_message(_text(self.language, "Client existiert nicht mehr.", "Client no longer exists."), ephemeral=True)
            return
        updated = self.db.extend_client_expiry(str(entry["id"]), "30d")
        await self.audit_cb(interaction, "client_extend", client_entry=updated, details={"validity": "30d", "source": "panel"})
        await self._refresh_message(interaction)

    @discord.ui.button(label="Lifetime", style=discord.ButtonStyle.primary, custom_id="d2dcs_panel_lifetime", row=0)
    async def lifetime(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        entry = self._entry()
        if not entry:
            await interaction.response.send_message(_text(self.language, "Client existiert nicht mehr.", "Client no longer exists."), ephemeral=True)
            return
        updated = self.db.set_client_expiry(str(entry["id"]), "lifetime")
        await self.audit_cb(interaction, "client_set_expiry", client_entry=updated, details={"validity": "lifetime", "source": "panel"})
        await self._refresh_message(interaction)

    @discord.ui.button(label="Sperren", style=discord.ButtonStyle.danger, custom_id="d2dcs_panel_toggle", row=1)
    async def toggle_access(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        entry = self._entry()
        if not entry:
            await interaction.response.send_message(_text(self.language, "Client existiert nicht mehr.", "Client no longer exists."), ephemeral=True)
            return
        new_enabled = not bool(entry.get("enabled", True))
        updated = self.db.set_client_enabled(str(entry["id"]), new_enabled)
        assert updated is not None
        if not new_enabled:
            await self.disconnect_cb(str(entry["id"]), "client disabled")
            action = "client_revoke"
        else:
            action = "client_enable"
        await self.audit_cb(interaction, action, client_entry=updated, details={"source": "panel"})
        await self._refresh_message(interaction)

    @discord.ui.button(label="Neues Pairing", style=discord.ButtonStyle.secondary, custom_id="d2dcs_panel_pairing", row=1)
    async def replacement_pairing(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        entry = self._entry()
        if not entry:
            await interaction.response.send_message(_text(self.language, "Client existiert nicht mehr.", "Client no longer exists."), ephemeral=True)
            return
        if client_status(entry) != "ACTIVE":
            await interaction.response.send_message(
                _text(self.language, "Der Client ist gesperrt oder abgelaufen. Bitte zuerst freischalten bzw. die Laufzeit anpassen.", "The client is disabled or expired. Enable it or adjust the expiry first."),
                ephemeral=True,
            )
            return
        pairing = self.db.create_pairing(
            display_name=str(entry.get("display_name") or self.member.display_name),
            token_validity="lifetime",
            pair_hours=24,
            discord_user_id=self.member.id,
            created_by_user_id=interaction.user.id,
            replacement_client_id=str(entry["id"]),
        )
        await self.audit_cb(
            interaction,
            "replacement_pairing_create",
            client_entry=entry,
            details={"pairing_id": pairing["id"], "pair_hours": 24, "source": "panel"},
        )
        code = str(pairing["code"])
        expiry = _discord_timestamp(pairing.get("expires_at"), "F")
        dm_ok = False
        try:
            dm = discord.Embed(
                title=_text(self.language, "Discord2DCS • Neues Pairing", "Discord2DCS • New pairing"),
                description=_text(self.language, "Für eine Neuinstallation diesen einmaligen Code im Community-Installer eingeben.", "For a reinstall, enter this one-time code in the Community Installer."),
            )
            dm.add_field(name=_text(self.language, "Pairing-Code", "Pairing code"), value=f"```{code}```", inline=False)
            if self.public_ws_url:
                dm.add_field(name=_text(self.language, "Serveradresse", "Server address"), value=f"`{self.public_ws_url}`", inline=False)
            dm.add_field(name=_text(self.language, "Gültig bis", "Valid until"), value=expiry, inline=False)
            dm.set_footer(text=_text(self.language, "Der Code ist nur einmal verwendbar. Die bestehende Client-Laufzeit bleibt erhalten.", "The code can only be used once. The existing client expiry remains unchanged."))
            await self.member.send(embed=dm)
            dm_ok = True
        except (discord.Forbidden, discord.HTTPException):
            dm_ok = False

        if self.language == "de":
            text = f"✅ Neues Pairing für {self.member.mention}\nCode: ```{code}```\nGültig bis: {expiry}\n"
            if self.public_ws_url:
                text += f"Serveradresse: `{self.public_ws_url}`\n"
            text += "📩 Zusätzlich per DM gesendet." if dm_ok else "⚠️ DM nicht möglich – Code hier kopieren."
        else:
            text = f"✅ New pairing for {self.member.mention}\nCode: ```{code}```\nValid until: {expiry}\n"
            if self.public_ws_url:
                text += f"Server address: `{self.public_ws_url}`\n"
            text += "📩 Also sent by DM." if dm_ok else "⚠️ DM unavailable – copy the code from this private response."
        await interaction.response.send_message(text, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())


class DcsClientAdminGroup(app_commands.Group):
    def __init__(
        self,
        *,
        bot: discord.Client,
        db: Database,
        config: AdminConfig,
        disconnect_cb: DisconnectCallback,
        online_cb: OnlineCallback,
    ) -> None:
        super().__init__(name="dcs-client", description="Manage Discord2DCS clients / Clients verwalten", guild_only=True)
        self.bot = bot
        self.db = db
        self.config = config
        self.disconnect_cb = disconnect_cb
        self.online_cb = online_cb

    async def _ensure_admin(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(_tx(interaction, "Dieser Befehl funktioniert nur auf dem Discord-Server.", "This command only works inside the Discord server."), ephemeral=True)
            return False

        if self.config.admin_channel_id and interaction.channel_id != self.config.admin_channel_id:
            await interaction.response.send_message(
                (_tx(interaction, "Discord2DCS-Adminbefehle sind nur in", "Discord2DCS admin commands are only allowed in") + f" <#{self.config.admin_channel_id}>."),
                ephemeral=True,
            )
            return False

        uid = str(interaction.user.id)
        roles = {str(role.id) for role in interaction.user.roles}
        allowed = uid in self.config.admin_user_ids or bool(roles & self.config.admin_role_ids)
        if self.config.allow_guild_administrators and interaction.user.guild_permissions.administrator:
            allowed = True

        if not allowed:
            configured = bool(self.config.admin_user_ids or self.config.admin_role_ids or self.config.allow_guild_administrators)
            message = _tx(interaction, "Du hast keine Berechtigung für die Discord2DCS-Clientverwaltung.", "You do not have permission to manage Discord2DCS clients.")
            if not configured:
                message += _tx(interaction, " Auf dem VPS sind noch keine ADMIN_USER_IDS/ADMIN_ROLE_IDS eingerichtet.", " No ADMIN_USER_IDS/ADMIN_ROLE_IDS are configured on the VPS yet.")
            await interaction.response.send_message(message, ephemeral=True)
            return False
        return True

    async def _audit(
        self,
        interaction: discord.Interaction,
        action: str,
        *,
        client_entry: dict[str, Any] | None = None,
        target_discord_user_id: str | int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        target_uid = str(target_discord_user_id) if target_discord_user_id is not None else None
        if client_entry and client_entry.get("discord_user_id"):
            target_uid = str(client_entry.get("discord_user_id"))
        self.db.audit(
            admin_user_id=str(interaction.user.id),
            admin_name=str(interaction.user),
            action=action,
            target_client_id=str(client_entry.get("id")) if client_entry else None,
            target_discord_user_id=target_uid,
            details=details or {},
        )

        if not self.config.admin_log_channel_id:
            return
        try:
            channel = self.bot.get_channel(self.config.admin_log_channel_id)
            if channel is None:
                channel = await self.bot.fetch_channel(self.config.admin_log_channel_id)
            lang = _interaction_language(interaction)
            embed = discord.Embed(title=_text(lang, "Discord2DCS • Admin-Aktion", "Discord2DCS • Admin action"))
            embed.add_field(name="Admin", value=interaction.user.mention, inline=True)
            embed.add_field(name=_text(lang, "Aktion", "Action"), value=action, inline=True)
            if target_uid:
                embed.add_field(name=_text(lang, "Benutzer", "User"), value=f"<@{target_uid}>", inline=True)
            if client_entry:
                embed.add_field(name="Client", value=f"`{client_entry.get('id', '')}`", inline=False)
            if details:
                safe = {k: v for k, v in details.items() if "code" not in k.lower() and "token" not in k.lower()}
                if safe:
                    embed.add_field(name=_text(lang, "Details", "Details"), value=f"```json\n{json.dumps(safe, ensure_ascii=False)[:900]}\n```", inline=False)
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except Exception:
            # Admin logging must not make the actual command fail.
            pass

    async def _deliver_pairing(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        pairing: dict[str, Any],
        *,
        replacement: bool,
    ) -> None:
        code = str(pairing["code"])
        pair_expiry = _discord_timestamp(pairing.get("expires_at"), "F")
        lang = _interaction_language(interaction)
        token_validity = _text(lang, "bestehende Laufzeit bleibt erhalten", "existing expiry remains unchanged") if replacement else str(pairing.get("token_validity", ""))
        dm_ok = False
        try:
            embed = discord.Embed(
                title="Discord2DCS • Pairing",
                description=_text(lang, "Starte den Community-Installer und gib dort diesen einmaligen Pairing-Code ein.", "Start the Community Installer and enter this one-time pairing code."),
            )
            embed.add_field(name=_text(lang, "Pairing-Code", "Pairing code"), value=f"```{code}```", inline=False)
            if self.config.public_ws_url:
                embed.add_field(name=_text(lang, "Serveradresse", "Server address"), value=f"`{self.config.public_ws_url}`", inline=False)
            embed.add_field(name=_text(lang, "Pairing gültig bis", "Pairing valid until"), value=pair_expiry, inline=False)
            embed.add_field(name=_text(lang, "Client-Laufzeit", "Client validity"), value=token_validity, inline=False)
            embed.set_footer(text=_text(lang, "Der Code ist nur einmal verwendbar. Nicht weitergeben.", "The code can only be used once. Do not share it."))
            await member.send(embed=embed)
            dm_ok = True
        except (discord.Forbidden, discord.HTTPException):
            dm_ok = False

        if lang == "de":
            text = (f"✅ Pairing für {member.mention} erstellt.\n" f"Pairing-ID: `{pairing['id']}`\n" f"Client-Laufzeit: **{token_validity}**\n" f"Pairing gültig bis: {pair_expiry}\n" f"Code: ```{code}```\n")
            if self.config.public_ws_url:
                text += f"Serveradresse: `{self.config.public_ws_url}`\n"
            text += "📩 Der Code wurde zusätzlich per DM an den Benutzer geschickt." if dm_ok else "⚠️ DM konnte nicht zugestellt werden. Kopiere den Code aus dieser nur für dich sichtbaren Antwort."
        else:
            text = (f"✅ Pairing created for {member.mention}.\n" f"Pairing ID: `{pairing['id']}`\n" f"Client validity: **{token_validity}**\n" f"Pairing valid until: {pair_expiry}\n" f"Code: ```{code}```\n")
            if self.config.public_ws_url:
                text += f"Server address: `{self.config.public_ws_url}`\n"
            text += "📩 The code was also sent to the user by DM." if dm_ok else "⚠️ DM could not be delivered. Copy the code from this private response."
        await interaction.followup.send(text, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    def _client_for_member(self, member: discord.Member) -> dict[str, Any] | None:
        return self.db.get_client_by_discord_user(member.id)

    @app_commands.command(name="create", description="Create client / neuen Client anlegen")
    @app_commands.describe(
        user="Discord member / Mitglied",
        validity="Client token validity / Laufzeit",
        custom_validity="Custom only / nur Benutzerdefiniert: 45d, 8w, 12h, until:2027-12-31",
        pair_hours="Pairing validity / Pairing-Gültigkeit (1-168 h)",
    )
    @app_commands.choices(validity=VALIDITY_CHOICES)
    async def create(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        validity: app_commands.Choice[str],
        custom_validity: str | None = None,
        pair_hours: app_commands.Range[int, 1, 168] = 24,
    ) -> None:
        if not await self._ensure_admin(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        if user.bot:
            await interaction.followup.send(_tx(interaction, "Bots können keinen Discord2DCS-Client erhalten.", "Bots cannot receive a Discord2DCS client."), ephemeral=True)
            return
        existing = self._client_for_member(user)
        if existing:
            await interaction.followup.send(
                _tx(interaction, f"Für {user.mention} existiert bereits Client `{existing['id']}`. Für eine Neuinstallation `/dcs-client pairing` verwenden.", f"Client `{existing['id']}` already exists for {user.mention}. Use `/dcs-client pairing` for a reinstall."),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return
        if any(str(p.get("discord_user_id") or "") == str(user.id) for p in self.db.list_open_pairings()):
            await interaction.followup.send(
                _tx(interaction, "Für diesen Benutzer existiert bereits ein offener Pairing-Code. Nutze `/dcs-client pairings` oder storniere ihn zuerst.", "An open pairing code already exists for this user. Use `/dcs-client pairings` or cancel it first."),
                ephemeral=True,
            )
            return
        try:
            validity_value = _validity_from_choice(validity, custom_validity)
            pairing = self.db.create_pairing(
                display_name=user.display_name,
                token_validity=validity_value,
                pair_hours=int(pair_hours),
                discord_user_id=user.id,
                created_by_user_id=interaction.user.id,
            )
        except ValueError as exc:
            await interaction.followup.send(f"❌ {exc}", ephemeral=True)
            return
        await self._audit(
            interaction,
            "pairing_create",
            target_discord_user_id=user.id,
            details={"pairing_id": pairing["id"], "validity": validity_value, "pair_hours": int(pair_hours)},
        )
        await self._deliver_pairing(interaction, user, pairing, replacement=False)

    @app_commands.command(name="list", description="List clients / Clients anzeigen")
    async def list_clients(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_admin(interaction):
            return
        clients = self.db.list_clients()
        if not clients:
            await interaction.response.send_message(_tx(interaction, "Noch keine Clients vorhanden.", "No clients yet."), ephemeral=True)
            return
        view = ClientListView(interaction.user.id, clients, self.online_cb, _interaction_language(interaction))
        if view.pages > 1:
            await interaction.response.send_message(
                embed=view.build_embed(),
                view=view,
                ephemeral=True,
            )
        else:
            # discord.py 2.6.x darf hier kein explizites view=None erhalten.
            # Ohne Pagination lassen wir den Parameter vollständig weg.
            await interaction.response.send_message(
                embed=view.build_embed(),
                ephemeral=True,
            )

    @app_commands.command(name="info", description="Client details / Client-Details")
    @app_commands.describe(user="Discord member / Mitglied")
    async def info(self, interaction: discord.Interaction, user: discord.Member) -> None:
        if not await self._ensure_admin(interaction):
            return
        entry = self._client_for_member(user)
        if not entry:
            await interaction.response.send_message(_tx(interaction, f"Für {user.mention} ist kein Client verknüpft.", f"No client is linked to {user.mention}."), ephemeral=True)
            return
        cid = str(entry["id"])
        embed = discord.Embed(title=f"Discord2DCS • {entry.get('display_name', user.display_name)}")
        embed.add_field(name="Discord", value=user.mention, inline=True)
        embed.add_field(name="Status", value=_status_label(entry, self.online_cb(cid), self.language), inline=True)
        embed.add_field(name="Client-ID", value=f"`{cid}`", inline=False)
        embed.add_field(name=_tx(interaction, "Erstellt", "Created"), value=_discord_timestamp(entry.get("created_at"), "F"), inline=True)
        embed.add_field(name=_tx(interaction, "Zuletzt gesehen", "Last seen"), value=_discord_timestamp(entry.get("last_seen_at"), "R") if entry.get("last_seen_at") else _tx(interaction, "nie", "never"), inline=True)
        embed.add_field(name=_tx(interaction, "Token-Ablauf", "Token expiry"), value=_discord_timestamp(entry.get("expires_at"), "F"), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="panel", description="Quick admin panel / Schnellpanel")
    @app_commands.describe(user="Discord member / Mitglied")
    async def panel(self, interaction: discord.Interaction, user: discord.Member) -> None:
        if not await self._ensure_admin(interaction):
            return
        entry = self._client_for_member(user)
        if not entry:
            await interaction.response.send_message(_tx(interaction, f"Für {user.mention} ist kein Client verknüpft.", f"No client is linked to {user.mention}."), ephemeral=True)
            return
        view = ClientAdminPanelView(
            owner_id=interaction.user.id,
            member=user,
            db=self.db,
            disconnect_cb=self.disconnect_cb,
            online_cb=self.online_cb,
            audit_cb=self._audit,
            public_ws_url=self.config.public_ws_url,
            language=_interaction_language(interaction),
        )
        await interaction.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)

    @app_commands.command(name="set-expiry", description="Set expiry / Laufzeit setzen")
    @app_commands.describe(user="Discord member / Mitglied", validity="New validity / neue Laufzeit", custom_validity="e.g. / z.B. 45d, 8w, until:2027-12-31")
    @app_commands.choices(validity=VALIDITY_CHOICES)
    async def set_expiry(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        validity: app_commands.Choice[str],
        custom_validity: str | None = None,
    ) -> None:
        if not await self._ensure_admin(interaction):
            return
        entry = self._client_for_member(user)
        if not entry:
            await interaction.response.send_message(_tx(interaction, "Für diesen Benutzer existiert kein Client.", "No client exists for this user."), ephemeral=True)
            return
        try:
            value = _validity_from_choice(validity, custom_validity)
            updated = self.db.set_client_expiry(str(entry["id"]), value)
        except ValueError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return
        await self._audit(interaction, "client_set_expiry", client_entry=updated, details={"validity": value})
        if client_status(updated) == "EXPIRED":
            await self.disconnect_cb(str(updated["id"]), "token expired")
        await interaction.response.send_message(
            _tx(interaction, f"✅ Laufzeit für {user.mention} gesetzt: **{_discord_timestamp(updated.get('expires_at'), 'F')}**", f"✅ Expiry for {user.mention} set to **{_discord_timestamp(updated.get('expires_at'), 'F')}**"),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @app_commands.command(name="extend", description="Extend expiry / Laufzeit verlängern")
    @app_commands.describe(user="Discord member / Mitglied", validity="Extension / Verlängerung", custom_validity="e.g. / z.B. 45d, 8w, until:2027-12-31")
    @app_commands.choices(validity=VALIDITY_CHOICES)
    async def extend(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        validity: app_commands.Choice[str],
        custom_validity: str | None = None,
    ) -> None:
        if not await self._ensure_admin(interaction):
            return
        entry = self._client_for_member(user)
        if not entry:
            await interaction.response.send_message(_tx(interaction, "Für diesen Benutzer existiert kein Client.", "No client exists for this user."), ephemeral=True)
            return
        try:
            value = _validity_from_choice(validity, custom_validity)
            updated = self.db.extend_client_expiry(str(entry["id"]), value)
        except (ValueError, KeyError) as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return
        await self._audit(interaction, "client_extend", client_entry=updated, details={"validity": value})
        await interaction.response.send_message(
            _tx(interaction, f"✅ Laufzeit für {user.mention} verlängert. Neuer Ablauf: **{_discord_timestamp(updated.get('expires_at'), 'F')}**", f"✅ Validity for {user.mention} extended. New expiry: **{_discord_timestamp(updated.get('expires_at'), 'F')}**"),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @app_commands.command(name="revoke", description="Disable client / Client sperren")
    @app_commands.describe(user="Discord member / Mitglied")
    async def revoke(self, interaction: discord.Interaction, user: discord.Member) -> None:
        if not await self._ensure_admin(interaction):
            return
        entry = self._client_for_member(user)
        if not entry:
            await interaction.response.send_message(_tx(interaction, "Für diesen Benutzer existiert kein Client.", "No client exists for this user."), ephemeral=True)
            return
        updated = self.db.set_client_enabled(str(entry["id"]), False)
        assert updated is not None
        await self.disconnect_cb(str(entry["id"]), "client disabled")
        await self._audit(interaction, "client_revoke", client_entry=updated)
        await interaction.response.send_message(_tx(interaction, f"⛔ {user.mention} wurde sofort gesperrt.", f"⛔ {user.mention} was disabled immediately."), ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="enable", description="Enable client / Client freischalten")
    @app_commands.describe(user="Discord member / Mitglied")
    async def enable(self, interaction: discord.Interaction, user: discord.Member) -> None:
        if not await self._ensure_admin(interaction):
            return
        entry = self._client_for_member(user)
        if not entry:
            await interaction.response.send_message(_tx(interaction, "Für diesen Benutzer existiert kein Client.", "No client exists for this user."), ephemeral=True)
            return
        updated = self.db.set_client_enabled(str(entry["id"]), True)
        assert updated is not None
        await self._audit(interaction, "client_enable", client_entry=updated)
        extra = _tx(interaction, " Token ist weiterhin abgelaufen – bitte zusätzlich die Laufzeit setzen.", " Token is still expired – please set a new expiry as well.") if client_status(updated) == "EXPIRED" else ""
        await interaction.response.send_message(_tx(interaction, f"✅ {user.mention} wurde freigeschaltet.{extra}", f"✅ {user.mention} was enabled.{extra}"), ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="pairing", description="New pairing code / neuen Pairing-Code erstellen")
    @app_commands.describe(user="Discord member / Mitglied", pair_hours="Pairing validity / Pairing-Gültigkeit (1-168 h)")
    async def pairing(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        pair_hours: app_commands.Range[int, 1, 168] = 24,
    ) -> None:
        if not await self._ensure_admin(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        entry = self._client_for_member(user)
        if not entry:
            await interaction.followup.send(_tx(interaction, "Für diesen Benutzer existiert kein Client. Nutze zuerst `/dcs-client create`.", "No client exists for this user. Use `/dcs-client create` first."), ephemeral=True)
            return
        access_state = client_status(entry)
        if access_state != "ACTIVE":
            await interaction.followup.send(
                _tx(interaction, "Der Client ist aktuell gesperrt oder abgelaufen. Bitte zuerst `/dcs-client enable` bzw. die Laufzeit anpassen.", "The client is currently disabled or expired. Use `/dcs-client enable` or adjust the expiry first."),
                ephemeral=True,
            )
            return
        pairing = self.db.create_pairing(
            display_name=str(entry.get("display_name") or user.display_name),
            token_validity="lifetime",
            pair_hours=int(pair_hours),
            discord_user_id=user.id,
            created_by_user_id=interaction.user.id,
            replacement_client_id=str(entry["id"]),
        )
        await self._audit(
            interaction,
            "replacement_pairing_create",
            client_entry=entry,
            details={"pairing_id": pairing["id"], "pair_hours": int(pair_hours)},
        )
        await self._deliver_pairing(interaction, user, pairing, replacement=True)

    @app_commands.command(name="delete", description="Delete client permanently / Client löschen")
    @app_commands.describe(user="Discord member / Mitglied")
    async def delete(self, interaction: discord.Interaction, user: discord.Member) -> None:
        if not await self._ensure_admin(interaction):
            return
        entry = self._client_for_member(user)
        if not entry:
            await interaction.response.send_message(_tx(interaction, "Für diesen Benutzer existiert kein Client.", "No client exists for this user."), ephemeral=True)
            return
        embed = discord.Embed(
            title=_tx(interaction, "⚠️ Client endgültig löschen?", "⚠️ Permanently delete client?"),
            description=_tx(
                interaction,
                f"**{user.display_name}** (`{entry['id']}`) wird aus der Datenbank entfernt. Der aktuelle Token funktioniert danach nicht mehr. Dieser Vorgang lässt sich nicht rückgängig machen.",
                f"**{user.display_name}** (`{entry['id']}`) will be removed from the database. The current token will stop working. This cannot be undone.",
            ),
        )
        view = DeleteClientView(
            owner_id=interaction.user.id,
            client_entry=entry,
            db=self.db,
            disconnect_cb=self.disconnect_cb,
            audit_cb=self._audit,
            language=_interaction_language(interaction),
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="pairings", description="Open pairings / offene Pairings")
    async def pairings(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_admin(interaction):
            return
        items = self.db.list_open_pairings()
        if not items:
            await interaction.response.send_message(_tx(interaction, "Keine offenen Pairing-Codes.", "No open pairing codes."), ephemeral=True)
            return
        lang = _interaction_language(interaction)
        embed = discord.Embed(title=_text(lang, "Discord2DCS • Offene Pairings", "Discord2DCS • Open pairings"), description=_text(lang, f"{len(items)} offene Pairing(s)", f"{len(items)} open pairing(s)"))
        for entry in items[:20]:
            uid = str(entry.get("discord_user_id") or "")
            user = f"<@{uid}>" if uid else entry.get("display_name", "DCS-Pilot")
            mode = _text(lang, "Token-Rotation", "Token rotation") if entry.get("replacement_client_id") else entry.get("token_validity", "")
            embed.add_field(
                name=f"{entry.get('id')} • {entry.get('display_name', '')}",
                value=f"{user}\n" + _text(lang, f"Typ/Laufzeit: **{mode}**\nAblauf: {_discord_timestamp(entry.get('expires_at'), 'R')}", f"Type/validity: **{mode}**\nExpiry: {_discord_timestamp(entry.get('expires_at'), 'R')}"),
                inline=False,
            )
        if len(items) > 20:
            embed.set_footer(text=_text(lang, f"Es werden die neuesten 20 von {len(items)} angezeigt.", f"Showing the newest 20 of {len(items)}."))
        await interaction.response.send_message(embed=embed, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="cancel-pairing", description="Cancel pairing / Pairing stornieren")
    @app_commands.describe(pairing_id="Pairing ID from / aus /dcs-client pairings")
    async def cancel_pairing(self, interaction: discord.Interaction, pairing_id: str) -> None:
        if not await self._ensure_admin(interaction):
            return
        entry = self.db.cancel_pairing(pairing_id.strip())
        if entry is None:
            await interaction.response.send_message(_tx(interaction, "Pairing-ID nicht gefunden oder bereits benutzt/storniert.", "Pairing ID not found or already used/cancelled."), ephemeral=True)
            return
        await self._audit(
            interaction,
            "pairing_cancel",
            target_discord_user_id=entry.get("discord_user_id"),
            details={"pairing_id": entry.get("id")},
        )
        await interaction.response.send_message(_tx(interaction, f"✅ Pairing `{entry.get('id')}` wurde ungültig gemacht.", f"✅ Pairing `{entry.get('id')}` was cancelled."), ephemeral=True)

    @app_commands.command(name="adopt", description="Link migrated client / migrierten Client zuordnen")
    @app_commands.describe(user="Discord member / Mitglied", client_id="Client ID from / aus /dcs-client list")
    async def adopt(self, interaction: discord.Interaction, user: discord.Member, client_id: str) -> None:
        if not await self._ensure_admin(interaction):
            return
        try:
            updated = self.db.adopt_client(client_id.strip(), user.id, user.display_name)
        except KeyError:
            await interaction.response.send_message(_tx(interaction, "Client-ID nicht gefunden.", "Client ID not found."), ephemeral=True)
            return
        except ValueError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return
        await self._audit(interaction, "client_adopt", client_entry=updated, details={"discord_user_id": str(user.id)})
        await interaction.response.send_message(
            _tx(interaction, f"✅ Client `{updated['id']}` ist jetzt {user.mention} zugeordnet.", f"✅ Client `{updated['id']}` is now linked to {user.mention}."),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @app_commands.command(name="audit", description="Admin audit log / Admin-Audit")
    @app_commands.describe(limit="Entries / Einträge (1-50)")
    async def audit(self, interaction: discord.Interaction, limit: app_commands.Range[int, 1, 50] = 20) -> None:
        if not await self._ensure_admin(interaction):
            return
        rows = self.db.recent_audit(int(limit))
        if not rows:
            await interaction.response.send_message(_tx(interaction, "Noch keine Audit-Einträge.", "No audit entries yet."), ephemeral=True)
            return
        lang = _interaction_language(interaction)
        embed = discord.Embed(title="Discord2DCS • Audit", description=_text(lang, f"Letzte {len(rows)} Aktion(en)", f"Latest {len(rows)} action(s)"))
        for row in rows[:20]:
            when = _discord_timestamp(row.get("created_at"), "R")
            admin = f"<@{row['admin_user_id']}>" if row.get("admin_user_id") else str(row.get("admin_name") or "system")
            target = f"<@{row['target_discord_user_id']}>" if row.get("target_discord_user_id") else (f"`{row.get('target_client_id')}`" if row.get("target_client_id") else "—")
            details = row.get("details") or {}
            detail_text = ", ".join(f"{k}={v}" for k, v in details.items() if "code" not in k.lower() and "token" not in k.lower())[:300]
            embed.add_field(
                name=f"{row.get('action')} • {when}",
                value=f"Admin: {admin}\n" + _text(lang, f"Ziel: {target}", f"Target: {target}") + (f"\n{detail_text}" if detail_text else ""),
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())


def install_admin_group(
    *,
    tree: app_commands.CommandTree,
    bot: discord.Client,
    db: Database,
    config: AdminConfig,
    disconnect_cb: DisconnectCallback,
    online_cb: OnlineCallback,
) -> DcsClientAdminGroup:
    group = DcsClientAdminGroup(
        bot=bot,
        db=db,
        config=config,
        disconnect_cb=disconnect_cb,
        online_cb=online_cb,
    )
    tree.add_command(group)
    return group
