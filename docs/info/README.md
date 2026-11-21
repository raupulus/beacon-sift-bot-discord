# Documentación técnica viva (`docs/info/`)

Índice maestro de la arquitectura, módulos, *slash commands*, decisiones técnicas e integraciones de **`beacon-sift-bot-discord`**.

> **Lectura dirigida:** al trabajar en un módulo lee **únicamente** su `.md` en `docs/info/`. Si tocas una integración con API externa, lee además `docs/info/apis/<api>.md` y, cuando se trate de Discord, sigue [`../apis/discord-api/README.md`](../apis/discord-api/README.md) en orden (`README.md` → `00-fundamentos.md` + `ERRATAS.md` + `LIMITACIONES.md` → solo el dominio necesario).

---

## Guías transversales y plantilla

| Documento | Propósito |
|---|---|
| [`commands.md`](./commands.md) | Catálogo completo de los 11 *slash commands* de Discord y comandos locales/Docker. |
| [`decisiones-tecnicas.md`](./decisiones-tecnicas.md) | Decisiones deliberadas de diseño (aislamiento SQLite, `Intents.default()`, *Embeds* HUD, `defer()`, *watermark* inicial, auto-pausa). |
| [`_MODULE_TEMPLATE.md`](./_MODULE_TEMPLATE.md) | Plantilla obligatoria de 9 apartados para documentar módulos nuevos. |

---

## Módulos del código (`src/`)

| Módulo | Documento | Ficheros fuente cubiertos |
|---|---|---|
| Configuración y modelos | [`config-y-modelos.md`](./config-y-modelos.md) | [`src/config.py`](../../src/config.py), [`src/models.py`](../../src/models.py), [`.env.example`](../../.env.example) |
| Persistencia SQLite | [`storage.md`](./storage.md) | [`src/storage.py`](../../src/storage.py) |
| Constructores de Embeds | [`embeds.md`](./embeds.md) | [`src/embeds.py`](../../src/embeds.py) |
| Control de permisos | [`permissions.md`](./permissions.md) | [`src/permissions.py`](../../src/permissions.py) |
| Dispatcher de alertas | [`dispatcher.md`](./dispatcher.md) | [`src/dispatcher.py`](../../src/dispatcher.py) |
| Comandos y arranque | [`commands-y-arranque.md`](./commands-y-arranque.md) | [`src/main.py`](../../src/main.py), [`src/commands/`](../../src/commands/__init__.py) |

---

## Integraciones con APIs

| Integración | Documento de integración (propio) | Referencia oficial destilada |
|---|---|---|
| `beacon-sift-web` (API v1 REST + Laravel Reverb) | [`apis/beacon-sift-web.md`](./apis/beacon-sift-web.md) | — *(servicio interno hermano; fuente directa en el código del bot)* |
| Discord API v10 (`discord.py 2.7.1`) | [`apis/discord-api.md`](./apis/discord-api.md) | [`docs/apis/discord-api/README.md`](../apis/discord-api/README.md) |

---

## Despliegue

| Guía | Documento |
|---|---|
| Despliegue con Docker y Docker Compose | [`docs/deploys/docker.md`](../deploys/docker.md) |

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
