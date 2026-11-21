# AGENTS.md — Guía de contexto y reglas para `beacon-sift-bot-discord`

Este documento define la arquitectura, convenciones y reglas obligatorias que cualquier agente o desarrollador debe seguir al trabajar en **`beacon-sift-bot-discord`** (`bot-discord/`), servicio independiente de **beacon-sift** (`https://feed.raupulus.dev`).

---

## 1. Propósito del servicio

Bot de **Discord** escrito en **Python 3.12+** con `discord.py` y empaquetado con **Docker** que conecta canales de servidores Discord con las noticias y alertas agregadas por `web/` (`feed.raupulus.dev`):

- **Alertas en tiempo real:** Se suscribe al canal WebSocket público de Laravel Reverb emitido por `web/` (`beacon.news`, evento `news.created`) y ejecuta *catch-up* incremental con `since_id` tras reconexiones.
- **Consultas bajo demanda:** Consume únicamente los 4 endpoints públicos `GET` JSON de solo lectura de `web/` (`/api/v1/status`, `/api/v1/sources`, `/api/v1/types`, `/api/v1/items`).
- **Suscripciones locales en SQLite:** Almacena en `data/bot.db` (volumen `/app/data` en Docker) las suscripciones por `channel_id`, estado `is_paused`, deduplicación (`dispatched_items`) y el cursor `last_processed_item_id`.

---

## 2. Estructura del repositorio independiente

```text
bot-discord/
├── AGENTS.md                           # Reglas, arquitectura y protocolo residente de documentación
├── CLAUDE.md                           # Puntero obligatorio a AGENTS.md
├── README.md                           # Documentación general y autoría
├── .python-version                     # Versión fijada (3.12)
├── .env.example                        # Variables de entorno sin secretos
├── .gitignore                          # Python, .venv, .env, SQLite local y /docs/{planning,auditorias}/
├── .dockerignore                       # Exclusiones para build Docker
├── Dockerfile                          # Imagen python:3.12-slim ejecutada como botuser
├── docker-compose.yml                  # Servicio independiente con volumen ./data:/app/data
├── pyproject.toml                      # Dependencias (uv/pip), pytest y ruff
├── uv.lock                             # Lockfile reproducible de dependencias
├── images/                             # Logotipo oficial e iconos del bot (logo.svg, PNGs)
├── docs/
│   ├── info/                           # Documentación técnica VIVA del servicio
│   │   ├── README.md                   # Índice maestro de docs/info/
│   │   ├── _MODULE_TEMPLATE.md         # Plantilla obligatoria de 9 apartados por módulo
│   │   ├── commands.md                 # 11 slash commands Discord y comandos uv/Docker
│   │   ├── decisiones-tecnicas.md      # Decisiones deliberadas de arquitectura
│   │   ├── config-y-modelos.md         # Settings (.env) y DTOs/Priority con color_int HUD
│   │   ├── storage.md                  # Esquema y operaciones SQLite (aiosqlite)
│   │   ├── embeds.md                   # Constructores de Discord Embeds y límites seguros
│   │   ├── permissions.md              # Control síncrono de administrador/manage_channels/DM
│   │   ├── dispatcher.md               # Enrutado, deduplicación y pausa ante Forbidden/NotFound
│   │   ├── commands-y-arranque.md      # BeaconDiscordBot, CommandTree y commands/*
│   │   └── apis/                       # Cómo integra este bot APIs externas
│   │       ├── beacon-sift-web.md      # Integración REST + Reverb con web/
│   │       └── discord-api.md          # Integración con Discord API v10 (sin duplicar spec)
│   ├── apis/
│   │   └── discord-api/                # Documentación oficial destilada y verificada de Discord
│   │       ├── README.md               # Índice y estado de verificación real
│   │       ├── 00-fundamentos.md       # Base v10, User-Agent, Auth Bot, Snowflakes y HTTP 401
│   │       ├── ERRATAS.md              # Matices verificados (Choice union, 3s defer, threads)
│   │       ├── LIMITACIONES.md         # Rate limits, 10k invalid reqs y topes de Embed/Comandos
│   │       ├── interacciones-y-slash-commands.md # Dominio CHAT_INPUT, choices y followup
│   │       ├── mensajeria-y-embeds.md  # Dominio Create Message y estructura Embed
│   │       ├── permisos-y-gateway.md   # Dominio bits de permisos y Gateway Intents
│   │       └── src/                    # Snapshots Markdown originales de docs.discord.com
│   └── deploys/
│       └── docker.md                   # Guía de despliegue con Dockerfile y Docker Compose
├── src/
│   ├── main.py                         # BeaconDiscordBot (CommandTree) + ReverbListener
│   ├── config.py                       # Validación de entorno con pydantic-settings
│   ├── models.py                       # Priority (con color_int HUD), NewsItem, SourceInfo, etc.
│   ├── storage.py                      # Persistencia async SQLite (aiosqlite)
│   ├── api_client.py                   # Cliente HTTP async (httpx) para /api/v1/*
│   ├── reverb_client.py                # Cliente WebSocket Pusher v7 (websockets)
│   ├── embeds.py                       # Constructores de Discord Embeds con paleta HUD
│   ├── permissions.py                  # Validación de administrator/manage_channels y DISCORD_ADMIN_IDS
│   ├── dispatcher.py                   # Filtrado, deduplicación y pausa automática ante Forbidden/NotFound
│   └── commands/                       # info.py y subscriptions.py
└── tests/                              # Tests automatizados pytest / pytest-asyncio (14 tests)
```

