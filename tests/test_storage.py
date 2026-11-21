"""Pruebas unitarias para la persistencia SQLite del bot de Discord."""

from __future__ import annotations

from pathlib import Path

from src.models import Priority
from src.storage import BotStorage


async def test_subscribe_update_and_unsubscribe(tmp_path: Path) -> None:
    storage = BotStorage(tmp_path / "bot.db")
    await storage.initialize()
    try:
        await storage.subscribe(1001, "cve", Priority.MEDIUM, guild_id=50, name="alertas")
        await storage.subscribe(1001, "linux", Priority.LOW)
        await storage.subscribe(1001, "cve", Priority.HIGH)

        subs = await storage.list_subscriptions(1001)
        assert len(subs) == 2
        assert subs[0].source_type == "cve"
        assert subs[0].min_priority == Priority.HIGH
        assert subs[1].source_type == "linux"

        removed_one = await storage.unsubscribe(1001, "linux")
        assert removed_one == 1
        assert len(await storage.list_subscriptions(1001)) == 1

        await storage.subscribe(1001, "all", Priority.CRITICAL)
        removed_all = await storage.unsubscribe(1001, "all")
        assert removed_all == 2
        assert await storage.list_subscriptions(1001) == []
    finally:
        await storage.close()


async def test_matching_channels_respects_priority_pause_and_dedup(tmp_path: Path) -> None:
    storage = BotStorage(tmp_path / "bot.db")
    await storage.initialize()
    try:
        await storage.subscribe(2001, "cve", Priority.HIGH)
        await storage.subscribe(2001, "all", Priority.LOW)

        await storage.subscribe(2002, "cve", Priority.CRITICAL)

        await storage.subscribe(2003, "cve", Priority.LOW)
        await storage.set_paused(2003, True)

        assert await storage.get_matching_channels("cve", Priority.HIGH.weight) == [2001]
        assert await storage.get_matching_channels("cve", Priority.CRITICAL.weight) == [2001, 2002]

        await storage.set_paused(2003, False)
        assert not await storage.is_paused(2003)
        assert await storage.get_matching_channels("cve", Priority.LOW.weight) == [2001, 2003]
    finally:
        await storage.close()


async def test_dispatched_deduplication_and_watermark(tmp_path: Path) -> None:
    storage = BotStorage(tmp_path / "bot.db")
    await storage.initialize()
    try:
        assert await storage.get_last_item_id() is None
        await storage.set_last_item_id(15)
        await storage.set_last_item_id(10)
        assert await storage.get_last_item_id() == 15

        assert not await storage.was_dispatched(1001, 99)
        await storage.mark_dispatched(1001, 99)
        await storage.mark_dispatched(1001, 99)
        assert await storage.was_dispatched(1001, 99)

        await storage.mark_dispatched(1001, 100)
        await storage._db().execute(
            "UPDATE dispatched_items SET dispatched_at = ? WHERE item_id = ?",
            ("2020-01-01T00:00:00+00:00", 99),
        )
        await storage._db().commit()

        deleted = await storage.prune_dispatched(retention_days=30)
        assert deleted == 1
        assert await storage.was_dispatched(1001, 99) is False
        assert await storage.was_dispatched(1001, 100) is True
    finally:
        await storage.close()
