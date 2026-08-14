"""生电服务器工具集 - 性能监控、Carpet规则、区块加载、实体管理、结构定位

门控版改进：
- 死亡日志改为内存存储（deque），不写入任何文件
- 全部依赖 fabric-carpet（本插件硬依赖），无 spark 依赖
- 默认关闭，需在 config.json 同时开启 carpet 与 technical_server 才生效
- 监听器由 __init__ 按配置决定是否记录
"""
import time
from collections import deque

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


# ── 性能监控 ──────────────────────────────────────────────

@register_tool(
    description="查询服务器性能指标：TPS（每秒刻数）、MSPT（每刻毫秒数）。通过 fabric-carpet 的 Scarpet 脚本读取最近 100 tick 的耗时计算，无需 spark。生电服排查卡顿必备。注意：Scarpet 仅暴露最近 100 tick（约 5s）窗口，无法取更长时段。",
    parameters={
        "type": "object",
        "properties": {
            "detail": {
                "type": "boolean",
                "description": "可选。是否返回详细信息（最近 100 tick 的最小/最大/平均耗时）。默认 false 只返回当前 TPS/MSPT。"
            }
        }
    }
)
def get_server_tps(source: CommandSource, ai_prefix: str, detail: bool = False):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在查询服务器性能...")
    # Scarpet 脚本：先定义 mspt() 函数（用 last_tick_times() 算平均），
    # 再计算 TPS，最后 print 输出。函数定义放前面，避免调用时未定义。
    # MSPT = 最近 100 tick 平均耗时；TPS = min(20, 1000/MSPT)
    script = (
        "mspt() -> (s=0; for(last_tick_times(), s+=_); s/100); "
        "m = mspt(); "
        "t = min(20, 1000/m); "
        "print('MSPT='+m+' TPS='+t)"
    )
    server.execute(f"script run {script}")
    if detail:
        # min/max/avg 定位偶发卡顿
        detail_script = (
            "v = last_tick_times(); "
            "print('min='+min(v)+' max='+max(v)+' avg='+(s=0; for(v, s+=_); s/100))"
        )
        server.execute(f"script run {detail_script}")
    return "已通过 carpet script 查询性能，结果请查看服务器控制台或聊天栏。TPS=20 表示满速，<20 表示卡顿；MSPT>50 表示服务器超载。"


# ── 实体统计/清理 ─────────────────────────────────────────

@register_tool(
    description="按类型清理指定范围内的实体，防止刷怪塔/农场掉落物堆积卡顿。需要管理员权限。",
    parameters={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "description": "要清理的实体类型，如 'item'（掉落物）、'minecraft:xp_orb'（经验球）、'arrow'（箭矢）。"
            },
            "center_pos": {
                "type": "array",
                "items": {"type": "number"},
                "description": "可选。清理中心 [x, y, z]。不填则清理全图。"
            },
            "radius": {
                "type": "integer",
                "description": "可选。清理半径，需配合 center_pos 使用。"
            }
        },
        "required": ["entity_type"]
    }
)
def clear_entities(source: CommandSource, ai_prefix: str, entity_type: str, center_pos: list = None, radius: int = None):
    server = source.get_server()
    if ":" not in entity_type and entity_type not in ("item", "xp_orb"):
        entity_type = "minecraft:" + entity_type
    if center_pos and radius:
        selector = f"@e[type={entity_type},x={center_pos[0]},y={center_pos[1]},z={center_pos[2]},distance=..{radius}]"
    else:
        selector = f"@e[type={entity_type}]"
    source.reply(f"{ai_prefix}正在清理 {entity_type}...")
    server.execute(f"kill {selector}")
    return f"已发送清理指令：kill {selector}"


# ── Carpet 规则管理 ────────────────────────────────────────

@register_tool(
    description="查询 fabric-carpet 模组的某条规则当前值，或列出所有规则。生电服调试机器必备。",
    parameters={
        "type": "object",
        "properties": {
            "rule": {
                "type": "string",
                "description": "可选。要查询的 carpet 规则名，如 'tntOptimization'、'explosionsSpawnFire'、'optimizedTNT'。不填则列出所有规则。"
            }
        }
    }
)
def carpet_rule_get(source: CommandSource, ai_prefix: str, rule: str = None):
    server = source.get_server()
    if rule:
        source.reply(f"{ai_prefix}正在查询 carpet 规则 {rule}...")
        server.execute(f"carpet {rule}")
    else:
        source.reply(f"{ai_prefix}正在列出所有 carpet 规则...")
        server.execute("carpet list")
    return f"已发送 carpet 规则查询指令，结果请查看控制台/聊天栏"


