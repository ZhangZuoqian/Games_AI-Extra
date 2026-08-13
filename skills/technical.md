# 生电服务器工具 (Technical Server Tools)

本 skill 指导 AI 在**生电/技术服**场景下使用性能监控、Carpet 调优、区块加载、实体管理等工具。这些工具由 `technical_server` 模块提供。

> ⚠️ **使用前请阅读本 skill**！调用 `read_skills("technical.md")` 获取完整说明。

---

## 核心原则

- **性能优先**：生电服最关心 TPS/MSPT，任何操作前先评估对性能影响
- **谨慎修改 Carpet 规则**：修改前必须先 `carpet_rule_get` 查询当前值，修改后告知用户可回滚
- **forceload 是强加载**：每个强加载区块都会持续占用服务器算力，不要无脑添加
- **实体清理要确认**：`clear_entities` 可能误伤玩家圈养动物，操作前先确认范围和类型
- **门控依赖**：本模块默认关闭，需在 `config.json` 同时开启 `carpet` 与 `technical_server` 才生效（所有命令依赖 fabric-carpet，无 spark 依赖）

---

## 工具清单

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `get_server_tps` | 查询 TPS/MSPT/tick 状态 | `detail?` |
| `carpet_rule_get` | 查询 Carpet 规则当前值 | `rule?` |
| `carpet_rule_set` | 修改 Carpet 规则 | `rule`, `value` |
| `forceload` | 管理强加载区块 | `action`, `from_pos?`, `to_pos?` |
| `locate_structure` | 定位附近结构坐标 | `structure`, `pos?` |
| `convert_dimension_pos` | 主世界↔下界坐标换算 | `from_dim`, `pos` |
| `query_death_log` | 查询死亡记录 | `player?`, `limit?` |
| `set_tickrate` | 临时调整 tick 速率 | `rate` |
| `clear_entities` | 清理实体 | `entity_type`, `center_pos?`, `radius?` |
| `scoreboard_query` | 查询分数 | `objective`, `target` |
| `scoreboard_set` | 设置分数 | `objective`, `target`, `score` |
| `scoreboard_manage` | 管理计分项 | `action`, `name?`, `criterion?` |

---

## 1. 性能监控（`get_server_tps`）

```
get_server_tps()                    # 只看当前 TPS/MSPT
get_server_tps(detail=True)         # 详细：5s/10s/1m 平均 TPS
```

**判读标准**：
- TPS = 20 → 满速，服务器正常
- TPS 15~20 → 轻微卡顿
- TPS < 15 → 明显卡顿，需排查
- MSPT < 50 → 健康
- MSPT 50~100 → 接近超载
- MSPT > 100 → 严重超载

---

## 2. Carpet 规则管理（`carpet_rule_get` / `carpet_rule_set`）

```
# 查询单条规则
carpet_rule_get(rule="tntOptimization")

# 列出所有规则
carpet_rule_get()

# 修改规则
carpet_rule_set(rule="tntOptimization", value="true")
carpet_rule_set(rule="explosionsSpawnFire", value="false")
```

**生电常用规则**：
- `tntOptimization` — TNT 优化（true/false）
- `optimizedTNT` — 优化 TNT（true/false）
- `explosionsSpawnFire` — 爆炸是否引火（true/false）
- `stackableShulkerBoxes` — 潜影盒可堆叠（true/false）
- `fillReportsEnabled` — 填充报告（true/false）

> ⚠️ 修改前先 `carpet_rule_get` 查询，修改后告知用户如何回滚（设回原值）

---

## 3. 强加载区块（`forceload`）

```
# 查询所有强加载区块
forceload(action="query")

# 添加强加载区块（from -> to 是矩形范围）
forceload(action="add", from_pos=[100, 100], to_pos=[200, 200])

# 添加单个区块
forceload(action="add", from_pos=[100, 100])

# 移除强加载区块
forceload(action="remove", from_pos=[100, 100], to_pos=[200, 200])

# 移除所有
forceload(action="remove_all")
```

**用途**：保持刷怪塔/农场常加载，玩家离开后机器仍运转。

> ⚠️ 强加载区块占用算力，建议只加载必要区域（如刷怪塔 16×16 即可）

---

## 4. 结构定位（`locate_structure`）

```
locate_structure(structure="stronghold")              # 找要塞
locate_structure(structure="bastion_remnant")         # 找堡垒遗迹
locate_structure(structure="ancient_city")            # 找远古城市
locate_structure(structure="fortress")                # 找下界要塞
locate_structure(structure="end_city")                # 找末地城
locate_structure(structure="mansion")                 # 找林地府邸
locate_structure(structure="monument")                # 找海底神殿
locate_structure(structure="village")                 # 找村庄
```

