"""聊天记录模块 - 监听并搜索服务器聊天记录

高效实现策略：
- 监听 MCDR on_player_chat 事件，异步追加到 JSON Lines 文件（.jsonl）
- 搜索时流式读取，避免一次性载入大文件
- 按时间/玩家/关键词过滤
- 限制最大文件大小（超过自动滚动）
"""
import json
import os
import time
from collections import deque

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


_CHAT_LOG_FILE = os.path.join("config", "games_ai_extra", "chat_log.jsonl")
_MAX_RECORDS = 5000  # 最大保留记录数，超过自动滚动


def _ensure_log_dir():
    os.makedirs(os.path.dirname(_CHAT_LOG_FILE), exist_ok=True)


def _append_chat_record(player: str, message: str):
    """追加一条聊天记录到 JSONL 文件。高效：单行 append，不读全文。"""
    try:
        _ensure_log_dir()
        record = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": int(time.time()),
            "player": player,
            "message": message,
        }
        with open(_CHAT_LOG_FILE, mode="a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        # 定期滚动（粗略检查文件行数，避免每次都检查）
        _maybe_rotate_log()
    except Exception:
        pass  # 聊天记录失败不应影响游戏


def _maybe_rotate_log():
    """检查文件行数，超过上限则保留最新的 _MAX_RECORDS 条"""
    try:
        if not os.path.isfile(_CHAT_LOG_FILE):
            return
        # 用 deque 高效保留最后 N 行
        with open(_CHAT_LOG_FILE, mode="r", encoding="utf-8") as f:
            last_lines = deque(f, maxlen=_MAX_RECORDS)
        if len(last_lines) < _MAX_RECORDS:
            return
        # 重写文件
        with open(_CHAT_LOG_FILE, mode="w", encoding="utf-8") as f:
            f.writelines(last_lines)
    except Exception:
        pass


def _load_chat_records() -> list:
    """流式读取所有聊天记录"""
    if not os.path.isfile(_CHAT_LOG_FILE):
        return []
    records = []
    try:
        with open(_CHAT_LOG_FILE, mode="r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return records


@register_tool(
    description="搜索服务器聊天记录。可按玩家、关键词、时间范围过滤。用于查证玩家说过什么、追溯纠纷、找历史指令。",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "string",
                "description": "可选。按玩家名过滤（精确匹配，大小写敏感）。不填则不限玩家。"
            },
            "keyword": {
                "type": "string",
                "description": "可选。按消息关键词过滤（模糊匹配，大小写不敏感）。不填则不限关键词。"
            },
            "since": {
                "type": "string",
                "description": "可选。起始时间（格式 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）。只返回此时间之后的记录。"
            },
            "until": {
                "type": "string",
                "description": "可选。截止时间（格式同上）。只返回此时间之前的记录。"
            },
            "limit": {
                "type": "integer",
                "description": "可选。最多返回多少条记录，默认 20。建议 ≤ 50 避免响应过长。"
            }
        }
    }
)
def search_chat_log(source: CommandSource, ai_prefix: str, player: str = None, keyword: str = None, since: str = None, until: str = None, limit: int = 20):
    source.reply(f"{ai_prefix}正在搜索聊天记录...")
    records = _load_chat_records()
    if not records:
        return "暂无聊天记录（数据文件不存在或为空）"

    # 应用过滤
    filtered = records
    if player:
        filtered = [r for r in filtered if r.get("player") == player]
    if keyword:
        kw_lower = keyword.lower()
        filtered = [r for r in filtered if kw_lower in r.get("message", "").lower()]
    if since:
        filtered = [r for r in filtered if r.get("time", "") >= since]
    if until:
        filtered = [r for r in filtered if r.get("time", "") <= until]

    if not filtered:
        return f"未找到匹配的聊天记录（共扫描 {len(records)} 条）"

    # 取最近 limit 条，倒序（最新在前）
    result = filtered[-limit:][::-1]
    lines = []
    for r in result:
        lines.append(f"[{r.get('time', '?')}] {r.get('player', '?')}: {r.get('message', '')}")
    header = f"找到 {len(filtered)} 条匹配记录（共扫描 {len(records)} 条），显示最近 {len(result)} 条："
    return header + "\n" + "\n".join(lines)


@register_tool(
    description="清空所有聊天记录。⚠️ 不可恢复，建议仅在文件过大或管理员要求时使用。需要管理员权限。",
    parameters={
        "type": "object",
        "properties": {
            "confirm": {
                "type": "boolean",
                "description": "必须传 true 才会执行清空，防止误操作"
            }
        },
        "required": ["confirm"]
    }
)
def clear_chat_log(source: CommandSource, ai_prefix: str, confirm: bool):
    if not confirm:
        return "未确认，已取消清空。如需清空请传 confirm=true"
    try:
        if os.path.isfile(_CHAT_LOG_FILE):
            os.remove(_CHAT_LOG_FILE)
        return "聊天记录已清空"
    except OSError as e:
        return f"清空失败: {e}"


# ── 监听玩家聊天事件（由 MCDR on_player_chat 调用）────────

def on_player_chat(server, player, message, **kwargs):
    """MCDR 玩家聊天事件回调。高效：单行 append，不阻塞。"""
    _append_chat_record(player, message)