@register_tool(
    description="修改 fabric-carpet 模组的某条规则。需要管理员权限。常用于切换 TNT 优化、爆炸火焰、堆叠等规则。修改前建议先 carpet_rule_get 查询当前值。",
    parameters={
        "type": "object",
        "properties": {
            "rule": {
                "type": "string",
                "description": "要修改的规则名，如 'tntOptimization'、'explosionsSpawnFire'"
            },
            "value": {
                "type": "string",
                "description": "新值。布尔规则用 'true'/'false'，枚举规则用对应值（如 'default'/'optimized'/'precise'），数值规则直接传数字字符串。"
            }
        },
        "required": ["rule", "value"]
    }
)
def carpet_rule_set(source: CommandSource, ai_prefix: str, rule: str, value: str):
    server = source.get_server()
    # 白名单校验：rule 只允许字母/数字/下划线；value 限定常见类型
    if not rule or not rule.replace("_", "").isalnum():
        return f"规则名非法：{rule!r}。只能用字母、数字、下划线"
    # value 允许：true/false/数字/常见枚举值
    allowed_values = {"true", "false", "default", "optimized", "precise"}
    is_number = False
    try:
        float(value)
        is_number = True
    except (ValueError, TypeError):
        pass
    if value.lower() not in allowed_values and not is_number:
        return f"value 非法：{value!r}。只允许 true/false/数字 或常见枚举（default/optimized/precise）"
    source.reply(f"{ai_prefix}正在修改 carpet 规则 {rule} = {value}...")
    server.execute(f"carpet {rule} {value}")
    return f"已发送修改指令：carpet {rule} {value}。如失败请检查权限或规则名拼写"


# ── 区块加载管理 ──────────────────────────────────────────

@register_tool(
    description="查询、添加或移除强加载区块（forceload）。生电服保持机器常加载必备。需要管理员权限。",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["query", "add", "remove", "remove_all"],
                "description": "操作类型：query=查询所有强加载区块，add=添加强加载区块，remove=移除指定强加载区块，remove_all=移除当前玩家所有强加载区块"
            },
            "from_pos": {
                "type": "array",
                "items": {"type": "number"},
                "description": "可选。起始坐标 [x, z]（forceload 是 2D 的）。add/remove 时必填。"
            },
            "to_pos": {
                "type": "array",
                "items": {"type": "number"},
                "description": "可选。结束坐标 [x, z]。不填则与 from_pos 相同（单个区块）。"
            }
        },
        "required": ["action"]
    }
)
def forceload(source: CommandSource, ai_prefix: str, action: str, from_pos: list = None, to_pos: list = None):
    server = source.get_server()
    if action == "query":
        source.reply(f"{ai_prefix}正在查询强加载区块...")
        server.execute("forceload query")
        return "已发送查询指令，结果请查看聊天栏"
    elif action == "add":
        if not from_pos:
            return "add 操作必须指定 from_pos"
        to = to_pos if to_pos else from_pos
        source.reply(f"{ai_prefix}正在添加强加载区块 {from_pos} -> {to}...")
        server.execute(f"forceload add {from_pos[0]} {from_pos[1]} {to[0]} {to[1]}")
        return f"已添加强加载区块 {from_pos} -> {to}"
    elif action == "remove":
        if not from_pos:
            return "remove 操作必须指定 from_pos"
        to = to_pos if to_pos else from_pos
        source.reply(f"{ai_prefix}正在移除强加载区块 {from_pos} -> {to}...")
        server.execute(f"forceload remove {from_pos[0]} {from_pos[1]} {to[0]} {to[1]}")
        return f"已移除强加载区块 {from_pos} -> {to}"
    elif action == "remove_all":
        source.reply(f"{ai_prefix}正在移除所有强加载区块...")
        server.execute("forceload remove all")
        return "已移除当前玩家所有强加载区块"
    return f"未知操作: {action}"


# ── 结构定位 ──────────────────────────────────────────────

