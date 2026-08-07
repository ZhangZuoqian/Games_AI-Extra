<div align="center">

# GamesAI Extra for MCDReforged

[English](/README.md)  |  [簡體中文](/README.zh-CN.md)  |  繁體中文

[回報問題](https://github.com/PengZixuan30/Games_AI-Extra/issues/new)  |  [提供想法](https://github.com/PengZixuan30/Games_AI-Extra/discussions/new/choose)

</div>

> [!NOTE]
> **GamesAI Extra** 是 [GamesAI](https://github.com/PengZixuan30/Games_AI) 的功能性擴展插件。它為 AI 提供了 **Carpet 假人（Bot）控制**工具和**路徑點（座標）管理**工具，允許 AI 在你的 Minecraft 伺服器上生成、控制假人以及管理路徑點。

> [!IMPORTANT]
> 此插件需要 **GamesAI >= 0.6.1** 已安裝並先載入。GamesAI Extra 遵循[擴展插件系統](https://github.com/PengZixuan30/Games_AI#在自己的mcdr插件中自訂工具)——以此方式註冊的工具與內建工具完全相同。

<details>
<summary>目錄（點擊展開）</summary>

- [GamesAI Extra for MCDReforged](#gamesai-extra-for-mcdreforged)
  - [安裝](#安裝)
  - [設定](#設定)
  - [工具與Skills](#工具與skills)
    - [Carpet 假人控制](#carpet-假人控制)
      - [生成與移除](#生成與移除)
      - [行為控制](#行為控制)
      - [移動控制](#移動控制)
      - [視角控制](#視角控制)
      - [快捷欄](#快捷欄)
      - [限時動作](#限時動作)
      - [自訂指令](#自訂指令)
    - [路徑點管理](#路徑點管理)
    - [Skills](#skills)
  - [依賴說明](#依賴說明)
  - [本次更新](#本次更新)
    - [Version 0.1.2](#version-012)
    - [Version 0.1.1](#version-011)
  - [授權條款](#授權條款)

</details>

## 安裝

在 MCDR 主控台中使用以下指令安裝插件：

`!!MCDR plugin install games_ai_extra`

---

或者從 [MCDR 插件倉庫](https://mcdreforged.com/plugin/games_ai_extra) 取得並放置到你的插件目錄中。

無需額外安裝 Python 套件——此插件僅依賴 `games_ai`。

## 設定

預設設定檔（`config/games_ai_extra/config.json`）結構如下：

```json
{
    "carpet": true,
    "location_plguin": false,
    "where2go_plugin": true
}
```

- **carpet**：設為 `true` 啟用 Carpet 假人工具；設為 `false` 停用。
- **location_plguin**：設為 `true` 啟用基於 [Location Marker](https://mcdreforged.com/plugin/location_marker) MCDR 插件的路徑點管理；設為 `false` 停用。
- **where2go_plugin**：設為 `true` 啟用基於 [Where2Go](https://mcdreforged.com/plugin/where2go) MCDR 插件的路徑點管理；設為 `false` 停用。

> [!TIP]
> `location_plguin` 和 `where2go_plugin` 提供的是同一套路徑點工具（`add_pos_pos`、`add_pos_here`、`remove_pos`、`search_pos`、`get_all_pos`）。建議只啟用**其中一個**，避免工具重複註冊。預設啟用 `where2go_plugin`。

修改設定後，使用 `!!gamesai reload` 使變更生效。

## 工具與Skills

啟用後，以下工具會自動註冊到 GamesAI 中，AI 可透過 `!!ask` 呼叫。

### Carpet 假人控制

> 🤖 **技能：** 操作假人之前務必閱讀 `carpet.md`。呼叫 `read_skills("carpet.md")` 取得完整說明。

假人控制工具由 `carpet` 模組提供。需要伺服器端安裝 **fabric-carpet** 模組。`spawn_bot` 和 `kill_bot` 額外註冊了 `@register_bot_tool()`，可供 Mineflayer 自主 Bot 控制器呼叫。

#### 生成與移除

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `spawn_bot` | `name`、`pos?`、`player?`、`dim?` | 在伺服器中生成一個假人。可指定 `pos`（座標 `[x, y, z]`）在特定位置生成，或指定 `player`（玩家名稱）在某玩家身邊生成。`pos` 與 `player` 互斥。可選指定 `dim`（如 `minecraft:the_nether`）在特定維度生成。不指定位置時在世界重生點生成。 |
| `kill_bot` | `name` | 移除（殺死）一個假人。此操作不可逆——如需重新使用請用 `spawn_bot` 重新生成。 |

#### 行為控制

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_action` | `name`、`action`、`interval?` | 控制假人執行動作。支援的動作：`attack`（攻擊，需手持武器）、`use`（右鍵目標）、`mine`（挖掘面前方塊）、`stop`（停止所有動作）、`drop`（丟棄手中物品）、`dropStack`（丟棄整組物品）、`jump`（跳躍）、`sneak`（切換潛行）、`swapHands`（交換左右手）、`mount`（騎乘附近實體）、`dismount`（下馬）。可選 `interval` 為遊戲刻（tick）間隔（預設 1）。 |

#### 移動控制

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_move` | `name`、`direction` | 讓假人持續向某個方向移動：`forward`（前進）、`backward`（後退）、`left`（向左）、`right`（向右）。假人會一直移動，直到發送 `stop` 動作或改變方向。 |

#### 視角控制

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_look` | `name`、`target` | 控制假人看向某個方向或座標。`target` 可以是方向詞（`north`、`south`、`east`、`west`、`up`、`down`）或座標（`"x y z"`，如 `"100 64 200"`）。 |

#### 快捷欄

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_hotbar` | `name`、`slot` | 切換假人目前選中的快捷欄格子（1~9）。切換後攻擊/使用/挖掘等操作將使用對應格子的物品。 |

#### 限時動作

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_timed_action` | `name`、`action`、`duration` | 讓假人執行一個限時動作，到達指定秒數後自動停止。支援：`attack`、`use`、`mine`、`forward`、`backward`、`left`、`right`。適合短時間操作（建議 ≤ 60 秒）。注意：會阻塞目前 AI 對話直到時間到達。 |

#### 自訂指令

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_command` | `name`、`command` | 向假人發送一條原始自訂 `/player` 指令，用於上述工具無法涵蓋的進階操作。指令會自動補全為 `player <name> <command>` 格式。需要了解 Carpet 假人指令。 |

### 路徑點管理

路徑點工具由 `location_plguin`（Location Marker）或 `where2go_plugin`（Where2Go）提供。同一時間只需啟用其中一個。

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `add_pos_pos` | `name`、`pos`、`dimension` | 在指定座標新增一個路徑點。`pos` 為 `[x, y, z]`，`dimension` 為維度（如 `overworld`、`the_nether`、`the_end`）。 |
| `add_pos_here` | `name` | 在玩家目前位置新增一個路徑點。僅玩家呼叫時有效（主控台無法使用）。 |
| `remove_pos` | `name` | 按名稱刪除一個路徑點。Where2Go 版本支援名稱模糊比對。 |
| `search_pos` | `name` | 按名稱搜尋路徑點並回傳詳細資訊。 |
| `get_all_pos` | _（無）_ | 取得所有已註冊的路徑點列表。 |

### Skills

GamesAI Extra 透過 `register_skills()` 提供以下內建技能：

| 技能檔案 | 描述 |
|---|---|
| `carpet.md` | 指導 AI 如何正確生成、控制和移除 Carpet 假人。操作假人之前務必讀取此技能檔案。 |

> [!TIP]
> Skills 就像 AI 的「標準作業程序 (SOP)」——確保 AI 每次都遵循正確的工作流程。AI 可使用 `read_skills` 工具讀取技能檔案。

## 依賴說明

每個工具模組需要對應的伺服器端依賴才能正常運作：

| 模組 | 所需依賴 |
|:---|:---|
| `carpet` | 伺服器端模組 [fabric-carpet](https://github.com/gnembon/fabric-carpet) |
| `location_plguin` | MCDR 插件 [Location Marker](https://mcdreforged.com/plugin/location_marker) |
| `where2go_plugin` | MCDR 插件 [Where2Go](https://mcdreforged.com/plugin/where2go) |

如果未安裝對應依賴，呼叫相關工具時將回傳錯誤提示。

## 本次更新

### Version 0.1.2

- 為 `spawn_bot` 和 `kill_bot` 添加 `@register_bot_tool()` 裝飾器，支援 Mineflayer Bot 呼叫
- 透過 `register_skills()` API 註冊 `carpet.md` 技能檔案（需 GamesAI 0.6.1+）
- 添加 `register_self()` 支援，`!!gamesai reload` 時自動重載
- 支援解壓目錄（開發模式）和打包 `.mcdr` zip（分發模式）兩種執行方式

### Version 0.1.1

- 新增路徑點管理工具，支援 `location_plguin`（Location Marker）和 `where2go_plugin`（Where2Go）模組
- 為 `spawn_bot` 和 `kill_bot` 添加 `@register_bot_tool()` 裝飾器，支援 Mineflayer Bot 呼叫
- 各工具模組可透過 `config.json` 獨立啟用/停用
- 首個正式版本，包含 Carpet 假人控制工具

## 授權條款

MIT License, Copyright (c) 2026 yello

<div align = "center">

---

[回到頂端](#gamesai-extra-for-mcdreforged)

</div>
