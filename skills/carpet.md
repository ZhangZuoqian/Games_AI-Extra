# Fake Player Control System (Carpet)

This skill governs the management of **Carpet mod** fake players (provided by the `games_ai_extra` plugin). Fake players are server-simulated virtual players capable of automated mining, attacking, building, and other tasks.

---

## Core Principles

> ⚠️ **Read this skill before operating!** Call `read_skills("carpet.md")` to get the full instructions. This file contains all specifications and best practices for fake player control — read it completely before any operation.

> ⚠️ **Check before controlling!** Before performing ANY control operation on a fake player, you **MUST call `get_online_players`** to confirm whether the fake player already exists. Note: `get_online_players` is a built-in GamesAI tool, always available.

> **Auto-spawn if missing!** If the fake player has not been spawned yet, **do NOT ask the user** — directly call `spawn_bot` to spawn it, then proceed with the requested control operation.

> 🤖 **Naming rule: all fake player names MUST have the `bot_` prefix!** Whatever name the user provides, you must prepend `bot_`. Example: user says "yello" → use `bot_yello`; user says "miner" → use `bot_miner`. When matching results from `get_online_players`, also use the `bot_`-prefixed name.

---

## Zero: Check if Fake Player Exists (Required)

Before performing **any control operation**, follow this workflow:

```
1. Call get_online_players to get the current online player list
2. Look for the target fake player name with `bot_` prefix (e.g., user says "yello" → search for `bot_yello`)
3. If exists → proceed directly with the control operation
4. If not exists → **do NOT ask the user; directly call `spawn_bot` to spawn, then execute the control operation**
```

**Carpet fake players appear in the online player list after spawning**, so `get_online_players` can directly verify their existence.

> 🤖 **Naming rule reminder**: all fake player names MUST have the `bot_` prefix! User says `yello` → use `bot_yello`. User says `miner1` → use `bot_miner1`. Use the prefixed name for spawning, controlling, and killing.

---

## Tool Reference

> 📦 The following tools are provided by the `carpet` module of `games_ai_extra`. Requires `"carpet": true` in config. `spawn_bot` and `kill_bot` additionally have `@register_bot_tool()`, making them available to the Mineflayer autonomous Bot controller.

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `get_online_players` | **Check online players (incl. fake players)** | None (GamesAI built-in) |
| `spawn_bot` | **Spawn a fake player** | `name` — bot name, `pos?`, `player?`, `dim?` |
| `kill_bot` | **Remove a fake player** | `name` |
| `bot_action` | Behavior control | `name`, `action`, `interval?` |
| `bot_move` | Movement control | `name`, `direction` |
| `bot_look` | Camera control | `name`, `target` |
| `bot_hotbar` | Hotbar slot | `name`, `slot` (1~9) |
| `bot_timed_action` | **Timed action (blocking)** | `name`, `action`, `duration` |
| `bot_command` | Raw custom command | `name`, `command` |

---

## 1. Spawning a Fake Player

```
# Spawn at world spawn
spawn_bot(name="Bob")

# Spawn at specific coordinates
spawn_bot(name="Bob", pos=[100, 64, -50])

# Spawn next to a player
spawn_bot(name="Bob", player="Steve")

# Spawn in a specific dimension at coordinates
spawn_bot(name="Bob", pos=[100, 64, -50], dim="minecraft:the_nether")

# Spawn in a specific dimension (no coordinates, uses ~ ~ ~)
spawn_bot(name="Bob", dim="minecraft:the_end")
```

- No parameters → spawns at **world spawn**
- `pos` (no `dim`) → spawns in the **Overworld** at the given coordinates, format `[x, y, z]`. ⚠️ `pos` and `player` are **mutually exclusive**
- `player` → spawns next to that player. ⚠️ **Do NOT pass `pos` or `dim` when using `player`** — `player` is mutually exclusive with both. Only pass `name` and `player`
- `dim` → spawns in the **specified dimension**. `dim` must be **exactly one of**: `"minecraft:overworld"`, `"minecraft:the_nether"`, `"minecraft:the_end"`. No other values allowed:
  - With `pos`: spawns at the specified coordinates in that dimension
  - Without `pos` (and without `player`): spawns at `~ ~ ~` in that dimension
  - ⚠️ `dim` and `player` are mutually exclusive
- 🤖 Name **MUST have `bot_` prefix** (e.g., `bot_stone_miner`, `bot_tree_farmer`)
- After spawning, the fake player is idle and needs action commands

---

## 2. Removing a Fake Player

```
kill_bot(name="Bob")
```

- Operation is **irreversible**
- To use the fake player again, re-spawn with `spawn_bot`

---

## 3. Behavior Control

```
bot_action(name="Bob", action="attack", interval=5)
```

| Action | Description | Typical Use |
|--------|-------------|-------------|
| `attack` | Attack entity in front | Mob farm AFK, zombie grinding |
| `use` | Right-click with held item | Farming, placing blocks, using items |
| `mine` | Break block in front | Mining, tree chopping, stone breaking |
| `stop` | **Stop all current actions** | Always stop before switching tasks |
| `drop` | Drop held item | Inventory cleanup |
| `dropStack` | Drop entire item stack | Bulk dropping |
| `jump` | Jump once | Crossing obstacles |
| `sneak` | Toggle sneak state | Safe edge operations |
| `swapHands` | Swap main/off hand items | Switch active item |
| `mount` | Ride nearby entity | Mount horse, enter minecart |
| `dismount` | Dismount vehicle | Exit mount |

**interval parameter:** Only applies to `attack`, `use`, `mine`. Unit is game ticks (20 ticks ≈ 1 second). Default: 1.

---

## 4. Movement Control

```
bot_move(name="Bob", direction="forward")
```

