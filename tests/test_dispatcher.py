"""Tests unitarios para AlertDispatcher en Discord."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import discord

from src.config import Settings
from src.dispatcher import AlertDispatcher
from src.models import NewsItem, Priority, SourceSummary
from src.storage import BotStorage


class FakeChannel:
    def __init__(self, channel_id: int, *, fail_forbidden: bool = False) -> None:
        self.channel_id = channel_id
        self.fail_forbidden = fail_forbidden
        self.sent_embeds: list[discord.Embed] = []

    async def send(self, *, embed: discord.Embed) -> None:
        if self.fail_forbidden:
            resp = SimpleNamespace(status=403, reason="Forbidden")
            raise discord.Forbidden(resp, "Missing Permissions")
        self.sent_embeds.append(embed)


class FakeDiscordClient:
    def __init__(self, channels: dict[int, FakeChannel]) -> None:
        self.channels = channels

    def get_channel(self, channel_id: int) -> FakeChannel | None:
        return self.channels.get(channel_id)

    async def fetch_channel(self, channel_id: int) -> Any:
        ch = self.channels.get(channel_id)
        if ch is None:
            resp = SimpleNamespace(status=404, reason="Not Found")
            raise discord.NotFound(resp, "Unknown Channel")
        return ch


def _make_item(
    item_id: int, item_type: str = "cve", priority: Priority = Priority.HIGH
) -> NewsItem:
    return NewsItem(
        id=item_id,
        title=f"Alert #{item_id}",
        url=f"https://example.org/{item_id}",
        type=item_type,
        priority=priority,
        priority_weight=priority.weight,
        published_at=datetime(2026, 11, 20, 14, 0, tzinfo=UTC),
        fetched_at=datetime(2026, 11, 20, 14, 1, tzinfo=UTC),
        snippet="Detalle breve",
        source=SourceSummary(slug="debian", name="Debian", url="https://debian.org"),
    )


async def test_dispatcher_sends_embeds_dedups_and_pauses_on_forbidden_or_not_found(
    tmp_path: Path,
) -> None:
    storage = BotStorage(tmp_path / "bot.db")
    await storage.initialize()
    try:
        await storage.subscribe(101, "cve", Priority.MEDIUM)
        await storage.subscribe(102, "cve", Priority.CRITICAL)  # no cumple HIGH
        await storage.subscribe(103, "all", Priority.LOW)  # Forbidden -> pausa automática
        await storage.subscribe(104, "cve", Priority.LOW)  # NotFound -> pausa automática

        ch101 = FakeChannel(101)
        ch103 = FakeChannel(103, fail_forbidden=True)
        client = FakeDiscordClient({101: ch101, 103: ch103})

        dispatcher = AlertDispatcher(
            client,
            storage,
            Settings(discord_show_thumbnails=True),
            min_interval_seconds=0.0,
        )
        delivered = await dispatcher.dispatch_item(_make_item(77, "cve", Priority.HIGH))

        assert delivered == 1
        assert len(ch101.sent_embeds) == 1
        assert ch101.sent_embeds[0].title == "Alert #77"

        assert await storage.is_paused(103) is True
        assert await storage.is_paused(104) is True
        assert await storage.is_paused(101) is False

        # Reenvío del mismo item -> deduplicado, 0 envíos
        assert await dispatcher.dispatch_item(_make_item(77, "cve", Priority.HIGH)) == 0
    finally:
        await storage.close()


async def test_dispatcher_prunes_periodically_and_isolates_dynamic_types(tmp_path: Path) -> None:
    storage = BotStorage(tmp_path / "bot.db")
    await storage.initialize()
    try:
        await storage.subscribe(201, "iot", Priority.LOW)
        await storage.subscribe(202, "cve", Priority.LOW)
        await storage.mark_dispatched(999, 1)
        await storage._db().execute(
            "UPDATE dispatched_items SET dispatched_at = ? WHERE channel_id = ?",
            ("2020-01-01T00:00:00+00:00", 999),
        )
        await storage._db().commit()

        ch201 = FakeChannel(201)
        ch202 = FakeChannel(202)
        client = FakeDiscordClient({201: ch201, 202: ch202})
        dispatcher = AlertDispatcher(
            client,
            storage,
            Settings(),
            prune_every=2,
            prune_retention_days=30,
            max_concurrency=4,
            min_interval_seconds=0.0,
        )

        assert await dispatcher.dispatch_item(_make_item(1, "iot", Priority.MEDIUM)) == 1
        assert len(ch201.sent_embeds) == 1
        assert len(ch202.sent_embeds) == 0
        assert await storage.was_dispatched(999, 1) is True

        # 2ª entrega dispara la poda por antigüedad (elimina fila de 2020 y conserva recientes)
        assert await dispatcher.dispatch_item(_make_item(2, "iot", Priority.HIGH)) == 1
        assert await storage.was_dispatched(201, 1) is True
        assert await storage.was_dispatched(201, 2) is True
        assert await storage.was_dispatched(999, 1) is False
    finally:
        await storage.close()
