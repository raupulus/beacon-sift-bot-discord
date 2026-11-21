# Módulo `embeds`

> Ficheros cubiertos: [`src/embeds.py`](../../src/embeds.py)

## 1. Qué hace y qué NO hace

- **Hace:**
  - Construye todos los `discord.Embed` del servicio con la paleta HUD de `beacon-sift` (`BRAND_COLOR`, `LIVE_COLOR`, `WARN_COLOR`, `ERROR_COLOR` y `Priority.color_int`).
  - Valida URLs HTTP/HTTPS (`safe_http_url`) para `embed.url`, `embed.thumbnail` y enlaces Markdown de `/latest`, `/search` y `/sources`.
  - Escapa corchetes `[` `]` en rótulos de enlaces Markdown (`_escape_md_label`) y trunca textos dentro de límites seguros de Discord.
- **NO hace:**
  - No realiza llamadas a Discord ni descarga/cachea imágenes de terceros (`thumbnail` apunta directo a la URL externa validada).

---

## 2. Modelo de datos

Constantes de color en [`src/embeds.py`](../../src/embeds.py):
- `BRAND_COLOR = 0x38BDF8` (cyan radar)
- `LIVE_COLOR = 0x10B981` (verde operativo)
- `WARN_COLOR = 0xF59E0B` (ámbar advertencia/pausa)
- `ERROR_COLOR = 0xEF4444` (rojo error/crítica)

---

## 3. Flujos principales

1. **`build_news_embed(item, show_thumbnail=True)`:**
   - `title`: `_truncate(item.title or "Sin titular", 250)`, `url=safe_http_url(item.url)`, `description=_truncate(item.snippet, 350)` si hay snippet.
   - `color`: `discord.Color(item.priority.color_int)`.
   - `timestamp`: `item.published_at` (Discord lo renderiza en la zona horaria del cliente).
   - 3 *fields* inline: `Fuente` (truncada a 100), `Tipo` (`` `#type` ``), `Prioridad` (`emoji + label_es`).
   - `thumbnail`: `embed.set_thumbnail(url=safe_thumb)` solo si `show_thumbnail` y `safe_http_url(item.image_url)` es válida.
   - Footer común: `"beacon-sift · feed.raupulus.dev"`.
2. **`build_news_list_embed(items, header, timezone_name)`:**
   - Lista ítems en `description` con títulos truncados a `140` chars, corchetes escapados y snippet a `120` chars; se detiene si supera `3800` caracteres.
3. **Constructores de comandos:** `build_help_embed()` (2 fields), `build_status_embed()` (3 fields si API `None`, 7 fields si OK), `build_sources_embed()` (tope 3800 en `description`), `build_types_embed()` (`type_lines` truncado a 1000 en field), `build_filters_embed()`.

---

## 4. Puntos de entrada (con auth, permisos y límites)

Funciones puras síncronas:
- `safe_http_url(url)`
- `format_datetime(dt, timezone_name="Europe/Madrid")` (fallback `UTC` si la zona es inválida)
- `build_news_embed(item, *, show_thumbnail=True)`
- `build_news_list_embed(items, header, timezone_name="Europe/Madrid")`
- `build_help_embed()`, `build_status_embed(...)`, `build_sources_embed(...)`, `build_types_embed(...)`, `build_filters_embed(...)`

---

## 5. Dependencias en ambos sentidos

- **Depende de:** `discord` (`discord.Embed`, `discord.Color`), librería estándar (`datetime`, `urllib.parse`, `zoneinfo`), [`src/models.py`](../../src/models.py), [`docs/apis/discord-api/LIMITACIONES.md`](../apis/discord-api/LIMITACIONES.md).
- **Consumido por:** [`src/dispatcher.py`](../../src/dispatcher.py), [`src/commands/info.py`](../../src/commands/info.py), [`src/commands/subscriptions.py`](../../src/commands/subscriptions.py).

---

## 6. Configuración (variables, valor por defecto y efecto)

| Variable (`.env`) | Atributo `Settings` | Valor por defecto | Efecto |
|---|---|---|---|
| `DISCORD_SHOW_THUMBNAILS` | `discord_show_thumbnails` | `True` | Activa o desactiva `embed.set_thumbnail()` en alertas enviadas por `AlertDispatcher`. |
| `BOT_TIMEZONE` | `bot_timezone` | `"Europe/Madrid"` | Zona horaria usada en `build_news_list_embed()` y `build_status_embed()`. |

---

## 7. Trampas conocidas

- **Diferencia de zonas horarias:** `build_news_embed()` usa `timestamp=item.published_at` nativo de Discord (el usuario ve su propia hora local), mientras que `build_news_list_embed()` y `build_status_embed()` formatean la hora como texto fijo usando `BOT_TIMEZONE`.
- **Sin corte explícito en `build_filters_embed`:** si un canal acumulase decenas de suscripciones, `description` o `rows` no aplican bucle de recorte como `build_sources_embed`.
- **Asunción de `_truncate(text, max_chars)`:** asume `max_chars >= 2` (con `<= 1` devolvería un slicing negativo inválido). Actualmente todos los llamadores pasan >= `100`.
- **Renderizado real en clientes Discord `⚠️ sin verificar`:** validado por inspección de atributos de `discord.Embed`, pendiente de envío real con `DISCORD_BOT_TOKEN`.

---

## 8. Tests que lo cubren

- [`tests/test_embeds.py`](../../tests/test_embeds.py):
  - `test_build_news_embed_sets_priority_color_limits_and_thumbnail`
  - `test_build_news_embed_rejects_unsafe_urls` (`javascript:`, `data:`)
  - `test_build_catalog_embeds` (incluye escape `\[Sec\]` y `\[CVE-2026-1\]` y todos los builders).

---

## 9. Pendiente real

- Añadir recorte seguro (`<= 3800` chars) en `build_filters_embed()` y guard `max_chars <= 1` en `_truncate()` para defensa ante cambios futuros.
- Verificar renderizado visual en un servidor Discord real (`⚠️ sin verificar`).

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