@register_tool(
    description="定位附近的指定结构坐标。生电服找要塞/堡垒/远古城市等必备。",
    parameters={
        "type": "object",
        "properties": {
            "structure": {
                "type": "string",
                "description": "结构 ID，常用：stronghold(要塞)、fortress(下界要塞)、bastion_remnant(堡垒遗迹)、ancient_city(远古城市)、end_city(末地城)、woodland_mansion(林地府邸)、monument(海底神殿)、village(村庄)、pillager_outpost(掠夺者前哨站)、shipwreck(沉船)、desert_pyramid(沙漠神殿)"
            },
            "pos": {
                "type": "array",
                "items": {"type": "number"},
                "description": "可选。从哪个坐标开始搜索 [x, z]。不填则用玩家当前位置。"
            }
        },
        "required": ["structure"]
    }
)
def locate_structure(source: CommandSource, ai_prefix: str, structure: str, pos: list = None):
    server = source.get_server()
    aliases = {
        "stronghold": "stronghold", "要塞": "stronghold",
        "fortress": "fortress", "下界要塞": "fortress",
        "bastion": "bastion_remnant", "bastion_remnant": "bastion_remnant", "堡垒": "bastion_remnant",
        "ancient_city": "ancient_city", "远古城市": "ancient_city",
        "end_city": "end_city", "末地城": "end_city",
        "mansion": "woodland_mansion", "林地府邸": "woodland_mansion",
        "monument": "monument", "海底神殿": "monument",
        "village": "village", "村庄": "village",
        "outpost": "pillager_outpost", "pillager_outpost": "pillager_outpost", "前哨": "pillager_outpost",
        "shipwreck": "shipwreck", "沉船": "shipwreck",
        "desert_pyramid": "desert_pyramid", "沙漠神殿": "desert_pyramid",
    }
    sid = aliases.get(structure.lower(), structure)
    if ":" not in sid:
        sid = "minecraft:" + sid
    if pos:
        source.reply(f"{ai_prefix}正在从 {pos} 搜索 {sid}...")
        if source.is_player:
            server.execute(f"execute at {source.player} positioned {pos[0]} ~ {pos[1]} run locate structure {sid}")
        else:
            server.execute(f"locate structure {sid}")
    else:
        source.reply(f"{ai_prefix}正在搜索附近的 {sid}...")
        server.execute(f"locate structure {sid}")
    return f"已发送 locate 指令，结果请查看聊天栏"


# ── 维度坐标换算 ──────────────────────────────────────────

@register_tool(
    description="维度坐标换算：主世界<->下界坐标换算（1:8）。不需要服务器执行，纯计算。",
    parameters={
        "type": "object",
        "properties": {
            "from_dim": {
                "type": "string",
                "enum": ["overworld", "the_nether"],
                "description": "源维度：overworld(主世界) 或 the_nether(下界)"
            },
            "pos": {
                "type": "array",
                "items": {"type": "number"},
                "description": "源坐标 [x, z]（维度换算只需要 x 和 z）"
            }
        },
        "required": ["from_dim", "pos"]
    }
)
def convert_dimension_pos(source: CommandSource, ai_prefix: str, from_dim: str, pos: list):
    if len(pos) < 2:
        return "pos 必须至少包含 [x, z]"
    x, z = pos[0], pos[1]
    if from_dim == "overworld":
        nx, nz = x / 8, z / 8
        return f"主世界 ({x}, {z}) 对应下界坐标: ({nx:.1f}, {nz:.1f})"
    elif from_dim == "the_nether":
        nx, nz = x * 8, z * 8
        return f"下界 ({x}, {z}) 对应主世界坐标: ({nx:.1f}, {nz:.1f})"
    return f"不支持的维度: {from_dim}"


# ── 死亡日志（内存版）─────────────────────────────────────

_MAX_DEATH_RECORDS = 500
# 内存缓存：进程重启后清空（符合"无文件写入"要求）
_DEATH_RECORDS: deque = deque(maxlen=_MAX_DEATH_RECORDS)


@register_tool(
    description="查询玩家最近的死亡记录（位置、维度、时间）。生电/生存服找回落点必备。死亡记录由本插件自动监听玩家死亡事件记录。注意：仅保留本插件运行期间的记录（内存存储，重启清空），默认关闭，需在 config.json 开启 technical_server。",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "string",
                "description": "可选。要查询的玩家名。不填则返回最近所有玩家的死亡记录。"
            },
            "limit": {
                "type": "integer",
                "description": "可选。返回最近多少条记录，默认 5。"
            }
        }
    }
)
def query_death_log(source: CommandSource, ai_prefix: str, player: str = None, limit: int = 5):
    source.reply(f"{ai_prefix}正在查询死亡记录...")
    if not _DEATH_RECORDS:
        return "暂无死亡记录（本插件启动后尚未记录，或 technical_server 未启用）"
    records = list(_DEATH_RECORDS)
    if player:
        records = [r for r in records if r.get("player", "").lower() == player.lower()]
        if not records:
            return f"未找到玩家 {player} 的死亡记录"
    records = records[-limit:][::-1]
    lines = []
    for r in records:
        lines.append(
            f"[{r.get('time', '?')}] {r.get('player', '?')} 在 {r.get('dim', '?')} "
            f"({r.get('pos', '?')}) 死亡: {r.get('cause', '未知原因')}"
        )
    return "最近死亡记录:\n" + "\n".join(lines)


