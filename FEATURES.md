# GamesAI Extra 功能说明文档

> [!NOTE]
> 本文档详细描述 GamesAI Extra 插件提供的所有工具模块及其用法。原版功能（Carpet 假人控制、航点管理）请参考 [README.md](README.md)。

## 目录

- [概述](#概述)
- [配置](#配置)
- [原版模块](#原版模块)
  - [Carpet 假人控制](#carpet-假人控制)
  - [航点管理](#航点管理)
- [扩展模块](#扩展模块)
  - [生电服工具](#生电服工具)
  - [生存服工具](#生存服工具)
  - [经济系统](#经济系统)
  - [批量假人](#批量假人)
  - [聊天记录](#聊天记录)
- [Skills 技能文件](#skills-技能文件)
- [依赖说明](#依赖说明)
- [事件监听](#事件监听)
- [注意事项](#注意事项)

---

## 概述

GamesAI Extra 是 [GamesAI](https://github.com/PengZixuan30/Games_AI) 的功能扩展插件，为 AI 提供额外的服务器操作工具。所有工具通过 `@register_tool()` 注册，与 GamesAI 内置工具完全等价，AI 可通过 `!!ask` 调用。

插件包含 **8 个工具模块**，共提供 **40+ 个工具**，覆盖假人控制、航点管理、生电服运维、生存服便利、经济系统、聊天记录等场景。

---

## 配置

配置文件位于 `config/games_ai_extra/config.json`，可独立开关每个模块：

```json
{
    "carpet": true,
    "location_plguin": false,
    "where2go_plugin": true,
    "technical_server": true,
    "survival_server": true,
    "economy": true,
    "bot_group": true,
    "chat_log": true
}
```

修改后执行 `!!gamesai reload` 生效。

> [!TIP]
> `location_plguin` 和 `where2go_plugin` 管理同一套航点工具，建议只启用其中一个。`where2go_plugin` 默认启用。

---

## 原版模块

### Carpet 假人控制

> 🤖 **Skill:** 操作前阅读 `carpet.md`。调用 `read_skills("carpet.md")` 获取完整说明。

由 `carpet` 模块提供，需要服务端安装 **fabric-carpet** 模组。

> [!IMPORTANT]
> **命名规则：所有假人名必须以 `bot_` 开头。** 用户说 "yello" → 使用 `bot_yello`。此规则在 `carpet.md` skill 中定义，所有涉及假人的模块均遵循此规则。

#### 生成与移除

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `spawn_bot` | `name`, `pos?`, `player?`, `dim?` | 生成假人。`pos` 指定坐标，`player` 指定在玩家身边生成，`dim` 指定维度。三者互斥（`pos` 可与 `dim` 组合）。 |
| `kill_bot` | `name` | 移除假人，不可逆。 |

> `spawn_bot` 和 `kill_bot` 额外标注了 `@register_bot_tool()`，可被 Mineflayer 自主 Bot 控制器调用。

#### 行为控制

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `bot_action` | `name`, `action`, `interval?` | 执行动作：`attack`/`use`/`mine`/`stop`/`drop`/`dropStack`/`jump`/`sneak`/`swapHands`/`mount`/`dismount`。`interval` 为动作间隔（tick）。 |
| `bot_move` | `name`, `direction` | 持续移动：`forward`/`backward`/`left`/`right`。 |
| `bot_look` | `name`, `target` | 看向方向或坐标。 |
| `bot_hotbar` | `name`, `slot` | 切换快捷栏（1-9）。 |
| `bot_timed_action` | `name`, `action`, `duration` | 限时动作，到时间自动停止。 |
| `bot_command` | `name`, `command` | 发送原始 `/player` 指令。 |

#### 使用示例

```
# 生成一个假人在坐标 (100, 64, 200)
spawn_bot(name="bot_miner", pos=[100, 64, 200])

# 让假人攻击（间隔 5 tick）
bot_action(name="bot_miner", action="attack", interval=5)

# 移除假人
kill_bot(name="bot_miner")
```

### 航点管理

由 `location_plguin`（Location Marker）或 `where2go_plugin`（Where2Go）模块提供，二选一。

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `add_pos_pos` | `name`, `pos`, `dimension` | 添加路径点（指定坐标）。 |
| `add_pos_here` | `name` | 在玩家当前位置添加路径点。 |
| `remove_pos` | `name` | 删除路径点。 |
| `search_pos` | `name` | 查询路径点。 |
| `get_all_pos` | 无 | 获取所有路径点。 |

---

## 扩展模块

### 生电服工具

> 📖 **Skill:** 使用前阅读 `technical.md`。调用 `read_skills("technical.md")` 获取完整说明。

由 `technical_server` 模块提供，默认开启。面向生电/技术服玩家，提供性能监控、Carpet 规则管理、区块加载、实体管理等功能。

#### 性能监控

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `get_server_tps` | `detail?` | 查询 TPS/MSPT。`detail=true` 返回 5s/10s/1m 历史数据。通过 carpet script 实现。 |
| `count_entities` | `center_pos?`, `radius?`, `entity_type?` | 统计实体数量，按类型分组。 |
| `set_tickrate` | `rate` | 临时调整 tick 速率（正常=20）。调试完务必恢复。 |

#### Carpet 规则管理

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `carpet_rule_get` | `rule?` | 查询 Carpet 规则。不填 `rule` 则列出所有规则。 |
| `carpet_rule_set` | `rule`, `value` | 修改 Carpet 规则（如 `tntOptimization`）。 |

#### 区块加载

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `forceload` | `action`, `from_pos?`, `to_pos?` | 管理强加载区块。`action` 支持 `query`/`add`/`remove`/`remove_all`。 |

#### 结构定位

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `locate_structure` | `structure`, `pos?` | 定位结构。支持中文别名（"要塞"→`stronghold`、"堡垒"→`bastion_remnant` 等）。 |

#### 坐标换算

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `convert_dimension_pos` | `from_dim`, `pos` | 主世界↔下界坐标换算（1:8 比例）。纯数学计算，无需服务端支持。 |

#### 死亡日志

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `query_death_log` | `player?`, `limit?` | 查询死亡记录。自动监听 `player_death` 事件记录，持久化到 JSON 文件。 |

#### 实体管理

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `clear_entities` | `entity_type`, `center_pos?`, `radius?` | 批量清理实体（掉落物/经验球/箭矢等）。 |

#### 历史结构截图

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `region_snapshot` | `action`, `pos?`, `snapshot_id?` | 查询/恢复区域快照。直接执行 `!!snapshot` 命令，需服务端安装 region_snapshot 类 MCDR 插件。 |

#### 计分板

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `scoreboard_query` | `objective`, `target` | 查询分数。`target` 支持玩家名、选择器（`@a`）、假名（`#total`）。 |
| `scoreboard_set` | `objective`, `target`, `score` | 设置分数。 |
| `scoreboard_manage` | `action`, `name?`, `criterion?` | 管理计分项（`list`/`add`/`remove`）。`criterion` 支持 `dummy`/`totalKillCount`/`minecraft.killed:minecraft.zombie` 等。 |

#### 使用示例

```
# 查询服务器 TPS（详细模式）
get_server_tps(detail=true)

# 修改 Carpet 规则
carpet_rule_set(rule="tntOptimization", value="true")

# 主世界坐标换算到下界
convert_dimension_pos(from_dim="overworld", pos=[800, -200])
# 返回：下界坐标 [100.0, -25.0]

# 查询玩家最近的死亡记录
query_death_log(player="Steve", limit=3)
```

---

### 生存服工具

> 📖 **Skill:** 使用前阅读 `survival.md`。调用 `read_skills("survival.md")` 获取完整说明。

由 `survival_server` 模块提供，默认开启。面向生存服玩家，提供传送、玩家信息、领地查询、天气时间控制等功能。

#### 传送系统

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `tpa_request` | `target` | 请求传送到目标玩家。需 EssentialsX。仅玩家可用。 |
| `home_manage` | `action`, `name?` | 管理个人 home。`action` 支持 `set`/`del`/`list`/`go`。仅玩家可用。 |
| `warp_manage` | `action`, `name?` | 公共传送点。`action` 支持 `go`/`list`。 |

#### 玩家信息

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `get_player_info` | `player?` | 查询在线玩家列表或单个玩家详情（坐标/生命/维度）。 |
| `view_inventory` | `player`, `slot_type?` | 查看玩家库存。`slot_type` 支持 `inventory`/`enderchest`/`equipment`。需 fabric-carpet。 |

#### 领地查询

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `query_claim` | `plugin?` | 查询当前位置领地信息。`plugin` 支持 `griefdefender`/`residence`/`lands`，默认 `griefdefender`。直接执行对应命令，由服务端处理。 |

#### 天气与时间

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `set_weather` | `weather`, `duration?` | 设置天气（`clear`/`rain`/`thunder`）。`duration` 单位为秒，自动转换为 tick。 |
| `set_time` | `time`, `mode?` | 设置游戏时间。`mode` 支持 `set`/`add`。 |

#### 公告与备份

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `broadcast` | `message` | 全服广播公告（带 `[公告]` 前缀）。 |
| `backup_manage` | `action` | 备份管理。`action` 支持 `list`/`make`/`confirm`。需 quick_backup_multi MCDR 插件。 |

#### 使用示例

```
# 设置家
home_manage(action="set", name="base")

# 传送到 warp 点
warp_manage(action="go", name="spawn")

# 查询玩家详情
get_player_info(player="Steve")

# 通过 Residence 查询领地
query_claim(plugin="residence")

# 广播公告
broadcast(message="活动开始！")
```

---

### 经济系统

> 📖 **Skill:** 使用前阅读 `economy.md`。调用 `read_skills("economy.md")` 获取完整说明。

由 `economy` 模块提供，默认开启。

> [!NOTE]
> 经济工具直接调用 EssentialsX 命令（`balance`/`pay`），由服务端处理。Vault 是 Bukkit 插件，MCDR 无法直接检测，因此本工具不依赖插件检测，若服务端未安装经济插件，命令将返回"未知命令"提示。

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `get_balance` | `player?` | 查询玩家余额。不填则查询调用者自己。 |
| `pay_player` | `to_player`, `amount` | 玩家间转账。仅玩家可用，`amount` 必须 > 0。 |
| `price_list` | `action`, `item?`, `price?` | 本地价格表管理（JSON 持久化）。`action` 支持 `query`/`set`/`list`/`remove`。 |

#### 使用示例

```
# 查询自己的余额
get_balance()

# 向 Alex 转账 100
pay_player(to_player="Alex", amount=100)

# 设置钻石价格
price_list(action="set", item="diamond", price=64)

# 查询所有价格
price_list(action="list")
```

---

### 批量假人

> 📖 **Skill:** 使用前阅读 `bot_group.md`。调用 `read_skills("bot_group.md")` 获取完整说明。

由 `bot_group` 模块提供，默认开启。基于 `carpet` 模块扩展，提供批量假人操作和组配置管理。

> [!IMPORTANT]
> **命名规则遵循 `carpet.md`。** 本模块不自动添加 `bot_` 前缀，AI 在调用前必须按 `carpet.md` skill 规则给假人名加前缀。这与原版 `carpet` 模块的工具行为完全一致。

#### 批量操作

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `group_spawn` | `bots` | 批量生成假人。`bots` 为配置列表，每项含 `name`（必填）、`pos?`、`dim?`、`player?`。内部调用 `spawn_bot`。 |
| `group_kill` | `names` | 批量移除假人。内部调用 `kill_bot`。 |
| `group_action` | `names`, `action`, `interval?` | 批量执行相同动作。内部调用 `bot_action`。 |

#### 组配置管理

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `save_group` | `group_name`, `bots`, `default_action?` | 保存假人组配置到 JSON。 |
| `group_run` | `group_name`, `action?` | 一键启动已保存的组（spawn + 执行默认动作）。`action` 可覆盖默认动作。 |
| `group_list` | 无 | 列出所有已保存的组。 |
| `group_delete` | `group_name` | 删除已保存的组。 |

#### 使用示例

```
# 批量生成 3 个假人（注意：名字必须带 bot_ 前缀）
group_spawn(bots=[
    {"name": "bot_attacker", "pos": [100, 64, 200]},
    {"name": "bot_collector", "pos": [102, 64, 200]},
    {"name": "bot_builder", "pos": [104, 64, 200]}
])

# 保存假人组
save_group(group_name="farm_team", bots=[
    {"name": "bot_a", "pos": [100, 64, 200]},
    {"name": "bot_b", "pos": [102, 64, 200]}
], default_action="attack")

# 一键启动
group_run(group_name="farm_team")
```

---

### 聊天记录

> 📖 **Skill:** 使用前阅读 `chat_log.md`。调用 `read_skills("chat_log.md")` 获取完整说明。

由 `chat_log` 模块提供，默认开启。自动监听 `player_chat` 事件记录所有玩家聊天。

> [!NOTE]
> 聊天记录以 JSONL 格式存储在 `config/games_ai_extra/chat_log.jsonl`，追加写入（不读全文），超过 5000 条自动滚动保留最新的。

| 工具 | 参数 | 说明 |
|:---:|:---:|:---|
| `search_chat_log` | `player?`, `keyword?`, `since?`, `until?`, `limit?` | 搜索聊天记录。支持按玩家（精确）、关键词（模糊、大小写不敏感）、时间范围过滤。结果按时间倒序（最新在前）。 |
| `clear_chat_log` | `confirm` | 清空所有聊天记录。必须传 `confirm=true` 才会执行。 |

#### 使用示例

```
# 查询某玩家最近 10 条消息
search_chat_log(player="Steve", limit=10)

# 按关键词搜索
search_chat_log(keyword="钻石")

# 按时间范围搜索
search_chat_log(since="2026-08-01", until="2026-08-13")

# 清空记录（需确认）
clear_chat_log(confirm=true)
```

---

## Skills 技能文件

每个模块配套一个 skill 文件，指导 AI 正确使用工具。AI 在调用工具前应先 `read_skills()` 阅读对应 skill。

| Skill 文件 | 对应模块 | 说明 |
|:---:|:---:|:---|
| `carpet.md` | carpet | 假人控制规范（原版） |
| `technical.md` | technical_server | 生电服工具使用规范 |
| `survival.md` | survival_server | 生存服工具使用规范 |
| `economy.md` | economy | 经济工具使用规范 |
| `bot_group.md` | bot_group | 批量假人操作规范 |
| `chat_log.md` | chat_log | 聊天记录搜索规范 |
| `newbie_guide.md` | 无（纯引导） | 新手引导流程 |

> Skills 同时支持解压目录模式和 `.mcdr` 压缩包模式读取。

---

## 依赖说明

| 依赖 | 类型 | 必需 | 说明 |
|:---:|:---:|:---:|:---|
| GamesAI >= 0.6.1 | MCDR 插件 | ✅ | 主插件，必须先加载 |
| fabric-carpet | 服务端模组 | ✅ | 假人控制、carpet script、TPS 查询依赖 |
| Location Marker | MCDR 插件 | ❌ | 航点管理（二选一） |
| Where2Go | MCDR 插件 | ❌ | 航点管理（二选一，默认） |
| EssentialsX | 服务端插件 | ❌ | 传送/home/warp/经济命令 |
| quick_backup_multi | MCDR 插件 | ❌ | 备份管理 |
| region_snapshot 类 | MCDR 插件 | ❌ | 历史结构截图 |
| GriefDefender/Residence/Lands | 服务端插件 | ❌ | 领地查询 |

> [!TIP]
> 标记为 ❌ 的依赖为可选。若未安装对应插件，相关工具会直接执行命令，服务端返回"未知命令"提示，不影响其他功能。

---

## 事件监听

插件自动监听以下 MCDR 事件：

| 事件 | 处理逻辑 | 存储位置 |
|:---:|:---|:---|
| `on_player_death` | 记录玩家死亡信息（玩家名、时间、位置、维度、死因） | `config/games_ai_extra/death_log.json` |
| `on_player_chat` | 记录玩家聊天消息（玩家名、时间、消息内容） | `config/games_ai_extra/chat_log.jsonl` |

- 死亡日志最多保留 500 条，超出自动滚动
- 聊天日志最多保留 5000 条，超出自动滚动
- 所有记录均为追加写入，不阻塞服务器

---

## 注意事项

1. **命名规则**：所有假人名必须以 `bot_` 开头，此规则在 `carpet.md` skill 中定义，所有模块遵循
2. **模块独立开关**：每个模块可在 `config.json` 中独立启用/禁用，互不影响
3. **非阻塞设计**：所有 `server.execute()` 调用均为非阻塞，结果通过聊天栏/控制台回显
4. **Bukkit 插件检测**：Vault/GriefDefender 等是 Bukkit 插件，MCDR 无法直接检测，相关工具直接执行命令由服务端处理
5. **数据持久化**：死亡日志、聊天日志、价格表、假人组配置均持久化到 `config/games_ai_extra/` 目录
6. **Skill 读取**：支持目录模式和 `.mcdr` zip 模式，两种部署方式均可正常注册 skill
