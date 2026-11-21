# Discord API v10 — Dominio: Interacciones y *Slash Commands*

- **Fuentes oficiales:** [`src/application-commands.md`](./src/application-commands.md), [`src/receiving-and-responding.md`](./src/receiving-and-responding.md)
- **Fecha de descarga:** `2026-11-20`
- **Fecha de verificación real:** `2026-11-20` *(especificación descargada; flujo Gateway/`tree.sync()`/`followup` en vivo `⚠️ sin verificar` sin `DISCORD_BOT_TOKEN`)*

---

## 1. Tipos y registro de comandos (`CHAT_INPUT`)

- Los *slash commands* corresponden a comandos de tipo `CHAT_INPUT` registrados vía API (`PUT /applications/{application.id}/commands` para globales o `/guilds/{guild.id}/commands` para servidor específico).
- **Reglas oficiales de estructura (`src/application-commands.md`):**
  - Las opciones obligatorias (`required=True`) deben definirse **siempre antes** que las opcionales.
  - Cuando una opción define `choices`, Discord restringe al usuario en la interfaz **únicamente** a esos valores declarados.
  - Soporta localización (`name_localizations`, `description_localizations`), aunque actualmente el bot registra solo texto en español.

---

## 2. Ciclo de vida de respuesta (`src/receiving-and-responding.md`)

1. Al invocar un *slash command*, Discord envía la interacción por Gateway (en `discord.py`) con un `interaction.token`.
2. **Respuesta inicial en <= 3 segundos:**
   - **Inmediata (`CHANNEL_MESSAGE_WITH_SOURCE`, tipo `4`):** `await interaction.response.send_message(...)`. Usada en `/help` y en errores rápidos de permisos o validación.
   - **Diferida (`DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE`, tipo `5`):** `await interaction.response.defer(ephemeral=...)`. Muestra al usuario el estado de carga *"pensando..."* y mantiene el `interaction.token` válido hasta **15 minutos** para responder después mediante `POST /webhooks/{application_id}/{interaction_token}` (`interaction.followup.send(...)`).
3. **Mensajes efímeros (`EPHEMERAL` flag):**
   - Solo visibles para el usuario que ejecutó el comando.
   - Si se hace `defer(ephemeral=...)`, la visibilidad efímera del primer `followup` queda fijada por la del `defer` inicial (según nota oficial: en `DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE` el flag `EPHEMERAL` aplica en la respuesta inicial).

> **`⚠️ sin verificar` en vivo:** la propagación de `tree.sync()` global vs `guild` y los tiempos reales de respuesta de interacciones quedan pendientes de prueba con `DISCORD_BOT_TOKEN`.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
