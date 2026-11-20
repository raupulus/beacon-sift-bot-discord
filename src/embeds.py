"""Constructores de Discord Embeds con paleta radar HUD (DESIGN.md)."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord

from src.models import ApiStatus, NewsItem, Priority, SourceInfo, Subscription, TypeInfo

BRAND_COLOR = 0x38BDF8
LIVE_COLOR = 0x10B981
WARN_COLOR = 0xF59E0B
ERROR_COLOR = 0xEF4444


def safe_http_url(url: str | None) -> str | None:
    """Valida que la URL tenga esquema HTTP o HTTPS antes de incrustarla en un Embed."""
    if not url:
        return None
    clean = url.strip()
    parsed = urlparse(clean)
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        return clean
    return None


def _get_zone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def format_datetime(dt: datetime | None, timezone_name: str = "Europe/Madrid") -> str:
    """Formatea una fecha en dd/mm/YYYY HH:MM según la zona horaria."""
    if dt is None:
        return "Fecha desconocida"
    return dt.astimezone(_get_zone(timezone_name)).strftime("%d/%m/%Y %H:%M")


def _truncate(text: str, max_chars: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "…"


def _escape_md_label(text: str) -> str:
    return text.replace("[", "\\[").replace("]", "\\]")


def build_news_embed(item: NewsItem, *, show_thumbnail: bool = True) -> discord.Embed:
    """Construye un Embed limpio de noticia cumpliendo BOT_COMMANDS_CONTRACT.md y DESIGN.md."""
    title = _truncate(item.title or "Sin titular", 250)
    safe_url = safe_http_url(item.url)
    description = _truncate(item.snippet, 350) if item.snippet else None

    embed = discord.Embed(
        title=title,
        url=safe_url,
        description=description,
        color=discord.Color(item.priority.color_int),
        timestamp=item.published_at,
    )

    source_name = item.source.name if item.source else "Fuente externa"
    embed.add_field(name="Fuente", value=_truncate(source_name, 100), inline=True)
    embed.add_field(name="Tipo", value=f"`#{item.type or 'general'}`", inline=True)
    embed.add_field(
        name="Prioridad",
        value=f"{item.priority.emoji} {item.priority.label_es}",
        inline=True,
    )

    if show_thumbnail:
        safe_thumb = safe_http_url(item.image_url)
        if safe_thumb is not None:
            embed.set_thumbnail(url=safe_thumb)

    embed.set_footer(text="beacon-sift · feed.raupulus.dev")
    return embed


def build_news_list_embed(
    items: list[NewsItem],
    header: str,
    timezone_name: str = "Europe/Madrid",
) -> discord.Embed:
    """Construye un Embed listado compacto para /latest y /search bajo límite de Discord."""
    lines: list[str] = []
    current_len = 0

    for idx, item in enumerate(items, start=1):
        title_clean = _escape_md_label(_truncate(item.title or "Sin titular", 140))
        safe_url = safe_http_url(item.url)
        title_md = f"[{title_clean}]({safe_url})" if safe_url else f"**{title_clean}**"
        source_name = item.source.name if item.source else "Fuente externa"
        date_str = format_datetime(item.published_at, timezone_name)
        meta = (
            f"{item.priority.emoji} `#{item.type}` · {item.priority.value} · "
            f"*{source_name}* · {date_str}"
        )
        block = f"**{idx}.** {title_md}\n{meta}"
        if item.snippet:
            block += f"\n> {_truncate(item.snippet, 120)}"

        if current_len + len(block) + 2 > 3800:
            break
        lines.append(block)
        current_len += len(block) + 2

    embed = discord.Embed(
        title=_truncate(header, 250),
        description="\n\n".join(lines),
        color=discord.Color(BRAND_COLOR),
    )
    embed.set_footer(text="beacon-sift · feed.raupulus.dev")
    return embed


def build_help_embed() -> discord.Embed:
    """Catálogo oficial de comandos de BOT_COMMANDS_CONTRACT.md."""
    embed = discord.Embed(
        title="beacon-sift · Comandos disponibles",
        description="Agregador de noticias y alertas en tiempo real (`feed.raupulus.dev`).",
        color=discord.Color(BRAND_COLOR),
    )
    embed.add_field(
        name="Consultas públicas",
        value=(
            "• `/help` — Muestra esta ayuda.\n"
            "• `/status` — Estado del bot, WebSocket Reverb y API web.\n"
            "• `/sources [type]` — Lista las fuentes activas.\n"
            "• `/types` — Lista tipos disponibles y prioridades válidas.\n"
            "• `/latest [type] [priority] [limit]` — Últimas noticias (default 5, máx. 10).\n"
            "• `/search <query> [type] [limit]` — Busca por palabra clave."
        ),
        inline=False,
    )
    embed.add_field(
        name="Suscripciones del canal (Administradores)",
        value=(
            "• `/subscribe <type|all> [min_priority]` — Suscribe el canal actual.\n"
            "• `/unsubscribe <type|all>` — Elimina una o todas las suscripciones.\n"
            "• `/filters` — Muestra los filtros activos del canal actual.\n"
            "• `/pause` — Pausa las alertas automáticas sin borrar filtros.\n"
            "• `/resume` — Reanuda las alertas automáticas.\n\n"
            "Prioridades válidas: `low`, `medium`, `high`, `critical`."
        ),
        inline=False,
    )
    embed.set_footer(text="beacon-sift · feed.raupulus.dev")
    return embed


def build_status_embed(
    api_status: ApiStatus | None,
    ws_connected: bool,
    last_event_at: datetime | None,
    timezone_name: str = "Europe/Madrid",
) -> discord.Embed:
    """Embed de estado del bot, WebSocket Reverb y API web."""
    ws_state = "🟢 Conectado" if ws_connected else "🟡 Desconectado (reintentando)"
    last_ev = format_datetime(last_event_at, timezone_name) if last_event_at else "Sin eventos aún"

    if api_status is None:
        embed = discord.Embed(
            title="Estado de beacon-sift",
            description="La API web no está disponible en este momento.",
            color=discord.Color(ERROR_COLOR),
        )
        embed.add_field(name="Bot Discord", value="🟢 Operativo", inline=True)
        embed.add_field(name="WebSocket Reverb", value=ws_state, inline=True)
        embed.add_field(name="Última alerta en vivo", value=last_ev, inline=False)
        embed.set_footer(text="beacon-sift · feed.raupulus.dev")
        return embed

    color = LIVE_COLOR if (api_status.status == "ok" and ws_connected) else WARN_COLOR
    last_sync = (
        format_datetime(api_status.last_sync_at, timezone_name)
        if api_status.last_sync_at
        else "Pendiente"
    )
    embed = discord.Embed(
        title="Estado de beacon-sift",
        color=discord.Color(color),
    )
    embed.add_field(name="Bot Discord", value="🟢 Operativo", inline=True)
    embed.add_field(
        name="API web",
        value=f"{'🟢 OK' if api_status.status == 'ok' else '🟠 ' + api_status.status} "
        f"(BD: `{api_status.database}`)",
        inline=True,
    )
    embed.add_field(
        name="WebSocket Reverb",
        value=f"{ws_state}\nCanal: `{api_status.ws_channel}`",
        inline=True,
    )
    embed.add_field(
        name="Fuentes activas",
        value=f"{api_status.sources_active} / {api_status.sources_total} "
        f"(con fallos: {api_status.sources_failing})",
        inline=True,
    )
    embed.add_field(name="Noticias indexadas", value=str(api_status.items_total), inline=True)
    embed.add_field(name="Última sincronización", value=last_sync, inline=True)
    embed.add_field(name="Última alerta en vivo", value=last_ev, inline=False)
    embed.set_footer(text="beacon-sift · feed.raupulus.dev")
    return embed


def build_sources_embed(
    sources: list[SourceInfo],
    filter_type: str | None = None,
) -> discord.Embed:
    """Embed listado de fuentes activas (/sources)."""
    title = f"Fuentes activas (#{filter_type})" if filter_type else "Fuentes activas"
    if not sources:
        msg = (
            f"No hay fuentes activas para el tipo `{filter_type}`."
            if filter_type
            else "No hay fuentes activas configuradas en este momento."
        )
        return discord.Embed(title=title, description=msg, color=discord.Color(WARN_COLOR))

    lines: list[str] = []
    total_len = 0
    for src in sources:
        health = "🟢" if src.consecutive_failures == 0 else "🟠"
        safe_url = safe_http_url(src.url)
        label = _escape_md_label(src.name)
        link = f"[{label}]({safe_url})" if safe_url else label
        row = f"{health} {link} — `#{src.type}` · {src.priority.value} · {src.interval_minutes}m"
        if total_len + len(row) + 1 > 3800:
            lines.append("*… listado truncado por límite de Discord.*")
            break
        lines.append(row)
        total_len += len(row) + 1

    embed = discord.Embed(
        title=f"{title} ({len(sources)})",
        description="\n".join(lines),
        color=discord.Color(BRAND_COLOR),
    )
    embed.set_footer(text="beacon-sift · feed.raupulus.dev")
    return embed


def build_types_embed(types: list[TypeInfo], priorities: list[Priority]) -> discord.Embed:
    """Embed de tipos disponibles y niveles de prioridad (/types)."""
    type_lines = (
        "\n".join(
            f"• `{t.type}` — {t.sources_count} fuente(s), {t.items_count} noticia(s)" for t in types
        )
        if types
        else "• *No hay tipos activos disponibles ahora mismo.*"
    )
    prio_lines = "\n".join(f"• {p.emoji} `{p.value}` ({p.label_es})" for p in priorities)

    embed = discord.Embed(
        title="Tipos y prioridades disponibles",
        color=discord.Color(BRAND_COLOR),
    )
    embed.add_field(name="Tipos de fuente", value=_truncate(type_lines, 1000), inline=False)
    embed.add_field(name="Niveles de prioridad", value=prio_lines, inline=False)
    embed.set_footer(text="beacon-sift · feed.raupulus.dev")
    return embed


def build_filters_embed(subscriptions: list[Subscription], paused: bool) -> discord.Embed:
    """Embed con los filtros y estado activo/pausado del canal actual (/filters)."""
    state_label = "⏸️ Pausado (usa `/resume` para reanudar)" if paused else "▶️ Activo"
    color = WARN_COLOR if paused else LIVE_COLOR

    if not subscriptions:
        embed = discord.Embed(
            title="Filtros del canal actual",
            description=(
                f"**Estado:** {state_label}\n\n"
                "No hay suscripciones activas en este canal.\n"
                "Usa `/subscribe <type|all> [min_priority]` para configurarlas."
            ),
            color=discord.Color(color),
        )
        embed.set_footer(text="beacon-sift · feed.raupulus.dev")
        return embed

    rows = "\n".join(
        f"• `{sub.source_type}` — prioridad mínima: {sub.min_priority.emoji} "
        f"`{sub.min_priority.value}` ({sub.min_priority.label_es})"
        for sub in subscriptions
    )
    embed = discord.Embed(
        title="Filtros del canal actual",
        description=f"**Estado:** {state_label}\n\n{rows}",
        color=discord.Color(color),
    )
    embed.set_footer(text="beacon-sift · feed.raupulus.dev")
    return embed
