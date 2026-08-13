"""生存服务器工具集 - 传送、玩家信息、库存查看、领地查询、天气时间控制

高效实现策略：
- 直接调用原版/MCDR 命令，不引入额外依赖
- 玩家信息查询使用 list 命令解析（最小开销）
- 库存查看优先用 carpet script，回退到原版命令
"""
import json
import os
import re
import time

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


# ── 传送系统 ──────────────────────────────────────────────

@register_tool(
    description="玩家传送请求（tpa）—— 请求传送到某玩家身边。需要服务器安装 EssentialsX 或类似传送插件。请求会发送给目标玩家，对方接受后才传送。",
    parameters={
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "要传送到的目标玩家名"
            }
        },
        "required": ["target"]
    }
)
def tpa_request(source: CommandSource, ai_prefix: str, target: str):
    server = source.get_server()
    if not source.is_player:
        return "控制台无法使用 tpa，请由玩家发起"
    source.reply(f"{ai_prefix}正在向 {target} 发送传送请求...")
    server.execute(f"tpa {target}")
    return f"已向 {target} 发送传送请求，等待对方接受"


@register_tool(
    description="设置/查询玩家的个人 home（家）。需要服务器安装 EssentialsX。home 是玩家私有的传送点，每个玩家可设置多个。",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["set", "del", "list", "go"],
                "description": "操作：set=设置家，del=删除家，list=列出所有家，go=传送到家"
            },
            "name": {
                "type": "string",
                "description": "家名称。set/del/go 必填，list 不需要。"
            }
        },
        "required": ["action"]
    }
)
def home_manage(source: CommandSource, ai_prefix: str, action: str, name: str = None):
    server = source.get_server()
    if not source.is_player:
        return "控制台无法管理 home，请由玩家发起"
    if action == "set":
        if not name:
            return "set 操作必须指定 home 名称"
        source.reply(f"{ai_prefix}正在设置家 {name}...")
        server.execute(f"sethome {name}")
        return f"已发送设置家 {name} 的指令"
    elif action == "del":
        if not name:
            return "del 操作必须指定 home 名称"
        server.execute(f"delhome {name}")
        return f"已发送删除家 {name} 的指令"
    elif action == "list":
        server.execute("homes")
        return "已请求列出所有家，结果请查看聊天栏"
    elif action == "go":
        if not name:
            return "go 操作必须指定 home 名称"
        server.execute(f"home {name}")
        return f"已发送传送到家 {name} 的指令"
    return f"未知操作: {action}"


@register_tool(
    description="传送到公共传送点 warp（需要管理员预设）。需要服务器安装 EssentialsX。warp 是全服共享的传送点，常用于出生点/商店/活动区。",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["go", "list"],
                "description": "操作：go=传送到 warp，list=列出所有 warp"
            },
            "name": {
                "type": "string",
                "description": "warp 名称。go 时必填。"
            }
        },
        "required": ["action"]
    }
)
def warp_manage(source: CommandSource, ai_prefix: str, action: str, name: str = None):
    server = source.get_server()
    if action == "list":
        server.execute("warps")
        return "已请求列出所有 warp，结果请查看聊天栏"
    elif action == "go":
        if not name:
            return "go 操作必须指定 warp 名称"
        server.execute(f"warp {name}")
        return f"已发送传送到 warp {name} 的指令"
    return f"未知操作: {action}"


# ── 玩家信息 ──────────────────────────────────────────────

@register_tool(
    description="查询当前在线玩家列表及基本信息（坐标、生命值、维度）。高效实现：调用 list + 各玩家 data query。",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "string",
                "description": "可选。只查询某个具体玩家的详情。不填则返回在线玩家列表。"
            }
        }
    }
)
def get_player_info(source: CommandSource, ai_prefix: str, player: str = None):
    server = source.get_server()
    if player:
        source.reply(f"{ai_prefix}正在查询玩家 {player} 的详情...")
        # 用 data get 查坐标/生命
        server.execute(f'execute as {player} run data get entity @s Pos')
        server.execute(f'execute as {player} run data get entity @s Health')
        server.execute(f'execute as {player} run data get entity @s Dimension')
        return f"已发送查询 {player} 详情的指令，结果请查看聊天栏"
    else:
        source.reply(f"{ai_prefix}正在查询在线玩家列表...")
        server.execute("list")
        return "已请求在线玩家列表，结果请查看聊天栏"


# ── 玩家库存查看 ──────────────────────────────────────────

@register_tool(
    description="查看玩家背包/装备的物品。需要 fabric-carpet 的 script run 能力或权限。用于借物/检查/借还管理。",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "string",
                "description": "目标玩家名"
            },
            "slot_type": {
                "type": "string",
                "enum": ["inventory", "enderchest", "equipment"],
                "description": "可选。查看类型：inventory=主背包，enderchest=末影箱，equipment=装备栏。默认 inventory。"
            }
        },
        "required": ["player"]
    }
)
def view_inventory(source: CommandSource, ai_prefix: str, player: str, slot_type: str = "inventory"):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在查询 {player} 的 {slot_type}...")
    # 用 carpet script 查询玩家库存
    if slot_type == "inventory":
        server.execute(f'script run print(player("{player}").inventory.main)')
    elif slot_type == "enderchest":
        server.execute(f'script run print(player("{player}").inventory.enderchest)')
    elif slot_type == "equipment":
        server.execute(f'script run print(player("{player}").inventory.armor)')
    else:
        return f"未知 slot_type: {slot_type}"
    return f"已发送查询指令，结果请查看控制台 carpet script 输出"


