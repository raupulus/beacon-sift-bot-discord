# Módulo `dispatcher`

> Ficheros cubiertos: [`src/dispatcher.py`](../../src/dispatcher.py)

## 1. Qué hace y qué NO hace

- **Hace:**
  - Resuelve en `BotStorage` los canales activos (`is_paused = 0`) suscritos al `type` y con `min_priority_weight <= item.priority_weight`.
  - Reparte de forma concurrente y acotada (`max_concurrency=10`, cadencia global `min_interval_seconds=0.04` ≈ 25 msg/s) para escalar a cientos/miles de canales sin bloqueos secuenciales.
  - Evita duplicados comprobando y registrando `(channel_id, item.id)` en `dispatched_items`, y dispara poda periódica por antigüedad (`prune_dispatched(retention_days=30)`) cada `prune_every` entregas (por defecto `250`).
  - Construye un único `discord.Embed` por noticia y lo envía resolviendo el canal desde caché (`get_channel`) o por API (`fetch_channel`).
  - Auto-pausa el canal si recibe `discord.Forbidden` o `discord.NotFound`, conservando sus filtros.
- **NO hace:**
  - No gestiona colas persistentes ni reintentos diferidos propios tras un `discord.HTTPException` no recuperado por `discord.py`.
  - No comprueba permisos `EMBED_LINKS` ni `SEND_MESSAGES_IN_THREADS` antes de intentar `channel.send()`.

---

## 2. Modelo de datos

No define tablas ni modelos propios; consume `NewsItem` ([`src/models.py`](../../src/models.py)), `BotStorage` y `discord.Embed`.

---

## 3. Flujos principales

1. `dispatch_item(item: NewsItem) -> int`:
   - Llama a `await self.storage.get_matching_channels(item.type, item.priority_weight)`. Si está vacío, devuelve `0`.
   - Construye `embed = build_news_embed(item, show_thumbnail=self.settings.discord_show_thumbnails)`.
   - Lanza `_deliver_one(channel_id)` concurrentemente con `asyncio.Semaphore(self.max_concurrency)` y regulación global `_acquire_rate_slot()`:
     - Si `await self.storage.was_dispatched(channel_id, item.id)` → omite.
     - Llama a `_send_to_channel(channel_id, embed)`.
     - Si devuelve `True` → `await self.storage.mark_dispatched(channel_id, item.id)`.
   - Al terminar el lote, acumula `delivered` y dispara `prune_dispatched(retention_days=self.prune_retention_days)` cada `prune_every` entregas.
2. `_send_to_channel(channel_id, embed)`:
   - Intenta `channel = self.client.get_channel(channel_id)`.
   - Si es `None` (no está en caché del Gateway o DM/hilo sin cachear), ejecuta `channel = await self.client.fetch_channel(channel_id)`.
   - Envía `await channel.send(embed=embed)` y retorna `True`.
   - Ante `discord.Forbidden` o `discord.NotFound`: registra log `WARNING` en inglés, llama a `await self.storage.set_paused(channel_id, True)` y retorna `False`.
   - Ante `discord.HTTPException`: registra `WARNING` en inglés y retorna `False`.

---

## 4. Puntos de entrada (con auth, permisos y límites)

- `AlertDispatcher(client, storage, settings, *, prune_every=250, prune_retention_days=30, max_concurrency=10, min_interval_seconds=0.04)`
- `async def dispatch_item(self, item: NewsItem) -> int` *(invocado como callback `on_item` desde `ReverbListener`)*

---

## 5. Dependencias en ambos sentidos

- **Depende de:** `discord` (`Forbidden`, `NotFound`, `HTTPException`, `Embed`), [`src/config.py`](../../src/config.py), [`src/embeds.py`](../../src/embeds.py), [`src/models.py`](../../src/models.py), [`src/storage.py`](../../src/storage.py), [`docs/apis/discord-api/mensajeria-y-embeds.md`](../apis/discord-api/mensajeria-y-embeds.md).
- **Consumido por:** [`src/main.py`](../../src/main.py) (inyectado como `on_item` de `ReverbListener`).

---

## 6. Configuración (variables, valor por defecto y efecto)

| Variable (`.env`) | Atributo `Settings` | Valor por defecto | Efecto |
|---|---|---|---|
| `DISCORD_SHOW_THUMBNAILS` | `discord_show_thumbnails` | `True` | Decide si el Embed de alerta incluye `thumbnail` cuando la noticia trae `image_url`. |

---

## 7. Trampas conocidas

- **Rate limits `429` delegados en `discord.py`:** `AlertDispatcher` no captura explícitamente HTTP `429` porque `discord.py` gestiona internamente los *rate limit buckets* y `Retry-After`; aun así, si fallara finalmente lanzará `HTTPException`.
- **Canal no textual:** si existiese un `channel_id` correspondiente a un objeto sin `.send()` (ej. canal de categoría o voz sin texto), fallaría al invocar `channel.send` (`⚠️ sin verificar` en vivo; los comandos de suscripción solo pueden ejecutarse desde canales donde llegan interacciones).
- **Envío real con `discord.Client` `⚠️ sin verificar`:** probado con `FakeDiscordClient` y `FakeChannel` en tests; pendiente validar contra servidor real.

---

## 8. Tests que lo cubren

- [`tests/test_dispatcher.py`](../../tests/test_dispatcher.py):
  - `test_dispatcher_sends_embeds_dedups_and_pauses_on_forbidden_or_not_found`: verifica filtrado por prioridad, envío por `get_channel`/`fetch_channel`, auto-pausa ante `Forbidden` (`403`) y `NotFound` (`404`) y deduplicación al reintentar el mismo `item.id`.
  - `test_dispatcher_prunes_periodically_and_isolates_dynamic_types`: verifica aislamiento de tipos dinámicos por canal y disparo periódico de `prune_dispatched(retention_days=30)`.

---

## 9. Pendiente real

- Probar entrega real en canal estándar e hilo (`thread`) con `DISCORD_BOT_TOKEN` (`⚠️ sin verificar`).
- Añadir verificación de `isinstance(channel, discord.abc.Messageable)` o manejo específico si algún canal devuelto por `fetch_channel` no soportase `send()`.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-21
