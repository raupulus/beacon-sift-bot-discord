"""Tests unitarios para el control de permisos en servidores y DMs de Discord."""

from __future__ import annotations

from types import SimpleNamespace

from src.config import Settings
from src.permissions import can_manage_subscriptions


def _make_interaction(
    *,
    guild: object | None = object(),
    administrator: bool = False,
    manage_channels: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        guild=guild,
        permissions=SimpleNamespace(administrator=administrator, manage_channels=manage_channels),
    )


def test_guild_permissions_allow_admin_or_manage_channels_only() -> None:
    settings = Settings()

    assert can_manage_subscriptions(_make_interaction(administrator=True), settings) is True
    assert can_manage_subscriptions(_make_interaction(manage_channels=True), settings) is True
    assert can_manage_subscriptions(_make_interaction(), settings) is False


def test_dm_permissions_follow_allow_dm_subscriptions_flag() -> None:
    i_dm = _make_interaction(guild=None)

    assert can_manage_subscriptions(i_dm, Settings(allow_dm_subscriptions=False)) is False
    assert can_manage_subscriptions(i_dm, Settings(allow_dm_subscriptions=True)) is True
