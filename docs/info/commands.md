# Comandos del bot y de desarrollo (`commands.md`)

Referencia verificada directamente contra [`src/commands/__init__.py`](../../src/commands/__init__.py), [`src/commands/info.py`](../../src/commands/info.py), [`src/commands/subscriptions.py`](../../src/commands/subscriptions.py), [`pyproject.toml`](../../pyproject.toml) y [`docker-compose.yml`](../../docker-compose.yml).

---

## 1. *Slash commands* de Discord (`CommandTree`)

Los **11 *slash commands*** se registran mediante `register_commands(tree, app_ctx)` dentro de `setup_hook()` ([`src/main.py`](../../src/main.py)) y se sincronizan en `DISCORD_DEV_GUILD_ID` (si está definido) o globalmente, manteniendo paridad funcional exacta con el bot hermano `beacon-sift-bot-telegram`.

### Comandos públicos de información y consulta (`src/commands/info.py`)

| Comando | Parámetros y tipos | Permisos | Respuesta y validaciones reales | Si API `web/` no responde |
|---|---|---|---|---|
| `/help` | *(ninguno)* | Todos | Respuesta inmediata (`send_message`) con `build_help_embed()`. | No depende de `web/`. |
| `/status` | *(ninguno)* | Todos | `defer()` + `get_status()` + `followup.send(embed=build_status_embed(...))`. | Devuelve Embed rojo (`ERROR_COLOR`) con estado degradado y WS Reverb. |
| `/sources` | `type: str \| None = None` | Todos | `defer()`; normaliza `type` a minúsculas si no está vacío; envía `build_sources_embed()`. | `followup.send(_API_UNAVAILABLE_MSG)`. |
| `/types` | *(ninguno)* | Todos | `defer()` + `get_types()` + `build_types_embed()`. | `followup.send(_API_UNAVAILABLE_MSG)`. |
| `/latest` | `type: str \| None = None`, `priority: Choice[str] \| None = None` (`PRIORITY_CHOICES`), `limit: int = 5` | Todos | Valida `1 <= limit <= 10` y prioridad antes de `defer()`; error responde `ephemeral=True`. Luego `defer()` y `build_news_list_embed()`. | `followup.send(_API_UNAVAILABLE_MSG)`. |
| `/search` | `query: str`, `type: str \| None = None`, `limit: int = 5` | Todos | Valida `query.strip()` no vacío y `1 <= limit <= 10` (`ephemeral=True` si falla). Luego `defer()` y `build_news_list_embed()`. | `followup.send(_API_UNAVAILABLE_MSG)`. |

### Comandos de gestión del canal (`src/commands/subscriptions.py`)

| Comando | Parámetros y tipos | Permisos | Validaciones y flujo | Efecto en SQLite (`data/bot.db`) |
|---|---|---|---|---|
| `/subscribe` | `type: str`, `min_priority: Choice[str] \| None = None` (`PRIORITY_CHOICES`) | Admin (`can_manage_subscriptions`) | Si no tiene permisos o `channel_id is None`, responde `ephemeral=True`. Valida `type` no vacío y `min_priority` (defecto `low`). Luego `defer(ephemeral=False)`; si `type != "all"`, valida contra `/api/v1/types`. | `UPSERT` en `channels` + `subscriptions` para `channel_id`. |
| `/unsubscribe` | `type: str` | Admin (`can_manage_subscriptions`) | Valida permisos, `channel_id` y `type` no vacío (`ephemeral=True` si falla). Luego `defer(ephemeral=False)` y borra esa regla o todas (`all`). | `DELETE` en `subscriptions` para `channel_id`. |
| `/filters` | *(ninguno)* | Todos en el canal | Valida `channel_id`; luego `defer()` y `followup.send(embed=build_filters_embed(...))`. | Solo lectura SQLite (`list_subscriptions` + `is_paused`). |
| `/pause` | *(ninguno)* | Admin (`can_manage_subscriptions`) | Valida permisos y `channel_id` (`ephemeral=True` si falla). Luego `defer(ephemeral=False)` y pausa entregas conservando filtros. | Marca `is_paused = 1` en `channels`. |
| `/resume` | *(ninguno)* | Admin (`can_manage_subscriptions`) | Valida permisos y `channel_id` (`ephemeral=True` si falla). Luego `defer(ephemeral=False)` y reanuda entregas. | Marca `is_paused = 0` en `channels`. |