| Direction | Description |
|-----------|-------------|
| `forward` | Move forward |
| `backward` | Move backward |
| `left` | Strafe left |
| `right` | Strafe right |

- The fake player moves **continuously** until a `stop` action is sent
- Changing direction overrides the previous movement command

---

## 5. Camera Control

```
bot_look(name="Bob", target="north")
bot_look(name="Bob", target="100 64 -50")
```

- Direction words: `north`, `south`, `east`, `west`, `up`, `down`
- Coordinate format: `"x y z"` (space-separated, quoted)
- After setting look direction, attack/use/mine will target that direction

---

## 6. Hotbar Slot

```
bot_hotbar(name="Bob", slot=1)
```

- Range: **1 ~ 9**
- After switching, `attack`/`use`/`mine` use the new slot's item
- Example: switch to pickaxe first, then `mine` to break stone

---

## 7. Timed Actions

```
# Move forward for 5 seconds then auto-stop
bot_timed_action(name="Bob", action="forward", duration=5)

# Attack for 30 seconds then auto-stop
bot_timed_action(name="Bob", action="attack", duration=30)
```

| Action | Description |
|--------|-------------|
| `attack` | Continuous attacking |
| `use` | Continuous right-click |
| `mine` | Continuous mining |
| `forward` | Continuous forward movement |
| `backward` | Continuous backward movement |
| `left` | Continuous left strafe |
| `right` | Continuous right strafe |

- `duration` is in **seconds**; `stop` is auto-called when time elapses
- ⚠️ **This tool blocks until the time elapses** — no other operations can run during this period. Best for short tasks (≤ 60s). For longer tasks, use `bot_action` + manual `stop`
- For interval control (e.g., attack every 5 ticks), use `bot_action` with manual `stop`

---

## 8. Typical Workflows

### Scenario A: Create an AFK mob grinder bot
> User: "Spawn a bot here to kill mobs"
1. `get_online_players` — check if `bot_guard` is online
2. If not online → `spawn_bot(name="bot_guard")` — auto-spawn (don't ask)
3. `bot_hotbar(name="bot_guard", slot=1)` — ensure weapon equipped
4. `bot_look(name="bot_guard", target="north")` — face mob spawn direction
5. `bot_action(name="bot_guard", action="attack", interval=10)` — continuous attack

### Scenario B: Control existing bot to mine
> User: "Make miner1 mine the stone in front"
1. `get_online_players` — check if `bot_miner1` exists (auto-add `bot_` prefix)
2. If not online → `spawn_bot(name="bot_miner1")` — auto-spawn
3. `bot_look(name="bot_miner1", target="down")` — look down
4. `bot_hotbar(name="bot_miner1", slot=1)` — switch to pickaxe
5. `bot_action(name="bot_miner1", action="mine", interval=1)` — continuous mining

### Scenario C: Timed forward movement
> User: "Make the bot walk forward for 10 seconds then stop"
1. `get_online_players` — check if target bot exists (use `bot_`-prefixed name)
2. If not online → auto `spawn_bot`
3. `bot_timed_action(name="bot_xxx", action="forward", duration=10)` — walk 10s then auto-stop

### Scenario D: Stop and remove a bot
> User: "Stop the mining bot"
1. `get_online_players` — check if `bot_miner1` exists
2. `bot_action(name="bot_miner1", action="stop")` — stop actions
3. `kill_bot(name="bot_miner1")` — remove the bot

### Scenario E: Spawn a bot next to a player
> User: "Spawn a bot next to me"
1. `get_online_players` — get online player list, confirm target player is online
2. `spawn_bot(name="bot_helper", player="<username>")` — spawn next to the player (⚠️ `player` and `pos` are mutually exclusive, don't pass both)
3. Continue with action commands as needed

### Scenario F: Spawn a bot in a specific dimension
> User: "Spawn a bot in the Nether at (100, 64, -50)"
1. `get_online_players` — check if `bot_miner` is online
2. If not online → `spawn_bot(name="bot_miner", pos=[100, 64, -50], dim="minecraft:the_nether")` — spawn in Nether
3. Continue with action commands

> User: "Spawn a bot in the End, no specific coordinates"
1. `get_online_players` — check if `bot_guard` is online
2. If not online → `spawn_bot(name="bot_guard", dim="minecraft:the_end")` — spawn at ~ ~ ~ in the End
3. Continue with action commands

---

## Important Notes

- **Read this skill first**: Always call `read_skills("carpet.md")` before operating fake players
- **Check before control**: Always call `get_online_players` to confirm the bot is online before any control operation (`get_online_players` is a GamesAI built-in tool, always available)
- **Auto-spawn if missing**: If the bot is not online, do NOT ask the user — directly `spawn_bot` and continue
- 🤖 **Naming rule**: All fake player names MUST have the `bot_` prefix! Always prepend `bot_` to whatever name the user provides
- **`player` is mutually exclusive with all other parameters**: When spawning with `player`, do NOT pass `pos` or `dim`. Only use `name` and `player`
- **`dim` dimension support**: Use `dim` to spawn in a specific dimension. Can combine with `pos` (specific coordinates in that dimension) or use alone (spawns at ~ ~ ~). ⚠️ `dim` and `player` are mutually exclusive
- **Stop before switching tasks**: Always call `stop` before changing a bot's task
- ⚠️ **`bot_timed_action` blocks**: This tool waits for the specified duration before returning. For long operations, use `bot_action` + manual `stop` instead
- **Unique bot names**: Two bots cannot share the same name simultaneously
- **Permission required**: The `/player` command requires server operator permissions (requires fabric-carpet mod installed)
- **Don't overuse**: Too many fake players can degrade server performance
- **Safety first**: Confirm the bot isn't performing critical tasks before removing it
- For operations not covered by the above tools, use `bot_command` to send raw commands
