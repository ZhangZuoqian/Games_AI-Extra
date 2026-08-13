# 经济系统工具 (Economy Tools)

本 skill 指导 AI 使用余额查询、转账、价格表等经济工具。由 `economy` 模块提供。

> ⚠️ **使用前请阅读本 skill**！调用 `read_skills("economy.md")` 获取完整说明。

---

## 核心原则

- **依赖经济插件**：余额查询/转账需要服务端安装 EssentialsX（或兼容 Vault 的经济插件）
- **玩家专属命令**：`balance`/`pay` 是玩家专属命令，MCDR 控制台无法代执行；本工具改为向玩家发送**可点击消息**，玩家点击后以本人身份执行
- **默认关闭**：需在 `config.json` 开启 `economy` 才会注册工具
- **价格表内存维护**：价格表由本插件内存存储（重启清空，不写入文件），AI 可读写

---

## 工具清单

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `get_balance` | 查询玩家余额 | `player?` |
| `pay_player` | 玩家间转账 | `to_player`, `amount` |
| `price_list` | 价格表管理 | `action`, `item?`, `price?` |

---

## 1. 余额查询（`get_balance`）

```
# 玩家查自己余额（发送可点击消息，玩家点击执行 /balance）
get_balance()

# 查询他人余额（直接执行 /balance <player>，控制台可执行）
get_balance(player="Steve")
```

> 依赖 EssentialsX（或兼容 Vault 的经济插件）。查自己余额时 `/balance` 是玩家专属命令，本工具发送可点击消息由玩家本人点击执行；查他人余额用 `/balance <player>`（控制台可执行，需 `essentials.balance.others` 权限）。结果在聊天栏返回。

---

## 2. 转账（`pay_player`）

```
pay_player(to_player="Steve", amount=100.5)
```

- 调用者必须是在线玩家
- `amount` 必须 > 0
- 余额不足会由 Vault 拒绝

---

## 3. 价格表（`price_list`）

```
# 查询单品价格（支持模糊匹配）
price_list(action="query", item="diamond")
price_list(action="query", item="minecraft:netherite_ingot")

# 列出全部价格
price_list(action="list")

# 设置价格（管理员）
price_list(action="set", item="diamond", price=64)
price_list(action="set", item="minecraft:netherite_ingot", price=1024)

# 删除价格
price_list(action="remove", item="diamond")
```

**价格表存储**：内存（重启清空，不写入文件）

> AI 可以通过 `modify_custom_tools` 让用户语音修改价格表，或直接调用 `price_list(action="set")`。

---

## 典型工作流

### 场景 A：玩家问钻石多少钱
1. `price_list(action="query", item="diamond")` — 查本地价格表
2. 如果没记录 → 建议管理员 `price_list(action="set", item="diamond", price=64)` 设置

### 场景 B：玩家转账
1. `get_balance()` — 先查自己余额是否够
2. `pay_player(to_player="Steve", amount=100)` — 转账

### 场景 C：管理员维护价格表
1. `price_list(action="list")` — 看当前价格表
2. `price_list(action="set", item="diamond", price=64)` — 新增/修改
3. `price_list(action="remove", item="old_item")` — 删除过期项

---

## 注意事项

- 经济类工具**强依赖 Vault**，缺失时工具返回明确错误
- 价格表是**本地 JSON**，与服务器实际商店价格可能不一致，AI 应说明
- 转账是**真金白银**，调用前向用户确认金额和收款人
