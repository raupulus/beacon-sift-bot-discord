# Discord API v10 — Dominio: Mensajería y *Embeds*

- **Fuentes oficiales:** [`src/message.md`](./src/message.md) (`Create Message`, `Embed Object`, `Embed Limits`)
- **Fecha de descarga:** `2026-11-20`
- **Fecha de verificación real:** `2026-11-20` *(especificación descargada; renderizado y `channel.send(embed=...)` reales `⚠️ sin verificar` sin token)*

---

## 1. Estructura relevante de `Create Message` y `Embed`

- Endpoint subyacente usado por `channel.send(embed=...)`: `POST /channels/{channel.id}/messages`.
- Un objeto `Embed` acepta los siguientes bloques utilizados por `src/embeds.py`:
  - `title`: titular principal (enlazado si se pasa `url` HTTP/HTTPS válida).
  - `description`: texto enriquecido con subconjunto Markdown de Discord (incluye enlaces `[texto](url)`, negritas `**...**`, cursivas `*...*`, código en línea `` `...` `` y citas `> ...`).
  - `color`: entero RGB de 24 bits (`0xRRGGBB`, por ejemplo `0x38BDF8` o `0xEF4444`).
  - `timestamp`: marca temporal ISO 8601 UTC que el cliente de Discord renderiza automáticamente según la zona horaria local de cada usuario.
  - `fields`: lista de objetos `{name, value, inline}` (máx. 25 campos; en el bot se usa `inline=True` de 3 columnas para Fuente/Tipo/Prioridad).
  - `thumbnail`: objeto `{url}` con imagen externa por URL HTTP/HTTPS directa (el bot pasa `item.image_url` sin descargar ni re-alojar imágenes de prensa).
  - `footer`: objeto `{text}` para atribución compacta (`beacon-sift · feed.raupulus.dev`).

---

## 2. Restricciones clave en envío y formato

1. Todos los límites exactos por campo (`256`, `4096`, `1024`, `2048`) y la suma combinada (`6000` caracteres) se resumen en [`LIMITACIONES.md`](./LIMITACIONES.md). Superar cualquiera devuelve `400 Bad Request`.
2. **Deduplicación por URL:** si un mensaje incluyera múltiples embeds con la misma `url`, Discord solo mostraría el primero (no afecta a `bot-discord/`, que envía 1 embed por mensaje).
3. **Escape Markdown en enlaces `[texto](url)`:** si el titular contiene `[` o `]` sin escapar dentro de `build_news_list_embed()` o `build_sources_embed()`, puede romper la sintaxis del enlace Markdown en `description`.

> **`⚠️ sin verificar` en vivo:** la previsualización real de `thumbnail` desde fuentes externas y los colores/campos en clientes Desktop y móvil de Discord quedan pendientes de prueba con `DISCORD_BOT_TOKEN`.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
