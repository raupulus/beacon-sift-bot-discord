# Discord API v10 — Fundamentos

- **Fuentes oficiales:** [`src/reference.md`](./src/reference.md) (`API Versioning`, `Authentication`, `User Agent`, `Content Type`, `Snowflakes`)
- **Fecha de descarga:** `2026-11-20`
- **Fecha de verificación real:** `2026-11-20` *(verificación HTTP sin token válido contra `discord.com/api/v10/users/@me`)*

---

## 1. Base URL, versionado y autenticación

- **URL base:** `https://discord.com/api`
- **Ruta versionada recomendada (`discord.py 2.7.1`):** `https://discord.com/api/v10` (las versiones 9 y 10 figuran como *Available*; las anteriores están *Deprecated* o *Discontinued* devolviendo `400 Bad Request`).
- **Autenticación de bots:** cabecera HTTP `Authorization: Bot <token>`.
- **Content-Type:** `application/json`, `application/x-www-form-urlencoded` o `multipart/form-data` (omitirlo en payloads provoca error `50035` *"Invalid form body"* o rechazo).
- **`User-Agent` obligatorio:** `DiscordBot ($url, $versionNumber)` (RFC 9110). Las peticiones HTTP sin un `User-Agent` válido pueden ser bloqueadas con error Cloudflare `1XXX`.

### Verificación real realizada (`2026-11-20`)

Petición ejecutada con `curl` contra `https://discord.com/api/v10/users/@me` enviando `Authorization: Bot INVALID.TOKEN.CHECK` y `User-Agent: DiscordBot (https://feed.raupulus.dev, 0.1.0)`:
- Código HTTP devuelto: `401`
- Cuerpo JSON devuelto:
  ```json
  {"message": "401: Unauthorized", "code": 0}
  ```
- Con esto queda verificada la conectividad HTTPS contra la API v10 y el formato JSON de rechazo `401`. El Gateway WebSocket y todas las rutas autenticadas quedan `⚠️ sin verificar` hasta disponer de un `DISCORD_BOT_TOKEN` real.

---

## 2. Identificadores *Snowflake*

Según [`src/reference.md`](./src/reference.md):
- Discord utiliza *snowflakes* de **64 bits sin signo** (`uint64`) para `guild_id`, `channel_id`, `user_id`, `command.id`, etc.
- En JSON sobre HTTP siempre se transmiten **como strings** para evitar desbordamientos en lenguajes sin enteros de 64 bits (por ejemplo JavaScript).
- `discord.py` los convierte a `int` de Python (precisión arbitraria), y SQLite almacena enteros con signo de hasta 64 bits (`INTEGER` soporta todos los *snowflakes* actuales de 64 bits hasta ~`9.22e18`, aunque hay que tenerlo en cuenta en JS/JSON externos).

---

## 3. Cliente usado (`discord.py 2.7.1`)

- Verificado en el entorno `.venv`: `discord.__version__ == '2.7.1'`, apuntando a `discord.http.Route.BASE == 'https://discord.com/api/v10'`.
- Gestiona internamente el Gateway WebSocket (`Identify`, *heartbeat*, reconexión), la serialización `User-Agent`, la conversión de *snowflakes* y los encabezados `X-RateLimit-*` por *bucket*.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