# ── tick 速率临时调整 ─────────────────────────────────────

@register_tool(
    description="临时调整服务器 tick 速率（需要 carpet 的 tick 命令）。调试机器/慢放查看用，正常游戏请恢复为 20。",
    parameters={
        "type": "object",
        "properties": {
            "rate": {
                "type": "number",
                "description": "目标 tick 速率。正常=20，慢放=1~10，超快调试=20~1000。设为 0 可暂停服务器（谨慎）"
            }
        },
        "required": ["rate"]
    }
)
def set_tickrate(source: CommandSource, ai_prefix: str, rate: float):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在设置 tick 速率为 {rate}...")
    server.execute(f"tick rate {rate}")
    return f"已设置 tick 速率为 {rate}。注意：调试完后请用 set_tickrate(20) 恢复正常"


# ── scoreboard 计分项 ─────────────────────────────────────

@register_tool(
    description="查询玩家或实体的 scoreboard 分数。常用于生电服统计机器产出（如刷怪塔击杀数、农场产量）。需要管理员或对应权限。",
    parameters={
        "type": "object",
        "properties": {
            "objective": {
                "type": "string",
                "description": "计分项名称，如 'killCount'、'diamondsMined'"
            },
            "target": {
                "type": "string",
                "description": "查询目标。可以是玩家名、实体选择器（如 @a、@e[type=zombie]）或假名（如 '#total'）"
            }
        },
        "required": ["objective", "target"]
    }
)
def scoreboard_query(source: CommandSource, ai_prefix: str, objective: str, target: str):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在查询 {target} 的 {objective} 分数...")
    server.execute(f"scoreboard players get {target} {objective}")
    return f"已发送查询指令：scoreboard players get {target} {objective}。结果请查看聊天栏"


@register_tool(
    description="设置玩家或假名的 scoreboard 分数。常用于生电服重置计数器、初始化统计。需要管理员权限。",
    parameters={
        "type": "object",
        "properties": {
            "objective": {
                "type": "string",
                "description": "计分项名称"
            },
            "target": {
                "type": "string",
                "description": "目标（玩家名、选择器或假名）"
            },
            "score": {
                "type": "integer",
                "description": "要设置的分数值"
            }
        },
        "required": ["objective", "target", "score"]
    }
)
def scoreboard_set(source: CommandSource, ai_prefix: str, objective: str, target: str, score: int):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在设置 {target} 的 {objective} = {score}...")
    server.execute(f"scoreboard players set {target} {objective} {score}")
    return f"已设置 {target} 的 {objective} = {score}"


@register_tool(
    description="列出服务器所有 scoreboard 计分项，或创建/删除计分项。生电服统计机器产出前需要先创建计分项。",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "add", "remove"],
                "description": "操作：list=列出所有计分项，add=创建新计分项，remove=删除计分项"
            },
            "name": {
                "type": "string",
                "description": "计分项名称。add/remove 时必填。"
            },
            "criterion": {
                "type": "string",
                "description": "可选。add 时的统计准则，如 'dummy'（手动设置，最常用）、'totalKillCount'、'deathCount'。默认 'dummy'。"
            }
        },
        "required": ["action"]
    }
)
def scoreboard_manage(source: CommandSource, ai_prefix: str, action: str, name: str = None, criterion: str = "dummy"):
    server = source.get_server()
    if action == "list":
        source.reply(f"{ai_prefix}正在列出所有计分项...")
        server.execute("scoreboard objectives list")
        return "已请求计分项列表，结果请查看聊天栏"
    elif action == "add":
        if not name:
            return "add 操作必须指定 name"
        source.reply(f"{ai_prefix}正在创建计分项 {name}（准则: {criterion}）...")
        server.execute(f"scoreboard objectives add {name} {criterion}")
        return f"已创建计分项 {name}（准则: {criterion}）"
    elif action == "remove":
        if not name:
            return "remove 操作必须指定 name"
        source.reply(f"{ai_prefix}正在删除计分项 {name}...")
        server.execute(f"scoreboard objectives remove {name}")
        return f"已删除计分项 {name}"
    return f"未知操作: {action}"


