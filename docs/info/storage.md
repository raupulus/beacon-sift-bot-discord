# Módulo `storage`

> Ficheros cubiertos: [`src/storage.py`](../../src/storage.py)

## 1. Qué hace y qué NO hace

- **Hace:**
  - Persiste de forma asíncrona en SQLite (`aiosqlite`, modo `WAL`, `foreign_keys=ON`) canales, suscripciones, estado de pausa, deduplicación de envíos y cursor global `last_processed_item_id`.
- **NO hace:**
  - No accede a PostgreSQL de `web/`, no guarda textos de noticias ni credenciales.
  - No ejecuta poda periódica automática de `dispatched_items` en segundo plano (aunque implementa `prune_dispatched()`).

---

## 2. Modelo de datos

Esquema creado por `BotStorage.initialize()` ([`src/storage.py#L34-L71`](../../src/storage.py#L34-L71)):

| Tabla | Clave primaria | Columnas relevantes | Notas |
|---|---|---|---|
| `channels` | `channel_id INTEGER` | `guild_id INTEGER`, `name TEXT`, `is_paused INTEGER DEFAULT 0`, `created_at TEXT`, `updated_at TEXT` | `guild_id` y `name` pueden ser `NULL` en DMs o actualizaciones sin contexto de servidor. |
| `subscriptions` | `(channel_id, source_type)` | `min_priority TEXT`, `min_priority_weight INTEGER`, `created_at TEXT` | `FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE`. |
| `bot_state` | `key TEXT` | `value TEXT` | Guarda `'last_processed_item_id'`. |
| `dispatched_items` | `(channel_id, item_id)` | `dispatched_at TEXT` | Índice `idx_dispatched_at` sobre `(dispatched_at)`. |

---

## 3. Flujos principales

1. **`initialize()`:** crea el directorio padre salvo `:memory:`, activa `WAL` y `foreign_keys=ON`, y ejecuta `CREATE TABLE IF NOT EXISTS`.
2. **`subscribe()` / `set_paused()`:** ejecutan `_ensure_channel(channel_id, guild_id, name)` preservando valores previos si `excluded.guild_id` o `excluded.name` llegan como `NULL` (`COALESCE`).
3. **`get_matching_channels(item_type, priority_weight)`:** devuelve `SELECT DISTINCT s.channel_id` de `subscriptions` ⋈ `channels` donde `is_paused = 0`, `min_priority_weight <= priority_weight` y `source_type IN (item_type, 'all')`.
4. **`was_dispatched` / `mark_dispatched`:** evitan duplicados usando clave `(channel_id, item_id)` e `INSERT OR IGNORE`.
5. **`set_last_item_id`:** monotónico creciente; ignora IDs `<= current`.

---

## 4. Puntos de entrada (con auth, permisos y límites)

Clase `BotStorage(db_path: str | Path)`:
- `initialize()`, `close()`
- `subscribe()`, `unsubscribe()` (soporta `'all'` devolviendo `cursor.rowcount`), `list_subscriptions()` (ordena `'all'` primero y luego alfabéticamente), `set_paused()`, `is_paused()`, `get_matching_channels()`
- `was_dispatched()`, `mark_dispatched()`, `prune_dispatched(keep_last=5000)`, `get_last_item_id()`, `set_last_item_id()`

---

## 5. Dependencias en ambos sentidos

- **Depende de:** `aiosqlite`, [`src/models.py`](../../src/models.py) (`Priority`, `Subscription`), `pathlib`, `datetime`.
- **Consumido por:** [`src/main.py`](../../src/main.py), [`src/dispatcher.py`](../../src/dispatcher.py), [`src/reverb_client.py`](../../src/reverb_client.py), [`src/commands/subscriptions.py`](../../src/commands/subscriptions.py).

---

## 6. Configuración (variables, valor por defecto y efecto)

| Variable (`.env`) | Atributo `Settings` | Valor por defecto | Efecto |
|---|---|---|---|
| `BOT_DB_PATH` | `bot_db_path` | `"data/bot.db"` | Ruta del fichero SQLite (`Dockerfile` fija `/app/data/bot.db`). |

---

## 7. Trampas conocidas

- **Uso antes de `initialize()`:** `_db()` lanza `RuntimeError("BotStorage no inicializado; llama antes a initialize().")`.
- **Diferencia entre `subscribe(..., 'all', ...)` y `unsubscribe(..., 'all')`:** la primera crea una regla `'all'`; la segunda elimina **todas** las suscripciones del `channel_id`.
- **Crecimiento indefinido de `dispatched_items`:** `prune_dispatched(keep_last=5000)` existe y pasa tests, pero **ningún módulo en `src/` lo invoca periódicamente aún**.
- **Sin sistema de migraciones:** cambios futuros de esquema sobre `data/bot.db` existente requerirán migración explícita (`ALTER TABLE`).

---

## 8. Tests que lo cubren

- [`tests/test_storage.py`](../../tests/test_storage.py):
  - `test_subscribe_update_and_unsubscribe`
  - `test_matching_channels_respects_priority_pause_and_dedup`
  - `test_dispatched_deduplication_and_watermark`

---

## 9. Pendiente real

- Invocar `storage.prune_dispatched()` periódicamente (por ejemplo al arrancar en `setup_hook()` o tras un número dado de alertas enviadas) para acotar el tamaño de `dispatched_items`.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
