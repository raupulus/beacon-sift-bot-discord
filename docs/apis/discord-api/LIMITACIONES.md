# Discord API v10 — Limitaciones y cuotas oficiales

- **Fuentes oficiales:** [`src/rate-limits.md`](./src/rate-limits.md), [`src/message.md`](./src/message.md), [`src/application-commands.md`](./src/application-commands.md), [`src/receiving-and-responding.md`](./src/receiving-and-responding.md)
- **Fecha de descarga:** `2026-11-20`
- **Fecha de verificación real:** `2026-11-20` *(datos verificados en la especificación oficial descargada; comportamiento real bajo carga y 429 `⚠️ sin verificar` sin `DISCORD_BOT_TOKEN`)*

---

## 1. Rate limits y prohibiciones temporales (`src/rate-limits.md`)

| Límite | Valor oficial | Notas |
|---|---|---|
| Límite global por bot | **50 peticiones/segundo** | Independiente de los límites por ruta (`X-RateLimit-Bucket`). Sin cabecera `Authorization`, aplica por IP. |
| Límites por ruta (*Per-Route*) | Dinámicos vía cabeceras `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset-After`, `X-RateLimit-Bucket` | `discord.py` respeta estos *buckets* automáticamente y reintenta tras `Retry-After` en HTTP `429`. |
| Límite de peticiones inválidas | **10 000 respuestas `401`/`403`/`429` cada 10 minutos** | Superarlo activa bloqueo temporal por IP desde Cloudflare. |

---

## 2. Límites de mensajes y *Embeds* (`src/message.md`)

| Campo / Recurso | Límite oficial | Cómo lo acota `src/embeds.py` |
|---|---|---|
| `content` (mensaje texto plano) | **2000 caracteres** | Mensajes de error/confirmación breves en comandos. |
| `embeds` por mensaje | **Hasta 10 `rich` embeds** | Se envía 1 Embed por mensaje. |
| `embed.title` | **256 caracteres** | `_truncate(..., 250)` |
| `embed.description` | **4096 caracteres** | Alerta individual: `350` chars; listados `/latest` y `/search`: tope acumulado `3800`; `/sources`: tope `3800`. |
| `embed.fields` (cantidad) | **Hasta 25 objetos `field`** | Alertas usan 3; `/help` usa 2; `/status` hasta 6; `/types` usa 2. |
| `field.name` | **256 caracteres** | Etiquetas fijas cortas (`"Fuente"`, `"Tipo"`, `"Prioridad"`, etc.). |
| `field.value` | **1024 caracteres** | `Fuente`: `_truncate(..., 100)`; `/types`: `_truncate(type_lines, 1000)`. |
| `footer.text` | **2048 caracteres** | Texto fijo `"beacon-sift · feed.raupulus.dev"`. |
| `author.name` | **256 caracteres** | No usado actualmente. |
| **Suma combinada total por mensaje** | **6000 caracteres** *(entre `title`, `description`, `field.name`, `field.value`, `footer.text` y `author.name` de todos los embeds del mensaje)* | Los topes individuales en `embeds.py` mantienen cada Embed muy por debajo de 6000 caracteres *(salvo `build_filters_embed` si existiesen decenas de filtros)* . |

> Los espacios iniciales y finales en campos de Embed son recortados automáticamente por Discord antes de medir el límite. Si un mensaje lleva varios embeds con la misma `url`, Discord los deduplica mostrando solo el primero.

---

## 3. Límites de *Slash Commands* e interacciones (`src/application-commands.md`, `src/receiving-and-responding.md`)

| Recurso | Límite oficial | Estado en `bot-discord/` |
|---|---|---|
| Comandos `CHAT_INPUT` globales | **100** *(y hasta 100 adicionales específicos por guild)* | **11 comandos** registrados según contrato. |
| Nombre de comando/opción (`CHAT_INPUT`) | **1–32 caracteres** minúsculas (`^[-_\u02BC\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32}$`) | Cumplido por los 11 comandos y sus opciones. |
| Descripción de comando / opción | **1–100 caracteres** | Descripciones cortas en `src/commands/*.py`. |
| Opciones por comando | **Máximo 25** *(las obligatorias deben preceder a las opcionales)* | Máximo 3 opciones en `/latest` y `/search`. |
| `choices` por opción (`STRING`/`INTEGER`/`NUMBER`) | **Máximo 25** (`name` 1–100 chars; `value` string <= 100 chars) | `PRIORITY_CHOICES` define 4 valores. |
| Plazo para respuesta inicial / `defer()` | **3 segundos** desde la recepción de la interacción | Cumplido con `defer()` antes de llamar a `web/` o SQLite. |
| Validez del `interaction.token` para `followup` / editar respuesta | **15 minutos** | Respuesta enviada en segundos tras `defer()`. |

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
