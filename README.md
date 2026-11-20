<p align="left">
  <img src="./images/logo-512x512.png" alt="beacon-sift Discord Bot" width="84" align="left" style="margin-right: 16px;">
  <h1>beacon-sift — Bot de Discord</h1>
</p>

<br clear="left"/>

Servicio independiente en **Python 3.12 + Docker** que distribuye en tiempo real hacia canales de **Discord** las noticias técnicas, avisos locales y alertas CVE agregadas por [`feed.raupulus.dev`](https://feed.raupulus.dev) mediante *Embeds* con paleta radar HUD y *slash commands*.

---

## Objetivo del servicio

- Recibir alertas en vivo mediante **WebSockets públicos** (Laravel Reverb en el canal `beacon.news`, evento `news.created`) y publicarlas en cada canal suscrito según **tipo de fuente** (`type`) y **prioridad mínima** (`low`, `medium`, `high`, `critical`).
- Realizar **catch-up automático** tras reconexiones usando `since_id` para no perder noticias ni duplicar alertas ya enviadas.
- Exponer los 11 *slash commands* definidos en `BOT_COMMANDS_CONTRACT.md` con paridad exacta respecto a `bot-telegram/`.
- Operar desacoplado de la base de datos PostgreSQL de `web/`, usando persistencia local en **SQLite** (`data/bot.db`) y consumiendo únicamente los endpoints públicos `GET /api/v1/{status,sources,types,items}`.

---

## Catálogo de comandos (`BOT_COMMANDS_CONTRACT.md`)

- **Consultas (públicos):** `/help`, `/status`, `/sources [type]`, `/types`, `/latest [type] [priority] [limit]`, `/search <query> [type] [limit]`
- **Gestión del canal (administradores / `manage_channels`):** `/subscribe <type|all> [min_priority]`, `/unsubscribe <type|all>`, `/filters`, `/pause`, `/resume`

---

## Ejecución en desarrollo local (`uv`)

```bash
# 1. Instalar dependencias con Python 3.12
uv sync --python 3.12

# 2. Configurar variables de entorno
cp .env.example .env
# Rellenar DISCORD_BOT_TOKEN, DISCORD_ADMIN_IDS, WEB_API_BASE_URL, REVERB_WS_URL y REVERB_APP_KEY

# 3. Ejecutar lint y tests
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest

# 4. Arrancar el bot
uv run python -m src.main
```

---

## Despliegue con Docker

```bash
cp .env.example .env
# Configurar credenciales y URLs en .env
docker compose up -d --build
```

La base de datos SQLite de suscripciones se persiste en `./data/bot.db` (montado en `/app/data`).

---

## Estructura del repositorio

```text
bot-discord/
├── AGENTS.md            # Reglas y arquitectura del servicio
├── README.md            # Documentación general
├── .python-version      # Versión fijada (3.12)
├── .env.example         # Plantilla de variables de entorno
├── .gitignore           # Exclusiones Python, secretos y SQLite local
├── .dockerignore        # Exclusiones de build Docker
├── Dockerfile           # Imagen ligera python:3.12-slim no-root
├── docker-compose.yml   # Servicio independiente con volumen ./data
├── pyproject.toml       # Dependencias y configuración pytest/ruff
├── images/              # Logotipo oficial e iconos (SVG y PNG)
├── src/
│   ├── main.py          # Entrypoint: BeaconDiscordBot + CommandTree + ReverbListener
│   ├── config.py        # Settings desde .env
│   ├── models.py        # DTOs y enum Priority con colores hex de DESIGN.md
│   ├── storage.py       # Persistencia SQLite (suscripciones, pausa y deduplicación)
│   ├── api_client.py    # Cliente async /api/v1/*
│   ├── reverb_client.py # Cliente WebSocket Pusher v7 + catch-up
│   ├── embeds.py        # Constructores de Discord Embeds HUD
│   ├── permissions.py   # Validación de administradores / manage_channels
│   ├── dispatcher.py    # Enrutado y envío de Embeds con deduplicación
│   └── commands/        # Slash commands info.py y subscriptions.py
└── tests/               # Suite automatizada pytest + pytest-asyncio
```

---

## Autoría y contacto

Creado por **Raúl Caro Pastorino (`@raupulus`)**, desarrollador Full Stack senior (PHP/Laravel, Python, PostgreSQL, JavaScript/Vue, Tailwind CSS), administrador de sistemas Linux/VPS y entusiasta del software libre, hardware *maker* e IoT.

- **Web / Portfolio:** [https://raupulus.dev](https://raupulus.dev)
- **GitHub:** [https://github.com/raupulus](https://github.com/raupulus)
- **GitLab:** [https://gitlab.com/raupulus](https://gitlab.com/raupulus)
- **Correo público:** `public@raupulus.dev`
