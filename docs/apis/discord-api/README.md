# Discord API v10 — Documentación destilada de terceros

- **Fuentes oficiales descargadas:** [`src/reference.md`](./src/reference.md), [`src/rate-limits.md`](./src/rate-limits.md), [`src/application-commands.md`](./src/application-commands.md), [`src/receiving-and-responding.md`](./src/receiving-and-responding.md), [`src/message.md`](./src/message.md), [`src/permissions.md`](./src/permissions.md), [`src/gateway.md`](./src/gateway.md) (origen: `https://docs.discord.com/developers/...`, `last-modified: Thu, 19 Nov 2026`)
- **Fecha de descarga de fuentes:** `2026-11-20`
- **Fecha de verificación real:** `2026-11-22` *(verificado en vivo con token real desde `.env` local: `GET /users/@me`, Gateway WebSocket con `Intents.default()`, `CommandTree.sync()` global de los 11 comandos y entrega E2E real de `Embed` desde `web/` + Reverb; quedan `⚠️ sin verificar` únicamente interacciones en vivo, hilos y errores `403`/`404`/`429` reales en producción)*
- **Cliente usado por el servicio:** `discord.py 2.7.1` (`discord.http.Route.BASE == "https://discord.com/api/v10"`)

---

## Orden obligatorio de lectura dirigida

Al trabajar sobre la integración con Discord, lee estos documentos en el orden siguiente:

1. [`README.md`](./README.md) *(este índice y estado de verificación)*
2. [`00-fundamentos.md`](./00-fundamentos.md) + [`ERRATAS.md`](./ERRATAS.md) + [`LIMITACIONES.md`](./LIMITACIONES.md)
3. **Solo** el dominio concreto que necesites:
   - [`interacciones-y-slash-commands.md`](./interacciones-y-slash-commands.md) — `CHAT_INPUT`, `choices`, sincronización global/guild, ventana de 3 s, `defer` y `followup`
   - [`mensajeria-y-embeds.md`](./mensajeria-y-embeds.md) — `Create Message`, estructura de `Embed` y límites de campos/contenido
   - [`permisos-y-gateway.md`](./permisos-y-gateway.md) — bits de permisos (`ADMINISTRATOR`, `MANAGE_CHANNELS`, envío/hilos), *Gateway Intents* estándar frente a privilegiados

> **Nota sobre `src/`:** el subdirectorio [`src/`](./src/) almacena copias oficiales sin editar de `docs.discord.com`. No se editan manualmente y no deben leerse de rutina; solo se consultan para auditar o actualizar esta destilación.

---

## Cómo integramos esta API en el proyecto

Qué módulos de `bot-discord/` llaman a cada recurso y cómo configuramos `discord.py` está documentado en [`docs/info/apis/discord-api.md`](../../info/apis/discord-api.md).

---

## Estado de verificación real (Regla 11)

| Aspecto | Estado | Evidencia / Nota |
|---|---|---|
| Base URL `https://discord.com/api/v10` y `discord.py 2.7.1` | ✅ Verificado (`2026-11-20`) | `discord.http.Route.BASE == "https://discord.com/api/v10"` + petición HTTPS real |
| Respuesta `401` ante token inválido (`Authorization: Bot ...`) | ✅ Verificado (`2026-11-20`) | `GET https://discord.com/api/v10/users/@me` devuelve `HTTP 401` con `{"message": "401: Unauthorized", "code": 0}` |
| Especificación Markdown oficial descargada (`docs.discord.com`) | ✅ Descargada (`2026-11-20`) | 7 documentos originales intactos en `src/` |
| Gateway WebSocket (`Intents.default()`) y `on_ready()` | ✅ Verificado (`2026-11-22`) | Conexión real a Discord Gateway sin intents privilegiados (`GET /users/@me` `200 OK`) |
| Sincronización de *slash commands* (`tree.sync()` global) | ✅ Verificado (`2026-11-22`) | Los 11 *slash commands* registrados globalmente en Discord (`DISCORD_DEV_GUILD_ID` opcional) |
| Envío real de *Embeds* en canal de texto (`get_channel()`, `channel.send()`) | ✅ Verificado (`2026-11-22`) | Prueba E2E real: RSS CVE simulado → `web/` → Reverb → `bot-discord` → Embed crítico en canal de servidor |
| Respuestas a interacciones (`send_message`, `defer()`, `followup.send()`, `ephemeral`) | `⚠️ sin verificar` | Cubierto mediante mocks en `tests/test_commands.py`; pendiente pulsación en vivo |
| Hilos (`thread`), `fetch_channel()` frío y errores `403`/`404`/`429` reales | `⚠️ sin verificar` | Cubierto mediante mocks en `tests/test_dispatcher.py` |

---

> Creado: 2026-11-20 · Última revisión: 2026-11-22