> **Nota sobre `PRIORITY_CHOICES`:** en Discord se muestran las 4 opciones (`Baja (low)`, `Media (medium)`, `Alta (high)`, `Crítica (critical)`) definidas en [`src/commands/__init__.py`](../../src/commands/__init__.py).

### Contrato compartido de paridad y formato mínimo

Principios obligatorios compartidos entre `beacon-sift-bot-discord` y `beacon-sift-bot-telegram`:

1. **Paridad exacta de catálogo:** los 11 comandos mantienen los mismos nombres lógicos, semántica de filtros (`type`, `priority`, `query`, `limit` `1..10` con defecto `5`) y reglas de autorización. No deben existir comandos huérfanos en una sola plataforma salvo excepción documentada.
2. **Formato mínimo por noticia entregada (*Embed*):**
   - Color HUD lateral según prioridad (`low=0x64748B`, `medium=0x38BDF8`, `high=0xF59E0B`, `critical=0xEF4444`).
   - Titular enlazado directamente a la URL original (`http`/`https`).
   - Fuente (`source`), tipo (`type`) y prioridad (`priority`).
   - Fecha de publicación (`timestamp` nativo de Discord en alertas; `BOT_TIMEZONE` en listados).
   - Extracto breve (*snippet*) limpio y truncado bajo los límites oficiales de Discord.
3. **Reglas unificadas de respuesta y errores:**
   - **Sin resultados:** responder claramente indicando que no hay elementos para los filtros aplicados.
   - **API `web/` no disponible:** responder con mensaje amigable (`_API_UNAVAILABLE_MSG` o *Embed* `ERROR_COLOR` en `/status`) sin exponer trazas ni secretos, registrando el fallo en inglés en `logger.warning`.
   - **Parámetros inválidos:** responder en `ephemeral=True` indicando qué parámetro es incorrecto y el uso esperado.

---

## 2. Comandos de desarrollo, calidad y ejecución local (`uv`)

Ejecutar siempre dentro de `bot-discord/` (`uv` respeta `.python-version = 3.12`):

| Objetivo | Comando | Resultado esperado |
|---|---|---|
| Instalar / sincronizar entorno | `uv sync --python 3.12` | Crea/actualiza `.venv` desde `uv.lock`. |
| Linter (Ruff) | `uv run ruff check src tests` | `All checks passed!` (reglas `E`, `F`, `I`, `UP`, `B`, `SIM`, máx. 100 columnas). |
| Verificación de formato | `uv run ruff format --check src tests` | `19 files already formatted` (o todos formateados). |
| Suite de tests | `uv run pytest` | `14 passed` (6 módulos de test en `tests/`, `asyncio_mode = "auto"`). |
| Arrancar el bot en local | `uv run python -m src.main` | Lee `.env`, inicializa SQLite, conecta Gateway + Reverb. Aborta con código `1` si falta `DISCORD_BOT_TOKEN`. |

---

## 3. Comandos Docker / Docker Compose

| Objetivo | Comando | Notas |
|---|---|---|
| Construir imagen local | `docker build -t beacon-sift-bot-discord .` | Imagen basada en `python:3.12-slim`, ejecuta como `botuser`. |
| Levantar servicio | `docker compose up -d --build` | Requiere `.env` en `bot-discord/` y monta `./data:/app/data`. |
| Ver logs en vivo | `docker compose logs -f bot-discord` | `bot.run(..., log_handler=None)` usa el logger raíz configurado por `configure_logging()`. |
| Parar servicio | `docker compose down` | Conserva `./data/bot.db` en el host. |

Más detalles de despliegue en [`docs/deploys/docker.md`](../deploys/docker.md).

---

> Creado: 2026-11-20 · Última revisión: 2026-11-21
