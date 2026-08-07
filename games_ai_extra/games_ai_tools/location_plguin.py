from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


@register_tool(description="添加一个路径点到坐标管理插件(location_marker), 推荐先查询坐标管理插件中已有的路径点", tr_key="adding_position", parameters={
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
    _location_marker = server.get_plugin_instance('location_marker')
    if _location_marker is not None:
        _location_marker.add_location(source, name, pos[0], pos[1], pos[2], dimension)
        return f"已添加路径点 {name}, 坐标: {pos}, 维度: {dimension}"
    else:
        return "无法获取 location_marker 插件实例"


@register_tool(description="将玩家现在的位置作为一个路径点添加到坐标管理插件(location_marker), 推荐先查询坐标管理插件中已有的路径点", tr_key="adding_position", parameters={
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
        _location_marker = server.get_plugin_instance('location_marker')
        if _location_marker is not None:
            _location_marker.add_location_here(source, name)
            return f"已添加路径点 {name}, 坐标: 玩家当前位置, 维度: 玩家当前维度"
        else:
            return "无法获取 location_marker 插件实例"
    else:
        source.reply(f'{ai_prefix}{server.rtr("games_ai.tools.consolo_add_here")}')
        return "控制台无法执行 add_pos_here 函数"


@register_tool(description="从坐标管理插件(location_marker)中删除一个路径点, 推荐先查询坐标管理插件中已有的路径点", tr_key="removing_position", parameters={
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
    _location_marker = server.get_plugin_instance('location_marker')
    if _location_marker is not None:
        _location_marker.delete_location(source, name)
        return f"名为 {name} 的路径点已删除"
    else:
        return "无法获取 location_marker 插件实例"


@register_tool(description="从坐标管理插件(location_marker)中查询一个路径点, 推荐先查询坐标管理插件中已有的路径点", tr_key="searching_position", parameters={
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
    _location_marker = server.get_plugin_instance('location_marker')
    if _location_marker is not None:
        waypoint_storage = _location_marker.storage
        waypoint_data = waypoint_storage.get(name)
        if waypoint_data is None:
            return f"名为 {name} 的路径点不存在"
        return f"路径点 {name} 的信息: {waypoint_data}"
    else:
        return "无法获取 location_marker 插件实例"


@register_tool(description="获取坐标管理插件(location_marker)中所有的路径点, 如果你想搜索某个坐标点, 你应该调用这一工具", tr_key="getting_all_pos")
def get_all_pos(source: CommandSource, ai_prefix: str):
    server = source.get_server()
    source.reply(f'{ai_prefix}{server.rtr("games_ai.tools.getting_all_pos")}')
    _location_marker = server.get_plugin_instance('location_marker')
    if _location_marker is not None:
        waypoint_storage = _location_marker.storage
        waypoint_data = waypoint_storage.get_locations()
        if not waypoint_data:
            return "没有路径点"
        return f"所有路径点信息: {waypoint_data}"
    else:
        return "无法获取 location_marker 插件实例"
