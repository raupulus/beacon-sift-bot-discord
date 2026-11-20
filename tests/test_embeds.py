"""Tests unitarios para constructores de Discord Embeds."""

from __future__ import annotations

from datetime import UTC, datetime

from src.embeds import (
    BRAND_COLOR,
    build_filters_embed,
    build_help_embed,
    build_news_embed,
    build_news_list_embed,
    build_sources_embed,
    build_status_embed,
    build_types_embed,
)
from src.models import (
    ApiStatus,
    NewsItem,
    Priority,
    SourceInfo,
    SourceSummary,
    Subscription,
    TypeInfo,
)


def test_build_news_embed_sets_priority_color_limits_and_thumbnail() -> None:
    long_title = "T" * 300
    long_snippet = "Resumen " * 100
    item = NewsItem(
        id=10,
        title=long_title,
        url="https://www.debian.org/security/2026/dsa-10",
        type="cve",
        priority=Priority.CRITICAL,
        priority_weight=4,
        published_at=datetime(2026, 11, 20, 14, 0, tzinfo=UTC),
        fetched_at=datetime(2026, 11, 20, 14, 5, tzinfo=UTC),
        snippet=long_snippet,
        image_url="https://cdn.example.org/thumb.png",
        source=SourceSummary(slug="debian", name="Debian Security", url="https://debian.org"),
    )

    embed = build_news_embed(item, show_thumbnail=True)

    assert embed.color is not None
    assert embed.color.value == Priority.CRITICAL.color_int
    assert embed.title is not None
    assert len(embed.title) <= 250
    assert embed.description is not None
    assert len(embed.description) <= 350
    assert embed.thumbnail.url == "https://cdn.example.org/thumb.png"
    assert len(embed.fields) == 3

    embed_no_thumb = build_news_embed(item, show_thumbnail=False)
    assert embed_no_thumb.thumbnail.url is None


def test_build_news_embed_rejects_unsafe_urls() -> None:
    item = NewsItem(
        id=1,
        title="Unsafe",
        url="javascript:alert(1)",
        type="news",
        priority=Priority.LOW,
        priority_weight=1,
        published_at=None,
        fetched_at=None,
        image_url="data:image/png;base64,abc",
    )

    embed = build_news_embed(item, show_thumbnail=True)
    assert embed.url is None
    assert embed.thumbnail.url is None


def test_build_catalog_embeds() -> None:
    help_embed = build_help_embed()
    assert help_embed.color is not None and help_embed.color.value == BRAND_COLOR
    assert len(help_embed.fields) == 2

    status = ApiStatus(
        status="ok",
        database="ok",
        last_sync_at=datetime(2026, 11, 20, 15, 0, tzinfo=UTC),
        sources_active=2,
        sources_failing=0,
        sources_total=2,
        items_total=40,
        ws_channel="beacon.news",
        ws_event="news.created",
    )
    status_ok = build_status_embed(status, True, None)
    assert status_ok.title == "Estado de beacon-sift"
    status_down = build_status_embed(None, False, None)
    assert "no está disponible" in (status_down.description or "")

    sources_embed = build_sources_embed(
        [
            SourceInfo(
                slug="debian-security",
                name="Debian [Sec]",
                url="https://www.debian.org/security/dsa",
                format="rss",
                type="cve",
                priority=Priority.HIGH,
                interval_minutes=30,
                is_active=True,
            )
        ],
        "cve",
    )
    assert "Debian \\[Sec\\]" in (sources_embed.description or "")

    types_embed = build_types_embed(
        [TypeInfo(type="cve", sources_count=1, items_count=40)],
        list(Priority),
    )
    assert len(types_embed.fields) == 2

    filters_embed = build_filters_embed(
        [
            Subscription(
                channel_id=123,
                source_type="cve",
                min_priority=Priority.HIGH,
                min_priority_weight=3,
            )
        ],
        paused=False,
    )
    assert "Activo" in (filters_embed.description or "")

    list_embed = build_news_list_embed(
        [
            NewsItem(
                id=5,
                title="[CVE-2026-1] Advisory",
                url="https://example.org/5",
                type="cve",
                priority=Priority.HIGH,
                priority_weight=3,
                published_at=datetime(2026, 11, 20, 12, 0, tzinfo=UTC),
                fetched_at=None,
                snippet="Extracto",
            )
        ],
        "Últimas noticias",
    )
    assert "\\[CVE-2026-1\\]" in (list_embed.description or "")