# ── 领地查询 ──────────────────────────────────────────────

@register_tool(
    description="查询当前位置的领地信息。领地插件（GriefDefender/Residence/Lands）是 Bukkit 插件，本工具直接尝试常见查询命令，由服务端处理；若未安装领地插件，服务端会返回未知命令提示。建议按服务器实际安装的领地插件选用对应命令。",
    parameters={
        "type": "object",
        "properties": {
            "plugin": {
                "type": "string",
                "enum": ["griefdefender", "residence", "lands"],
                "description": "可选。领地插件类型。不填则默认尝试 griefdefender。"
            }
        }
    }
)
def query_claim(source: CommandSource, ai_prefix: str, plugin: str = "griefdefender"):
    server = source.get_server()
    if not source.is_player:
        return "控制台无法查询领地，需要由玩家在目标位置发起查询"
    cmd_map = {
        "griefdefender": "gd claim info",
        "residence": "res info",
        "lands": "lands info",
    }
    cmd = cmd_map.get(plugin)
    if not cmd:
        return f"未知领地插件类型: {plugin}，支持: griefdefender/residence/lands"
    source.reply(f"{ai_prefix}正在通过 {plugin} 查询当前位置领地信息...")
    # 直接执行命令，由服务端处理；若未安装对应插件，服务端会返回未知命令
    server.execute(cmd)
    return f"已发送查询指令: /{cmd}。若提示未知命令，说明服务端未安装 {plugin} 领地插件。"


# ── 天气时间控制 ──────────────────────────────────────────

@register_tool(
    description="设置服务器天气。需要管理员权限。生存服日常用：晴天方便建造/探索。",
    parameters={
        "type": "object",
        "properties": {
            "weather": {
                "type": "string",
                "enum": ["clear", "rain", "thunder"],
                "description": "天气：clear=晴天，rain=下雨，thunder=雷暴"
            },
            "duration": {
                "type": "integer",
                "description": "可选。持续时间（秒），原版单位是 tick，本工具会自动乘 20。不填则使用游戏默认。"
            }
        },
        "required": ["weather"]
    }
)
def set_weather(source: CommandSource, ai_prefix: str, weather: str, duration: int = None):
    server = source.get_server()
    if weather == "clear":
        cmd = "weather clear"
    elif weather == "rain":
        cmd = "weather rain"
    elif weather == "thunder":
        cmd = "weather thunder"
    else:
        return f"未知天气: {weather}"
    if duration:
        cmd += f" {duration * 20}"
    source.reply(f"{ai_prefix}正在设置天气为 {weather}...")
    server.execute(cmd)
    return f"已发送天气设置指令：/{cmd}"


@register_tool(
    description="设置服务器时间（游戏内时间）。需要管理员权限。0=日出，6000=正午，12000=日落，18000=半夜。",
    parameters={
        "type": "object",
        "properties": {
            "time": {
                "type": "integer",
                "description": "目标游戏时间（0-24000）。常用：0=日出，6000=正午，12000=日落，18000=半夜"
            },
            "mode": {
                "type": "string",
                "enum": ["set", "add"],
                "description": "可选。set=直接设置（默认），add=增加时间"
            }
        },
        "required": ["time"]
    }
)
def set_time(source: CommandSource, ai_prefix: str, time: int, mode: str = "set"):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在设置时间为 {time}...")
    server.execute(f"time {mode} {time}")
    return f"已发送时间设置指令：time {mode} {time}"


# ── 公告广播 ──────────────────────────────────────────────

@register_tool(
    description="向全服广播一条公告消息（带前缀）。需要管理员权限。生存服活动通知/紧急公告用。",
    parameters={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "要广播的消息内容"
            }
        },
        "required": ["message"]
    }
)
def broadcast(source: CommandSource, ai_prefix: str, message: str):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在广播公告...")
    # 用 tellraw 给所有玩家发带前缀的消息
    import json as _json
    text = _json.dumps({"text": f"[公告] {message}", "color": "gold"}, ensure_ascii=False)
    server.execute(f"tellraw @a {text}")
    return f"已广播: [公告] {message}"


# ── 备份查询/触发 ──────────────────────────────────────────

@register_tool(
    description="查询或触发服务器备份。需要 MCDR 安装 quick_backup_multi 插件。生存服防熊/防回档必备。",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "make", "confirm"],
                "description": "操作：list=列出已有备份，make=创建新备份，confirm=确认备份（如果插件需要）"
            },
            "slot": {
                "type": "string",
                "description": "可选。备份槽位名（如 slot_a/slot_b/slot_c）。list/make 时可用。"
            }
        },
        "required": ["action"]
    }
)
def backup_manage(source: CommandSource, ai_prefix: str, action: str, slot: str = None):
    server = source.get_server()
    # quick_backup_multi 是 MCDR 插件，可以用 get_plugin_metadata 检测
    # 但为稳健起见，直接执行命令，由 MCDR 处理；若未安装，!!qb 命令会被忽略
    if action == "list":
        server.execute("!!qb list")
        return "已请求备份列表，结果请查看聊天栏。若无响应，说明服务端未安装 quick_backup_multi 插件。"
    elif action == "make":
        server.execute("!!qb make")
        return "已触发创建新备份。若无响应，说明服务端未安装 quick_backup_multi 插件。"
    elif action == "confirm":
        server.execute("!!qb confirm")
        return "已发送确认指令。"
    return f"未知操作: {action}"
