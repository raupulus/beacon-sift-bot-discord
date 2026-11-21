# Discord API v10 — Dominio: Permisos y *Gateway Intents*

- **Fuentes oficiales:** [`src/permissions.md`](./src/permissions.md), [`src/gateway.md`](./src/gateway.md)
- **Fecha de descarga:** `2026-11-20`
- **Fecha de verificación real:** `2026-11-20` *(bitfields e intents de `discord.py 2.7.1` verificados en local; comportamiento en vivo contra Gateway y servidores Discord `⚠️ sin verificar`)*

---

## 1. Permisos bitwise relevantes (`src/permissions.md`)

| Permiso oficial | Valor hexadecimal / Bit | Uso y matiz importante |
|---|---|---|
| `ADMINISTRATOR` | `0x0000000000000008` `(1 << 3)` | Concede todos los permisos e ignora sobrescrituras (*overwrites*) por canal. Comprobado en `permissions.py` para administrar suscripciones. |
| `MANAGE_CHANNELS` | `0x0000000000000010` `(1 << 4)` | Permite gestionar canales. Comprobado en `permissions.py` para `/subscribe`, `/unsubscribe`, `/pause`, `/resume`. |
| `VIEW_CHANNEL` | `0x0000000000000400` `(1 << 10)` | Requerido para que el bot vea el canal; si se deniega por *overwrite*, ignora permisos de envío en ese canal. |
| `SEND_MESSAGES` | `0x0000000000000800` `(1 << 11)` | Requerido para enviar mensajes en canales de texto/anuncios (no otorga envío en hilos). |
| `EMBED_LINKS` | `0x0000000000004000` `(1 << 14)` | Imprescindible para que el bot pueda enviar *Embeds* en canales donde publica alertas por `channel.send()`. |
| `SEND_MESSAGES_IN_THREADS` | `0x0000004000000000` `(1 << 38)` | Necesario si un usuario suscribe o consulta el bot dentro de un hilo (*thread*). |

- Discord evalúa y entrega los permisos efectivos del usuario invocante directamente dentro del payload de cada `Interaction` (`interaction.permissions` en `discord.py`), sin requerir llamadas HTTP extra.

---

## 2. *Gateway Intents* (`src/gateway.md`)

- El *Gateway* de Discord filtra los eventos enviados al bot mediante una máscara binaria `intents` en el handshake `IDENTIFY`.
- **Intents privilegiados (exigen activación explícita en Discord Developer Portal y revisión para >= 100 servidores):**
  - `GUILD_MEMBERS` (`1 << 1`)
  - `GUILD_PRESENCES` (`1 << 8`)
  - `MESSAGE_CONTENT` (`1 << 15`)
- **Configuración verificada de este bot (`discord.Intents.default()` en `discord.py 2.7.1`):**
  - Valor numérico: `53575421` (`guilds=True`, `guild_messages=True`, `dm_messages=True`).
  - Los tres intents privilegiados permanecen en `False` (`message_content=False`, `members=False`, `presences=False`), porque los *slash commands* (`INTERACTION_CREATE`) no dependen de intents y no requieren leer contenido de mensajes ordinarios.

> **`⚠️ sin verificar` en vivo:** la entrega en hilos (`SEND_MESSAGES_IN_THREADS`) y el rechazo `403 Forbidden` cuando falte `EMBED_LINKS` quedan pendientes de prueba con token y servidor Discord real.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
