"""Motor de distribución selectiva de alertas hacia los canales de Discord suscritos."""

from __future__ import annotations

import logging
from typing import Any

import discord

from src.config import Settings
from src.embeds import build_news_embed
from src.models import NewsItem
from src.storage import BotStorage

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """Evalúa suscripciones en SQLite, deduplica y envía Embeds a Discord."""

    def __init__(self, client: Any, storage: BotStorage, settings: Settings) -> None:
        self.client = client
        self.storage = storage
        self.settings = settings

    async def dispatch_item(self, item: NewsItem) -> int:
        """Envía una noticia nueva a todos los canales que cumplan tipo, prioridad y pausa."""
        channel_ids = await self.storage.get_matching_channels(item.type, item.priority_weight)
        if not channel_ids:
            return 0

        embed = build_news_embed(item, show_thumbnail=self.settings.discord_show_thumbnails)
        delivered = 0

        for channel_id in channel_ids:
            if await self.storage.was_dispatched(channel_id, item.id):
                continue

            sent = await self._send_to_channel(channel_id, embed)
            if sent:
                await self.storage.mark_dispatched(channel_id, item.id)
                delivered += 1

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
                "Sin acceso o canal inexistente (%s); pausando alertas automáticas.",
                channel_id,
            )
            await self.storage.set_paused(channel_id, True)
            return False
        except discord.HTTPException as exc:
            logger.warning("Error HTTP de Discord enviando a canal %s: %s", channel_id, exc)
            return False
