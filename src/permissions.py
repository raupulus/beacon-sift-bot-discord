"""Control de permisos para comandos de suscripción y gestión de canal en Discord."""

from __future__ import annotations

import discord

from src.config import Settings


def can_manage_subscriptions(interaction: discord.Interaction, settings: Settings) -> bool:
    """Comprueba si el usuario tiene permiso de administración sobre el canal o el bot."""
    if interaction.user.id in settings.admin_ids:
        return True

    if interaction.guild is None:
        return settings.allow_dm_subscriptions

    perms = interaction.permissions
    return bool(perms.administrator or perms.manage_channels)
