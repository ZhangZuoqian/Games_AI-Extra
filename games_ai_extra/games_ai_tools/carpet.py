import threading

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool, register_bot_tool


def _rcon_exec(server, command: str) -> str | None:
    """模块私有：RCON 优先执行一条控制台命令（普通命令专用）。

    契约（与调用方约定）：
    - 返回非空字符串 → RCON 通路成功，返回命令输出文本；
    - 返回 None → RCON 未连接或发送失败，本函数内部已调用 server.execute 执行完该命令，
      调用方禁止再次执行（防止同一条命令执行两遍）。
    仅 send_command 阶段的通信异常输出 warning 日志；未连接属正常情况，安静降级。
    """
    # RCON 未连接：安静降级执行（正常情况，不打日志）
    if not server.is_rcon_running():
        server.execute(command)
        return None
    # RCON 已连接，尝试发送指令；rcon_query 内部已捕获通信异常并重试，失败返回 None
    resp = server.rcon_query(command)
    if resp is None:
        # RCON 标记在线但通信失败，输出 warning 方便排查 RCON 网络问题
        server.logger.warning("[games_ai_extra] RCON命令发送失败, 回退至server.execute模式")
        server.execute(command)
        return None
    return resp

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
            "description": "可选。让假人在某个具体玩家旁边生成。[注意] 传入 player 时不得同时传入 pos 或 dim，即 player 与 pos、dim 均互斥。若要在玩家身边生成则只传 player，不传其他参数。"
        },
        "dim": {
            "type": "string",
            "description": "可选。目标维度 ID，如 minecraft:overworld、minecraft:the_nether、minecraft:the_end。指定后假人将在该维度生成。若同时指定 pos，则在维度的指定坐标生成；若不指定 pos，则在维度的 ~ ~ ~ 位置生成。[注意] 与 player 互斥，传入 player 时不要传入 dim。配合 pos 使用时需要确保坐标合法。"
        }
    },
    "required": ["name"]
})
@register_bot_tool()
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
            source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.spawning_bot_at_dim_pos", name=name, dim=dim, pos=pos)}')
            server.execute(f"{cmd_prefix}player {name} spawn at {pos[0]} {pos[1]} {pos[2]} facing 0 0 in {dim}")
            return f"假人 {name} 已在维度 {dim} 的坐标 {pos} 处生成"
        elif player:
            source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.spawning_bot_near_player", name=name, player=player)}')
            server.execute(f"execute as {player} at @s run player {name} spawn")
            return f"假人 {name} 已生成在 {player} 的位置"
        else:
            source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.spawning_bot_in_dim", name=name, dim=dim)}')
            server.execute(f"{cmd_prefix}player {name} spawn at ~ ~ ~ facing 0 0 in {dim}")
            return f"假人 {name} 已在维度 {dim} 的 ~ ~ ~ 位置生成"
    else:
        if pos and len(pos) == 3:
            source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.spawning_bot_at_pos", name=name, pos=pos)}')
            server.execute(f"{cmd_prefix}player {name} spawn at {pos[0]} {pos[1]} {pos[2]}")
            return f"假人 {name} 已在坐标 {pos} 处生成"
        elif player:
            source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.spawning_bot_near_player", name=name, player=player)}')
            server.execute(f"execute as {player} at @s run player {name} spawn")
            return f"假人 {name} 已生成在 {player} 的位置"
        else:
            if source.is_player:
                # 默认行为：不指定位置时，在召唤者（玩家）身边生成
                source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.spawning_bot_near_player", name=name, player=source.player)}')
                server.execute(f"execute as {source.player} at @s run player {name} spawn")
                return f"假人 {name} 已生成在 {source.player} 身边"
            # 控制台调用无召唤者：在世界出生点生成
            source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.spawning_bot", name=name)}')
            server.execute(f"player {name} spawn")
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
@register_bot_tool()
def kill_bot(source: CommandSource, ai_prefix: str, name: str):
    server = source.get_server()
    source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.killing_bot", name=name)}')
    server.execute(f"player {name} kill")
    return f"假人 {name} 已移除"

