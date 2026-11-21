# Módulo `permissions`

> Ficheros cubiertos: [`src/permissions.py`](../../src/permissions.py)

## 1. Qué hace y qué NO hace

- **Hace:**
  - Determina de forma **síncrona** si el usuario que invoca una `discord.Interaction` puede gestionar suscripciones o pausa del canal actual (`can_manage_subscriptions`).
- **NO hace:**
  - No realiza peticiones HTTP adicionales a Discord ni consulta caché de roles (usa los permisos efectivos entregados dentro del payload de la interacción).
  - No restringe los comandos de consulta ni `/filters`.

---

## 2. Modelo de datos

No define tablas ni modelos propios. Evalúa:
- `interaction.guild` (`None` en mensajes directos / DMs)
- `interaction.permissions` (`administrator`, `manage_channels`)
- `settings.allow_dm_subscriptions`

---

## 3. Flujos principales

Orden de evaluación en [`can_manage_subscriptions()`](../../src/permissions.py#L10-L16):

1. Si `interaction.guild is None` (mensaje directo / DM) → devuelve **`settings.allow_dm_subscriptions`** (`False` por defecto).
2. En servidor (*guild*): lee `perms = interaction.permissions` y devuelve **`bool(perms.administrator or perms.manage_channels)`** *(en Discord el propietario del servidor tiene `administrator=True` automáticamente)*.

---

## 4. Puntos de entrada (con auth, permisos y límites)

- `def can_manage_subscriptions(interaction: discord.Interaction, settings: Settings) -> bool`

---

## 5. Dependencias en ambos sentidos

- **Depende de:** `discord` (`discord.Interaction`), [`src/config.py`](../../src/config.py), [`docs/apis/discord-api/permisos-y-gateway.md`](../apis/discord-api/permisos-y-gateway.md).
- **Consumido por:** [`src/commands/subscriptions.py`](../../src/commands/subscriptions.py) (`/subscribe`, `/unsubscribe`, `/pause`, `/resume`).

---

## 6. Configuración (variables, valor por defecto y efecto)

| Variable (`.env`) | Atributo `Settings` | Valor por defecto | Efecto |
|---|---|---|---|
| `ALLOW_DM_SUBSCRIPTIONS` | `allow_dm_subscriptions` | `False` | Permite (`true`) o deniega (`false`) administrar alertas por DM. En servidores gestionan siempre sus propios dueños y administradores sin configuración manual en `.env`. |

---

## 7. Trampas conocidas

- **Permisos en Discord vs visibilidad del menú:** actualmente los *slash commands* de administración no usan `@app_commands.default_permissions(...)`; aparecen en el menú para todos y validan el permiso al ejecutarse (respondiendo `ephemeral=True` con `_DENIED_MSG`).
- **Permisos efectivos en `Interaction` reales `⚠️ sin verificar`:** comprobado mediante mocks en `test_permissions.py` y `test_commands.py`; pendiente validar en vivo contra servidor real con sobrescrituras de canal (*overwrites*).

---

## 8. Tests que lo cubren

- [`tests/test_permissions.py`](../../tests/test_permissions.py):
  - Permisos `administrator`, `manage_channels`, miembro sin permisos y flag `allow_dm_subscriptions` en DM.
- [`tests/test_commands.py`](../../tests/test_commands.py) (`test_subscription_commands_permissions_and_lifecycle`):
  - Miembro sin `administrator`/`manage_channels` en guild → denegado `ephemeral=True`.
  - Usuario en DM con `allow_dm_subscriptions=False` → denegado `ephemeral=True`.
  - Usuario con `manage_channels=True` o `administrator=True` → permitido.

---

## 9. Pendiente real

- Verificar en servidor Discord real el comportamiento en canales privados e hilos (`⚠️ sin verificar`).

---

> Creado: 2026-11-20 · Última revisión: 2026-11-21
