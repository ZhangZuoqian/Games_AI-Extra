# 生存服务器工具 (Survival Server Tools)

本 skill 指导 AI 在**生存服**场景下使用传送、玩家信息、库存、领地、天气时间等工具。由 `survival_server` 模块提供。

> ⚠️ **使用前请阅读本 skill**！调用 `read_skills("survival.md")` 获取完整说明。

---

## 核心原则

- **玩家发起**：传送/home/tpa 等必须由玩家本人发起，控制台只能查询
- **依赖检测**：多数工具依赖 EssentialsX / 领地插件，使用前先确认插件存在
- **权限谨慎**：天气/时间/备份等管理员命令，调用前告知用户

---

## 工具清单

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `tpa_request` | 请求传送到某玩家 | `target` |
| `home_manage` | 管理个人家 | `action`, `name?` |
| `warp_manage` | 公共传送点 | `action`, `name?` |
| `get_player_info` | 查询玩家信息 | `player?` |
| `view_inventory` | 查看玩家库存 | `player`, `slot_type?` |
| `query_claim` | 查询领地归属 | `pos?` |
| `set_weather` | 设置天气 | `weather`, `duration?` |
| `set_time` | 设置时间 | `time`, `mode?` |
| `broadcast` | 全服公告 | `message` |
| `backup_manage` | 备份管理 | `action`, `slot?` |

---

## 1. 传送（`tpa_request` / `home_manage` / `warp_manage`）

```
# tpa 请求传送到某玩家
tpa_request(target="Steve")

# 设置/删除/列出/传送 home
home_manage(action="set", name="base")
home_manage(action="del", name="old_base")
home_manage(action="list")
home_manage(action="go", name="base")

# warp 公共传送点
warp_manage(action="list")
warp_manage(action="go", name="spawn")
```

> 这些命令依赖 EssentialsX 插件。控制台无法发起，必须由玩家触发。

---

## 2. 玩家信息（`get_player_info`）

```
# 列出在线玩家
get_player_info()

# 查询某玩家详情（坐标/生命/维度）
get_player_info(player="Steve")
```

---

## 3. 库存查看（`view_inventory`）

```
view_inventory(player="Steve")                                   # 主背包
view_inventory(player="Steve", slot_type="enderchest")           # 末影箱
view_inventory(player="Steve", slot_type="equipment")            # 装备栏
```

> 依赖 fabric-carpet 的 `script run` 能力。结果在控制台输出。

---

## 4. 领地查询（`query_claim`）

```
# 玩家原地查询
query_claim()

# 指定坐标查询（需领地插件支持远程查询）
query_claim(pos=[100, 64, -50])
```

> 自动检测 GriefDefender / Residence / Lands 插件。

---

## 5. 天气时间（`set_weather` / `set_time`）

```
# 天气
set_weather(weather="clear")                # 晴天
set_weather(weather="rain")                 # 下雨
set_weather(weather="thunder")              # 雷暴
set_weather(weather="clear", duration=600)  # 晴天 10 分钟

# 时间
set_time(time=0)          # 日出
set_time(time=6000)       # 正午
set_time(time=12000)      # 日落
set_time(time=18000)      # 半夜
set_time(time=1000, mode="add")   # 时间 +1000
```

> 需要管理员权限。

---

## 6. 公告广播（`broadcast`）

```
broadcast(message="今晚 8 点活动开始，请到主城集合！")
```

> 消息会带 `[公告]` 前缀，金色文字。需要管理员权限。

---

## 7. 备份管理（`backup_manage`）

```
backup_manage(action="list")       # 列出已有备份
backup_manage(action="make")       # 创建新备份
backup_manage(action="confirm")    # 确认备份
```

> 依赖 quick_backup_multi MCDR 插件。建议重要操作前先 `make`。

---

## 典型工作流

### 场景 A：玩家想回家
> 用户："我想回基地"
1. `home_manage(action="list")` — 看有哪些家
2. `home_manage(action="go", name="base")` — 传送

### 场景 B：玩家死亡找回落点
1. `query_death_log(player="Steve", limit=1)` — 查最近死亡位置（来自 technical 模块）
2. 引导玩家 tpa 到附近玩家或 warp 到附近点
3. 必要时 `backup_manage(action="make")` 先备份再救援

### 场景 C：管理员发活动通知
1. `broadcast(message="今晚 8 点双倍经验活动开始！")`

### 场景 D：领地纠纷查询
1. 玩家原地 → `query_claim()` — 看领地归属和权限

---

## 注意事项

- 传送/home/tpa 类命令**必须玩家本人发起**，AI 只能引导
- 库存/领地查询结果在聊天栏或控制台，AI 需读取后解读
- 天气/时间/备份是管理员操作，**先告知用户再执行**
- 依赖插件缺失时工具会返回明确错误，AI 应解释并建议安装
