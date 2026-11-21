# Módulo `config-y-modelos`

> Ficheros cubiertos: [`src/config.py`](../../src/config.py), [`src/models.py`](../../src/models.py), [`.env.example`](../../.env.example)

## 1. Qué hace y qué NO hace

- **Hace:**
  - Carga y normaliza las 12 variables de entorno del bot mediante `pydantic-settings` (`Settings`).
  - Parsea `DISCORD_DEV_GUILD_ID` (`int | None`) tolerando valores vacíos o no numéricos.
  - Define la enumeración `Priority` (`low`, `medium`, `high`, `critical`) con `weight`, `label_es`, `emoji`, `color_int` (colores HUD) y `parse()`.
  - Define los DTOs inmutables (`frozen=True, slots=True`) para deserializar respuestas JSON de `web/` y suscripciones locales (`SourceSummary`, `NewsItem`, `SourceInfo`, `TypeInfo`, `ApiStatus`, `Subscription`).
- **NO hace:**
  - No abre conexiones ni valida en `__init__` que `DISCORD_BOT_TOKEN` no esté vacío (se comprueba en `main()`).

---

## 2. Modelo de datos

### `Priority` (`StrEnum` en `src/models.py`)

| Miembro | Valor | `weight` | `label_es` | `emoji` | `color_int` (hex) |
|---|---|---|---|---|---|
| `Priority.LOW` | `"low"` | `1` | `"Baja"` | `⚪` | `0x64748B` |
| `Priority.MEDIUM` | `"medium"` | `2` | `"Media"` | `🔵` | `0x38BDF8` |
| `Priority.HIGH` | `"high"` | `3` | `"Alta"` | `🟠` | `0xF59E0B` |
| `Priority.CRITICAL` | `"critical"` | `4` | `"Crítica"` | `🔴` | `0xEF4444` |

### DTOs (`src/models.py`)

- `SourceSummary(slug, name, url)` — fuente asociada a una noticia (`name` cae a `slug` o `"Fuente externa"`).
- `NewsItem(id, title, url, type, priority, priority_weight, published_at, fetched_at, snippet=None, image_url=None, author=None, tags=[], source=None)`
- `SourceInfo(slug, name, url, format, type, priority, interval_minutes, is_active, last_fetched_at=None, last_success_at=None, consecutive_failures=0)`
- `TypeInfo(type, sources_count, items_count)`
- `ApiStatus(status, database, last_sync_at, sources_active, sources_failing, sources_total, items_total, ws_channel, ws_event)`
- `Subscription(channel_id, source_type, min_priority, min_priority_weight)`

---

## 3. Flujos principales

1. `Settings()` lee `.env` (`UTF-8`, `extra="ignore"`), recorta `/` final en `web_api_base_url` / `reverb_ws_url` y normaliza `log_level` a mayúsculas.
2. `*.from_api_dict(data)` transforma los JSON recibidos de `web/` y normaliza timestamps ISO (`Z` → `+00:00`, fallback `UTC` si llegan sin zona) vía `_parse_iso_datetime()`.

---

## 4. Puntos de entrada (con auth, permisos y límites)

- `Settings` + propiedad `dev_guild_id -> int | None`.
- `Priority.parse(value: str | None) -> Priority | None` y métodos `from_api_dict()` en cada DTO.

> `NewsItem.from_api_dict` requiere `data["id"]` convertible a `int` (lanza `KeyError` o `ValueError` si falta o no es entero).

---

## 5. Dependencias en ambos sentidos

- **Depende de:** `pydantic`, `pydantic-settings`, librería estándar (`dataclasses`, `datetime`, `enum`).
- **Consumido por:** `storage.py`, `api_client.py`, `reverb_client.py`, `embeds.py`, `permissions.py`, `dispatcher.py`, `commands/*` y `main.py`.

---

## 6. Configuración (variables, valor por defecto y efecto)

Declaradas en [`src/config.py`](../../src/config.py) y [`.env.example`](../../.env.example):

| Variable (`.env`) | Atributo `Settings` | Valor por defecto | Efecto |
|---|---|---|---|
| `DISCORD_BOT_TOKEN` | `discord_bot_token` | `""` | Token del bot; `main()` aborta con `exit(1)` si está vacío. |
| `DISCORD_DEV_GUILD_ID` | `discord_dev_guild_id` | `""` | Snowflake opcional para sincronizar comandos en un servidor de pruebas al arrancar. |
| `ALLOW_DM_SUBSCRIPTIONS` | `allow_dm_subscriptions` | `False` | Permite (`true`) o deniega (`false`) configurar alertas por DM. |
| `DISCORD_SHOW_THUMBNAILS` | `discord_show_thumbnails` | `True` | Añade `thumbnail` al *Embed* de alerta cuando `image_url` es HTTP/HTTPS válido. |
| `WEB_API_BASE_URL` | `web_api_base_url` | `"http://127.0.0.1:8000"` | URL base HTTP de `web/`. |
| `WEB_API_TIMEOUT_SECONDS` | `web_api_timeout_seconds` | `10.0` | Timeout de `httpx` contra `web/`. |
| `REVERB_WS_URL` | `reverb_ws_url` | `"ws://127.0.0.1:8080"` | URL base WebSocket de Laravel Reverb. |
| `REVERB_APP_KEY` | `reverb_app_key` | `"beacon-sift-public-key"` | Clave pública de Reverb. |
| `REVERB_CHANNEL` | `reverb_channel` | `"beacon.news"` | Canal público suscrito. |
| `BOT_DB_PATH` | `bot_db_path` | `"data/bot.db"` | Ruta a SQLite local (`Dockerfile` fija `/app/data/bot.db`). |
| `BOT_TIMEZONE` | `bot_timezone` | `"Europe/Madrid"` | Zona horaria IANA usada en listados y `/status` de `embeds.py`. |
| `LOG_LEVEL` | `log_level` | `"INFO"` | Nivel raíz de logging (`DEBUG`, `INFO`, `WARNING`, etc.). |

---

## 7. Trampas conocidas

- **Valores inválidos ignorados silenciosamente:** `dev_guild_id` ignora valores no enteros devolviendo `None` (un error tipográfico en `DISCORD_DEV_GUILD_ID` haría sincronizar globalmente sin aviso).
- **Fallback silencioso en `NewsItem.from_api_dict`:** una prioridad desconocida desde la API cae a `Priority.LOW`.

---

## 8. Tests que lo cubren

- [`tests/test_main_and_config.py`](../../tests/test_main_and_config.py) — verifica normalización de URLs/`log_level`, `Settings.dev_guild_id` y `_parse_iso_datetime()`.
- [`tests/test_api_client.py`](../../tests/test_api_client.py), [`tests/test_embeds.py`](../../tests/test_embeds.py), [`tests/test_dispatcher.py`](../../tests/test_dispatcher.py), [`tests/test_commands.py`](../../tests/test_commands.py) ejercitan `Settings`, `Priority` (`color_int`, `weight`, `parse`), zona horaria y los DTOs.

---

## 9. Pendiente real

- Ninguno actualmente.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-21
