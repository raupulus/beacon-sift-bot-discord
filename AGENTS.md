# AGENTS.md — Guía de contexto y reglas para `beacon-sift-bot-discord`

Este documento define la arquitectura, convenciones y reglas obligatorias que cualquier agente o desarrollador debe seguir al trabajar en **`beacon-sift-bot-discord`** (`bot-discord/`), servicio independiente de **beacon-sift** (`https://feed.raupulus.dev`).

---

## 1. Propósito del servicio

Bot de **Discord** escrito en **Python** y empaquetado con **Docker** que conecta canales de servidores Discord con las noticias y alertas agregadas por el servicio `web/` (`feed.raupulus.dev`):

- **Alertas en tiempo real:** Se suscribe al canal WebSocket público de Laravel Reverb emitido por `web/` (`beacon.news`, evento `news.created`) para publicar al instante las entradas nuevas que cumplan los filtros configurados en cada canal.
- **Consultas bajo demanda:** Consume los 4 endpoints públicos `GET` JSON de solo lectura de `web/` (`/api/v1/status`, `/api/v1/sources`, `/api/v1/types`, `/api/v1/items`).
- **Suscripciones por canal:** Almacena localmente en su propio almacenamiento persistente (p. ej. SQLite en volumen Docker) las reglas por servidor/canal (`guild_id`, `channel_id`, `type`, `min_priority`, estado `paused/active` y último cursor procesado).

---

## 2. Estructura del repositorio independiente

Este repositorio es **totalmente independiente** respecto a `web/` y `bot-telegram/`:

```text
bot-discord/
├── AGENTS.md           # Reglas y arquitectura del servicio
├── README.md           # Documentación general y autoría
├── .gitignore          # Exclusiones de Python, entornos y datos locales
├── images/             # Logotipo oficial e iconos del bot (logo.svg, PNGs)
└── src/                # Código fuente Python del bot
```

### Reglas de aislamiento
- **Nunca** importar módulos de `web/` o `bot-telegram/` ni conectarse directamente a la base de datos PostgreSQL de `web/`.
- Toda comunicación con `web/` se realiza exclusivamente por **WebSockets públicos** (Laravel Reverb) y por los **endpoints `GET` JSON de solo lectura** (`/api/v1/...`).
- Gestiona sus propias dependencias, `Dockerfile`, `.env.example`, tests y persistencia local.

---

## 3. Contrato obligatorio de comandos (`BOT_COMMANDS_CONTRACT.md`)

Este bot **DEBE cumplir íntegramente** el contrato común definido en el `BOT_COMMANDS_CONTRACT.md` del proyecto `beacon-sift`:

- **Consultas (*slash commands*):** `/help`, `/status`, `/sources [type]`, `/types`, `/latest [type] [priority] [limit]`, `/search <query> [type] [limit]`
- **Gestión de canal (solo administradores):** `/subscribe <type|all> [min_priority]`, `/unsubscribe <type|all>`, `/filters`, `/pause`, `/resume`
- **Paridad estricta:** Si se modifica un comando, parámetro o permiso, debe actualizarse primero `BOT_COMMANDS_CONTRACT.md` y replicarse de forma equivalente en `bot-telegram/`.
- **Formato en Discord:** *Embeds* limpios con color semántico según prioridad (`low`, `medium`, `high`, `critical`), titular enlazado a la fuente original, fuente, tipo, prioridad, fecha y extracto breve (*snippet*).

---

## 4. Directrices legales (agregación responsable)

- Publicar únicamente **titular enlazado a la fuente original, fuente, tipo, prioridad, fecha y extracto breve**.
- **Nunca** realizar scraping ni reproducir artículos completos.

---

## 5. Política de Git y calidad

- Commits atómicos y en imperativo/Conventional Commits con enfoque claro (`feat: ...`, `fix: ...`, `docs: ...`).
- Código Python limpio, tipado (`type hints`) y con tests automatizados antes de cerrar cambios funcionales.

---

## 6. Privacidad, autoría y seguridad

- **Autor:** Raúl Caro Pastorino (`@raupulus`) — [https://raupulus.dev](https://raupulus.dev)
- **Correo personal estrictamente prohibido:** NUNCA utilizar bajo ningún concepto ningún correo personal o privado del creador.
- **Único correo público permitido:** `public@raupulus.dev`
- **Sin secretos en el repositorio:** Nunca versionar tokens de Discord (`DISCORD_BOT_TOKEN`), archivos `.env`, bases SQLite locales ni rutas privadas. Usar siempre `.env.example`.