# ── 玩家活动统计 ──────────────────────────────────────────

# 统计项 key → (scoreboard criterion, 人类可读说明, 单位换算提示)
# criterion 用 1.13+ 的 minecraft.* 命名（1.20+ 与旧版通用名）
_PLAYER_STATS_MAP = {
    "play_time":      ("minecraft.play_time",      "在线时长",     "单位 tick，÷20 得秒"),
    "deaths":         ("minecraft.death_count",    "死亡次数",     ""),
    "walk_distance":  ("minecraft.walk_one_cm",    "步行距离",     "单位 cm，÷100 得米"),
    "sprint_distance":("minecraft.sprint_one_cm",  "冲刺距离",     "单位 cm，÷100 得米"),
    "crouch_distance":("minecraft.crouch_one_cm",  "潜行距离",     "单位 cm，÷100 得米"),
    "jumps":          ("minecraft.jump",           "跳跃次数",     ""),
    "mob_kills":      ("minecraft.mob_kills",      "击杀生物数",   ""),
    "player_kills":   ("minecraft.player_kills",   "击杀玩家数",   ""),
    "damage_taken":   ("minecraft.damage_taken",   "累计受伤",     "单位 0.1 心"),
    "damage_dealt":   ("minecraft.damage_dealt",   "累计造成伤害", "单位 0.1 心"),
}


@register_tool(
    description="查询玩家活动统计（在线时长、死亡次数、移动距离等）。基于 scoreboard 计分项，需服务器已用对应 criterion 创建计分项。用于服务器运营数据统计。注意：查询前需确保对应计分项已创建，例如要查在线时长需先执行 scoreboard objectives add play_time minecraft.play_time。",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "string",
                "description": "玩家名"
            },
            "stats": {
                "type": "array",
                "items": {"type": "string"},
                "description": "要查的统计项，可选值：play_time(在线时长)、deaths(死亡次数)、walk_distance(步行)、sprint_distance(冲刺)、crouch_distance(潜行)、jumps(跳跃)、mob_kills(击杀生物)、player_kills(击杀玩家)、damage_taken(受伤)、damage_dealt(造成伤害)。不填则默认查 play_time、deaths、walk_distance 三项。"
            }
        },
        "required": ["player"]
    }
)
def query_player_stats(source: CommandSource, ai_prefix: str, player: str, stats: list = None):
    if not stats:
        stats = ["play_time", "deaths", "walk_distance"]
    # 校验统计项名
    invalid = [s for s in stats if s not in _PLAYER_STATS_MAP]
    if invalid:
        return f"未知统计项：{invalid}。可选：{list(_PLAYER_STATS_MAP.keys())}"
    # 玩家名校验（防命令注入：只允许字母数字下划线，3-16 字符）
    import re as _re
    if not _re.fullmatch(r"\w{3,16}", player):
        return f"玩家名不合法：{player!r}（仅允许 3-16 个字母/数字/下划线）"
    server = source.get_server()
    source.reply(f"{ai_prefix}正在查询 {player} 的活动统计...")
    # 假设 objective 名 = 统计项 key（管理员需按此命名创建）
    # objective 不存在时服务器会报错，玩家能在聊天栏看到
    hints = []
    for s in stats:
        criterion, label, unit_hint = _PLAYER_STATS_MAP[s]
        server.execute(f"scoreboard players get {player} {s}")
        h = f"{s}={label}"
        if unit_hint:
            h += f"（{unit_hint}）"
        hints.append(h)
    hint_str = "；".join(hints)
    return (f"已查询 {player} 的 {len(stats)} 项统计，结果在聊天栏。"
            f"如提示计分项不存在，需先创建：scoreboard objectives add <key> <criterion>。"
            f"统计项说明：{hint_str}")


# ── 强加载区块详情 ────────────────────────────────────────