# 行为控制

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
    source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.bot_executing_action", name=name, action=action)}')
    cmd = f"player {name} {action}"
    if action in ("attack", "use", "mine"):
        cmd += f" interval {interval}"
    server.execute(cmd)
    return f"假人 {name} 正在执行 {action}（间隔={interval} tick）"

# 移动控制

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
    source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.bot_moving", name=name, direction=direction)}')
    server.execute(f"player {name} move {direction}")
    return f"假人 {name} 正在向 {direction} 移动。如需停止，请使用 stop 动作"

# 视角控制

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
    source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.bot_looking", name=name, target=target)}')
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

# 快捷栏

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
    source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.bot_switching_hotbar", name=name, slot=slot)}')
    server.execute(f"player {name} hotbar {slot}")
    return f"假人 {name} 的快捷栏已切换到第 {slot} 格"

# 限时动作

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

    source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.bot_timed_action", name=name, action=action, duration=duration)}')
    server.execute(cmd)
    # 用 threading.Timer 替代 time.sleep，避免阻塞 MCDR 主线程
    threading.Timer(duration, lambda: server.execute(f"player {name} stop")).start()
    return f"假人 {name} 已开始 {duration} 秒的 {action}，{duration} 秒后自动停止（不阻塞后续操作）"

# 自定义指令

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
    source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.executing_player_command", command=full_cmd)}')
    server.execute(full_cmd)
    return f"已对假人 {name} 执行: /{full_cmd}"


# 精准传送

@register_tool(description="将假人精准传送到指定坐标。与重新生成(spawn)不同，传送会保留假人的物品栏、血量、状态与朝向，不会重置假人。支持跨维度传送（可选 dim）。可选让假人传送后立即看向某个坐标（facing，适合传送后直接面对目标）。[精准说明] 若传入的 x/z 为整数（方块坐标），会自动 +0.5 对齐到方块中心，避免假人站在方块交界/角上；传入小数坐标则按精确位置传送。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        },
        "pos": {
            "type": "array",
            "items": {
                "type": "number"
            },
            "description": "目标坐标 [x, y, z]。x/z 为整数时会自动对齐方块中心（+0.5）；如需精确小数位置请传小数。y 为脚部高度坐标。"
        },
        "dim": {
            "type": "string",
            "description": "可选。目标维度 ID，如 minecraft:overworld、minecraft:the_nether、minecraft:the_end。不填则保持在当前维度传送"
        },
        "facing": {
            "type": "array",
            "items": {
                "type": "number"
            },
            "description": "可选。传送后看向的坐标 [x, y, z]"
        }
    },
    "required": ["name", "pos"]
})
@register_bot_tool()
def bot_teleport(source: CommandSource, ai_prefix: str, name: str, pos: list, dim: str | None = None, facing: list | None = None):
    if len(pos) != 3:
        return f"坐标格式应为 [x, y, z]，你传入的是 {pos}"
    if facing is not None and len(facing) != 3:
        return f"facing 格式应为 [x, y, z]，你传入的是 {facing}"
    server = source.get_server()
    # 坐标归一化：整数 x/z 自动 +0.5 对齐方块中心，避免假人站在方块交界/角上
    tx, ty, tz = (float(v) for v in pos)
    if tx.is_integer():
        tx += 0.5
    if tz.is_integer():
        tz += 0.5
    if dim:
        cmd = f"execute in {dim} run tp {name} {tx} {ty} {tz}"
    else:
        cmd = f"tp {name} {tx} {ty} {tz}"
    if facing is not None:
        cmd += f" facing {facing[0]} {facing[1]} {facing[2]}"
    source.reply(f"{ai_prefix}正在将假人 {name} 传送到 {tx}, {ty}, {tz}..." + (f"（维度 {dim}）" if dim else ""))
    # RCON 优先执行，能同步拿回 tp 输出（如 "Teleported X to ..."）；RCON 不可用自动降级 server.execute
    resp = _rcon_exec(server, cmd)
    if resp is not None and resp.strip():
        return f"假人 {name} 传送完成: {resp.strip()}"
    return f"假人 {name} 已传送到 {tx}, {ty}, {tz}" + (f"（维度 {dim}）" if dim else "") + (f"，朝向 {facing}" if facing is not None else "")


