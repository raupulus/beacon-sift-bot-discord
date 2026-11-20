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
├── AGENTS.md            # Reglas y arquitectura del servicio
├── README.md            # Documentación general y autoría
├── .python-version      # Versión fijada (3.12)
├── .env.example         # Variables de entorno sin secretos
├── .gitignore           # Exclusiones de Python, .venv, .env y SQLite local
├── .dockerignore        # Exclusiones para build Docker
├── Dockerfile           # Imagen python:3.12-slim ejecutada como botuser
├── docker-compose.yml   # Servicio independiente con volumen ./data:/app/data
├── pyproject.toml       # Dependencias (uv/pip), pytest y ruff
├── images/              # Logotipo oficial e iconos del bot (logo.svg, PNGs)
├── src/
│   ├── main.py          # BeaconDiscordBot (CommandTree) + ReverbListener
│   ├── config.py        # Validación de entorno con pydantic-settings
│   ├── models.py        # Priority (con color_int HUD), NewsItem, SourceInfo, TypeInfo, ApiStatus
│   ├── storage.py       # Persistencia async SQLite (aiosqlite)
│   ├── api_client.py    # Cliente HTTP async (httpx) para /api/v1/*
│   ├── reverb_client.py # Cliente WebSocket Pusher v7 (websockets)
│   ├── embeds.py        # Constructores de Discord Embeds con paleta DESIGN.md
│   ├── permissions.py   # Validación de administrator/manage_channels y DISCORD_ADMIN_IDS
│   ├── dispatcher.py    # Filtrado, deduplicación y pausa automática ante Forbidden/NotFound
│   └── commands/        # info.py y subscriptions.py
└── tests/               # Tests automatizados pytest / pytest-asyncio
```

### Reglas de aislamiento
- **Nunca** importar módulos de `web/` o `bot-telegram/` ni conectarse directamente a la base de datos PostgreSQL de `web/`.
- Toda comunicación con `web/` se realiza exclusivamente por **WebSockets públicos** (Laravel Reverb) y por los **endpoints `GET` JSON de solo lectura** (`/api/v1/...`).

---

## 3. Contrato obligatorio de comandos (`BOT_COMMANDS_CONTRACT.md`)

Este bot **DEBE cumplir íntegramente** el contrato común definido en el `BOT_COMMANDS_CONTRACT.md` de `beacon-sift`:

- **Consultas (*slash commands*):** `/help`, `/status`, `/sources [type]`, `/types`, `/latest [type] [priority] [limit]`, `/search <query> [type] [limit]`
- **Gestión de canal (solo administradores / `manage_channels`):** `/subscribe <type|all> [min_priority]`, `/unsubscribe <type|all>`, `/filters`, `/pause`, `/resume`
- **Paridad estricta:** No introducir comandos huérfanos fuera del contrato. Si se modifica un comando, parámetro o permiso, actualizar primero `BOT_COMMANDS_CONTRACT.md` y replicarlo en `bot-telegram/`.
- **Formato en Discord:** *Embeds* limpios con color según prioridad (`low=#64748B`, `medium=#38BDF8`, `high=#F59E0B`, `critical=#EF4444`), titular enlazado a la fuente original, fuente, tipo, prioridad, fecha (`timestamp`) y extracto breve (*snippet*) bajo límites de Discord.

---

## 4. Directrices legales (agregación responsable)

- Publicar únicamente **titular enlazado a la fuente original, fuente, tipo, prioridad, fecha y extracto breve**.
- **Nunca** realizar scraping ni reproducir artículos completos ni descargar imágenes de prensa.

---

## 5. Política de Git y calidad

- Commits atómicos (`feat: ...`, `fix: ...`, `chore: ...`, `docs: ...`).
- Validación obligatoria antes de cerrar cambios:
  - `uv run ruff check src tests`
  - `uv run ruff format --check src tests`
  - `uv run pytest`

---

## 6. Privacidad, autoría y seguridad

- **Autor:** Raúl Caro Pastorino (`@raupulus`) — [https://raupulus.dev](https://raupulus.dev)
- **Correo personal estrictamente prohibido:** NUNCA utilizar bajo ningún concepto ningún correo personal o privado del creador.
- **Único correo público permitido:** `public@raupulus.dev`
- **Sin secretos en el repositorio:** Nunca versionar tokens de Discord (`DISCORD_BOT_TOKEN`), archivos `.env`, bases SQLite locales (`data/`) ni rutas privadas. Usar siempre `.env.example`.
