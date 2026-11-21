"""Tests unitarios para configuración, parseo de fechas y setup_hook de Discord."""

from __future__ import annotations

import asyncio
from datetime import UTC
from pathlib import Path
from typing import Any

from src.config import Settings
from src.main import BeaconDiscordBot
from src.models import _parse_iso_datetime


def test_settings_normalization_dev_guild_and_iso_datetime() -> None:
    settings = Settings(
        discord_dev_guild_id=" 123456789012345678 ",
        web_api_base_url="https://feed.raupulus.dev///",
        reverb_ws_url="wss://feed.raupulus.dev/",
        log_level=" debug ",
    )
    assert settings.dev_guild_id == 123456789012345678
    assert settings.web_api_base_url == "https://feed.raupulus.dev"
    assert settings.reverb_ws_url == "wss://feed.raupulus.dev"
    assert settings.log_level == "DEBUG"

    assert Settings(discord_dev_guild_id="invalid").dev_guild_id is None
    assert Settings(discord_dev_guild_id="").dev_guild_id is None

    dt_z = _parse_iso_datetime("2026-11-21T10:00:00Z")
    assert dt_z is not None and dt_z.tzinfo == UTC
    dt_naive = _parse_iso_datetime("2026-11-21T10:00:00")
    assert dt_naive is not None and dt_naive.tzinfo == UTC
    assert _parse_iso_datetime("invalid-date") is None
    assert _parse_iso_datetime(None) is None


async def test_setup_hook_initializes_prunes_syncs_and_closes(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    settings = Settings(
        discord_bot_token="FAKE_TOKEN",
        bot_db_path=str(tmp_path / "bot.db"),
    )
    bot = BeaconDiscordBot(settings)

    synced: list[Any] = []
    reverb_started = asyncio.Event()

    async def fake_sync(*, guild: Any = None) -> list[Any]:
        synced.append(guild)
        return []

    async def fake_run_forever(stop_event: asyncio.Event) -> None:
        reverb_started.set()
        await stop_event.wait()

    monkeypatch.setattr(bot.tree, "sync", fake_sync)
    monkeypatch.setattr(bot.reverb_listener, "run_forever", fake_run_forever)

    await bot.setup_hook()
    await asyncio.wait_for(reverb_started.wait(), timeout=2.0)

    assert synced == [None]
    assert (tmp_path / "bot.db").exists()
    assert len(bot.tree.get_commands()) == 11

    await bot.close()
    assert bot._reverb_task is not None and bot._reverb_task.done()
