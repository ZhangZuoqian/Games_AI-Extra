from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool

@register_tool(description="获取服务器的白名单列表")
def get_whitelist_name(source: CommandSource, ai_prefix: str):
    server = source.get_server()
    source.reply(f'{ai_prefix}{server.rtr("games_ai_extra.tools.getting_whitelist")}')
    __whitelist_api = server.get_plugin_instance('whitelist_api')
    if __whitelist_api is None:
        return "无法获取白名单插件实例"
    whitelist = __whitelist_api.get_whitelist()
    names = [player.name for player in whitelist]
    names.sort()
    if names:
        return ", ".join(names)
    else:
        return "无白名单玩家"
    
@register_tool(description="在白名单中添加一名玩家,推荐在添加之前先查询白名单", perm=3, parameters={
    "type": "object",
    "properties": {
        "player": {
            "type": "string",
            "description": "要添加到白名单的玩家名称。只能添加一个。"
        }
    },
    "required": ["player"]
})
def add_to_whitelist(source: CommandSource, ai_prefix: str, player: str):
    if source.get_permission_level() < 3:
        return "向你发起这项命令的玩家没有权限使用此功能"
    source.reply(f'{ai_prefix}{source.get_server().rtr("games_ai_extra.tools.adding_whitelist", player=player)}')
    __whitelist_api = source.get_server().get_plugin_instance('whitelist_api')
    if __whitelist_api is None:
        return "无法获取白名单插件实例"
    try:
        __whitelist_api.add_player(player)
    except Exception as e:
        return f"将玩家 {player} 添加到白名单失败: {e}"
    return f"玩家 {player} 已添加到白名单"

@register_tool(description="删除一名白名单中的玩家,推荐在删除之前先查询白名单", perm=3, parameters={
    "type": "object",
    "properties": {
        "player": {
            "type": "string",
            "description": "要从白名单中移除的玩家名称。只能移除一个。"
        }
    },
    "required": ["player"]
})
def remove_from_whitelist(source: CommandSource, ai_prefix: str, player: str):
    if source.get_permission_level() < 3:
        return "向你发起这项命令的玩家没有权限使用此功能"
    source.reply(f'{ai_prefix}{source.get_server().rtr("games_ai_extra.tools.removing_whitelist", player=player)}')
    __whitelist_api = source.get_server().get_plugin_instance('whitelist_api')
    if __whitelist_api is None:
        return "无法获取白名单插件实例"
    try:
        __whitelist_api.remove_player(player)
    except Exception as e:
        return f"将玩家 {player} 从白名单移除失败: {e}"
    return f"玩家 {player} 已从白名单中移除"