# Carpet 机器人管理技能指南

你拥有完整的 Carpet 机器人管理工具集，可以用自然语言帮助用户管理机器人。

> 💡 机器人（Bot）是通过 Carpet Mod 生成的模拟玩家，可以执行各种自动化任务。


## 可用工具速查

### 查询类
| 工具名 | 用途 |
|--------|------|
| `list_bots` | 列出所有机器人 |
| `check_bot` | 检查机器人是否存在 |
| `bot_names` | 获取机器人名称列表（简洁版） |
| `bot_status` | 获取机器人详细信息（位置/血量/模式/手持物品） |
| `bot_inventory` | 获取机器人背包物品列表 |

### 生成与移除
| 工具名 | 用途 |
|--------|------|
| `spawn_bot` | 生成机器人（支持坐标/玩家身边/维度） |
| `kill_bot` | 移除机器人 |

### 控制类
| 工具名 | 用途 |
|--------|------|
| `bot_action` | 执行动作：attack/use/mine/stop/drop/dropStack/jump/sneak/swapHands/mount/dismount |
| `bot_move` | 持续移动：forward/backward/left/right |
| `bot_look` | 看向方向词（north/south/east/west/up/down） |
| `bot_look_at` | 看向具体坐标（x y z） |
| `bot_turn` | 原地转身（正数=右转，负数=左转） |
| `bot_hotbar` | 切换快捷栏（1~9） |
| `bot_timed_action` | 执行限时动作（秒数到达后自动停止） |
| `bot_teleport` | 传送机器人到坐标或玩家身边 |
| `bot_pause` | 暂停当前动作 |
| `bot_resume` | 恢复暂停的动作 |
| `bot_spectate` | 进入旁观模式 |
| `bot_spectate_target` | 监视指定玩家或实体 |

### 物品管理
| 工具名 | 用途 |
|--------|------|
| `bot_drop_offhand` | 丢弃副手物品 |
| `bot_drop_all` | 清空机器人所有物品（⚠️ 谨慎使用） |

### 批量操作
| 工具名 | 用途 |
|--------|------|
| `bot_all` | 让所有机器人同时执行动作 |

### 高级操作
| 工具名 | 用途 |
|--------|------|
| `bot_command` | 执行任意 /player 命令（高级用户） |


## 标准工作流程

### 场景1：生成机器人
1. **检查名称冲突**：调用 `list_bots` 查看当前机器人列表
2. **如果名称可用**：调用 `spawn_bot`
3. **确认结果**：告知用户生成成功
