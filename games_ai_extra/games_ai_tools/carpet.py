import time

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool

@register_tool(description="在服务器中生成一个假人。可以指定坐标(pos)在特定位置生成，或指定玩家名(player)在某个玩家身边生成。pos 和 player 互斥，只能二选一。两个都不填则在世界出生点生成。可选指定维度(dim)在特定维度（如 minecraft:the_nether）生成：若同时指定 pos 则在维度指定坐标生成，若不指定 pos 则在维度 ~ ~ ~ 位置生成。创建假人后需通过其他工具控制其行为。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字，建议使用英文和下划线"
        },
        "pos": {
            "type": "array",
            "items": {
                "type": "number"
            },
            "description": "可选。假人生成的坐标，格式为 [x, y, z]。与 player 互斥，二选一。不填且不传 player 则根据是否指定 dim 决定行为。"
        },
        "player": {
            "type": "string",
            "description": "可选。让假人在某个具体玩家旁边生成。⚠️ 传入 player 时不得同时传入 pos 或 dim，即 player 与 pos、dim 均互斥。若要在玩家身边生成则只传 player，不传其他参数。"
        },
        "dim": {
            "type": "string",
            "description": "可选。目标维度 ID，如 minecraft:overworld、minecraft:the_nether、minecraft:the_end。指定后假人将在该维度生成。若同时指定 pos，则在维度的指定坐标生成；若不指定 pos，则在维度的 ~ ~ ~ 位置生成。⚠️ 与 player 互斥，传入 player 时不要传入 dim。配合 pos 使用时需要确保坐标合法。"
        }
    },
    "required": ["name"]
})
def spawn_bot(source: CommandSource, ai_prefix: str, name: str, pos: list | None = None, player: str | None = None, dim: str | None = None):
    server = source.get_server()
    if source.is_player:
        exe_player = source.player
        cmd_prefix = f"execute as {exe_player} run "
    else:
        exe_player = "Server Control Panel"
        cmd_prefix = ""
    if dim:
        if pos and len(pos) == 3:
            source.reply(f"{ai_prefix}正在在维度 {dim} 的坐标 {pos} 处生成假人 {name} ...")
            server.execute(f"{cmd_prefix}player {name} spawn at {pos[0]} {pos[1]} {pos[2]} facing 0 0 in {dim}")
            return f"假人 {name} 已在维度 {dim} 的坐标 {pos} 处生成"
        elif player:
            source.reply(f"{ai_prefix}正在在 {player} 身边生成假人 {name} ...")
            server.execute(f"execute as {player} at @s run player {name} spawn")
            return f"假人 {name} 已生成在 {player} 的位置"
        else:
            source.reply(f"{ai_prefix}正在在维度 {dim} 生成假人 {name} ...")
            server.execute(f"{cmd_prefix}player {name} spawn at ~ ~ ~ facing 0 0 in {dim}")
            return f"假人 {name} 已在维度 {dim} 的 ~ ~ ~ 位置生成"
    else:
        if pos and len(pos) == 3:
            source.reply(f"{ai_prefix}正在在坐标 {pos} 处生成假人 {name} ...")
            server.execute(f"{cmd_prefix}player {name} spawn at {pos[0]} {pos[1]} {pos[2]}")
            return f"假人 {name} 已在坐标 {pos} 处生成"
        elif player:
            source.reply(f"{ai_prefix}正在在 {player} 身边生成假人 {name} ...")
            server.execute(f"execute as {player} at @s run player {name} spawn")
            return f"假人 {name} 已生成在 {player} 的位置"
        else:
            source.reply(f"{ai_prefix}正在生成假人 {name} ...")
            server.execute(f"{cmd_prefix}player {name} spawn")
            return f"假人 {name} 已在出生点生成"

@register_tool(description="移除（杀死）一个假人，假人将从服务器中消失。这个操作不可逆，如果之后还需要该假人，请使用 spawn_bot 重新生成。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "要移除的假人名字"
        }
    },
    "required": ["name"]
})
def kill_bot(source: CommandSource, ai_prefix: str, name: str):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在移除假人 {name} ...")
    server.execute(f"player {name} kill")
    return f"假人 {name} 已移除"

# ── 行为控制 ──────────────────────────────────────────────

@register_tool(description="控制假人执行一个动作。攻击(attack)需要假人手持武器；使用(use)会右键点击面前的目标；挖掘(mine)会挖掘面前的方块；停止(stop)会取消当前所有动作；丢物品(drop)会丢弃手中物品；潜行(sneak)用于切换潜行状态；交换左右手(swapHands)；骑乘(mount)会骑上附近的实体；下马(dismount)。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        },
        "action": {
            "type": "string",
            "enum": ["attack", "use", "mine", "stop", "drop", "dropStack", "jump", "sneak", "swapHands", "mount", "dismount"],
            "description": "要执行的动作：attack=攻击，use=右键使用，mine=挖掘，stop=停止一切动作，drop=丢物品，dropStack=丢整组物品，jump=跳跃，sneak=切换潜行，swapHands=交换左右手，mount=骑乘，dismount=下马"
        },
        "interval": {
            "type": "integer",
            "description": "动作间隔（游戏刻 tick）。默认1代表每tick执行一次。攻击/使用/挖掘时可以调大间隔来降低频率。"
        }
    },
    "required": ["name", "action"]
})
def bot_action(source: CommandSource, ai_prefix: str, name: str, action: str, interval: int = 1):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在让假人 {name} 执行 {action} ...")
    cmd = f"player {name} {action}"
    if action in ("attack", "use", "mine"):
        cmd += f" interval {interval}"
    server.execute(cmd)
    return f"假人 {name} 正在执行 {action}（间隔={interval} tick）"

