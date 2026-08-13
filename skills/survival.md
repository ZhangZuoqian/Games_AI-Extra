# 生存服务器工具 (Survival Server Tools)

本 skill 指导 AI 在**生存服**场景下使用传送、玩家信息、领地、天气时间等工具。由 `survival_server` 模块提供。

> ⚠️ **使用前请阅读本 skill**！调用 `read_skills("survival.md")` 获取完整说明。

---

## 核心原则

- tpa/home/warp/领地查询这些是玩家专属命令，MCDR 控制台代执行没用，所以改成发可点击消息让玩家自己点
- 多数工具靠 EssentialsX / 领地插件，不检测装没装，直接发命令，没装会提示未知命令
- 天气/时间/备份是管理员命令，调用前先跟用户说一声
- 默认关闭，要在 `config.json` 里开 `survival_server` 才注册

---

## 工具清单

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `tpa_request` | 请求传送到某玩家 | `target` |
| `home_manage` | 管理个人家 | `action`, `name?` |
| `warp_manage` | 公共传送点 | `action`, `name?` |
| `get_player_info` | 查询玩家信息 | `player?` |
| `query_claim` | 查询领地归属 | `plugin?` |
| `set_weather` | 设置天气 | `weather`, `duration?` |
| `set_time` | 设置时间 | `time`, `mode?` |
| `broadcast` | 全服公告 | `message` |
| `backup_manage` | 备份管理 | `action`, `slot?`, `comment?` |

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

> 这些命令依赖 EssentialsX 插件，均为玩家专属命令。本工具会向调用玩家发送**可点击消息**（tellraw），玩家点击后以本人身份执行，解决控制台无法代执行玩家命令的问题。控制台发起时会提示让玩家自行点击。

---

## 2. 玩家信息（`get_player_info`）

```
# 列出在线玩家
get_player_info()

# 查询某玩家详情（坐标/生命/维度）
get_player_info(player="Steve")
```

---

## 3. 领地查询（`query_claim`）

```
# 玩家原地查询（默认 GriefDefender）
query_claim()

# 指定领地插件类型查询
query_claim(plugin="griefdefender")   # GriefDefender（默认）
query_claim(plugin="residence")       # Residence
query_claim(plugin="lands")           # Lands
```

> 领地插件是 Bukkit 的，命令只能玩家执行，所以发可点击消息让玩家自己点。`plugin` 选哪个插件，默认 griefdefender，没装就提示未知命令。

---

## 4. 天气时间（`set_weather` / `set_time`）

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

## 5. 公告广播（`broadcast`）

```
broadcast(message="今晚 8 点活动开始，请到主城集合！")
```

> 消息会带 `[公告]` 前缀，金色文字。需要管理员权限。

---

## 6. 备份管理（`backup_manage`）

```
backup_manage(action="list")                          # 列出已有备份槽位
backup_manage(action="make", comment="打boss前")        # 创建新备份（存至槽位1，已有后移）
backup_manage(action="back", slot=1)                  # 发起回档请求（默认槽位1）
backup_manage(action="confirm")                       # 确认回档（back 之后才生效）
backup_manage(action="abort")                         # 中断回档
```

> 依赖 quick_backup_multi MCDR 插件。**回档是两步流程**：先 `back` 发起请求，再 `confirm` 确认才真正执行，防止误操作。建议重要操作前先 `make`。

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

- 传送/home/tpa 类命令**必须玩家本人发起**，AI 会发送可点击消息让玩家点击执行
- 领地查询结果在聊天栏或控制台，AI 需读取后解读
- 天气/时间/备份是管理员操作，**先告知用户再执行**
- 插件没装的话服务端会提示未知命令，跟用户说一声让装上
