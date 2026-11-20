"""Slash commands de gestión del canal (/subscribe, /unsubscribe, /filters, /pause, /resume)."""

from __future__ import annotations

import discord
from discord import app_commands

from src.api_client import WebApiUnavailableError
from src.commands import PRIORITY_CHOICES, BotAppContext, resolve_priority_arg
from src.embeds import build_filters_embed
from src.models import Priority
from src.permissions import can_manage_subscriptions

_DENIED_MSG = "⛔ Este comando está restringido a administradores del canal o del bot."
_NO_CHANNEL_MSG = "❌ No se pudo identificar el canal actual."
_API_UNAVAILABLE_MSG = (
    "⚠️ No se pudo validar el tipo con la API de **beacon-sift**. "
    "Inténtalo de nuevo en unos instantes."
)


def register_subscription_commands(
    tree: app_commands.CommandTree[discord.Client],
    ctx: BotAppContext,
) -> None:
    """Registra los 5 comandos de gestión de suscripciones en el árbol de Discord."""

    @tree.command(
        name="subscribe",
        description="Suscribe el canal actual a un tipo de fuente (o 'all') y prioridad mínima",
    )
    @app_commands.describe(
        type="Tipo de fuente (ej: cve, linux) o 'all' para todas",
        min_priority="Prioridad mínima a recibir (por defecto: low)",
    )
    @app_commands.choices(min_priority=PRIORITY_CHOICES)
    async def subscribe_cmd(
        interaction: discord.Interaction,
        type: str,
        min_priority: app_commands.Choice[str] | None = None,
    ) -> None:
        if not can_manage_subscriptions(interaction, ctx.settings):
            await interaction.response.send_message(_DENIED_MSG, ephemeral=True)
            return

        if interaction.channel_id is None:
            await interaction.response.send_message(_NO_CHANNEL_MSG, ephemeral=True)
            return

        target_type = type.strip().lower()
        if not target_type:
            await interaction.response.send_message(
                "❌ Debes indicar un tipo válido o `all`.\n"
                "Uso esperado: `/subscribe <type|all> [min_priority]`",
                ephemeral=True,
            )
            return

        resolved_prio = Priority.LOW
        if min_priority is not None:
            parsed = resolve_priority_arg(min_priority)
            if parsed is None:
                await interaction.response.send_message(
                    "❌ Prioridad inválida. Valores válidos: `low`, `medium`, `high`, `critical`.",
                    ephemeral=True,
                )
                return
            resolved_prio = parsed

        await interaction.response.defer(ephemeral=False)

        if target_type != "all":
            try:
                types, _ = await ctx.api_client.get_types()
            except WebApiUnavailableError:
                await interaction.followup.send(_API_UNAVAILABLE_MSG)
                return

            valid_types = {t.type for t in types}
            if target_type not in valid_types:
                available = ", ".join(sorted(valid_types)) or "ninguno"
                await interaction.followup.send(
                    f"❌ El tipo `{target_type}` no existe.\n"
                    f"Tipos disponibles: `{available}` (o `all`)."
                )
                return

        await ctx.storage.subscribe(
            interaction.channel_id,
            target_type,
            resolved_prio,
            guild_id=interaction.guild_id,
            name=getattr(interaction.channel, "name", None),
        )
        await interaction.followup.send(
            f"✅ Suscripción guardada para `{target_type}` con prioridad mínima "
            f"{resolved_prio.emoji} `{resolved_prio.value}`."
        )

    @tree.command(
        name="unsubscribe",
        description="Elimina la suscripción del canal actual para un tipo o 'all'",
    )
    @app_commands.describe(type="Tipo de fuente a eliminar o 'all' para borrar todas")
    async def unsubscribe_cmd(interaction: discord.Interaction, type: str) -> None:
        if not can_manage_subscriptions(interaction, ctx.settings):
            await interaction.response.send_message(_DENIED_MSG, ephemeral=True)
            return

        if interaction.channel_id is None:
            await interaction.response.send_message(_NO_CHANNEL_MSG, ephemeral=True)
            return

        target_type = type.strip().lower()
        if not target_type:
            await interaction.response.send_message(
                "❌ Uso esperado: `/unsubscribe <type|all>`",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=False)
        removed = await ctx.storage.unsubscribe(interaction.channel_id, target_type)

        if removed == 0:
            await interaction.followup.send(
                f"No había ninguna suscripción activa para `{target_type}` en este canal."
            )
            return

        if target_type == "all":
            await interaction.followup.send(
                f"🗑️ Eliminadas todas las suscripciones ({removed}) de este canal."
            )
        else:
            await interaction.followup.send(
                f"🗑️ Suscripción eliminada para `{target_type}` en este canal."
            )

    @tree.command(
        name="filters",
        description="Muestra las suscripciones y filtros activos en el canal actual",
    )
    async def filters_cmd(interaction: discord.Interaction) -> None:
        if interaction.channel_id is None:
            await interaction.response.send_message(_NO_CHANNEL_MSG, ephemeral=True)
            return

        await interaction.response.defer()
        subs = await ctx.storage.list_subscriptions(interaction.channel_id)
        paused = await ctx.storage.is_paused(interaction.channel_id)
        await interaction.followup.send(embed=build_filters_embed(subs, paused))

    @tree.command(
        name="pause",
        description="Pausa temporalmente el envío automático de alertas en el canal actual",
    )
    async def pause_cmd(interaction: discord.Interaction) -> None:
        if not can_manage_subscriptions(interaction, ctx.settings):
            await interaction.response.send_message(_DENIED_MSG, ephemeral=True)
            return

        if interaction.channel_id is None:
            await interaction.response.send_message(_NO_CHANNEL_MSG, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)
        await ctx.storage.set_paused(
            interaction.channel_id,
            True,
            guild_id=interaction.guild_id,
            name=getattr(interaction.channel, "name", None),
        )
        await interaction.followup.send(
            "⏸️ Alertas automáticas pausadas en este canal. Los filtros se mantienen guardados."
        )

    @tree.command(
        name="resume",
        description="Reanuda el envío automático de alertas en el canal actual",
    )
    async def resume_cmd(interaction: discord.Interaction) -> None:
        if not can_manage_subscriptions(interaction, ctx.settings):
            await interaction.response.send_message(_DENIED_MSG, ephemeral=True)
            return

        if interaction.channel_id is None:
            await interaction.response.send_message(_NO_CHANNEL_MSG, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)
        await ctx.storage.set_paused(
            interaction.channel_id,
            False,
            guild_id=interaction.guild_id,
            name=getattr(interaction.channel, "name", None),
        )
        await interaction.followup.send("▶️ Alertas automáticas reanudadas en este canal.")
