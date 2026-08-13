"""生存服务器工具集 - 传送、玩家信息、领地查询、天气时间控制

门控版改进：
- 玩家专属命令（tpa/home/warp/sethome/delhome/领地查询）改用 tellraw 可点击消息
  让玩家本人点击执行，解决 MCDR execute() 以控制台身份执行玩家命令无效的问题
- 控制台发起时返回提示，由 AI 转告玩家点击
- 默认关闭，需在 config.json 开启 survival_server
- 无文件写入
"""
import json as _json

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


def _send_clickable_cmd(source: CommandSource, label: str, command: str, hint: str = "") -> str:
    """向玩家发送一条可点击消息，玩家点击后以本人身份执行 command。

    解决 MCDR execute() 以控制台身份执行玩家专属命令（如 tpa/home/warp）无效的问题。
    返回给 AI 的说明文本。
    """
    server = source.get_server()
    if not source.is_player:
        # 控制台无法代玩家执行玩家专属命令，提示由玩家自行点击
        return (
            f"该命令需由玩家本人执行（控制台无法代执行）。请让目标玩家在聊天栏输入：/{command}"
            + (f"\n说明：{hint}" if hint else "")
        )
    player = source.player
    # tellraw clickEvent run_command：玩家点击后以本人身份执行该命令
    msg = {
        "text": f"[{label}] ",
        "color": "aqua",
        "clickEvent": {"action": "run_command", "value": f"/{command}"},
        "hoverEvent": {"action": "show_text", "value": f"点击执行 /{command}"},
    }
    server.execute(f"tellraw {player} {_json.dumps(msg, ensure_ascii=False)}")
    return (
        f"已向 {player} 发送可点击的「{label}」消息，玩家点击后将以本人身份执行 /{command}。"
        + (f"\n说明：{hint}" if hint else "")
    )


# ── 传送系统（玩家专属命令，用 tellraw 可点击）──────────────

@register_tool(
    description="玩家传送请求（tpa）—— 请求传送到某玩家身边。需要服务器安装 EssentialsX 或类似传送插件。会向调用玩家发送可点击消息，玩家点击后以本人身份发起 tpa 请求（控制台 execute 无法代玩家执行 tpa，故用此方式）。",
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
    source.reply(f"{ai_prefix}正在准备向 {target} 发送传送请求...")
    return _send_clickable_cmd(source, "点击传送", f"tpa {target}", "点击后向目标玩家发送传送请求")


@register_tool(
    description="设置/查询玩家的个人 home（家）。需要服务器安装 EssentialsX。set/del/go 会向调用玩家发送可点击消息由其本人执行；list 直接查询。",
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
    if action == "set":
        if not name:
            return "set 操作必须指定 home 名称"
        source.reply(f"{ai_prefix}正在准备设置家 {name}...")
        return _send_clickable_cmd(source, "点击设置家", f"sethome {name}")
    elif action == "del":
        if not name:
            return "del 操作必须指定 home 名称"
        source.reply(f"{ai_prefix}正在准备删除家 {name}...")
        return _send_clickable_cmd(source, "点击删除家", f"delhome {name}")
    elif action == "list":
        server.execute("homes")
        return "已请求列出所有家，结果请查看聊天栏"
    elif action == "go":
        if not name:
            return "go 操作必须指定 home 名称"
        source.reply(f"{ai_prefix}正在准备传送到家 {name}...")
        return _send_clickable_cmd(source, "点击回家", f"home {name}")
    return f"未知操作: {action}"


@register_tool(
    description="传送到公共传送点 warp（需要管理员预设）。需要服务器安装 EssentialsX。go 会向调用玩家发送可点击消息由其本人执行；list 直接查询。",
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
        source.reply(f"{ai_prefix}正在准备传送到 warp {name}...")
        return _send_clickable_cmd(source, "点击传送", f"warp {name}")
    return f"未知操作: {action}"


# ── 玩家信息查询（控制台可执行）──────────────────────────

@register_tool(
    description="查询当前在线玩家列表，或某玩家的坐标/生命/维度（通过 data get，控制台可执行）。",
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
        server.execute(f'execute as {player} run data get entity @s Pos')
        server.execute(f'execute as {player} run data get entity @s Health')
        server.execute(f'execute as {player} run data get entity @s Dimension')
        return f"已发送查询 {player} 详情的指令，结果请查看聊天栏"
    else:
        source.reply(f"{ai_prefix}正在查询在线玩家列表...")
        server.execute("list")
        return "已请求在线玩家列表，结果请查看聊天栏"


# ── 领地查询（玩家专属命令，用 tellraw 可点击）──────────────

@register_tool(
    description="查询当前位置的领地信息。领地插件（GriefDefender/Residence/Lands）是 Bukkit 插件，命令仅玩家可用，故向调用玩家发送可点击消息由其本人执行；若未安装领地插件，服务端会返回未知命令提示。",
    parameters={
        "type": "object",
        "properties": {
            "plugin": {
                "type": "string",
                "enum": ["griefdefender", "residence", "lands"],
                "description": "可选。领地插件类型。不填则默认 griefdefender。"
            }
        }
    }
)
def query_claim(source: CommandSource, ai_prefix: str, plugin: str = "griefdefender"):
    cmd_map = {
        "griefdefender": "gd claim info",
        "residence": "res info",
        "lands": "lands info",
    }
    cmd = cmd_map.get(plugin)
    if not cmd:
        return f"未知领地插件类型: {plugin}，支持: griefdefender/residence/lands"
    source.reply(f"{ai_prefix}正在准备通过 {plugin} 查询当前位置领地信息...")
    return _send_clickable_cmd(
        source, "点击查询领地", cmd,
        f"若提示未知命令，说明服务端未安装 {plugin} 领地插件"
    )


# ── 天气时间控制（管理员命令，控制台可执行）────────────────

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


# ── 公告广播（控制台可执行）──────────────────────────────

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
    text = _json.dumps({"text": f"[公告] {message}", "color": "gold"}, ensure_ascii=False)
    server.execute(f"tellraw @a {text}")
    return f"已广播: [公告] {message}"


# ── 备份查询/触发（MCDR 插件命令，控制台可执行）────────────

@register_tool(
    description="查询或触发服务器备份。需要 MCDR 安装 quick_backup_multi 插件。生存服防熊/防回档必备。",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "make", "confirm"],
                "description": "操作：list=列出已有备份，make=创建新备份，confirm=确认备份（如果插件需要）"
            }
        },
        "required": ["action"]
    }
)
def backup_manage(source: CommandSource, ai_prefix: str, action: str):
    server = source.get_server()
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
