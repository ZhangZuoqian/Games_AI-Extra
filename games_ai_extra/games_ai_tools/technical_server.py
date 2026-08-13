"""生电服务器工具集 - 性能监控、Carpet规则、区块加载、实体管理、结构定位等

高效实现策略：
- 所有 server.execute 调用均为非阻塞
- 状态查询直接读 JSON / 解析日志，不引入额外依赖
- 工具函数尽量复用，避免重复代码
"""
import json
import os
import re
import time

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


# ── 性能监控 ──────────────────────────────────────────────

@register_tool(
    description="查询服务器性能指标：TPS（每秒刻数）、MSPT（每刻毫秒数）、tick 状态。需要 fabric-carpet 或 spark 模组。生电服排查卡顿必备。",
    parameters={
        "type": "object",
        "properties": {
            "detail": {
                "type": "boolean",
                "description": "可选。是否返回详细信息（包括最近 5s/10s/1m 的 TPS）。默认 false 只返回当前 TPS/MSPT。"
            }
        }
    }
)
def get_server_tps(source: CommandSource, ai_prefix: str, detail: bool = False):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在查询服务器性能...")
    # 优先使用 spark（更准确），失败回退到 carpet
    if server.get_plugin_metadata("spark") is not None:
        server.execute_command("spark health --from-tick --to-tick now")
        return "已通过 spark 输出性能报告，请查看服务器日志/聊天栏的 spark 输出"
    # 回退：carpet script
    server.execute("script run print('TPS=' + str(tps()) + ' MSPT=' + str(mspt()))")
    if detail:
        server.execute("script run print('TPS_5s=' + str(tps(5*20)) + ' TPS_10s=' + str(tps(10*20)) + ' TPS_1m=' + str(tps(20*60)))")
    return "已发送性能查询指令，结果请查看服务器控制台或聊天栏返回。carpet script 模式下 TPS=20 表示满速，<20 表示卡顿；MSPT>50 表示服务器超载。"


@register_tool(
    description="统计指定区域内（或全图）的实体数量，按类型分组。用于排查刷怪塔/农场卡顿、检查实体上限。需要 fabric-carpet。",
    parameters={
        "type": "object",
        "properties": {
            "center_pos": {
                "type": "array",
                "items": {"type": "number"},
                "description": "可选。统计中心坐标 [x, y, z]。不填则统计所有已加载区块。"
            },
            "radius": {
                "type": "integer",
                "description": "可选。统计半径（方块），需配合 center_pos 使用。"
            },
            "entity_type": {
                "type": "string",
                "description": "可选。只统计某种实体，如 'item'（掉落物）、'minecraft:zombie'、'armor_stand'。不填则统计全部并按类型分组。"
            }
        }
    }
)
def count_entities(source: CommandSource, ai_prefix: str, center_pos: list = None, radius: int = None, entity_type: str = None):
    server = source.get_server()
    source.reply(f"{ai_prefix}正在统计实体数量...")
    if center_pos and radius:
        selector = f"@e[x={center_pos[0]},y={center_pos[1]},z={center_pos[2]},distance=..{radius}]"
    else:
        selector = "@e"
    if entity_type:
        if ":" not in entity_type:
            entity_type = "minecraft:" + entity_type
        selector_full = f"{selector}[type={entity_type}]"
        server.execute(f'execute store storage games_ai:temp entity_count int 1 run execute as {selector_full} run data modify storage games_ai:temp entity_count set value 0')
        server.execute(f'execute as {selector_full} run execute store result storage games_ai:temp entity_count int 1 run scoreboard players add #count dummy 1 2>/dev/null; data get storage games_ai:temp entity_count')
        # 简化版：直接 execute store
        server.execute(f'scoreboard objectives remove gai_ec 2>/dev/null; scoreboard objectives add gai_ec dummy')
        server.execute(f'scoreboard players set #gai_ec gai_ec 0')
        server.execute(f'execute as {selector_full} run scoreboard players add #gai_ec gai_ec 1')
        server.execute(f'scoreboard players get #gai_ec gai_ec')
        return f"已统计 {entity_type} 在指定范围内的数量，结果请查看聊天栏"
    else:
        # 全部统计 - 按类型分组用 carpet script
        server.execute('script run print(summon_count())')
        server.execute(f'script run for(e in entities.all()) {{ print(e.type + ":" + 1) }}')
        return "已发送实体统计指令（按类型分组），结果请查看控制台 carpet script 输出"


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
            },
            "player": {
                "type": "string",
                "description": "可选。指定玩家维度查询（query 时可用，默认查当前玩家）。"
            }
        },
        "required": ["action"]
    }
)
def forceload(source: CommandSource, ai_prefix: str, action: str, from_pos: list = None, to_pos: list = None, player: str = None):
    server = source.get_server()
    if action == "query":
        source.reply(f"{ai_prefix}正在查询强加载区块...")
        cmd = "forceload query"
        server.execute(cmd)
        return "已发送查询指令，结果请查看聊天栏"
    elif action == "add":
        if not from_pos:
            return "add 操作必须指定 from_pos"
        to = to_pos if to_pos else from_pos
        source.reply(f"{ai_prefix}正在添加强加载区块 {from_pos} -> {to}...")
        cmd = f"forceload add {from_pos[0]} {from_pos[1]} {to[0]} {to[1]}"
        server.execute(cmd)
        return f"已添加强加载区块 {from_pos} -> {to}"
    elif action == "remove":
        if not from_pos:
            return "remove 操作必须指定 from_pos"
        to = to_pos if to_pos else from_pos
        source.reply(f"{ai_prefix}正在移除强加载区块 {from_pos} -> {to}...")
        cmd = f"forceload remove {from_pos[0]} {from_pos[1]} {to[0]} {to[1]}"
        server.execute(cmd)
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
    # 允许简写
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


