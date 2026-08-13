# 假人批量脚本 (Bot Group Operations)

本 skill 指导 AI 使用批量假人操作：一次 spawn/kill/action 多个假人，保存和复用假人组配置。由 `bot_group` 模块提供，基于 `carpet` 模块扩展。

> ⚠️ **使用前请阅读本 skill**！调用 `read_skills("bot_group.md")` 获取完整说明。

> ⚠️ 同时建议先读 `carpet.md` skill，了解假人基础控制。

---

## 核心原则

- **bot_ 前缀**：所有假人名自动加 `bot_` 前缀（同 carpet 模块规则）
- **复用 carpet 工具**：批量操作内部调用 `spawn_bot`/`kill_bot`/`bot_action`
- **组配置可保存**：常用假人组保存为 JSON，后续一键启动

---

## 工具清单

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `group_spawn` | 批量生成假人 | `bots` |
| `group_kill` | 批量移除假人 | `names` |
| `group_action` | 批量执行相同动作 | `names`, `action`, `interval?` |
| `save_group` | 保存假人组配置 | `group_name`, `bots`, `default_action?` |
| `group_run` | 一键启动已保存组 | `group_name`, `action?` |
| `group_list` | 列出所有保存的组 | 无 |
| `group_delete` | 删除保存的组 | `group_name` |

---

## 1. 批量生成（`group_spawn`）

```
group_spawn(bots=[
    {"name": "attacker", "pos": [100, 64, -50]},
    {"name": "collector", "pos": [102, 64, -50]},
    {"name": "builder", "pos": [104, 64, -50], "dim": "minecraft:overworld"}
])
```

每个 bot 配置：
- `name`（必填）— 自动加 `bot_` 前缀
- `pos`（可选）— `[x, y, z]`
- `dim`（可选）— 维度 ID
- `player`（可选）— 在某玩家身边生成（与 pos/dim 互斥）

---

## 2. 批量移除（`group_kill`）

```
group_kill(names=["attacker", "collector", "builder"])
```

---

## 3. 批量动作（`group_action`）

```
# 让一组假人同时攻击
group_action(names=["attacker", "guard1", "guard2"], action="attack", interval=10)

# 同时停止
group_action(names=["attacker", "guard1", "guard2"], action="stop")

# 同时挖矿
group_action(names=["miner1", "miner2"], action="mine", interval=1)
```

支持的动作同 `bot_action`：attack / use / mine / stop / drop / dropStack / jump / sneak / swapHands / mount / dismount

---

## 4. 保存假人组（`save_group`）

```
save_group(
    group_name="farm_team",
    bots=[
        {"name": "attacker", "pos": [100, 64, -50]},
        {"name": "collector", "pos": [102, 64, -50]}
    ],
    default_action="attack"
)
```

保存后可通过 `group_run` 一键启动。

**组配置文件**：`config/games_ai_extra/bot_groups.json`

---

## 5. 一键启动组（`group_run`）

```
# 启动组（用组的默认动作）
group_run(group_name="farm_team")

# 启动组但覆盖动作
group_run(group_name="farm_team", action="mine")
```

`group_run` 内部：
1. 调用 `group_spawn` 批量 spawn
2. 调用 `group_action` 批量执行默认动作（或覆盖动作）

---

## 6. 列出 / 删除组

```
group_list()                              # 列出所有保存的组
group_delete(group_name="old_team")       # 删除某组
```

---

## 典型工作流

### 场景 A：建刷怪塔分工假人组
> 用户："帮我建个 5 人刷怪塔团队"
1. `save_group(group_name="mob_farm", bots=[...5 个假人配置...], default_action="attack")`
2. `group_run(group_name="mob_farm")` — 一键启动
3. 需要停止时 `group_action(names=[...], action="stop")`
4. 收工 `group_kill(names=[...])`

### 场景 B：调试时临时 spawn 一组
```
group_spawn(bots=[
    {"name": "test1", "pos": [100, 64, -50]},
    {"name": "test2", "pos": [100, 64, -48]}
])
group_action(names=["test1", "test2"], action="attack")
# 完事
group_kill(names=["test1", "test2"])
```

### 场景 C：管理已保存的组
1. `group_list()` — 看有哪些组
2. `group_run(group_name="mine_squad")` — 启动某组
3. `group_delete(group_name="old_unused")` — 删除不用的组

---

## 注意事项

- **假人数量有上限**：太多假人会严重拖慢服务器，建议单组 ≤ 10 个
- **bot_ 前缀自动添加**：用户传 "attacker" 实际生成 "bot_attacker"
- **批量操作有延迟**：spawn 多个假人会顺序执行，每个有微小延迟
- **组配置持久化**：保存后服务器重启仍然有效，除非手动 `group_delete`
- **与 carpet 模块兼容**：批量工具内部调用 carpet 单个工具，行为一致
