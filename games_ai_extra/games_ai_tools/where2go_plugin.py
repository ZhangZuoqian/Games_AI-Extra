import json
import os

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


def _get_where2go_command_prefix(server) -> str:
    """读取 where2go 配置中的命令前缀，默认返回 '!!wp'"""
    config_path = os.path.join("config", "where2go", "config.json")
    if not os.path.isfile(config_path):
        return "!!wp"
    with open(config_path, mode="r", encoding="utf-8") as f:
        try:
            where2go_config = json.loads(f.read())
        except json.JSONDecodeError:
            return "!!wp"
    return where2go_config.get("command", {"waypoints": "!!wp"}).get("waypoints", "!!wp")


def _load_where2go_data() -> tuple[list[dict] | None, str | None]:
    """加载 where2go 数据文件，返回 (数据列表, 错误信息)"""
    data_path = os.path.join("config", "where2go", "data.json")
    if not os.path.isfile(data_path):
        return None, "where2go 数据文件尚不存在，请先添加路径点"
    with open(data_path, mode="r", encoding="utf-8") as f:
        try:
            waypoints: list[dict] = json.load(f)
        except json.JSONDecodeError:
            return None, "无法解析 where2go 数据文件，文件可能已损坏"
    return waypoints, None


@register_tool(description="添加一个路径点到坐标管理插件(where2go), 推荐先查询坐标管理插件中已有的路径点", tr_key="adding_position", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "路径点的名称"
        },
        "pos": {
            "type": "array",
            "items": {
                "type": "number"
            },
            "description": "路径点的坐标，格式为 [x, y, z]"
        },
        "dimension": {
            "type": "string",
            "description": "路径点所在的维度，例如 overworld、the_nether、the_end, 分别对应主世界、下界和末地"
        }
    },
    "required": ["name", "pos", "dimension"]
})
def add_pos_pos(source: CommandSource, ai_prefix: str, name: str, pos: list, dimension: str):
    server = source.get_server()
    source.reply(f'{ai_prefix}{server.rtr("games_ai.tools.adding_position", name=name, pos=pos, dimension=dimension)}')
    _where2go = server.get_plugin_metadata('where2go')
    if _where2go is not None:
        command_main = _get_where2go_command_prefix(server)
        server.execute_command(f"{command_main} addpos {pos[0]} {pos[1]} {pos[2]} {dimension} {name}", source)
        return f"已添加路径点 {name}, 坐标: {pos}, 维度: {dimension}"
    else:
        return "无法获取 where2go 插件实例"


@register_tool(description="将玩家现在的位置作为一个路径点添加到坐标管理插件(where2go), 推荐先查询坐标管理插件中已有的路径点", tr_key="adding_position", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "路径点的名称"
        },
    },
    "required": ["name"]
})
def add_pos_here(source: CommandSource, ai_prefix: str, name: str):
    server = source.get_server()
    if source.is_player:
        source.reply(f'{ai_prefix}{server.rtr("games_ai.tools.adding_position", name=name, pos="玩家当前位置", dimension="玩家当前维度")}')
        _where2go = server.get_plugin_metadata('where2go')
        if _where2go is not None:
            command_main = _get_where2go_command_prefix(server)
            server.execute_command(f"{command_main} addhere {name}", source)
            return f"已在玩家位置添加路径点 {name}"
        else:
            return "无法获取 where2go 插件实例"
    else:
        source.reply(f'{ai_prefix}{server.rtr("games_ai.tools.consolo_add_here")}')
        return "控制台无法执行 add_pos_here 函数"


@register_tool(description="从坐标管理插件(where2go)中删除一个路径点, 推荐先查询坐标管理插件中已有的路径点", tr_key="removing_position", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "路径点的名称"
        }
    },
    "required": ["name"]
})
def remove_pos(source: CommandSource, ai_prefix: str, name: str):
    server = source.get_server()
    source.reply(f'{ai_prefix}{server.rtr("games_ai.tools.removing_position", name=name)}')
    _where2go = server.get_plugin_metadata('where2go')
    if _where2go is not None:
        waypoints, err = _load_where2go_data()
        if err is not None:
            return err
        waypoint_id_list = []
        for wp in waypoints:
            if name.lower() in wp.get("waypoint", {}).get("name", "").lower():
                waypoint_id_list.append(wp.get("id", ""))
        if not waypoint_id_list:
            return f"名为 {name} 的坐标点不存在"
        elif len(waypoint_id_list) > 1:
            return f"名为 {name} 的坐标点匹配到了多个, 无法精确匹配, 匹配结果: {waypoint_id_list}"
        else:
            waypoint_id = waypoint_id_list[0]
            command_main = _get_where2go_command_prefix(server)
            server.execute_command(f"{command_main} remove {waypoint_id}", source)
            return f"名为 {name} 的路径点已删除"
    else:
        return "无法获取 where2go 插件实例"


@register_tool(description="从坐标管理插件(where2go)中查询一个路径点, 推荐先查询坐标管理插件中已有的路径点", tr_key="searching_position", parameters={
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "路径点的名称"
        }
    },
    "required": ["name"]
})
def search_pos(source: CommandSource, ai_prefix: str, name: str):
    server = source.get_server()
    source.reply(f'{ai_prefix}{server.rtr("games_ai.tools.searching_position", name=name)}')
    _where2go = server.get_plugin_metadata('where2go')
    if _where2go is not None:
        waypoints, err = _load_where2go_data()
        if err is not None:
            return err
        if not waypoints:
            return f"名为 {name} 的路径点不存在（当前无任何路径点）"
        matches = [
            wp for wp in waypoints
            if name.lower() in wp.get("waypoint", {}).get("name", "").lower()
        ]
        if not matches:
            return f"名为 {name} 的路径点不存在"
        lines = []
        for wp in matches:
            w = wp["waypoint"]
            lines.append(
                f"[{wp['id']}] {w['name']} | "
                f"坐标: {w['pos']} | 维度: {w['dimension']} | "
                f"创建者: {wp['creator']} | 时间: {wp['create_time']}"
            )
        return f"路径点 {name} 的搜索结果（{len(matches)} 条）:\n" + "\n".join(lines)
    else:
        return "无法获取 where2go 插件实例"


@register_tool(description="获取坐标管理插件(where2go)中所有的路径点, 如果你想搜索某个坐标点, 你应该调用这一工具", tr_key="getting_all_pos")
def get_all_pos(source: CommandSource, ai_prefix: str):
    server = source.get_server()
    source.reply(f'{ai_prefix}{server.rtr("games_ai.tools.getting_all_pos")}')
    _where2go = server.get_plugin_metadata('where2go')
    if _where2go is not None:
        waypoints, err = _load_where2go_data()
        if err is not None:
            return err
        return f"所有路径点信息: {waypoints}"
    else:
        return "无法获取 where2go 插件实例"
