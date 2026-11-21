# Integración con Discord API v10

- **Cliente usado:** `discord.py 2.7.1` (`https://discord.com/api/v10`)
- **Documentación oficial destilada (terceros):** [`docs/apis/discord-api/README.md`](../../apis/discord-api/README.md)
- **Fecha de descarga de especificación oficial:** `2026-11-20`
- **Fecha de verificación real:** `2026-11-20` *(verificado acceso HTTPS y formato JSON `401` contra `https://discord.com/api/v10/users/@me`; llamadas autenticadas y Gateway `⚠️ sin verificar` al no existir `DISCORD_BOT_TOKEN` real)*

> Este documento describe **únicamente cómo integra este bot Discord API v10** y qué módulos la consumen. La especificación, límites y erratas oficiales residen en [`docs/apis/discord-api/`](../../apis/discord-api/README.md) para no duplicar datos oficiales.

---

## 1. Puntos de integración en el código

| Recurso Discord / `discord.py` | Dónde lo llamamos | Para qué y parámetros clave | Estado de verificación real |
|---|---|---|---|
| Gateway WebSocket (`Intents.default()`) | [`src/main.py`](../../../src/main.py) (`BeaconDiscordBot`) | Mantiene sesión del bot, recibe `INTERACTION_CREATE` sin intents privilegiados y evita duplicar logs con `log_handler=None`. | `⚠️ sin verificar` |
| `CommandTree.sync()` | [`src/main.py`](../../../src/main.py) (`setup_hook`) | Registra los 11 *slash commands*; usa `DISCORD_DEV_GUILD_ID` (copia a guild) si está definido o sync global si no. | `⚠️ sin verificar` |
| `interaction.response` / `followup` | [`src/commands/info.py`](../../../src/commands/info.py), [`src/commands/subscriptions.py`](../../../src/commands/subscriptions.py) | Respuesta inmediata en `/help` y errores (`ephemeral=True`); `defer()` + `followup.send()` en consultas I/O. | `⚠️ sin verificar` |
| `interaction.permissions` | [`src/permissions.py`](../../../src/permissions.py) (`can_manage_subscriptions`) | Comprueba `administrator` o `manage_channels` en guilds, más `DISCORD_ADMIN_IDS` y `ALLOW_DM_SUBSCRIPTIONS`. | `⚠️ sin verificar` |
| `get_channel()` / `fetch_channel()` / `send(embed=...)` | [`src/dispatcher.py`](../../../src/dispatcher.py) (`AlertDispatcher`) | Envía `discord.Embed` de alertas; captura `Forbidden`/`NotFound` para auto-pausar el canal y `HTTPException` para loguear fallos. | `⚠️ sin verificar` |

---

## 2. Convenciones de integración aplicadas

1. **Sin intents privilegiados:** `discord.Intents.default()` deja `message_content=False`, `members=False` y `presences=False`, cumpliendo la arquitectura basada en *slash commands*.
2. **Margen bajo ventana de 3 segundos:** todo handler que llama a `BeaconApiClient` o `BotStorage` ejecuta primero `await interaction.response.defer(...)` para respetar el timeout inicial descrito en [`ERRATAS.md`](../../apis/discord-api/ERRATAS.md).
3. **Topes seguros en Embeds:** [`src/embeds.py`](../../../src/embeds.py) recorta `title` (250), `description` (350 en alerta / 3800 en listas) y `fields` dentro de las cuotas de [`LIMITACIONES.md`](../../apis/discord-api/LIMITACIONES.md).
4. **Protección frente a baneos por peticiones inválidas:** auto-pausar canales con `Forbidden` (`403`) o `NotFound` (`404`) corta la generación repetida de `403` por noticias posteriores.

---

## 3. Pendiente de verificación con token real (`⚠️ sin verificar`)

Cuando se disponga de un `DISCORD_BOT_TOKEN` de pruebas, validar en vivo y actualizar la cabecera de [`docs/apis/discord-api/README.md`](../../apis/discord-api/README.md):
- Conexión al Gateway WebSocket (`on_ready()`).
- Sincronización inmediata con `DISCORD_DEV_GUILD_ID` y selector desplegable de `PRIORITY_CHOICES`.
- Invocación real de los 11 *slash commands*, respuesta `ephemeral=True` y entrega automática de alertas con `Embed` en canal estándar e hilo (`thread`).
- Auto-pausa real al revocar permisos (`EMBED_LINKS` o `SEND_MESSAGES`) o eliminar el canal.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