# ── 移动控制 ──────────────────────────────────────────────

@register_tool(description="控制假人朝指定方向移动。假人会持续向该方向移动，直到你发送 stop 动作或改变方向为止。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        },
        "direction": {
            "type": "string",
            "enum": ["forward", "backward", "left", "right"],
            "description": "移动方向：forward=前进，backward=后退，left=向左，right=向右"
        }
    },
    "required": ["name", "direction"]
})
def bot_move(source: CommandSource, ai_prefix: str, name: str, direction: str):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在让假人 {name} 向 {direction} 移动...")
    server.execute(f"player {name} move {direction}")
    return f"假人 {name} 正在向 {direction} 移动。如需停止，请使用 stop 动作"

# ── 视角控制 ──────────────────────────────────────────────

@register_tool(description="控制假人的视线方向。可以看向方向词（north/south/east/west/up/down）或者具体坐标（x y z）。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        },
        "target": {
            "type": "string",
            "description": "视线目标。可以是方向词（north、south、east、west、up、down）或坐标（格式：x y z，如 '100 64 200'）"
        }
    },
    "required": ["name", "target"]
})
def bot_look(source: CommandSource, ai_prefix: str, name: str, target: str):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在让假人 {name} 看向 {target} ...")
    direction_words = {"north", "south", "east", "west", "up", "down"}
    target_lower = target.strip().lower()
    if target_lower in direction_words or target_lower.startswith("at "):
        cmd = f"player {name} look {target}"
    elif len(target.split()) == 3:
        cmd = f"player {name} look at {target}"
    else:
        cmd = f"player {name} look {target}"
    server.execute(cmd)
    return f"假人 {name} 正在看向 {target}"

# ── 快捷栏 ────────────────────────────────────────────────

@register_tool(description="切换假人当前选中的快捷栏格子，范围为 1~9。切换后假人的攻击/使用/挖掘等操作将使用对应格子的物品。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        },
        "slot": {
            "type": "integer",
            "description": "快捷栏编号，范围 1~9"
        }
    },
    "required": ["name", "slot"]
})
def bot_hotbar(source: CommandSource, ai_prefix: str, name: str, slot: int):
    server = source.get_server()
    if not (1 <= slot <= 9):
        return f"快捷栏编号必须在 1~9 之间，你输入的是 {slot}"
    source.reply(f"{ai_prefix}正在切换假人 {name} 的快捷栏到第 {slot} 格...")
    server.execute(f"player {name} hotbar {slot}")
    return f"假人 {name} 的快捷栏已切换到第 {slot} 格"

# ── 限时动作 ────────────────────────────────────────────

@register_tool(description="让假人执行一个限时动作，到达指定秒数后自动停止。适用于\"前进5秒后停\"、\"攻击30秒后停\"等场景。注意此工具会阻塞等待直到时间到达（期间无法执行其他操作），适合短时间操作（建议 ≤ 60 秒）。不支持与 interval 同时指定；如需间隔攻击请用 bot_action 手动控制。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        },
        "action": {
            "type": "string",
            "enum": ["attack", "use", "mine", "forward", "backward", "left", "right"],
            "description": "限时动作：attack=攻击，use=右键使用，mine=挖掘，forward=前进，backward=后退，left=向左，right=向右"
        },
        "duration": {
            "type": "number",
            "description": "持续时间（秒），到达时间后假人自动执行 stop"
        }
    },
    "required": ["name", "action", "duration"]
})
def bot_timed_action(source: CommandSource, ai_prefix: str, name: str, action: str, duration: float):
    server = source.get_server()

    move_actions = {
        "forward": "move forward",
        "backward": "move backward",
        "left": "move left",
        "right": "move right",
    }

    if action in move_actions:
        cmd = f"player {name} {move_actions[action]}"
    else:
        cmd = f"player {name} {action}"

    source.reply(f"{ai_prefix}假人 {name} 开始 {action}，将持续 {duration} 秒...")
    server.execute(cmd)
    time.sleep(duration)
    server.execute(f"player {name} stop")
    return f"假人 {name} 已完成 {duration} 秒的 {action}，已自动停止"

# ── 自定义指令 ────────────────────────────────────────────

@register_tool(description="向假人发送一条原始的自定义 /player 指令，用于上述工具无法覆盖的高级操作。请在了解 Carpet 假人指令的前提下使用。命令会自动补全为 'player <name> <command>' 格式。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        },
        "command": {
            "type": "string",
            "description": "要执行的 /player 子命令和参数（不含 player 和假人名），例如 'turn'、'dropStack'、'attack interval 5'"
        }
    },
    "required": ["name", "command"]
})
def bot_command(source: CommandSource, ai_prefix: str, name: str, command: str):
    server = source.get_server()
    full_cmd = f"player {name} {command}"
    source.reply(f"{ai_prefix}正在执行: /{full_cmd}")
    server.execute(full_cmd)
    return f"已对假人 {name} 执行: /{full_cmd}"