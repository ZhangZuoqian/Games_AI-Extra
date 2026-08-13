# 经济系统工具 (Economy Tools)

本 skill 指导 AI 使用余额查询、转账、价格表等经济工具。由 `economy` 模块提供。

> ⚠️ **使用前请阅读本 skill**！调用 `read_skills("economy.md")` 获取完整说明。

---

## 核心原则

- **依赖 Vault**：余额查询/转账需要服务端安装 Vault + 经济插件（EssentialsX Economy / iConomy 等）
- **转账需玩家发起**：`pay_player` 必须由在线玩家调用，控制台不行
- **价格表本地维护**：价格表由本插件 JSON 文件管理，AI 可读写

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
# 玩家查自己余额
get_balance()

# 查询某玩家余额
get_balance(player="Steve")
```

> 依赖 Vault。结果在聊天栏返回。

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

**价格表文件**：`config/games_ai_extra/price_list.json`

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