### Reglas de aislamiento y ecosistema `beacon-sift`
- Este directorio es un **repositorio Git independiente y autocontenido** (`raupulus/beacon-sift-bot-discord`). No depende de ninguna raíz compartida ni de archivos externos fuera del repo.
- **Nunca** importar módulos de los repos hermanos ni conectarse directamente a la base de datos PostgreSQL de `web/`.
- Toda comunicación con `web/` se realiza exclusivamente por **WebSockets públicos** (Laravel Reverb) y por los **endpoints `GET` JSON de solo lectura** (`/api/v1/...`).
- **Ecosistema independiente de `beacon-sift`:**
  - Servicio Web / API / Reverb: [GitHub (`raupulus/beacon-sift-web`)](https://github.com/raupulus/beacon-sift-web) · [GitLab](https://gitlab.com/raupulus/beacon-sift-web)
  - Bot hermano de Telegram: [GitHub (`raupulus/beacon-sift-bot-telegram`)](https://github.com/raupulus/beacon-sift-bot-telegram) · [GitLab](https://gitlab.com/raupulus/beacon-sift-bot-telegram)

---

## 3. Contrato obligatorio de comandos y paridad

El contrato operativo vive **autocontenido en este repositorio** en [`docs/info/commands.md`](./docs/info/commands.md) y mantiene paridad estricta con el bot hermano `beacon-sift-bot-telegram`:

- **Consultas (*slash commands*):** `/help`, `/status`, `/sources [type]`, `/types`, `/latest [type] [priority] [limit]`, `/search <query> [type] [limit]`
- **Gestión de canal (solo administradores / `manage_channels`, salvo `/filters` abierto en el canal):** `/subscribe <type|all> [min_priority]`, `/unsubscribe <type|all>`, `/filters`, `/pause`, `/resume`
- **Paridad estricta:** mismos nombres lógicos, parámetros (`type`, `priority`, `limit`, `query`), rangos (`limit=1..10`, defecto `5`), semántica de permisos y manejo amigable de errores (sin resultados, API caída sin exponer trazas ni secretos, y uso esperado ante parámetros inválidos). No introducir comandos huérfanos sin actualizar [`docs/info/commands.md`](./docs/info/commands.md) y replicar el cambio en `beacon-sift-bot-telegram`.
- **Formato mínimo en Discord:** *Embeds* limpios con color según prioridad (`low=#64748B`, `medium=#38BDF8`, `high=#F59E0B`, `critical=#EF4444`), titular enlazado directamente a la fuente original, fuente, tipo, prioridad, fecha (`timestamp`) y extracto breve (*snippet*) bajo límites de Discord.

---

## 4. Documentación

Protocolo obligatorio aplicable a **todas** las tareas presentes y futuras en este repositorio.

### Estructura bajo `docs/`
- [`docs/info/`](./docs/info/README.md) — documentación técnica **VIVA** del proyecto (`<modulo>.md`, `commands.md`, `decisiones-tecnicas.md`, `_MODULE_TEMPLATE.md` y `apis/<api>.md`).
- `docs/apis/<api>/` — documentación **oficial destilada y verificada** de APIs de terceros (`README.md`, `00-fundamentos.md`, `ERRATAS.md`, `LIMITACIONES.md`, un `.md` por dominio y `src/` con copias originales intactas que no se editan ni se leen de rutina).
- [`docs/deploys/`](./docs/deploys/docker.md) — guías reales de despliegue.
- `docs/future/` — crear solo cuando exista una idea decidida y explícitamente aplazada (no es deuda técnica ni bugs; prohibidas carpetas vacías).
- `docs/planning/` (`<NN>-<fase>.md`, `dudas/`, `archived/`) y `docs/auditorias/` — **[NO GIT · EFÍMERO · POR DESARROLLADOR]**. Deben permanecer en [`.gitignore`](./.gitignore) (`/docs/planning/` y `/docs/auditorias/`). **Prohibido enlazarlos desde ningún archivo versionado.**

### Reglas permanentes (1–13)
1. **Mismo commit:** toda tarea de código termina con su documentación actualizada **en el mismo commit**.
2. **Jerarquía de verdad:** `código > docs/info/ > AGENTS.md > resto`. `docs/planning/`, `docs/future/` y `docs/auditorias/` nunca son fuente de verdad del estado actual.
3. **Discrepancias:** si se detecta una diferencia entre documentación y código, se corrige en el mismo commit en que se detecta.
4. **Ciclo de módulos:** módulo modificado → actualizar su `.md`; módulo nuevo → crear desde [`_MODULE_TEMPLATE.md`](./docs/info/_MODULE_TEMPLATE.md) e indexar en [`docs/info/README.md`](./docs/info/README.md) y en este `AGENTS.md`; módulo eliminado → borrar su `.md` y sacarlo de **todos** los índices.
5. **Pie obligatorio en `docs/`:** todo `.md` propio bajo `docs/` (excluyendo snapshots originales en `docs/apis/<api>/src/`) termina con separador `---` y la línea exacta:
   `> Creado: YYYY-MM-DD · Última revisión: YYYY-MM-DD`
   La fecha de creación no cambia nunca; la de revisión se actualiza en el commit del cambio.
6. **Checklists verificables:** en planificaciones (`- [ ]`), marcar `[x]` significa verificado funcionando y cumpliendo, no simplemente escrito.
7. **Ciclo efímero (`docs/planning/` y `docs/auditorias/`):** crear → trabajar → verificar → promocionar lo duradero → **BORRAR** (`archived/` es sala de espera temporal, no histórico).
8. **Promoción antes de borrar lo efímero:** comportamiento de módulo → `docs/info/<modulo>.md`; decisión deliberada → `docs/info/decisiones-tecnicas.md`; trampa duradera → tabla de trampas de `AGENTS.md`; cambio de estructura o comandos → `AGENTS.md` / `commands.md`; idea aplazada → `docs/future/`; regresión → test automatizado.
9. **Integridad de enlaces:** nada versionado puede enlazar a `docs/planning/` ni a `docs/auditorias/`, ni se sacarán de `.gitignore`.
10. **Lectura dirigida:** al tocar un módulo lee **solo** su `.md`; si tocas una API de terceros añade `docs/apis/<api>/` en orden estricto: `README.md` → `00-fundamentos.md` + `ERRATAS.md` + `LIMITACIONES.md` → solo el dominio necesario. No leer el resto de `docs/info/`, `docs/future/`, `archived/` ni `src/`.
11. **Verificación real de APIs externas:** nunca asumir ni configurar contra una API de terceros sin comprobarlo con una petición real; lo no comprobado en vivo se marca explícitamente `⚠️ sin verificar`.
12. **Idiomas:** documentación, comentarios, docstrings y textos para el usuario en **español**; identificadores, nombres de fichero/directorio y **mensajes de log (`logger.*`) en inglés** (campos JSON de APIs de terceros tal como llegan).
13. **Atribución y limpieza:** usar `@raupulus` y `public@raupulus.dev` cuando aplique. Prohibidas firmas de agente en commits, PRs o documentación (`Co-Authored-By`, «Generated with…», identificadores de sesión).

### Disparadores y plantillas rápidas
- **Disparadores clave:** cambio en lógica/esquema/rutas de módulo → `docs/info/<modulo>.md`; nuevo comando/script → `commands.md`; cambio de directorios → árbol de `AGENTS.md`; tocar API externa → `docs/info/apis/<api>.md` (+ `docs/apis/<api>/` sin duplicar spec oficial); planificación/auditoría/duda → efímero en `docs/planning/` o `docs/auditorias/` y promoción al cerrar.
- **Plantillas obligatorias:**
  - *Módulo:* [`_MODULE_TEMPLATE.md`](./docs/info/_MODULE_TEMPLATE.md) (9 apartados).
  - *Fase:* Objetivo · Contexto y motivo · Alcance (dentro/fuera) · Trabajo por módulo con checklist (`documentación actualizada` y `tests`) · Criterio de cierre.
  - *Duda (`D<NN>`):* Estado `[ ] Pendiente | [x] Resuelta | [ ] Ignorada` · Qué bloquea · Contexto · Opciones con implicaciones · Respuesta · Consecuencia aplicada antes de borrar.
  - *Auditoría:* Cabecera (fecha, revisión, alcance, método) · Resumen por severidad (`Crítico`/`Alto`/`Medio`/`Bajo`) · Hallazgos (`<PREFIJO>-C01`, estado, `fichero:línea`, descripción, **cómo se verificó**, impacto, corrección) · No hallazgos · Recomendaciones no verificadas.
  - *API de terceros:* Cabecera con fuentes, fecha de descarga y fecha de verificación real.

### Índice maestro de `docs/info/`
- **Índice general:** [`docs/info/README.md`](./docs/info/README.md)
- **Plantilla de módulo:** [`docs/info/_MODULE_TEMPLATE.md`](./docs/info/_MODULE_TEMPLATE.md)
- **Comandos:** [`docs/info/commands.md`](./docs/info/commands.md)
- **Decisiones técnicas:** [`docs/info/decisiones-tecnicas.md`](./docs/info/decisiones-tecnicas.md)
- **Módulos:**
  - [`docs/info/config-y-modelos.md`](./docs/info/config-y-modelos.md) (`src/config.py`, `src/models.py`)
  - [`docs/info/storage.md`](./docs/info/storage.md) (`src/storage.py`)
  - [`docs/info/embeds.md`](./docs/info/embeds.md) (`src/embeds.py`)
  - [`docs/info/permissions.md`](./docs/info/permissions.md) (`src/permissions.py`)
  - [`docs/info/dispatcher.md`](./docs/info/dispatcher.md) (`src/dispatcher.py`)
  - [`docs/info/commands-y-arranque.md`](./docs/info/commands-y-arranque.md) (`src/main.py`, `src/commands/*`)
- **Integraciones APIs:**
  - [`docs/info/apis/beacon-sift-web.md`](./docs/info/apis/beacon-sift-web.md) (`src/api_client.py`, `src/reverb_client.py`)
  - [`docs/info/apis/discord-api.md`](./docs/info/apis/discord-api.md) → referencia oficial en [`docs/apis/discord-api/README.md`](./docs/apis/discord-api/README.md)
- **Despliegue:** [`docs/deploys/docker.md`](./docs/deploys/docker.md)

### Tabla de trampas conocidas
| Trampa | Módulos afectados | Efecto / Cómo evitarla |
|---|---|---|
| Python != `3.12` (`audioop` eliminado en 3.13) | Entorno local (`uv`), `discord.py` | Usar siempre `uv run ...` o `uv sync --python 3.12` (`.python-version = 3.12`). |
| `Choice[str] \| str \| None` en `@app_commands` | `commands/info.py`, `commands/subscriptions.py` | `discord.py 2.7.1` lanza `TypeError` al registrar si se incluye `str` en la unión; usar siempre `app_commands.Choice[str] \| None`. |
| Ventana de 3 s de interacción | `commands/*` | Todo comando que consulta `web/` o SQLite debe llamar antes a `interaction.response.defer(...)`. |
| `DISCORD_DEV_GUILD_ID` + sync global posterior | `main.py` (`setup_hook`) | Si `copy_global_to(guild=...)` registró comandos locales y luego se arranca solo global, el dev guild mostrará comandos duplicados. |
| `prune_dispatched()` sin programar | `storage.py` | Existe el método y test, pero ningún flujo en `src/` lo invoca periódicamente aún. |
| Límite de 10 000 peticiones inválidas / 10 min | `dispatcher.py` | Repetir `401`/`403`/`429` causa ban temporal Cloudflare; mantener siempre la auto-pausa ante `Forbidden`/`NotFound`. |
| Envío en hilos requiere permiso específico | `dispatcher.py` | `SEND_MESSAGES` no incluye hilos; el bot necesita `SEND_MESSAGES_IN_THREADS` (y `EMBED_LINKS`) en el canal/hilo destino. |
| Flujos Discord en vivo sin token | `main.py`, `commands/*`, `dispatcher.py` | Transporte HTTPS/`401` verificado contra `discord.com/api/v10`, pero Gateway, sync y envíos reales siguen `⚠️ sin verificar`. |

### Checklist antes de dar cualquier tarea por terminada
- [ ] Documentación del módulo tocado actualizada en el **mismo commit**
- [ ] Fechas de `Última revisión` (`2026-11-20` o fecha actual) al día en los archivos tocados
- [ ] Módulos nuevos indexados en `docs/info/README.md` y en este `AGENTS.md`
- [ ] Módulos eliminados fuera de todos los índices
- [ ] Ningún archivo versionado enlaza a `docs/planning/` ni a `docs/auditorias/`
- [ ] `/docs/planning/` y `/docs/auditorias/` siguen en `.gitignore`
- [ ] Lo duradero de planificaciones o auditorías cerradas promocionado, y los ficheros efímeros borrados
- [ ] Checklists `[x]` verificados ejecutando código/tests reales, no asumidos
- [ ] Árbol de estructura de este `AGENTS.md` refleja los directorios reales

---

## 5. Directrices legales (agregación responsable)

- Publicar únicamente **titular enlazado a la fuente original, fuente, tipo, prioridad, fecha y extracto breve**.
- **Nunca** realizar scraping ni reproducir artículos completos ni descargar imágenes de prensa.

---

## 6. Política de Git y calidad

- Commits atómicos (`feat: ...`, `fix: ...`, `chore: ...`, `docs: ...`) **sin firmas de agente**.
- Validación obligatoria antes de cerrar cambios:
  - `uv run ruff check src tests`
  - `uv run ruff format --check src tests`
  - `uv run pytest`

---

## 7. Privacidad, autoría y seguridad

- **Autor:** Raúl Caro Pastorino (`@raupulus`) — [https://raupulus.dev](https://raupulus.dev)
- **Correo personal estrictamente prohibido:** NUNCA utilizar bajo ningún concepto ningún correo personal o privado del creador.
- **Único correo público permitido:** `public@raupulus.dev`
- **Sin secretos en el repositorio:** Nunca versionar tokens de Discord (`DISCORD_BOT_TOKEN`), archivos `.env`, bases SQLite locales (`data/`) ni rutas privadas. Usar siempre `.env.example`.
