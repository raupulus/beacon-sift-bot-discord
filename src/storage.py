"""Persistencia local en SQLite para suscripciones por canal, pausa y deduplicación."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from src.models import Priority, Subscription


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class BotStorage:
    """Almacenamiento async en SQLite para el estado independiente del bot de Discord."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Abre la conexión y crea el esquema SQLite si no existe."""
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = await aiosqlite.connect(str(self.db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")

        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                name TEXT,
                is_paused INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                channel_id INTEGER NOT NULL,
                source_type TEXT NOT NULL,
                min_priority TEXT NOT NULL,
                min_priority_weight INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (channel_id, source_type),
                FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dispatched_items (
                channel_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                dispatched_at TEXT NOT NULL,
                PRIMARY KEY (channel_id, item_id)
            );

            CREATE INDEX IF NOT EXISTS idx_dispatched_at
                ON dispatched_items (dispatched_at);
            """
        )
        await self._conn.commit()

    async def close(self) -> None:
        """Cierra la conexión SQLite abierta."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    def _db(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("BotStorage no inicializado; llama antes a initialize().")
        return self._conn

    async def _ensure_channel(
        self,
        channel_id: int,
        guild_id: int | None = None,
        name: str | None = None,
    ) -> None:
        now = _utc_now_iso()
        await self._db().execute(
            """
            INSERT INTO channels (channel_id, guild_id, name, is_paused, created_at, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                guild_id = COALESCE(excluded.guild_id, channels.guild_id),
                name = COALESCE(excluded.name, channels.name),
                updated_at = excluded.updated_at
            """,
            (channel_id, guild_id, name, now, now),
        )

    async def subscribe(
        self,
        channel_id: int,
        source_type: str,
        min_priority: Priority,
        guild_id: int | None = None,
        name: str | None = None,
    ) -> None:
        """Crea o actualiza una suscripción para el canal."""
        normalized_type = source_type.strip().lower()
        now = _utc_now_iso()
        await self._ensure_channel(channel_id, guild_id, name)
        await self._db().execute(
            """
            INSERT INTO subscriptions (
                channel_id, source_type, min_priority, min_priority_weight, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(channel_id, source_type) DO UPDATE SET
                min_priority = excluded.min_priority,
                min_priority_weight = excluded.min_priority_weight
            """,
            (channel_id, normalized_type, min_priority.value, min_priority.weight, now),
        )
        await self._db().commit()

    async def unsubscribe(self, channel_id: int, source_type: str) -> int:
        """Elimina una suscripción específica o todas si source_type == 'all'."""
        normalized_type = source_type.strip().lower()
        if normalized_type == "all":
            cursor = await self._db().execute(
                "DELETE FROM subscriptions WHERE channel_id = ?",
                (channel_id,),
            )
        else:
            cursor = await self._db().execute(
                "DELETE FROM subscriptions WHERE channel_id = ? AND source_type = ?",
                (channel_id, normalized_type),
            )
        await self._db().commit()
        return cursor.rowcount

    async def list_subscriptions(self, channel_id: int) -> list[Subscription]:
        """Lista las suscripciones configuradas en un canal."""
        cursor = await self._db().execute(
            """
            SELECT channel_id, source_type, min_priority, min_priority_weight
            FROM subscriptions
            WHERE channel_id = ?
            ORDER BY CASE WHEN source_type = 'all' THEN 0 ELSE 1 END, source_type ASC
            """,
            (channel_id,),
        )
        rows = await cursor.fetchall()
        result: list[Subscription] = []
        for row in rows:
            priority = Priority.parse(str(row["min_priority"])) or Priority.LOW
            result.append(
                Subscription(
                    channel_id=int(row["channel_id"]),
                    source_type=str(row["source_type"]),
                    min_priority=priority,
                    min_priority_weight=int(row["min_priority_weight"]),
                )
            )
        return result

    async def set_paused(
        self,
        channel_id: int,
        paused: bool,
        guild_id: int | None = None,
        name: str | None = None,
    ) -> None:
        """Pausa o reanuda el envío automático de alertas en el canal."""
        await self._ensure_channel(channel_id, guild_id, name)
        await self._db().execute(
            """
            UPDATE channels
            SET is_paused = ?, updated_at = ?
            WHERE channel_id = ?
            """,
            (1 if paused else 0, _utc_now_iso(), channel_id),
        )
        await self._db().commit()

    async def is_paused(self, channel_id: int) -> bool:
        """Indica si el canal tiene pausadas las alertas automáticas."""
        cursor = await self._db().execute(
            "SELECT is_paused FROM channels WHERE channel_id = ?",
            (channel_id,),
        )
        row = await cursor.fetchone()
        return bool(row["is_paused"]) if row is not None else False

    async def get_matching_channels(self, item_type: str, priority_weight: int) -> list[int]:
        """Devuelve IDs de canales activos (no pausados) que coinciden sin duplicados."""
        normalized_type = item_type.strip().lower()
        cursor = await self._db().execute(
            """
            SELECT DISTINCT s.channel_id
            FROM subscriptions s
            INNER JOIN channels c ON c.channel_id = s.channel_id
            WHERE c.is_paused = 0
              AND s.min_priority_weight <= ?
              AND s.source_type IN (?, 'all')
            ORDER BY s.channel_id ASC
            """,
            (priority_weight, normalized_type),
        )
        rows = await cursor.fetchall()
        return [int(row["channel_id"]) for row in rows]

    async def was_dispatched(self, channel_id: int, item_id: int) -> bool:
        """Comprueba si una noticia ya fue enviada al canal."""
        cursor = await self._db().execute(
            """
            SELECT 1 FROM dispatched_items
            WHERE channel_id = ? AND item_id = ?
            LIMIT 1
            """,
            (channel_id, item_id),
        )
        return await cursor.fetchone() is not None

    async def mark_dispatched(self, channel_id: int, item_id: int) -> None:
        """Registra una noticia como enviada al canal."""
        await self._db().execute(
            """
            INSERT OR IGNORE INTO dispatched_items (channel_id, item_id, dispatched_at)
            VALUES (?, ?, ?)
            """,
            (channel_id, item_id, _utc_now_iso()),
        )
        await self._db().commit()

    async def prune_dispatched(self, keep_last: int = 5000) -> int:
        """Conserva únicamente los últimos N registros de deduplicación."""
        cursor = await self._db().execute(
            """
            DELETE FROM dispatched_items
            WHERE rowid NOT IN (
                SELECT rowid FROM dispatched_items
                ORDER BY dispatched_at DESC, rowid DESC
                LIMIT ?
            )
            """,
            (max(0, keep_last),),
        )
        await self._db().commit()
        return cursor.rowcount

    async def get_last_item_id(self) -> int | None:
        """Lee el último ID de noticia procesado en tiempo real/catch-up."""
        cursor = await self._db().execute(
            "SELECT value FROM bot_state WHERE key = 'last_processed_item_id'"
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        try:
            return int(row["value"])
        except ValueError:
            return None

    async def set_last_item_id(self, item_id: int) -> None:
        """Actualiza el cursor de último ID procesado (solo avanza si es mayor)."""
        current = await self.get_last_item_id()
        if current is not None and item_id <= current:
            return
        await self._db().execute(
            """
            INSERT INTO bot_state (key, value)
            VALUES ('last_processed_item_id', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(item_id),),
        )
        await self._db().commit()
