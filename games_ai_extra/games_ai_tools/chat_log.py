"""聊天记录模块 - 监听并搜索服务器聊天记录（内存版）

门控版改进：
- 完全内存存储（deque），不写入任何文件
- 默认关闭，需在 config.json 显式开启 chat_log
- 监听器由 __init__ 按配置决定是否记录
"""
import time
from collections import deque

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


_MAX_RECORDS = 5000
# 内存缓存：进程重启后清空（符合"无文件写入"要求）
_CHAT_RECORDS: deque = deque(maxlen=_MAX_RECORDS)


def _append_chat_record(player: str, message: str):
    """追加一条聊天记录到内存。高效：deque 自动滚动，O(1)。"""
    _CHAT_RECORDS.append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": int(time.time()),
        "player": player,
        "message": message,
    })


@register_tool(
    description="搜索服务器聊天记录。可按玩家、关键词、时间范围过滤。用于查证玩家说过什么、追溯纠纷。注意：仅保留本插件运行期间的记录（内存存储，重启清空），默认关闭，需在 config.json 开启 chat_log。",
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
    if not _CHAT_RECORDS:
        return "暂无聊天记录（本插件启动后尚未记录任何消息，或 chat_log 未启用）"

    records = list(_CHAT_RECORDS)
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

    result = filtered[-limit:][::-1]
    lines = []
    for r in result:
        lines.append(f"[{r.get('time', '?')}] {r.get('player', '?')}: {r.get('message', '')}")
    header = f"找到 {len(filtered)} 条匹配记录（共扫描 {len(records)} 条），显示最近 {len(result)} 条："
    return header + "\n" + "\n".join(lines)


@register_tool(
    description="清空所有聊天记录（内存）。⚠️ 不可恢复。需要管理员权限。仅清空当前运行期间的记录。",
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
    _CHAT_RECORDS.clear()
    return "聊天记录已清空"


# ── 监听玩家聊天事件（由 __init__ on_player_chat 按配置调用）────────

def on_player_chat(server, player, message, **kwargs):
    """MCDR 玩家聊天事件回调。高效：内存 append，O(1)。"""
    _append_chat_record(player, message)
