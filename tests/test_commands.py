"""Tests unitarios para todos los slash commands del contrato BOT_COMMANDS_CONTRACT.md."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import discord
import httpx
from discord import app_commands

from src.api_client import BeaconApiClient
from src.commands import BotAppContext, register_commands
from src.config import Settings
from src.dispatcher import AlertDispatcher
from src.reverb_client import ReverbListener
from src.storage import BotStorage


class FakeResponse:
    def __init__(self) -> None:
        self.deferred = False
        self.messages: list[dict[str, Any]] = []

    async def defer(self, *, ephemeral: bool = False) -> None:
        self.deferred = True

    async def send_message(self, content: str | None = None, **kwargs: Any) -> None:
        self.messages.append({"content": content, **kwargs})


class FakeFollowup:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send(self, content: str | None = None, **kwargs: Any) -> None:
        self.messages.append({"content": content, **kwargs})


def _make_interaction(
    *,
    channel_id: int = 555,
    guild_id: int | None = 100,
    user_id: int = 10,
    administrator: bool = False,
    manage_channels: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        channel_id=channel_id,
        guild_id=guild_id,
        guild=SimpleNamespace(id=guild_id) if guild_id is not None else None,
        channel=SimpleNamespace(id=channel_id, name="alertas"),
        user=SimpleNamespace(id=user_id),
        permissions=SimpleNamespace(administrator=administrator, manage_channels=manage_channels),
        response=FakeResponse(),
        followup=FakeFollowup(),
    )


def _api_transport(*, fail: bool = False) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if fail:
            return httpx.Response(503)

        if request.url.path == "/api/v1/status":
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "database": "ok",
                    "last_sync_at": "2026-11-20T14:00:00+00:00",
                    "sources": {"active": 2, "failing": 0, "total": 2},
                    "items_total": 12,
                    "websocket": {"channel": "beacon.news", "event": "news.created"},
                },
            )
        if request.url.path == "/api/v1/types":
            return httpx.Response(
                200,
                json={
                    "types": [
                        {"type": "cve", "sources_count": 1, "items_count": 8},
                        {"type": "linux", "sources_count": 1, "items_count": 4},
                    ],
                    "priorities": [
                        {"value": "low", "label": "Baja", "weight": 1},
                        {"value": "medium", "label": "Media", "weight": 2},
                        {"value": "high", "label": "Alta", "weight": 3},
                        {"value": "critical", "label": "Crítica", "weight": 4},
                    ],
                },
            )
        if request.url.path == "/api/v1/sources":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "slug": "debian-security",
                            "name": "Debian Security",
                            "url": "https://www.debian.org/security/dsa",
                            "format": "rss",
                            "type": "cve",
                            "priority": "high",
                            "interval_minutes": 30,
                            "is_active": True,
                        }
                    ]
                },
            )
        if request.url.path == "/api/v1/items":
            if request.url.params.get("q") == "notfound":
                return httpx.Response(200, json={"data": []})
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 99,
                            "title": "DSA-99 OpenSSL update",
                            "url": "https://debian.org/dsa-99",
                            "snippet": "Resumen breve",
                            "type": "cve",
                            "priority": "high",
                            "priority_weight": 3,
                            "published_at": "2026-11-20T14:00:00+00:00",
                            "fetched_at": "2026-11-20T14:05:00+00:00",
                            "source": {
                                "slug": "debian-security",
                                "name": "Debian Security",
                                "url": "https://debian.org",
                            },
                        }
                    ]
                },
            )
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def _command_map(tree: app_commands.CommandTree[discord.Client]) -> dict[str, Any]:
    return {cmd.name: cmd for cmd in tree.get_commands()}


async def test_registers_exact_contract_commands_and_runs_info_commands(tmp_path: Path) -> None:
    storage = BotStorage(tmp_path / "bot.db")
    await storage.initialize()
    api_client = BeaconApiClient("http://localhost:8000", transport=_api_transport())
    settings = Settings(discord_admin_ids="999")
    dispatcher = AlertDispatcher(SimpleNamespace(), storage, settings)
    reverb = ReverbListener(
        "ws://localhost:8080", "k", "beacon.news", api_client, storage, dispatcher.dispatch_item
    )
    reverb.is_connected = True
    ctx = BotAppContext(settings, storage, api_client, dispatcher, reverb)

    tree = app_commands.CommandTree(discord.Client(intents=discord.Intents.default()))
    register_commands(tree, ctx)
    cmds = _command_map(tree)

    expected = {
        "help",
        "status",
        "sources",
        "types",
        "latest",
        "search",
        "subscribe",
        "unsubscribe",
        "filters",
        "pause",
        "resume",
    }
    assert set(cmds.keys()) == expected

    try:
        i_help = _make_interaction()
        await cmds["help"].callback(i_help)
        assert i_help.response.messages[0]["embed"].title == "beacon-sift · Comandos disponibles"

        i_status = _make_interaction()
        await cmds["status"].callback(i_status)
        assert i_status.response.deferred is True
        assert i_status.followup.messages[0]["embed"].title == "Estado de beacon-sift"

        i_sources = _make_interaction()
        await cmds["sources"].callback(i_sources, "cve")
        assert "Debian Security" in i_sources.followup.messages[0]["embed"].description

        i_types = _make_interaction()
        await cmds["types"].callback(i_types)
        assert len(i_types.followup.messages[0]["embed"].fields) == 2

        i_latest = _make_interaction()
        await cmds["latest"].callback(
            i_latest,
            "cve",
            app_commands.Choice(name="Alta", value="high"),
            5,
        )
        assert "DSA-99 OpenSSL update" in i_latest.followup.messages[0]["embed"].description

        i_bad_limit = _make_interaction()
        await cmds["latest"].callback(i_bad_limit, None, None, 25)
        assert i_bad_limit.response.messages[0]["ephemeral"] is True

        i_search = _make_interaction()
        await cmds["search"].callback(i_search, "OpenSSL", "cve", 5)
        assert "DSA-99 OpenSSL update" in i_search.followup.messages[0]["embed"].description

        i_empty_search = _make_interaction()
        await cmds["search"].callback(i_empty_search, "notfound", None, 5)
        assert "No se encontraron noticias" in i_empty_search.followup.messages[0]["content"]
    finally:
        await api_client.close()
        await storage.close()


async def test_info_commands_handle_unavailable_api(tmp_path: Path) -> None:
    storage = BotStorage(tmp_path / "bot.db")
    await storage.initialize()
    api_client = BeaconApiClient("http://localhost:8000", transport=_api_transport(fail=True))
    settings = Settings()
    dispatcher = AlertDispatcher(SimpleNamespace(), storage, settings)
    reverb = ReverbListener(
        "ws://localhost:8080", "k", "beacon.news", api_client, storage, dispatcher.dispatch_item
    )
    ctx = BotAppContext(settings, storage, api_client, dispatcher, reverb)

    tree = app_commands.CommandTree(discord.Client(intents=discord.Intents.default()))
    register_commands(tree, ctx)
    cmds = _command_map(tree)

    try:
        i_status = _make_interaction()
        await cmds["status"].callback(i_status)
        assert "no está disponible" in i_status.followup.messages[0]["embed"].description

        i_latest = _make_interaction()
        await cmds["latest"].callback(i_latest, None, None, 5)
        assert "no está disponible" in i_latest.followup.messages[0]["content"]
    finally:
        await api_client.close()
        await storage.close()


async def test_subscription_commands_permissions_and_lifecycle(tmp_path: Path) -> None:
    storage = BotStorage(tmp_path / "bot.db")
    await storage.initialize()
    api_client = BeaconApiClient("http://localhost:8000", transport=_api_transport())
    settings = Settings(discord_admin_ids="999", allow_dm_subscriptions=False)
    dispatcher = AlertDispatcher(SimpleNamespace(), storage, settings)
    reverb = ReverbListener(
        "ws://localhost:8080", "k", "beacon.news", api_client, storage, dispatcher.dispatch_item
    )
    ctx = BotAppContext(settings, storage, api_client, dispatcher, reverb)

    tree = app_commands.CommandTree(discord.Client(intents=discord.Intents.default()))
    register_commands(tree, ctx)
    cmds = _command_map(tree)

    try:
        # Miembro sin permisos en servidor -> denegado ephemeral
        i_member = _make_interaction(user_id=50, administrator=False, manage_channels=False)
        await cmds["subscribe"].callback(i_member, "cve", None)
        assert i_member.response.messages[0]["ephemeral"] is True
        assert "restringido a administradores" in i_member.response.messages[0]["content"]

        # DM de usuario no global admin -> denegado
        i_dm = _make_interaction(guild_id=None, user_id=50)
        await cmds["pause"].callback(i_dm)
        assert i_dm.response.messages[0]["ephemeral"] is True

        # Usuario con manage_channels -> permitido; tipo desconocido rechazado
        i_mod = _make_interaction(channel_id=777, user_id=20, manage_channels=True)
        await cmds["subscribe"].callback(i_mod, "inexistente", None)
        assert "no existe" in i_mod.followup.messages[0]["content"]

        # Suscripción válida
        i_sub = _make_interaction(channel_id=777, user_id=20, manage_channels=True)
        await cmds["subscribe"].callback(
            i_sub,
            "cve",
            app_commands.Choice(name="Alta", value="high"),
        )
        assert "Suscripción guardada" in i_sub.followup.messages[0]["content"]

        # Pause, filters, resume
        i_pause = _make_interaction(channel_id=777, user_id=999)  # Global DISCORD_ADMIN_IDS
        await cmds["pause"].callback(i_pause)
        assert "pausadas" in i_pause.followup.messages[0]["content"]

        i_filters = _make_interaction(channel_id=777, user_id=50)  # /filters visible
        await cmds["filters"].callback(i_filters)
        assert "Pausado" in i_filters.followup.messages[0]["embed"].description

        i_resume = _make_interaction(channel_id=777, user_id=999)
        await cmds["resume"].callback(i_resume)
        assert "reanudadas" in i_resume.followup.messages[0]["content"]

        # Unsubscribe
        i_unsub = _make_interaction(channel_id=777, administrator=True)
        await cmds["unsubscribe"].callback(i_unsub, "cve")
        assert "Suscripción eliminada" in i_unsub.followup.messages[0]["content"]
    finally:
        await api_client.close()
        await storage.close()
