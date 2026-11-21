"""Motor de distribución selectiva de alertas hacia los canales de Discord suscritos."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import discord

from src.config import Settings
from src.embeds import build_news_embed
from src.models import NewsItem
from src.storage import BotStorage

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """Evalúa suscripciones en SQLite, deduplica y envía Embeds a Discord."""

    def __init__(
        self,
        client: Any,
        storage: BotStorage,
        settings: Settings,
        *,
        prune_every: int = 250,
        prune_retention_days: int = 30,
        max_concurrency: int = 10,
        min_interval_seconds: float = 0.04,
    ) -> None:
        self.client = client
        self.storage = storage
        self.settings = settings
        self.prune_every = max(1, prune_every)
        self.prune_retention_days = max(0, prune_retention_days)
        self.max_concurrency = max(1, max_concurrency)
        self.min_interval_seconds = max(0.0, min_interval_seconds)
        self._delivered_since_prune = 0
        self._rate_lock = asyncio.Lock()
        self._next_send_at = 0.0

    async def _acquire_rate_slot(self) -> None:
        """Regula la cadencia global de envíos para evitar ráfagas hacia Discord."""
        if self.min_interval_seconds <= 0:
            return
        async with self._rate_lock:
            now = time.monotonic()
            if now < self._next_send_at:
                await asyncio.sleep(self._next_send_at - now)
                now = time.monotonic()
            self._next_send_at = now + self.min_interval_seconds

    async def dispatch_item(self, item: NewsItem) -> int:
        """Envía una noticia nueva a todos los canales que cumplan tipo, prioridad y pausa."""
        channel_ids = await self.storage.get_matching_channels(item.type, item.priority_weight)
        if not channel_ids:
            return 0

        embed = build_news_embed(item, show_thumbnail=self.settings.discord_show_thumbnails)
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _deliver_one(channel_id: int) -> bool:
            async with semaphore:
                if await self.storage.was_dispatched(channel_id, item.id):
                    return False

                await self._acquire_rate_slot()
                sent = await self._send_to_channel(channel_id, embed)
                if not sent:
                    return False

                await self.storage.mark_dispatched(channel_id, item.id)
                return True

        results = await asyncio.gather(*(_deliver_one(cid) for cid in channel_ids))
        delivered = sum(1 for ok in results if ok)

        if delivered > 0:
            self._delivered_since_prune += delivered
            if self._delivered_since_prune >= self.prune_every:
                self._delivered_since_prune = 0
                await self.storage.prune_dispatched(retention_days=self.prune_retention_days)

        return delivered

    async def _send_to_channel(self, channel_id: int, embed: discord.Embed) -> bool:
        try:
            channel = self.client.get_channel(channel_id)
            if channel is None:
                channel = await self.client.fetch_channel(channel_id)
            await channel.send(embed=embed)
            return True
        except (discord.Forbidden, discord.NotFound):
            logger.warning(
                "Missing access or unknown channel (%s); pausing automatic alerts.",
                channel_id,
            )
            await self.storage.set_paused(channel_id, True)
            return False
        except discord.HTTPException as exc:
            logger.warning("Discord HTTP error sending to channel %s: %s", channel_id, exc)
            return False
