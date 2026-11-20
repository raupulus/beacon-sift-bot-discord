"""Registro de los 11 slash commands definidos en BOT_COMMANDS_CONTRACT.md."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord
from discord import app_commands

from src.api_client import BeaconApiClient
from src.config import Settings
from src.dispatcher import AlertDispatcher
from src.models import Priority
from src.storage import BotStorage

if TYPE_CHECKING:
    from src.reverb_client import ReverbListener

PRIORITY_CHOICES: list[app_commands.Choice[str]] = [
    app_commands.Choice(name="Baja (low)", value=Priority.LOW.value),
    app_commands.Choice(name="Media (medium)", value=Priority.MEDIUM.value),
    app_commands.Choice(name="Alta (high)", value=Priority.HIGH.value),
    app_commands.Choice(name="Crítica (critical)", value=Priority.CRITICAL.value),
]


@dataclass(slots=True)
class BotAppContext:
    """Dependencias compartidas inyectadas en los comandos de Discord."""

    settings: Settings
    storage: BotStorage
    api_client: BeaconApiClient
    dispatcher: AlertDispatcher
    reverb_listener: ReverbListener


def resolve_priority_arg(raw: app_commands.Choice[str] | str | None) -> Priority | None:
    """Normaliza un parámetro de prioridad recibido como Choice o str."""
    if raw is None:
        return None
    value = raw.value if isinstance(raw, app_commands.Choice) else str(raw)
    return Priority.parse(value)


def register_commands(tree: app_commands.CommandTree[discord.Client], ctx: BotAppContext) -> None:
    """Registra exactamente los 11 comandos de BOT_COMMANDS_CONTRACT.md sin comandos huérfanos."""
    from src.commands.info import register_info_commands
    from src.commands.subscriptions import register_subscription_commands

    register_info_commands(tree, ctx)
    register_subscription_commands(tree, ctx)
