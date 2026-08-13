"""假人批量脚本工具集 - 一次操作多个 Carpet 假人

高效实现策略：
- 复用 carpet.py 已有的 spawn_bot/kill_bot/bot_action 等工具
- 批量 spawn/kill/action 直接遍历调用，避免重复代码
- group 配置可保存到 JSON 复用
"""
import json
import os

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool

from games_ai_extra.games_ai_tools.carpet import spawn_bot, kill_bot, bot_action, bot_hotbar, bot_look


_GROUP_DB_FILE = os.path.join("config", "games_ai_extra", "bot_groups.json")


def _load_groups() -> dict:
    if not os.path.isfile(_GROUP_DB_FILE):
        return {}
    try:
        with open(_GROUP_DB_FILE, mode="r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_groups(data: dict):
    os.makedirs(os.path.dirname(_GROUP_DB_FILE), exist_ok=True)
    with open(_GROUP_DB_FILE, mode="w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@register_tool(
    description="批量生成多个假人。每个假人可指定不同坐标/维度。常用于农场分工：一个攻击一个捡物一个放方块。",
    parameters={
        "type": "object",
        "properties": {
            "bots": {
                "type": "array",
                "description": "假人配置列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "假人名（自动加 bot_ 前缀）"},
                        "pos": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "可选。生成坐标 [x, y, z]"
                        },
                        "dim": {"type": "string", "description": "可选。维度 ID"},
                        "player": {"type": "string", "description": "可选。在某玩家身边生成（与 pos/dim 互斥）"}
                    },
                    "required": ["name"]
                }
            }
        },
        "required": ["bots"]
    }
)
def group_spawn(source: CommandSource, ai_prefix: str, bots: list):
    source.reply(f"{ai_prefix}正在批量生成 {len(bots)} 个假人...")
    results = []
    for cfg in bots:
        name = cfg.get("name", "")
        if not name:
            results.append("跳过：缺少 name")
            continue
        if not name.startswith("bot_"):
            name = "bot_" + name
        pos = cfg.get("pos")
        dim = cfg.get("dim")
        player = cfg.get("player")
        try:
            r = spawn_bot(source, ai_prefix, name=name, pos=pos, player=player, dim=dim)
            results.append(f"{name}: {r}")
        except Exception as e:
            results.append(f"{name}: 失败 - {e}")
    return "批量生成完成:\n" + "\n".join(results)


@register_tool(
    description="批量移除多个假人。",
    parameters={
        "type": "object",
        "properties": {
            "names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "要移除的假人名列表（自动加 bot_ 前缀）"
            }
        },
        "required": ["names"]
    }
)
def group_kill(source: CommandSource, ai_prefix: str, names: list):
    source.reply(f"{ai_prefix}正在批量移除 {len(names)} 个假人...")
    results = []
    for n in names:
        if not n.startswith("bot_"):
            n = "bot_" + n
        try:
            r = kill_bot(source, ai_prefix, name=n)
            results.append(f"{n}: {r}")
        except Exception as e:
            results.append(f"{n}: 失败 - {e}")
    return "批量移除完成:\n" + "\n".join(results)


@register_tool(
    description="让多个假人同时执行相同动作。例如一组假人同时 attack 或同时 mine。常用于多人农场协作。",
    parameters={
        "type": "object",
        "properties": {
            "names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "假人名列表（自动加 bot_ 前缀）"
            },
            "action": {
                "type": "string",
                "enum": ["attack", "use", "mine", "stop", "drop", "dropStack", "jump", "sneak", "swapHands", "mount", "dismount"],
                "description": "动作类型（同 bot_action）"
            },
            "interval": {
                "type": "integer",
                "description": "可选。动作间隔（tick），仅对 attack/use/mine 生效。"
            }
        },
        "required": ["names", "action"]
    }
)
def group_action(source: CommandSource, ai_prefix: str, names: list, action: str, interval: int = 1):
    source.reply(f"{ai_prefix}正在让 {len(names)} 个假人执行 {action}...")
    results = []
    for n in names:
        if not n.startswith("bot_"):
            n = "bot_" + n
        try:
            r = bot_action(source, ai_prefix, name=n, action=action, interval=interval)
            results.append(f"{n}: {r}")
        except Exception as e:
            results.append(f"{n}: 失败 - {e}")
    return "批量动作完成:\n" + "\n".join(results)


@register_tool(
    description="保存一个假人组配置（名字列表 + 默认动作），方便后续一键调用。例如保存一个 5 人农场组，之后 group_run 直接启动。",
    parameters={
        "type": "object",
        "properties": {
            "group_name": {
                "type": "string",
                "description": "组名（如 'farm_team'、'mine_squad'）"
            },
            "bots": {
                "type": "array",
                "description": "假人配置列表（同 group_spawn 的 bots 参数格式）"
            },
            "default_action": {
                "type": "string",
                "description": "可选。该组默认动作（如 'attack'、'mine'）"
            }
        },
        "required": ["group_name", "bots"]
    }
)
def save_group(source: CommandSource, ai_prefix: str, group_name: str, bots: list, default_action: str = None):
    groups = _load_groups()
    groups[group_name] = {
        "bots": bots,
        "default_action": default_action,
    }
    _save_groups(groups)
    return f"已保存假人组 {group_name}（{len(bots)} 个假人，默认动作: {default_action or '无'}）"


@register_tool(
    description="一键运行已保存的假人组：spawn + 执行默认动作。",
    parameters={
        "type": "object",
        "properties": {
            "group_name": {
                "type": "string",
                "description": "假人组名（由 save_group 保存）"
            },
            "action": {
                "type": "string",
                "description": "可选。覆盖组的默认动作。不填则用 default_action。"
            }
        },
        "required": ["group_name"]
    }
)
def group_run(source: CommandSource, ai_prefix: str, group_name: str, action: str = None):
    groups = _load_groups()
    if group_name not in groups:
        return f"未找到假人组 {group_name}。可用 group_list 查看所有组"
    g = groups[group_name]
    bots = g.get("bots", [])
    act = action or g.get("default_action")
    # 1. 批量 spawn
    spawn_result = group_spawn(source, ai_prefix, bots=bots)
    # 2. 批量执行动作
    if act:
        names = []
        for b in bots:
            n = b.get("name", "")
            if n and not n.startswith("bot_"):
                n = "bot_" + n
            if n:
                names.append(n)
        action_result = group_action(source, ai_prefix, names=names, action=act)
        return f"组 {group_name} 已启动:\n{spawn_result}\n\n{action_result}"
    return f"组 {group_name} 已 spawn（无默认动作）:\n{spawn_result}"


@register_tool(
    description="列出所有已保存的假人组。",
    parameters={
        "type": "object",
        "properties": {}
    }
)
def group_list(source: CommandSource, ai_prefix: str):
    groups = _load_groups()
    if not groups:
        return "暂无已保存的假人组"
    lines = []
    for name, g in groups.items():
        bots = g.get("bots", [])
        act = g.get("default_action", "无")
        lines.append(f"- {name}: {len(bots)} 个假人, 默认动作={act}")
    return "已保存的假人组:\n" + "\n".join(lines)


@register_tool(
    description="删除一个已保存的假人组。",
    parameters={
        "type": "object",
        "properties": {
            "group_name": {
                "type": "string",
                "description": "要删除的组名"
            }
        },
        "required": ["group_name"]
    }
)
def group_delete(source: CommandSource, ai_prefix: str, group_name: str):
    groups = _load_groups()
    if group_name not in groups:
        return f"未找到假人组 {group_name}"
    del groups[group_name]
    _save_groups(groups)
    return f"已删除假人组 {group_name}"
