<div align="center">

# GamesAI Extra for MCDReforged

English  |  [简体中文](/README.zh-CN.md)  |  [繁體中文](/README.zh-TW.md)

[Report an Issue](https://github.com/PengZixuan30/Games_AI-Extra/issues/new)  |  [Share an Idea](https://github.com/PengZixuan30/Games_AI-Extra/discussions/new/choose)

</div>

> [!NOTE]
> **GamesAI Extra** is a functional extension for [GamesAI](https://github.com/PengZixuan30/Games_AI). It provides Carpet fake player (bot) control tools, allowing the AI to spawn, control, and manage fake players on your Minecraft server.

> [!IMPORTANT]
> This plugin requires **GamesAI >= 0.6.0** to be installed and loaded first.

<details>
<summary>Table of Contents (click to expand)</summary>

- [GamesAI Extra for MCDReforged](#gamesai-extra-for-mcdreforged)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Tools](#tools)
    - [Spawn \& Kill](#spawn--kill)
    - [Behavior Control](#behavior-control)
    - [Movement Control](#movement-control)
    - [Camera Control](#camera-control)
    - [Hotbar](#hotbar)
    - [Timed Actions](#timed-actions)
    - [Custom Commands](#custom-commands)
  - [License](#license)

</details>

## Installation

Install this plugin alongside [GamesAI](https://github.com/PengZixuan30/Games_AI) in your MCDR plugin directory.

Use the following command in the MCDR console:

`!!MCDR plugin install games_ai_extra`

---

Or download it from the [MCDR Plugin Repository](https://mcdreforged.com/plugin/games_ai_extra) and place it in your plugin directory.

No additional Python packages are required — this plugin only depends on `games_ai`.

## Configuration

The default configuration file (`config/games_ai_extra/config.json`) structure is as follows:

```json
{
    "carpet": true
}
```

- **carpet**: Set to `true` to enable the Carpet fake player tools. Set to `false` to disable them.

After modifying the configuration, use `!!gamesai reload` to apply the changes.

## Tools

Once enabled, the following tools are automatically registered with GamesAI and can be called by the AI through `!!ask`.

### Spawn & Kill

| Tool | Parameters | Description |
|:---:|:---:|:---|
| `spawn_bot` | `name`, `pos?`, `player?`, `dim?` | Spawn a fake player on the server. Specify `pos` (coordinates `[x, y, z]`) to spawn at a location, or `player` (username) to spawn next to a player. `pos` and `player` are mutually exclusive. Optionally specify `dim` (e.g. `minecraft:the_nether`) to spawn in a different dimension. If no location is given, spawns at world spawn. |
| `kill_bot` | `name` | Remove (kill) a fake player. This operation is irreversible — use `spawn_bot` to recreate if needed. |

### Behavior Control

| Tool | Parameters | Description |
|:---:|:---:|:---|
| `bot_action` | `name`, `action`, `interval?` | Make a fake player perform an action. Supported actions: `attack` (requires weapon), `use` (right-click target), `mine` (break block in front), `stop` (cancel all actions), `drop` (drop held item), `dropStack` (drop entire stack), `jump`, `sneak` (toggle), `swapHands`, `mount` (ride nearby entity), `dismount`. Optional `interval` in game ticks (default: 1). |

### Movement Control

| Tool | Parameters | Description |
|:---:|:---:|:---|
| `bot_move` | `name`, `direction` | Make a fake player move continuously in a direction: `forward`, `backward`, `left`, or `right`. The bot keeps moving until you send a `stop` action or change direction. |

### Camera Control

| Tool | Parameters | Description |
|:---:|:---:|:---|
| `bot_look` | `name`, `target` | Make a fake player look at a direction or coordinates. `target` can be a direction word (`north`, `south`, `east`, `west`, `up`, `down`) or coordinates (`"x y z"`, e.g. `"100 64 200"`). |

### Hotbar

| Tool | Parameters | Description |
|:---:|:---:|:---|
| `bot_hotbar` | `name`, `slot` | Switch the fake player's selected hotbar slot (1–9). After switching, actions like attack/use/mine will use the item in that slot. |

### Timed Actions

| Tool | Parameters | Description |
|:---:|:---:|:---|
| `bot_timed_action` | `name`, `action`, `duration` | Make a fake player perform an action for a specified duration (in seconds), then automatically stop. Supports: `attack`, `use`, `mine`, `forward`, `backward`, `left`, `right`. Best suited for short operations (≤ 60s). Note: blocks the current AI conversation until time is up. |

### Custom Commands

| Tool | Parameters | Description |
|:---:|:---:|:---|
| `bot_command` | `name`, `command` | Send a raw custom `/player` command for advanced operations not covered by the above tools. The command is automatically prefixed with `player <name>`. Requires familiarity with Carpet bot commands. |

## License

MIT License, Copyright (c) 2026 yello

<div align = "center">

---

[Back to Top](#gamesai-extra-for-mcdreforged)

</div>
