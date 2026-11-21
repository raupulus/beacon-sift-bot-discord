# Discord API v10 — Erratas, matices y trampas verificadas

- **Fuentes oficiales:** [`src/reference.md`](./src/reference.md), [`src/rate-limits.md`](./src/rate-limits.md), [`src/application-commands.md`](./src/application-commands.md), [`src/receiving-and-responding.md`](./src/receiving-and-responding.md), [`src/permissions.md`](./src/permissions.md)
- **Fecha de descarga:** `2026-11-20`
- **Fecha de verificación real:** `2026-11-20` *(verificado `401` HTTP y comportamiento real de `discord.py 2.7.1` al registrar comandos; flujos autenticados `⚠️ sin verificar`)*

---

## 1. Verificado en ejecución real / librería local (`2026-11-20`)

1. **Anotación de tipos con `@app_commands.choices` en `discord.py 2.7.1`:**
   - Anotar un parámetro con `priority: app_commands.Choice[str] | str | None = None` provoca `TypeError: unsupported types given inside Union[Choice[str], str, None]` al decorar el *slash command* (verificado durante la implementación en `bot-discord`).
   - **Solución aplicada:** usar `app_commands.Choice[str] | None = None` en las firmas registradas por `@tree.command(...)`, manteniendo `resolve_priority_arg()` compatible con ambos tipos en `src/commands/__init__.py`.

2. **Aviso de deprecación de `audioop` en Python 3.12 (`discord.player`):**
   - Verificado al ejecutar `pytest` en `discord.py 2.7.1`: `discord/player.py:30` importa `audioop` y emite `DeprecationWarning` porque Python 3.13 eliminó `audioop` de la librería estándar. Mantener Python `3.12` (`.python-version`) evita roturas potenciales en módulos internos de `discord.py`.

3. **Respuesta HTTP `401` real contra `discord.com/api/v10/users/@me`:**
   - Devuelve estado HTTP `401` con `{"message": "401: Unauthorized", "code": 0}` cuando el token `Bot` es inválido.

---

## 2. Matices de la especificación con impacto directo en nuestro código (`⚠️ sin verificar` con token real)

1. **Ventana estricta de 3 segundos para interacciones (`src/receiving-and-responding.md`):**
   - Toda interacción (`/comando`) exige respuesta inicial (`CHANNEL_MESSAGE_WITH_SOURCE` o `DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE`) en **menos de 3 segundos**, o el `interaction.token` queda invalidado.
   - Por eso `/status`, `/sources`, `/types`, `/latest`, `/search`, `/subscribe`, `/unsubscribe`, `/filters`, `/pause` y `/resume` ejecutan `await interaction.response.defer(...)` antes de consultar `web/` o SQLite, y devuelven resultado por `interaction.followup.send()`.

2. **Límite de 10 000 peticiones inválidas cada 10 minutos (`src/rate-limits.md`):**
   - Discord banea temporalmente por IP (Cloudflare ban) a aplicaciones que superen **10 000 respuestas `401`, `403` o `429` en 10 minutos**.
   - Auto-pausar un canal inmediatamente en `AlertDispatcher` tras capturar `discord.Forbidden` (`403`) o `discord.NotFound` (`404`) es vital para no acumular `403` repetidos en cada nueva noticia.

3. **`SEND_MESSAGES` no implica permiso en hilos (`src/permissions.md`):**
   - La tabla de permisos especifica que `SEND_MESSAGES` permite enviar mensajes en canales de texto y crear publicaciones en foros, *"does not allow sending messages in threads"*; enviar en hilos requiere `SEND_MESSAGES_IN_THREADS` (o `ADMINISTRATOR`). Si un usuario suscribe un hilo y al bot le falta `SEND_MESSAGES_IN_THREADS`, el envío fallará con `403 Forbidden` y el canal/hilo se auto-pausará (`⚠️ sin verificar` en vivo).

4. **Sincronización global vs guild (`src/application-commands.md`):**
   - `tree.sync()` sin `guild` actualiza comandos globales (con propagación cacheada en clientes), mientras que `tree.sync(guild=...)` (`DISCORD_DEV_GUILD_ID`) actualiza de inmediato en ese servidor de pruebas. Además, si se copia global a guild (`copy_global_to`) **y** luego se sincronizara global sin limpiar la guild en el mismo servidor, aparecerían comandos duplicados en el servidor de dev (`⚠️ sin verificar` en vivo).

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
