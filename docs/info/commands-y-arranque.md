# Módulo `commands-y-arranque`

> Ficheros cubiertos: [`src/main.py`](../../src/main.py), [`src/commands/__init__.py`](../../src/commands/__init__.py), [`src/commands/info.py`](../../src/commands/info.py), [`src/commands/subscriptions.py`](../../src/commands/subscriptions.py)

## 1. Qué hace y qué NO hace

- **Hace:**
  - Configura el sistema de logging y comprueba `DISCORD_BOT_TOKEN` antes de iniciar `BeaconDiscordBot` (`src/main.py`).
  - Inicializa `BotStorage`, registra exactamente los **11 *slash commands*** en `app_commands.CommandTree`, los sincroniza en `DISCORD_DEV_GUILD_ID` o globalmente, y arranca `ReverbListener.run_forever()` en `setup_hook()`.
  - Detiene ordenadamente la tarea WebSocket, cierra `httpx.AsyncClient`, cierra `BotStorage` y llama a `super().close()` en `BeaconDiscordBot.close()`.
- **NO hace:**
  - No usa comandos de prefijo de texto (`!comando`); `discord.Intents.default()` mantiene `message_content=False`.
  - No define comandos propios fuera de `BOT_COMMANDS_CONTRACT.md`.

---

## 2. Modelo de datos

En [`src/commands/__init__.py`](../../src/commands/__init__.py):
- `@dataclass(slots=True) class BotAppContext`: agrupa `settings`, `storage`, `api_client`, `dispatcher` y `reverb_listener`.
- `PRIORITY_CHOICES: list[app_commands.Choice[str]]`: las 4 prioridades del contrato (`low`, `medium`, `high`, `critical`) mostradas como selector nativo en Discord.

En [`src/main.py`](../../src/main.py):
- `BeaconDiscordBot(discord.Client)`: posee `self.tree`, `self.storage`, `self.api_client`, `self.dispatcher`, `self.reverb_listener`, `self.app_ctx`, `self._stop_event` y `self._reverb_task`.

---

## 3. Flujos principales

### Arranque y ciclo de vida (`src/main.py`)

1. `main()` carga `Settings()`, configura `logging.basicConfig()` (y silencia `httpx` a `WARNING`), valida `discord_bot_token.strip()` (`sys.exit(1)` si falta) y ejecuta `bot.run(settings.discord_bot_token, log_handler=None)`.
2. `setup_hook()`:
   - `await self.storage.initialize()`
   - `register_commands(self.tree, self.app_ctx)`
   - Si `settings.dev_guild_id is not None`: `copy_global_to(guild=...)` + `await self.tree.sync(guild=...)`. Si no: `await self.tree.sync()`.
   - Crea tarea `asyncio` `"reverb-listener"` ejecutando `reverb_listener.run_forever(self._stop_event)`.
3. `on_ready()`: registra `INFO` (`Discord bot connected as %s`).
4. `close()`: activa `_stop_event`, cancela `_reverb_task`, cierra `api_client` y `storage`, llama a `super().close()` y registra cierre.

### Manejo de interacciones (`src/commands/`)

- Comandos rápidos o fallos de validación/permisos: responden de inmediato con `interaction.response.send_message(..., ephemeral=True)` (salvo `/help` que envía Embed público).
- Comandos con I/O (`web/` o SQLite): ejecutan `await interaction.response.defer(...)` primero y devuelven resultado por `interaction.followup.send(...)`. Detalle completo de los 11 comandos en [`commands.md`](./commands.md).

---

## 4. Puntos de entrada (con auth, permisos y límites)

- CLI / contenedor: `python -m src.main` → `main()`.
- Helpers compartidos en `src/commands/__init__.py`: `resolve_priority_arg()`, `register_commands()`.
- Registro modular: `register_info_commands(tree, ctx)` y `register_subscription_commands(tree, ctx)`.

---

## 5. Dependencias en ambos sentidos

- **Depende de:** `discord` (`Client`, `Intents`, `Object`, `app_commands`, `Interaction`), y todos los módulos internos (`config`, `models`, `storage`, `api_client`, `reverb_client`, `embeds`, `permissions`, `dispatcher`).
- **Consumido por:** `Dockerfile` (`CMD ["python", "-m", "src.main"]`) y `tests/test_commands.py`.

---

## 6. Configuración (variables, valor por defecto y efecto)

| Variable (`.env`) | Atributo `Settings` | Valor por defecto | Efecto |
|---|---|---|---|
| `DISCORD_BOT_TOKEN` | `discord_bot_token` | `""` | Token del bot; obligatorio para iniciar `main()`. |
| `DISCORD_DEV_GUILD_ID` | `discord_dev_guild_id` | `""` | Si tiene un ID válido, sincroniza *slash commands* en ese servidor de desarrollo en vez de solo globalmente. |
| `LOG_LEVEL` | `log_level` | `"INFO"` | Nivel raíz de logging en `configure_logging()`. |
| `BOT_TIMEZONE` | `bot_timezone` | `"Europe/Madrid"` | Zona horaria pasada a `build_status_embed` y `build_news_list_embed`. |

---

## 7. Trampas conocidas

- **Anotación estricta para `@app_commands.choices` en `discord.py 2.7.1`:** usar `Choice[str] | str | None` lanza `TypeError` al registrar el comando en `CommandTree`. Debe anotarse siempre como `app_commands.Choice[str] | None` (documentado en [`ERRATAS.md`](../apis/discord-api/ERRATAS.md)).
- **`tree.copy_global_to(guild=...)` + ejecución posterior sin `DISCORD_DEV_GUILD_ID`:** si primero sincronizas con `DISCORD_DEV_GUILD_ID` y luego arrancas el mismo bot en producción global contra el mismo servidor, el servidor dev verá comandos duplicados hasta limpiar los comandos de guild.
- **Validación con `DISCORD_BOT_TOKEN` real `⚠️ sin verificar`:** `setup_hook()`, `on_ready()` y el Gateway WebSocket de `discord.py` no se han ejecutado aún contra Discord real.

---

## 8. Tests que lo cubren

- [`tests/test_commands.py`](../../tests/test_commands.py):
  - `test_registers_exact_contract_commands_and_runs_info_commands` (comprueba conjunto exacto de 11 nombres en `CommandTree` y flujos `/help`, `/status`, `/sources`, `/types`, `/latest`, límite `1..10`, `/search`).
  - `test_info_commands_handle_unavailable_api` (`/status` degradado y `/latest` ante HTTP `503`).
  - `test_subscription_commands_permissions_and_lifecycle` (permisos, validaciones, `/subscribe`, `/pause`, `/filters`, `/resume`, `/unsubscribe`).

> Nota: `BeaconDiscordBot.setup_hook()` y `close()` (`src/main.py`) no tienen test unitario dedicado; solo compilación, `register_commands` e import check Docker.

---

## 9. Pendiente real

- Probar arranque real `python -m src.main` con `DISCORD_BOT_TOKEN` (Gateway, `tree.sync()`, *choices* en cliente Discord y respuesta `followup`) (`⚠️ sin verificar`).
- Añadir soporte de árbol explícito de *graceful error* en `tree.on_error` si algún error inesperado ocurriera tras `defer()`.

---

> Creado: 2026-11-20 · Última revisión: 2026-11-20
