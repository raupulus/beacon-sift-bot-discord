# Discord API v10 — Documentación destilada de terceros

- **Fuentes oficiales descargadas:** [`src/reference.md`](./src/reference.md), [`src/rate-limits.md`](./src/rate-limits.md), [`src/application-commands.md`](./src/application-commands.md), [`src/receiving-and-responding.md`](./src/receiving-and-responding.md), [`src/message.md`](./src/message.md), [`src/permissions.md`](./src/permissions.md), [`src/gateway.md`](./src/gateway.md) (origen: `https://docs.discord.com/developers/...`, `last-modified: Thu, 19 Nov 2026`)
- **Fecha de descarga de fuentes:** `2026-11-20`
- **Fecha de verificación real:** `2026-11-20` *(parcial: transporte HTTPS a `discord.com/api/v10`, cabeceras `Authorization`/`User-Agent` y error JSON `401` verificados en vivo; los flujos autenticados quedan marcados como `⚠️ sin verificar` al no existir `DISCORD_BOT_TOKEN` real en el entorno)*
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
| Gateway WebSocket (`Intents.default()`) y `on_ready()` | `⚠️ sin verificar` | Requiere `DISCORD_BOT_TOKEN` real |
| Sincronización de *slash commands* (`tree.sync()` global / `guild`) | `⚠️ sin verificar` | Requiere `DISCORD_BOT_TOKEN` real (`DISCORD_DEV_GUILD_ID` opcional) |
| Respuestas a interacciones (`send_message`, `defer()`, `followup.send()`, `ephemeral`) | `⚠️ sin verificar` | Cubierto solo mediante mocks en `tests/test_commands.py` |
| Envío de *Embeds* en canales/hilos (`fetch_channel()`, `channel.send()`) y errores `403`/`404`/`429` | `⚠️ sin verificar` | Cubierto solo mediante mocks en `tests/test_dispatcher.py` |

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