# 自动索敌攻击

@register_tool(description="让假人开启自动索敌攻击模式：自动扫描周围最近的敌对生物（怪物），转身看向它并持续攻击，直到目标死亡/消失后自动寻找下一个目标。可指定索敌半径和扫描间隔。注意：假人需手持武器才能造成伤害；使用 bot_stop_combat 可停止自动索敌。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        },
        "radius": {
            "type": "integer",
            "description": "可选。索敌半径（格），默认 16。半径越大扫描范围越广"
        },
        "interval": {
            "type": "integer",
            "description": "可选。扫描与攻击间隔（游戏刻，1 秒=20 刻），默认 10（0.5 秒）。调大更省性能，调小反应更快"
        }
    },
    "required": ["name"]
})
@register_bot_tool()
def bot_auto_combat(source: CommandSource, ai_prefix: str, name: str, radius: int = 16, interval: int = 10):
    server = source.get_server()
    if radius <= 0:
        return f"索敌半径必须为正数，你输入的是 {radius}"
    if interval <= 0:
        return f"扫描间隔必须为正数，你输入的是 {interval}"
    # 先卸载旧实例，再以新参数加载（避免重复启动多个循环）
    server.execute("script unload bot_combat")
    server.execute(f"script load bot_combat global {name} {radius} {interval}")
    source.reply(f"{ai_prefix}假人 {name} 已开启自动索敌攻击（半径 {radius} 格，间隔 {interval} 刻）。请确保假人手持武器。")
    return f"假人 {name} 已开启自动索敌攻击：自动检测半径 {radius} 格内最近的怪物并转向攻击。如需停止请调用 bot_stop_combat。"


@register_tool(description="停止假人的自动索敌攻击模式。关闭 bot_auto_combat 开启的自动索敌循环，并让假人停止当前动作。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        }
    },
    "required": ["name"]
})
@register_bot_tool()
def bot_stop_combat(source: CommandSource, ai_prefix: str, name: str):
    server = source.get_server()
    server.execute("script unload bot_combat")
    server.execute(f"player {name} stop")
    return f"假人 {name} 已停止自动索敌攻击"


@register_tool(description="让假人进入保护模式：假人自动跟随指定玩家，并攻击该玩家周围半径内的敌对生物，守护玩家安全。无怪物时假人保持在玩家身后跟随，有怪物时优先转向攻击怪物。可指定保护半径和扫描间隔。假人需手持武器才能造成伤害；使用 bot_stop_combat 可停止保护。", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "假人的名字"
        },
        "player": {
            "type": "string",
            "description": "要保护的玩家名"
        },
        "radius": {
            "type": "integer",
            "description": "可选。保护/索敌半径（格），默认 8。以被保护玩家为中心"
        },
        "interval": {
            "type": "integer",
            "description": "可选。扫描与攻击间隔（游戏刻，1 秒=20 刻），默认 10（0.5 秒）"
        }
    },
    "required": ["name", "player"]
})
@register_bot_tool()
def bot_protect_player(source: CommandSource, ai_prefix: str, name: str, player: str, radius: int = 8, interval: int = 10):
    server = source.get_server()
    if radius <= 0:
        return f"保护半径必须为正数，你输入的是 {radius}"
    if interval <= 0:
        return f"扫描间隔必须为正数，你输入的是 {interval}"
    # 先卸载旧实例，再以保护模式加载（避免重复启动多个循环）
    server.execute("script unload bot_combat")
    server.execute(f"script load bot_combat global protect {name} {player} {radius} {interval}")
    source.reply(f"{ai_prefix}假人 {name} 已开启保护模式，守护 {player}（半径 {radius} 格，间隔 {interval} 刻）。请确保假人手持武器。")
    return f"假人 {name} 已开启保护模式：跟随 {player} 并自动攻击其周围 {radius} 格内的怪物。如需停止请调用 bot_stop_combat。"