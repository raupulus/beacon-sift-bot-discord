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
- `interaction.user.id`
- `interaction.guild` (`None` en mensajes directos / DMs)
- `interaction.permissions` (`administrator`, `manage_channels`)
- `settings.admin_ids` y `settings.allow_dm_subscriptions`

---

## 3. Flujos principales

Orden de evaluación en [`can_manage_subscriptions()`](../../src/permissions.py#L10-L19):

1. Si `interaction.user.id in settings.admin_ids` → devuelve **`True`** *(superadministrador global del bot)*.
2. Si `interaction.guild is None` (mensaje directo / DM) → devuelve **`settings.allow_dm_subscriptions`** (`False` por defecto).
3. En servidor (*guild*): lee `perms = interaction.permissions` y devuelve **`bool(perms.administrator or perms.manage_channels)`**.

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
| `DISCORD_ADMIN_IDS` | `discord_admin_ids` (`admin_ids`) | `""` | IDs numéricos con permiso administrativo global en cualquier servidor o DM. |
| `ALLOW_DM_SUBSCRIPTIONS` | `allow_dm_subscriptions` | `False` | Permite (`true`) o deniega (`false`) administrar alertas por DM a usuarios fuera de `DISCORD_ADMIN_IDS`. |

---

## 7. Trampas conocidas

- **Permisos en Discord vs visibilidad del menú:** actualmente los *slash commands* de administración no usan `@app_commands.default_permissions(...)`; aparecen en el menú para todos y validan el permiso al ejecutarse (respondiendo `ephemeral=True` con `_DENIED_MSG`), lo que permite además respetar `DISCORD_ADMIN_IDS` aunque el usuario no tenga rol admin del servidor.
- **Permisos efectivos en `Interaction` reales `⚠️ sin verificar`:** comprobado mediante mocks en `test_commands.py`; pendiente validar en vivo contra servidor real con sobrescrituras de canal (*overwrites*).

---

## 8. Tests que lo cubren

- [`tests/test_commands.py`](../../tests/test_commands.py) (`test_subscription_commands_permissions_and_lifecycle`):
  - Miembro sin `administrator`/`manage_channels` en guild → denegado `ephemeral=True`.
  - Usuario no admin en DM (`guild_id=None`, `allow_dm_subscriptions=False`) → denegado `ephemeral=True`.
  - Usuario con `manage_channels=True`, con `administrator=True` o incluido en `DISCORD_ADMIN_IDS` → permitido.

---

## 9. Pendiente real

- Verificar en servidor Discord real el comportamiento en canales privados e hilos (`⚠️ sin verificar`).

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
