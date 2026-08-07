<div align="center">

# GamesAI Extra for MCDReforged

[English](/README.md)  |  [简体中文](/README.zh-CN.md)  |  繁體中文

[回報問題](https://github.com/PengZixuan30/Games_AI-Extra/issues/new)  |  [提供想法](https://github.com/PengZixuan30/Games_AI-Extra/discussions/new/choose)

</div>

> [!NOTE]
> **GamesAI Extra** 是 [GamesAI](https://github.com/PengZixuan30/Games_AI) 的功能性擴展插件。它為 AI 提供了 Carpet 假人（Bot）控制工具，允許 AI 在你的 Minecraft 伺服器上生成、控制和管理假人。

> [!IMPORTANT]
> 此插件需要 **GamesAI >= 0.6.0** 已安裝並先載入。

<details>
<summary>目錄（點擊展開）</summary>

- [GamesAI Extra for MCDReforged](#gamesai-extra-for-mcdreforged)
  - [安裝](#安裝)
  - [設定](#設定)
  - [工具](#工具)
    - [生成與移除](#生成與移除)
    - [行為控制](#行為控制)
    - [移動控制](#移動控制)
    - [視角控制](#視角控制)
    - [快捷欄](#快捷欄)
    - [限時動作](#限時動作)
    - [自訂指令](#自訂指令)
  - [授權條款](#授權條款)

</details>

## 安裝

將此插件與 [GamesAI](https://github.com/PengZixuan30/Games_AI) 一起安裝到你的 MCDR 插件目錄中。

在 MCDR 主控台中使用以下指令安裝：

`!!MCDR plugin install games_ai_extra`

---

或者從 [MCDR 插件倉庫](https://mcdreforged.com/plugin/games_ai_extra) 取得並放置到你的插件目錄中。

無需額外安裝 Python 套件——此插件僅依賴 `games_ai`。

## 設定

預設設定檔（`config/games_ai_extra/config.json`）結構如下：

```json
{
    "carpet": true
}
```

- **carpet**：設為 `true` 啟用 Carpet 假人工具；設為 `false` 停用。

修改設定後，使用 `!!gamesai reload` 使變更生效。

## 工具

啟用後，以下工具會自動註冊到 GamesAI 中，AI 可透過 `!!ask` 呼叫。

### 生成與移除

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `spawn_bot` | `name`、`pos?`、`player?`、`dim?` | 在伺服器中生成一個假人。可指定 `pos`（座標 `[x, y, z]`）在特定位置生成，或指定 `player`（玩家名稱）在某玩家身邊生成。`pos` 與 `player` 互斥。可選指定 `dim`（如 `minecraft:the_nether`）在特定維度生成。不指定位置時在世界重生點生成。 |
| `kill_bot` | `name` | 移除（殺死）一個假人。此操作不可逆——如需重新使用請用 `spawn_bot` 重新生成。 |

### 行為控制

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_action` | `name`、`action`、`interval?` | 控制假人執行動作。支援的動作：`attack`（攻擊，需手持武器）、`use`（右鍵目標）、`mine`（挖掘面前方塊）、`stop`（停止所有動作）、`drop`（丟棄手中物品）、`dropStack`（丟棄整組物品）、`jump`（跳躍）、`sneak`（切換潛行）、`swapHands`（交換左右手）、`mount`（騎乘附近實體）、`dismount`（下馬）。可選 `interval` 為遊戲刻（tick）間隔（預設 1）。 |

### 移動控制

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_move` | `name`、`direction` | 讓假人持續向某個方向移動：`forward`（前進）、`backward`（後退）、`left`（向左）、`right`（向右）。假人會一直移動，直到發送 `stop` 動作或改變方向。 |

### 視角控制

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_look` | `name`、`target` | 控制假人看向某個方向或座標。`target` 可以是方向詞（`north`、`south`、`east`、`west`、`up`、`down`）或座標（`"x y z"`，如 `"100 64 200"`）。 |

### 快捷欄

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_hotbar` | `name`、`slot` | 切換假人目前選中的快捷欄格子（1~9）。切換後攻擊/使用/挖掘等操作將使用對應格子的物品。 |

### 限時動作

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_timed_action` | `name`、`action`、`duration` | 讓假人執行一個限時動作，到達指定秒數後自動停止。支援：`attack`、`use`、`mine`、`forward`、`backward`、`left`、`right`。適合短時間操作（建議 ≤ 60 秒）。注意：會阻塞目前 AI 對話直到時間到達。 |

### 自訂指令

| 工具 | 參數 | 用途 |
|:---:|:---:|:---|
| `bot_command` | `name`、`command` | 向假人發送一條原始自訂 `/player` 指令，用於上述工具無法涵蓋的進階操作。指令會自動補全為 `player <name> <command>` 格式。需要了解 Carpet 假人指令。 |

## 授權條款

MIT License, Copyright (c) 2026 yello

<div align = "center">

---

[回到頂端](#gamesai-extra-for-mcdreforged)

</div>