**支持中文别名**：`要塞`、`堡垒`、`远古城市`、`下界要塞`、`末地城`、`林地府邸`、`海底神殿`、`村庄`、`前哨`、`沉船`、`沙漠神殿`

---

## 5. 维度坐标换算（`convert_dimension_pos`）

```
# 主世界 -> 下界
convert_dimension_pos(from_dim="overworld", pos=[800, -200])
# 输出：主世界 (800, -200) 对应下界坐标: (100.0, -25.0)

# 下界 -> 主世界
convert_dimension_pos(from_dim="the_nether", pos=[100, -25])
# 输出：下界 (100, -25) 对应主世界坐标: (800.0, -200.0)
```

**用途**：建下界传送门、对齐主世界机器。

---

## 6. 死亡记录查询（`query_death_log`）

```
# 查询最近 5 条死亡记录
query_death_log()

# 查询某玩家最近死亡
query_death_log(player="Steve", limit=3)
```

死亡记录由插件自动监听 `player_death` 事件记录到**内存**（不写入文件，重启清空）。

---

## 7. Tick 速率调整（`set_tickrate`）

```
set_tickrate(rate=20)         # 正常速度
set_tickrate(rate=5)          # 慢放 4 倍（调试机器用）
set_tickrate(rate=100)        # 超快（加速测试）
set_tickrate(rate=0)          # 暂停（⚠️ 谨慎）
```

> ⚠️ 调试完务必 `set_tickrate(rate=20)` 恢复正常

---

## 8. 实体清理（`clear_entities`）

```
# 清理全图掉落物
clear_entities(entity_type="item")

# 清理某区域经验球
clear_entities(entity_type="xp_orb", center_pos=[100, 64, -50], radius=32)

# 清理全图箭矢
clear_entities(entity_type="arrow")
```

> ⚠️ 清理范围请确认，避免误伤玩家圈养动物

---

## 9. 计分板管理（`scoreboard_*`）

```
# 列出所有计分项
scoreboard_manage(action="list")

# 创建计分项（默认 dummy 准则，手动设置值）
scoreboard_manage(action="add", name="killCount")
scoreboard_manage(action="add", name="zombieKills", criterion="minecraft.killed:minecraft.zombie")

# 查询分数
scoreboard_query(objective="killCount", target="Steve")
scoreboard_query(objective="killCount", target="#total")

# 设置分数
scoreboard_set(objective="killCount", target="#total", score=0)  # 重置计数器

# 删除计分项
scoreboard_manage(action="remove", name="oldCount")
```

**常见准则**：
- `dummy` — 手动设置（最常用，做计数器）
- `totalKillCount` — 总击杀数
- `deathCount` — 死亡次数
- `minecraft.killed:minecraft.zombie` — 击杀僵尸数

---

## 典型工作流

### 场景 A：服务器卡顿排查
> 用户："服务器很卡，帮我看看"
1. `get_server_tps(detail=True)` — 看 TPS/MSPT
2. 如果 MSPT 高 → `clear_entities(entity_type="item")` — 清理掉落物
3. 检查 forceload → `forceload(action="query")`
4. 必要时调慢 tickrate 调试 → `set_tickrate(rate=10)`

### 场景 B：调试 TNT 机器
1. `carpet_rule_get(rule="tntOptimization")` — 查当前规则
2. `carpet_rule_set(rule="tntOptimization", value="true")` — 开启优化
3. `set_tickrate(rate=5)` — 慢放观察
4. 调试完 `set_tickrate(rate=20)` — 恢复

### 场景 C：找远古城市建农场
1. `locate_structure(structure="ancient_city")` — 定位
2. `convert_dimension_pos(from_dim="overworld", pos=[x, z])` — 算下界坐标
3. `forceload(action="add", from_pos=[x, z])` — 强加载该区域
4. 用 `bot_group` 模块批量 spawn 假人分工（见 bot_group.md skill）

---

## 注意事项

- 大部分命令需要**管理员权限**（OP 或 carpet 权限）
- `carpet_rule_set` / `set_tickrate` / `forceload` / `clear_entities` 都是修改性操作，**先告知用户再执行**
- 性能查询结果通过聊天栏/控制台返回，AI 需要读取后向用户解读
- 死亡日志文件最多保留 500 条，超出自动滚动
