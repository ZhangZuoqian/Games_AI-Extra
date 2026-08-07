<div align="center">

# GamesAI Extra for MCDReforged

[English](/README.md)  |  简体中文  |  [繁體中文](/README.zh-TW.md)

[反馈问题](https://github.com/PengZixuan30/Games_AI-Extra/issues/new)  |  [反馈想法](https://github.com/PengZixuan30/Games_AI-Extra/discussions/new/choose)

</div>

> [!NOTE]
> **GamesAI Extra** 是 [GamesAI](https://github.com/PengZixuan30/Games_AI) 的功能性扩展插件。它为 AI 提供了 Carpet 假人（Bot）控制工具，允许 AI 在你的 Minecraft 服务器上生成、控制和管理假人。

> [!IMPORTANT]
> 此插件需要 **GamesAI >= 0.6.0** 已安装并先加载。

<details>
<summary>目录（点击展开）</summary>

- [GamesAI Extra for MCDReforged](#gamesai-extra-for-mcdreforged)
  - [安装](#安装)
  - [配置](#配置)
  - [工具](#工具)
    - [生成与移除](#生成与移除)
    - [行为控制](#行为控制)
    - [移动控制](#移动控制)
    - [视角控制](#视角控制)
    - [快捷栏](#快捷栏)
    - [限时动作](#限时动作)
    - [自定义指令](#自定义指令)
  - [许可证](#许可证)

</details>

## 安装

将此插件与 [GamesAI](https://github.com/PengZixuan30/Games_AI) 一起安装到你的 MCDR 插件目录中。

在 MCDR 控制台中使用以下命令安装：

`!!MCDR plugin install games_ai_extra`

---

或者从 [MCDR 插件仓库](https://mcdreforged.com/plugin/games_ai_extra) 获取并放置到你的插件目录中。

无需额外安装 Python 包——此插件仅依赖 `games_ai`。

## 配置

默认配置文件（`config/games_ai_extra/config.json`）结构如下：

```json
{
    "carpet": true
}
```

- **carpet**：设为 `true` 启用 Carpet 假人工具；设为 `false` 禁用。

修改配置后，使用 `!!gamesai reload` 使更改生效。

## 工具

启用后，以下工具会自动注册到 GamesAI 中，AI 可通过 `!!ask` 调用。

### 生成与移除

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `spawn_bot` | `name`、`pos?`、`player?`、`dim?` | 在服务器中生成一个假人。可指定 `pos`（坐标 `[x, y, z]`）在特定位置生成，或指定 `player`（玩家名）在某玩家身边生成。`pos` 与 `player` 互斥。可选指定 `dim`（如 `minecraft:the_nether`）在特定维度生成。不指定位置时在世界出生点生成。 |
| `kill_bot` | `name` | 移除（杀死）一个假人。此操作不可逆——如需重新使用请用 `spawn_bot` 重新生成。 |

### 行为控制

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_action` | `name`、`action`、`interval?` | 控制假人执行动作。支持的动作：`attack`（攻击，需手持武器）、`use`（右键目标）、`mine`（挖掘面前方块）、`stop`（停止所有动作）、`drop`（丢弃手中物品）、`dropStack`（丢弃整组物品）、`jump`（跳跃）、`sneak`（切换潜行）、`swapHands`（交换左右手）、`mount`（骑乘附近实体）、`dismount`（下马）。可选 `interval` 为游戏刻（tick）间隔（默认 1）。 |

### 移动控制

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_move` | `name`、`direction` | 让假人持续向某个方向移动：`forward`（前进）、`backward`（后退）、`left`（向左）、`right`（向右）。假人会一直移动，直到发送 `stop` 动作或改变方向。 |

### 视角控制

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_look` | `name`、`target` | 控制假人看向某个方向或坐标。`target` 可以是方向词（`north`、`south`、`east`、`west`、`up`、`down`）或坐标（`"x y z"`，如 `"100 64 200"`）。 |

### 快捷栏

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_hotbar` | `name`、`slot` | 切换假人当前选中的快捷栏格子（1~9）。切换后攻击/使用/挖掘等操作将使用对应格子的物品。 |

### 限时动作

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_timed_action` | `name`、`action`、`duration` | 让假人执行一个限时动作，到达指定秒数后自动停止。支持：`attack`、`use`、`mine`、`forward`、`backward`、`left`、`right`。适合短时间操作（建议 ≤ 60 秒）。注意：会阻塞当前 AI 对话直到时间到达。 |

### 自定义指令

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_command` | `name`、`command` | 向假人发送一条原始自定义 `/player` 指令，用于上述工具无法覆盖的高级操作。命令会自动补全为 `player <name> <command>` 格式。需要了解 Carpet 假人指令。 |

## 许可证

MIT License, Copyright (c) 2026 yello

<div align = "center">

---

[回到顶部](#gamesai-extra-for-mcdreforged)

</div>
