# 聊天记录工具 (Chat Log Tools)

本 skill 指导 AI 使用聊天记录搜索功能。由 `chat_log` 模块提供，自动监听 `player_chat` 事件记录所有玩家聊天。

> ⚠️ **使用前请阅读本 skill**！调用 `read_skills("chat_log.md")` 获取完整说明。

---

## 核心原则

- **自动记录**：所有玩家聊天由插件自动监听并写入 `config/games_ai_extra/chat_log.jsonl`
- **高效存储**：使用 JSONL 格式（每行一条），追加写入不读全文，文件超过 5000 条自动滚动
- **隐私提示**：聊天记录包含玩家私聊内容（如通过 !!ask 发送的），AI 查询结果应只返回必要信息

---

## 工具清单

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `search_chat_log` | 搜索聊天记录 | `player?`, `keyword?`, `since?`, `until?`, `limit?` |
| `clear_chat_log` | 清空所有记录 | `confirm` |

---

## 1. 搜索聊天记录（`search_chat_log`）

```
# 查询某玩家最近 10 条消息
search_chat_log(player="Steve", limit=10)

# 按关键词搜索
search_chat_log(keyword="钻石")

# 按时间范围搜索
search_chat_log(since="2026-08-01", until="2026-08-13")

# 组合查询：某玩家在某时间范围内说了某关键词
search_chat_log(player="Steve", keyword="交易", since="2026-08-10", limit=20)

# 不带任何过滤，返回最近 20 条
search_chat_log()
```

**参数说明**：
- `player` — 精确匹配玩家名（大小写敏感）
- `keyword` — 模糊匹配消息内容（大小写不敏感）
- `since` / `until` — 时间范围，格式 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`
- `limit` — 最多返回条数，默认 20，建议 ≤ 50

**返回格式**：最新在前，每行一条 `[时间] 玩家: 消息`

---

## 2. 清空记录（`clear_chat_log`）

```
clear_chat_log(confirm=true)
```

⚠️ 不可恢复操作，必须传 `confirm=true` 才会执行。

---

## 典型工作流

### 场景 A：查证玩家说过的话
> 用户："Steve 昨天有没有说过要卖钻石？"
1. `search_chat_log(player="Steve", keyword="钻石", since="2026-08-12")` — 查昨天 Steve 提到钻石的话

### 场景 B：追溯纠纷
> 用户："刚才谁骂人了？"
1. `search_chat_log(limit=50)` — 看最近 50 条聊天
2. 根据时间定位争议内容

### 场景 C：找历史指令
> 用户："我昨天输的 !!qb make 备份叫什么来着？"
1. `search_chat_log(player="你的名字", keyword="!!qb", since="2026-08-12")` — 找你昨天输过的 qb 命令

### 场景 D：管理员维护
> 聊天记录文件太大
1. `clear_chat_log(confirm=true)` — 清空重新记录

---

## 注意事项

- 聊天记录**只包含插件加载后**的消息，加载前的历史不会被记录
- 文件最多保留 **5000 条**，超过自动滚动（删除最旧的）
- `search_chat_log` 是**流式读取**，文件大也不会爆内存
- 搜索结果按**时间倒序**（最新在前）
- 清空操作**不可恢复**，请谨慎
