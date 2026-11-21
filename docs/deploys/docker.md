# Despliegue con Docker (`docker.md`)

Guía verificada directamente contra [`Dockerfile`](../../Dockerfile), [`docker-compose.yml`](../../docker-compose.yml), [`.dockerignore`](../../.dockerignore) y [`.env.example`](../../.env.example).

---

## 1. Resumen del contenedor

- **Imagen base:** `python:3.12-slim`
- **Instalación:** `pip install --no-cache-dir .` (dependencias declaradas en [`pyproject.toml`](../../pyproject.toml)).
- **Usuario de ejecución:** usuario sin privilegios `botuser`.
- **Directorio de trabajo:** `/app` (`src/` e `images/` copiados).
- **Persistencia:** volumen `/app/data` con variable `ENV BOT_DB_PATH=/app/data/bot.db` definida en el `Dockerfile`.
- **Comando de arranque:** `CMD ["python", "-m", "src.main"]`.

---

## 2. Requisitos previos en el host / VPS

1. Docker Engine + Docker Compose v2 (`docker compose`).
2. Acceso de red desde el contenedor hacia el servicio `web/`:
   - `WEB_API_BASE_URL` (HTTP/HTTPS hacia `/api/v1/*`)
   - `REVERB_WS_URL` (`ws://` o `wss://` hacia Laravel Reverb)
3. Aplicación creada en Discord Developer Portal con `DISCORD_BOT_TOKEN` y permisos de invitación en el servidor destino (`applications.commands`, `View Channels`, `Send Messages`, `Embed Links` y `Send Messages in Threads` si se usa en hilos).

---

## 3. Pasos de despliegue

1. Preparar variables de entorno en `bot-discord/` sin versionar `.env`:
   ```bash
   cp .env.example .env
   ```
2. Rellenar en `.env` al menos:
   - `DISCORD_BOT_TOKEN`
   - `DISCORD_DEV_GUILD_ID` *(solo en desarrollo; dejar vacío en producción para sincronización global únicamente)*
   - `WEB_API_BASE_URL` y `REVERB_WS_URL` apuntando al servicio `web/` accesible desde Docker *(evitar `127.0.0.1` dentro del contenedor salvo red `host`)*
   - `REVERB_APP_KEY` y `REVERB_CHANNEL` coincidentes con `web/`
3. Construir y levantar en segundo plano:
   ```bash
   docker compose up -d --build
   ```
4. Verificar logs de arranque:
   ```bash
   docker compose logs -f bot-discord
   ```
   Deben aparecer líneas `INFO` en inglés confirmando sincronización de *slash commands*, conexión a Discord (`Discord bot connected as ...`) y suscripción a Reverb (`Subscribed to public WebSocket channel '...'`).

---

## 4. Persistencia SQLite con volumen nombrado

- [`docker-compose.yml`](../../docker-compose.yml) monta el volumen nombrado `bot_discord_data:/app/data`, fija `BOT_DB_PATH=/app/data/bot.db` y configura `restart: unless-stopped`.
- Al usar un **volumen nombrado** en lugar de un *bind-mount* `./data`, Docker inicializa automáticamente el volumen heredando los permisos `botuser:botuser` definidos en el [`Dockerfile`](../../Dockerfile), evitando errores `readonly database` en servidores Linux VPS al recrear o actualizar el contenedor.
- Para copias de seguridad consistentes en modo WAL (`bot.db`, `bot.db-wal`, `bot.db-shm`), realiza backup usando `.backup` de `sqlite3` dentro del contenedor o con el contenedor detenido brevemente.

---

## 5. Actualización y comprobación mínima

```bash
git pull
docker compose up -d --build
docker compose logs --tail=50 bot-discord
```

---

> Creado: 2026-11-20 · Última revisión: 2026-11-21
