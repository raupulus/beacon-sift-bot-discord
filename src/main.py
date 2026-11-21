"""Punto de entrada principal de beacon-sift-bot-discord."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sys

import discord
from discord import app_commands

from src.api_client import BeaconApiClient
from src.commands import BotAppContext, register_commands
from src.config import Settings
from src.dispatcher import AlertDispatcher
from src.reverb_client import ReverbListener
from src.storage import BotStorage

logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    """Configura logging estándar legible para consola y Docker."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


class BeaconDiscordBot(discord.Client):
    """Cliente de Discord que coordina CommandTree, SQLite, API v1 y Reverb."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(intents=discord.Intents.default())
        self.settings = settings
        self.tree = app_commands.CommandTree(self)
        self.storage = BotStorage(settings.bot_db_path)
        self.api_client = BeaconApiClient(
            base_url=settings.web_api_base_url,
            timeout_seconds=settings.web_api_timeout_seconds,
        )
        self.dispatcher = AlertDispatcher(self, self.storage, settings)
        self.reverb_listener = ReverbListener(
            ws_url=settings.reverb_ws_url,
            app_key=settings.reverb_app_key,
            channel=settings.reverb_channel,
            api_client=self.api_client,
            storage=self.storage,
            on_item=self.dispatcher.dispatch_item,
        )
        self.app_ctx = BotAppContext(
            settings=settings,
            storage=self.storage,
            api_client=self.api_client,
            dispatcher=self.dispatcher,
            reverb_listener=self.reverb_listener,
        )
        self._stop_event = asyncio.Event()
        self._reverb_task: asyncio.Task[None] | None = None

    async def setup_hook(self) -> None:
        """Inicializa SQLite, registra/sincroniza los 11 slash commands y arranca Reverb."""
        await self.storage.initialize()
        register_commands(self.tree, self.app_ctx)

        if self.settings.dev_guild_id is not None:
            guild = discord.Object(id=self.settings.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("Slash commands synced to dev guild %s.", self.settings.dev_guild_id)
        else:
            await self.tree.sync()
            logger.info("Slash commands synced globally.")

        self._reverb_task = asyncio.create_task(
            self.reverb_listener.run_forever(self._stop_event),
            name="reverb-listener",
        )

    async def on_ready(self) -> None:
        logger.info("Discord bot connected as %s", self.user)

    async def close(self) -> None:
        """Detiene Reverb y cierra recursos de red y SQLite ordenadamente."""
        self._stop_event.set()
        if self._reverb_task is not None:
            self._reverb_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reverb_task
        await self.api_client.close()
        await self.storage.close()
        await super().close()
        logger.info("beacon-sift-bot-discord resources closed.")


def main() -> None:
    """Arranca el bot de Discord."""
    settings = Settings()
    configure_logging(settings.log_level)

    if not settings.discord_bot_token.strip():
        logger.error("Missing DISCORD_BOT_TOKEN in environment (.env). Aborting startup.")
        sys.exit(1)

    bot = BeaconDiscordBot(settings)
    bot.run(settings.discord_bot_token, log_handler=None)


if __name__ == "__main__":
    main()
