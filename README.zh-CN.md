<div align="center">

# GamesAI Extra for MCDReforged

[English](/README.md)  |  简体中文  |  [繁體中文](/README.zh-TW.md)

[反馈问题](https://github.com/PengZixuan30/Games_AI-Extra/issues/new)  |  [反馈想法](https://github.com/PengZixuan30/Games_AI-Extra/discussions/new/choose)

</div>

> [!NOTE]
> **GamesAI Extra** 是 [GamesAI](https://github.com/PengZixuan30/Games_AI) 的功能性扩展插件。它为 AI 提供了 **Carpet 假人（Bot）控制**工具和**路径点（坐标）管理**工具，允许 AI 在你的 Minecraft 服务器上生成、控制假人以及管理路径点。

> [!IMPORTANT]
> 此插件需要 **GamesAI >= 0.6.1** 已安装并先加载。GamesAI Extra 遵循[扩展插件系统](https://github.com/PengZixuan30/Games_AI#在自己的mcdr插件中自定义工具)——以此方式注册的工具与内置工具完全相同。

<details>
<summary>目录（点击展开）</summary>

- [GamesAI Extra for MCDReforged](#gamesai-extra-for-mcdreforged)
  - [安装](#安装)
  - [配置](#配置)
  - [工具与Skills](#工具与skills)
    - [Carpet 假人控制](#carpet-假人控制)
      - [生成与移除](#生成与移除)
      - [行为控制](#行为控制)
      - [移动控制](#移动控制)
      - [视角控制](#视角控制)
      - [快捷栏](#快捷栏)
      - [限时动作](#限时动作)
      - [自定义指令](#自定义指令)
    - [路径点管理](#路径点管理)
    - [Skills](#skills)
  - [依赖说明](#依赖说明)
  - [本次更新](#本次更新)
    - [Version 0.1.2](#version-012)
    - [Version 0.1.1](#version-011)
  - [许可证](#许可证)

</details>

## 安装

在 MCDR 控制台中使用以下命令安装插件：

`!!MCDR plugin install games_ai_extra`

---

或者从 [MCDR 插件仓库](https://mcdreforged.com/plugin/games_ai_extra) 获取并放置到你的插件目录中。

无需额外安装 Python 包——此插件仅依赖 `games_ai`。

## 配置

默认配置文件（`config/games_ai_extra/config.json`）结构如下：

```json
{
    "carpet": true,
    "location_plguin": false,
    "where2go_plugin": true
}
```

- **carpet**：设为 `true` 启用 Carpet 假人工具；设为 `false` 禁用。
- **location_plguin**：设为 `true` 启用基于 [Location Marker](https://mcdreforged.com/plugin/location_marker) MCDR 插件的路径点管理；设为 `false` 禁用。
- **where2go_plugin**：设为 `true` 启用基于 [Where2Go](https://mcdreforged.com/plugin/where2go) MCDR 插件的路径点管理；设为 `false` 禁用。

> [!TIP]
> `location_plguin` 和 `where2go_plugin` 提供的是同一套路径点工具（`add_pos_pos`、`add_pos_here`、`remove_pos`、`search_pos`、`get_all_pos`）。建议只启用**其中一个**，避免工具重复注册。默认启用 `where2go_plugin`。

修改配置后，使用 `!!gamesai reload` 使更改生效。

## 工具与Skills

启用后，以下工具会自动注册到 GamesAI 中，AI 可通过 `!!ask` 调用。

### Carpet 假人控制

> 🤖 **技能：** 操作假人之前务必阅读 `carpet.md`。调用 `read_skills("carpet.md")` 获取完整说明。

假人控制工具由 `carpet` 模块提供。需要服务端安装 **fabric-carpet** 模组。`spawn_bot` 和 `kill_bot` 额外注册了 `@register_bot_tool()`，可供 Mineflayer 自主 Bot 控制器调用。

#### 生成与移除

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `spawn_bot` | `name`、`pos?`、`player?`、`dim?` | 在服务器中生成一个假人。可指定 `pos`（坐标 `[x, y, z]`）在特定位置生成，或指定 `player`（玩家名）在某玩家身边生成。`pos` 与 `player` 互斥。可选指定 `dim`（如 `minecraft:the_nether`）在特定维度生成。不指定位置时在世界出生点生成。 |
| `kill_bot` | `name` | 移除（杀死）一个假人。此操作不可逆——如需重新使用请用 `spawn_bot` 重新生成。 |

#### 行为控制

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_action` | `name`、`action`、`interval?` | 控制假人执行动作。支持的动作：`attack`（攻击，需手持武器）、`use`（右键目标）、`mine`（挖掘面前方块）、`stop`（停止所有动作）、`drop`（丢弃手中物品）、`dropStack`（丢弃整组物品）、`jump`（跳跃）、`sneak`（切换潜行）、`swapHands`（交换左右手）、`mount`（骑乘附近实体）、`dismount`（下马）。可选 `interval` 为游戏刻（tick）间隔（默认 1）。 |

#### 移动控制

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_move` | `name`、`direction` | 让假人持续向某个方向移动：`forward`（前进）、`backward`（后退）、`left`（向左）、`right`（向右）。假人会一直移动，直到发送 `stop` 动作或改变方向。 |

#### 视角控制

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_look` | `name`、`target` | 控制假人看向某个方向或坐标。`target` 可以是方向词（`north`、`south`、`east`、`west`、`up`、`down`）或坐标（`"x y z"`，如 `"100 64 200"`）。 |

#### 快捷栏

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_hotbar` | `name`、`slot` | 切换假人当前选中的快捷栏格子（1~9）。切换后攻击/使用/挖掘等操作将使用对应格子的物品。 |

#### 限时动作

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_timed_action` | `name`、`action`、`duration` | 让假人执行一个限时动作，到达指定秒数后自动停止。支持：`attack`、`use`、`mine`、`forward`、`backward`、`left`、`right`。适合短时间操作（建议 ≤ 60 秒）。注意：会阻塞当前 AI 对话直到时间到达。 |

#### 自定义指令

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `bot_command` | `name`、`command` | 向假人发送一条原始自定义 `/player` 指令，用于上述工具无法覆盖的高级操作。命令会自动补全为 `player <name> <command>` 格式。需要了解 Carpet 假人指令。 |

### 路径点管理

路径点工具由 `location_plguin`（Location Marker）或 `where2go_plugin`（Where2Go）提供。同一时间只需启用其中一个。

| 工具 | 参数 | 用途 |
|:---:|:---:|:---|
| `add_pos_pos` | `name`、`pos`、`dimension` | 在指定坐标添加一个路径点。`pos` 为 `[x, y, z]`，`dimension` 为维度（如 `overworld`、`the_nether`、`the_end`）。 |
| `add_pos_here` | `name` | 在玩家当前位置添加一个路径点。仅玩家调用时有效（控制台无法使用）。 |
| `remove_pos` | `name` | 按名称删除一个路径点。Where2Go 版本支持名称模糊匹配。 |
| `search_pos` | `name` | 按名称搜索路径点并返回详细信息。 |
| `get_all_pos` | _（无）_ | 获取所有已注册的路径点列表。 |

### Skills

GamesAI Extra 通过 `register_skills()` 提供以下内置技能：

| 技能文件 | 描述 |
|---|---|
| `carpet.md` | 指导 AI 如何正确生成、控制和移除 Carpet 假人。操作假人之前务必读取此技能文件。 |

> [!TIP]
> Skills 就像 AI 的「标准作业程序 (SOP)」——确保 AI 每次都遵循正确的工作流程。AI 可使用 `read_skills` 工具读取技能文件。

## 依赖说明

每个工具模块需要对应的服务端依赖才能正常工作：

| 模块 | 所需依赖 |
|:---|:---|
| `carpet` | 服务端模组 [fabric-carpet](https://github.com/gnembon/fabric-carpet) |
| `location_plguin` | MCDR 插件 [Location Marker](https://mcdreforged.com/plugin/location_marker) |
| `where2go_plugin` | MCDR 插件 [Where2Go](https://mcdreforged.com/plugin/where2go) |

如果未安装对应依赖，调用相关工具时将返回错误提示。

## 本次更新

### Version 0.1.2

- 为 `spawn_bot` 和 `kill_bot` 添加 `@register_bot_tool()` 装饰器，支持 Mineflayer Bot 调用
- 通过 `register_skills()` API 注册 `carpet.md` 技能文件（需 GamesAI 0.6.1+）
- 添加 `register_self()` 支持，`!!gamesai reload` 时自动重载
- 支持解压目录（开发模式）和打包 `.mcdr` zip（分发模式）两种运行方式

### Version 0.1.1

- 新增路径点管理工具，支持 `location_plguin`（Location Marker）和 `where2go_plugin`（Where2Go）模块
- 为 `spawn_bot` 和 `kill_bot` 添加 `@register_bot_tool()` 装饰器，支持 Mineflayer Bot 调用
- 各工具模块可通过 `config.json` 独立启用/禁用
- 首个正式版本，包含 Carpet 假人控制工具

## 许可证

MIT License, Copyright (c) 2026 yello

<div align = "center">

---

[回到顶部](#gamesai-extra-for-mcdreforged)

</div>
