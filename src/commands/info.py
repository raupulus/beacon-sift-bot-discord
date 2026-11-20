"""Slash commands públicos (/help, /status, /sources, /types, /latest, /search)."""

from __future__ import annotations

import discord
from discord import app_commands

from src.api_client import WebApiUnavailableError
from src.commands import PRIORITY_CHOICES, BotAppContext, resolve_priority_arg
from src.embeds import (
    build_help_embed,
    build_news_list_embed,
    build_sources_embed,
    build_status_embed,
    build_types_embed,
)

_API_UNAVAILABLE_MSG = (
    "⚠️ La API de **beacon-sift** no está disponible en este momento. "
    "Inténtalo de nuevo en unos instantes."
)


def register_info_commands(
    tree: app_commands.CommandTree[discord.Client],
    ctx: BotAppContext,
) -> None:
    """Registra los 6 comandos de información y consulta en el árbol de Discord."""

    @tree.command(name="help", description="Muestra la lista de comandos disponibles y su uso")
    async def help_cmd(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=build_help_embed())

    @tree.command(name="status", description="Indica el estado del bot, WebSocket Reverb y API web")
    async def status_cmd(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            api_status = await ctx.api_client.get_status()
        except WebApiUnavailableError:
            api_status = None

        embed = build_status_embed(
            api_status=api_status,
            ws_connected=ctx.reverb_listener.is_connected,
            last_event_at=ctx.reverb_listener.last_event_at,
            timezone_name=ctx.settings.bot_timezone,
        )
        await interaction.followup.send(embed=embed)

    @tree.command(name="sources", description="Lista las fuentes configuradas activas")
    @app_commands.describe(type="Filtrar fuentes por tipo (ej: cve, linux)")
    async def sources_cmd(
        interaction: discord.Interaction,
        type: str | None = None,
    ) -> None:
        await interaction.response.defer()
        clean_type = type.strip().lower() if type and type.strip() else None
        try:
            sources = await ctx.api_client.get_sources(source_type=clean_type)
        except WebApiUnavailableError:
            await interaction.followup.send(_API_UNAVAILABLE_MSG)
            return

        await interaction.followup.send(embed=build_sources_embed(sources, clean_type))

    @tree.command(
        name="types",
        description="Lista los tipos de fuente disponibles y niveles de prioridad válidos",
    )
    async def types_cmd(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            types, priorities = await ctx.api_client.get_types()
        except WebApiUnavailableError:
            await interaction.followup.send(_API_UNAVAILABLE_MSG)
            return

        await interaction.followup.send(embed=build_types_embed(types, priorities))

    @tree.command(
        name="latest",
        description="Devuelve las últimas noticias filtrables por tipo y prioridad mínima",
    )
    @app_commands.describe(
        type="Tipo de fuente opcional (ej: cve, linux)",
        priority="Prioridad mínima opcional",
        limit="Número de noticias a mostrar (entre 1 y 10; por defecto 5)",
    )
    @app_commands.choices(priority=PRIORITY_CHOICES)
    async def latest_cmd(
        interaction: discord.Interaction,
        type: str | None = None,
        priority: app_commands.Choice[str] | None = None,
        limit: int = 5,
    ) -> None:
        if limit < 1 or limit > 10:
            await interaction.response.send_message(
                "❌ El parámetro `limit` debe estar entre **1** y **10**.\n"
                "Uso esperado: `/latest [type] [priority] [limit]`",
                ephemeral=True,
            )
            return

        parsed_priority = None
        if priority is not None:
            parsed_priority = resolve_priority_arg(priority)
            if parsed_priority is None:
                await interaction.response.send_message(
                    "❌ Prioridad inválida. Valores válidos: `low`, `medium`, `high`, `critical`.\n"
                    "Uso esperado: `/latest [type] [priority] [limit]`",
                    ephemeral=True,
                )
                return

        clean_type = type.strip().lower() if type and type.strip() else None
        await interaction.response.defer()

        try:
            items = await ctx.api_client.get_items(
                source_type=clean_type,
                min_priority=parsed_priority,
                per_page=limit,
            )
        except WebApiUnavailableError:
            await interaction.followup.send(_API_UNAVAILABLE_MSG)
            return

        if not items:
            await interaction.followup.send(
                "No hay noticias disponibles para los filtros indicados."
            )
            return

        header = "Últimas noticias"
        if clean_type:
            header += f" · #{clean_type}"
        if parsed_priority:
            header += f" · >={parsed_priority.value}"

        embed = build_news_list_embed(items, header, ctx.settings.bot_timezone)
        await interaction.followup.send(embed=embed)

    @tree.command(name="search", description="Busca noticias por palabra clave")
    @app_commands.describe(
        query="Palabras clave a buscar",
        type="Tipo de fuente opcional para acotar la búsqueda",
        limit="Número de resultados (entre 1 y 10; por defecto 5)",
    )
    async def search_cmd(
        interaction: discord.Interaction,
        query: str,
        type: str | None = None,
        limit: int = 5,
    ) -> None:
        clean_query = query.strip()
        if not clean_query:
            await interaction.response.send_message(
                "❌ Debes indicar un término de búsqueda `<query>`.\n"
                "Uso esperado: `/search <query> [type] [limit]`",
                ephemeral=True,
            )
            return

        if limit < 1 or limit > 10:
            await interaction.response.send_message(
                "❌ El parámetro `limit` debe estar entre **1** y **10**.\n"
                "Uso esperado: `/search <query> [type] [limit]`",
                ephemeral=True,
            )
            return

        clean_type = type.strip().lower() if type and type.strip() else None
        await interaction.response.defer()

        try:
            items = await ctx.api_client.get_items(
                source_type=clean_type,
                query=clean_query,
                per_page=limit,
            )
        except WebApiUnavailableError:
            await interaction.followup.send(_API_UNAVAILABLE_MSG)
            return

        if not items:
            await interaction.followup.send(f"No se encontraron noticias para `{clean_query}`.")
            return

        header = f"Resultados para '{clean_query}'"
        if clean_type:
            header += f" · #{clean_type}"

        embed = build_news_list_embed(items, header, ctx.settings.bot_timezone)
        await interaction.followup.send(embed=embed)
