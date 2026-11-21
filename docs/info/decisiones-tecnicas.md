# Decisiones técnicas (`decisiones-tecnicas.md`)

Registro de decisiones deliberadas de arquitectura e implementación en `beacon-sift-bot-discord` cuyo porqué conviene preservar para evitar regresiones o "correcciones" accidentales.

---

## 1. Persistencia local en SQLite WAL desacoplada de `web/`

- **Decisión:** El bot guarda canales, suscripciones, *watermark* y deduplicación en SQLite local (`BOT_DB_PATH=data/bot.db` con `PRAGMA journal_mode=WAL;`) vía `aiosqlite`.
- **Motivo:** Regla estricta de aislamiento entre servicios de `beacon-sift`: `bot-discord/` no importa código de `web/` ni accede a su PostgreSQL; consume únicamente los 4 `GET /api/v1/*` y el canal WebSocket público de Reverb.

---

## 2. `discord.Intents.default()` sin intents privilegiados

- **Decisión:** `BeaconDiscordBot` hereda de `discord.Client` instanciado con `intents=discord.Intents.default()`, manteniendo desactivados `message_content`, `members` y `presences`.
- **Motivo:** El bot opera exclusivamente con *slash commands* (`INTERACTION_CREATE`) y envío por `channel_id`, por lo que no necesita leer mensajes de texto ni requerir aprobación especial de intents privilegiados en Discord Developer Portal al escalar a >= 100 servidores.

---

## 3. Uso obligatorio de `defer()` antes de consultar `web/`

- **Decisión:** Salvo `/help` y los rechazos síncronos de permisos o parámetros (`ephemeral=True`), todos los comandos llaman primero a `await interaction.response.defer(...)` y responden por `interaction.followup.send(...)`.
- **Motivo:** Discord invalida la interacción si no recibe acuse inicial en **3 segundos** ([`docs/apis/discord-api/ERRATAS.md`](../apis/discord-api/ERRATAS.md)). Cualquier latencia puntual de la API de `web/` causaría errores sin `defer()`.

---

## 4. `DISCORD_DEV_GUILD_ID` para sincronización instantánea en desarrollo

- **Decisión:** Si `DISCORD_DEV_GUILD_ID` está configurado en `.env`, `setup_hook()` hace `tree.copy_global_to(guild=...)` y `tree.sync(guild=...)`; si no, ejecuta `tree.sync()` global.
- **Motivo:** La sincronización global de *slash commands* en Discord puede tardar en propagarse a clientes, mientras que la sincronización acotada a un servidor de desarrollo es inmediata y agiliza pruebas.

---

## 5. *Embeds* con paleta HUD y sin re-alojar imágenes de prensa

- **Decisión:** [`src/embeds.py`](../../src/embeds.py) asigna el color lateral del *Embed* según la prioridad (`low=#64748B`, `medium=#38BDF8`, `high=#F59E0B`, `critical=#EF4444`) alineado con `DESIGN.md` de `web/`, y si `DISCORD_SHOW_THUMBNAILS=true` pasa `item.image_url` directamente a `embed.set_thumbnail(url=...)` previa validación HTTP/HTTPS.
- **Motivo:** Respeta las directrices legales de agregación responsable sin descargar ni re-hospedar imágenes de terceros.

---

## 6. *Watermark* inicial en arranque + *catch-up* por `since_id`

- **Decisión:** Si `bot_state` no tiene `last_processed_item_id`, `ReverbListener.run_catchup()` toma el último `id` de `/api/v1/items?order=desc&per_page=1` como cursor sin emitir histórico retroactivo. En reconexiones siguientes recupera lo emitido desde `since_id` en orden `asc` (hasta `max_pages=10` páginas de `50`).
- **Motivo:** Evita inundar canales suscritos con todo el histórico al iniciar contra una instancia `web/` existente y previene ráfagas contra rate limits de Discord.

---

## 7. Auto-pausa ante `discord.Forbidden` o `discord.NotFound`

- **Decisión:** Si `fetch_channel()` o `channel.send()` lanza `Forbidden` (`403`) o `NotFound` (`404`), `AlertDispatcher` marca `is_paused = 1` en SQLite sin borrar `subscriptions`.
- **Motivo:** Además de permitir recuperar filtros si se restaura acceso con `/resume`, evita repetir errores `403` en cada noticia nueva y protege frente al límite de **10 000 peticiones inválidas cada 10 minutos** de Discord (Cloudflare IP ban).

---

## 8. Python `3.12` fijado, logging propio unificado y logs en inglés

- **Decisión de runtime:** Python `3.12` fijado en `.python-version` y `Dockerfile` (`python:3.12-slim`); evita la eliminación de `audioop` de Python `3.13` que dispara aviso de deprecación en `discord/player.py`.
- **Decisión de logging:** `bot.run(token, log_handler=None)` evita que `discord.py` duplique handlers sobre `logging.basicConfig()`. Documentación, comentarios y textos al usuario en **español**; identificadores, ficheros y mensajes `logger.*` en **inglés**.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