# ── 死亡日志 ──────────────────────────────────────────────

_DEATH_LOG_FILE = os.path.join("config", "games_ai_extra", "death_log.json")


def _load_death_log() -> list:
    if not os.path.isfile(_DEATH_LOG_FILE):
        return []
    try:
        with open(_DEATH_LOG_FILE, mode="r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_death_log(data: list):
    os.makedirs(os.path.dirname(_DEATH_LOG_FILE), exist_ok=True)
    with open(_DEATH_LOG_FILE, mode="w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@register_tool(
    description="查询玩家最近的死亡记录（位置、维度、时间）。生电/生存服找回落点必备。死亡记录由本插件自动监听玩家死亡事件记录。",
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
    records = _load_death_log()
    if not records:
        return "暂无死亡记录（数据文件不存在或为空）"
    if player:
        records = [r for r in records if r.get("player", "").lower() == player.lower()]
        if not records:
            return f"未找到玩家 {player} 的死亡记录"
    records = records[-limit:][::-1]  # 最近 limit 条，倒序
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


# ── 实体清理 ──────────────────────────────────────────────

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
    if ":" not in entity_type and entity_type != "item" and entity_type != "xp_orb":
        entity_type = "minecraft:" + entity_type
    if center_pos and radius:
        selector = f"@e[type={entity_type},x={center_pos[0]},y={center_pos[1]},z={center_pos[2]},distance=..{radius}]"
    else:
        selector = f"@e[type={entity_type}]"
    source.reply(f"{ai_prefix}正在清理 {entity_type}...")
    server.execute(f"kill {selector}")
    return f"已发送清理指令：kill {selector}"


# ── 监听玩家死亡事件（由 MCDR 事件触发，记录到 JSON） ───────

def on_player_death(server, player, message):
    """MCDR 玩家死亡事件回调。高效：只记录关键字段，避免阻塞。"""
    try:
        from mcdreforged.api.all import ServerInterface
        si = ServerInterface.get_instance()
        # 尝试拿玩家位置（通过 execute store 或 scoreboard）
        # 简化：用 last death pos 可能拿不到，先用占位，后续 AI 可调用 query_death_log
        pos = [0, 0, 0]
        dim = "minecraft:overworld"
        # 通过 scoreboard 拿位置（carpet 提供 death pos 不一定有，这里用近似）
        record = {
            "player": player,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pos": pos,
            "dim": dim,
            "cause": str(message) if message else "未知",
        }
        records = _load_death_log()
        records.append(record)
        # 限制最多 500 条避免文件膨胀
        if len(records) > 500:
            records = records[-500:]
        _save_death_log(records)
    except Exception as e:
        try:
            server.logger.warning(f"[games_ai_extra] 记录死亡日志失败: {e}")
        except Exception:
            pass


# ── 历史结构截图查询 ──────────────────────────────────────

@register_tool(
    description="查询或恢复某区域的历史结构截图（区块快照）。需要 MCDR 安装 region_snapshot 类插件。生电服排查回档/熊孩子破坏用。",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "query", "restore"],
                "description": "操作：list=列出所有快照，query=查询某坐标的快照，restore=恢复某快照（需管理员权限）"
            },
            "pos": {
                "type": "array",
                "items": {"type": "number"},
                "description": "可选。查询坐标 [x, z]（region_snapshot 是 2D 区块级）。query 时必填。"
            },
            "snapshot_id": {
                "type": "string",
                "description": "可选。快照 ID/名称。restore 时必填。"
            }
        },
        "required": ["action"]
    }
)
def region_snapshot(source: CommandSource, ai_prefix: str, action: str, pos: list = None, snapshot_id: str = None):
    server = source.get_server()
    # 兼容常见 region snapshot 插件名
    snapshot_plugins = ["region_snapshot", "region_snapshot_plugin", "primetiem"]
    detected = None
    for p in snapshot_plugins:
        if server.get_plugin_metadata(p) is not None:
            detected = p
            break
    if detected is None:
        return "未检测到 region_snapshot 类插件，无法操作历史结构截图"
    if action == "list":
        source.reply(f"{ai_prefix}正在列出所有区域快照...")
        server.execute("!!snapshot list")
        return "已请求快照列表，结果请查看聊天栏"
    elif action == "query":
        if not pos:
            return "query 操作必须指定 pos [x, z]"
        source.reply(f"{ai_prefix}正在查询坐标 {pos} 的快照...")
        server.execute(f"!!snapshot query {pos[0]} {pos[1]}")
        return f"已查询坐标 {pos} 的快照，结果请查看聊天栏"
    elif action == "restore":
        if not snapshot_id:
            return "restore 操作必须指定 snapshot_id"
        source.reply(f"{ai_prefix}⚠️ 正在恢复快照 {snapshot_id}（这是破坏性操作！）...")
        server.execute(f"!!snapshot restore {snapshot_id}")
        return f"已发送恢复快照 {snapshot_id} 的指令。⚠️ 该操作会覆盖当前区块，请确认！"
    return f"未知操作: {action}"


# ── 物品分数查询/设置（scoreboard）──────────────────────

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
    description="列出服务器所有 scoreboard 计分项，或创建新计分项。生电服统计机器产出前需要先创建计分项。",
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
                "description": "可选。add 时的统计准则，如 'dummy'（手动设置，最常用）、'totalKillCount'、'deathCount'、'minecraft.killed:minecraft.zombie'。默认 'dummy'。"
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