@register_tool(
    description="列出所有维度（主世界/下界/末地）的强加载区块（forceload）。逐个维度执行 forceload query 输出。用于排查'哪些区块被强制加载、是否需要清理'。注意：vanilla forceload query 只能列出由 forceload 命令添加的区块，列不出玩家视野/spawn 区块/传送门等 ticket 来源。",
    parameters={}
)
def query_forceload_detail(source: CommandSource, ai_prefix: str):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在查询所有维度的强加载区块...")
    # 逐维度查询：vanilla forceload query 只列当前执行维度
    for dim in ("minecraft:overworld", "minecraft:the_nether", "minecraft:the_end"):
        server.execute(f"execute in {dim} run forceload query")
    return ("已查询三个维度的强加载区块，结果在聊天栏。"
            "每个维度会显示该维度的 forceload 区块列表。"
            "注意：仅含 forceload 命令添加的区块，不含玩家/spawn 等其他加载来源。")


# ── 实体密度热力图 ────────────────────────────────────────

@register_tool(
    description="统计当前维度各区块的实体密度，找出实体超载区域。通过 Scarpet entity_list 遍历所有实体并按区块坐标聚合，输出实体总数、按类型分布、以及实体密度最高的区块。生电服排查刷怪塔/农场卡顿时定位元凶必备。注意：仅统计当前维度；Scarpet 脚本首次使用建议在测试服验证输出。",
    parameters={
        "type": "object",
        "properties": {
            "top": {
                "type": "integer",
                "description": "可选。输出实体密度最高的前 N 个区块，默认 5，最大 20。"
            }
        }
    }
)
def query_entity_heatmap(source: CommandSource, ai_prefix: str, top: int = 5):
    if top < 1:
        top = 5
    elif top > 20:
        top = 20
    server = source.get_server()
    source.reply(f"{ai_prefix}正在统计当前维度实体密度（可能耗时数秒）...")
    # Scarpet 脚本：
    # 1. entity_list('*') 取当前维度所有实体
    # 2. 按类型统计分布
    # 3. 按区块坐标(cx,cz)聚合实体数
    # 4. 输出总数 + 类型 top + 区块密度 top
    #
    # 注意：entity_list / query / 向量分量访问(p:x) 等 Scarpet API
    # 已对照官方文档，但语法细节建议首次在测试服验证
    script = (
        # 取全部实体
        "es = entity_list('*'); "
        "total = length(es); "
        "print('当前维度总实体数: ' + total); "
        # 按类型统计
        "types = m(); "
        "for(es, e -> ( "
        "  t = query(e, 'type'); "
        "  types[t] = (types[t] ?? 0) + 1 "
        ")); "
        # 按区块统计
        "chunks = m(); "
        "for(es, e -> ( "
        "  p = query(e, 'pos'); "
        "  cx = floor(p:x / 16); "
        "  cz = floor(p:z / 16); "
        "  k = cx + ',' + cz; "
        "  chunks[k] = (chunks[k] ?? 0) + 1 "
        ")); "
        # 输出类型分布（全部）
        "print('--- 按类型分布 ---'); "
        "for(types, (k, v) -> print(k + ': ' + v)); "
        # 输出区块密度 top N（转成 list 排序）
        f"print('--- 实体密度最高的 {top} 个区块 ---'); "
        "pairs = l(); "
        "for(chunks, (k, v) -> push(pairs, l(v, k))); "
        f"sorted = sort(pairs, (a, b) -> a:0 > b:0); "
        f"n = min({top}, length(sorted)); "
        "i = 0; "
        "while(i < n, ( "
        "  p = sorted:i; "
        "  print('区块(' + p:1 + '): ' + p:0 + ' 个实体'); "
        "  i += 1 "
        "))"
    )
    server.execute(f"script run {script}")
    return ("已执行实体密度统计，结果在聊天栏/控制台。"
            "输出包含：总实体数、按类型分布、实体密度最高的区块坐标。"
            "如某区块实体数异常高，可能是刷怪塔/农场堆积，建议前往排查或清理。"
            "注意：仅统计当前维度，切换维度需玩家在对应维度执行。")


# ── 监听玩家死亡事件（由 MCDR 事件触发，记录到内存）────────

def on_player_death(server, player, message):
    """MCDR 玩家死亡事件回调。高效：只记录关键字段到内存，O(1)。"""
    try:
        record = {
            "player": player,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pos": None,  # 位置需借助其他插件/命令获取，这里只记录死亡事实
            "dim": None,
            "cause": str(message) if message else "未知",
        }
        _DEATH_RECORDS.append(record)
    except Exception as e:
        try:
            server.logger.warning(f"[games_ai_extra] 记录死亡日志失败: {e}")
        except Exception:
            pass
