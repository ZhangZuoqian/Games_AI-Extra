"""经济系统工具集 - 余额查询、转账、价格查询

门控版改进：
- 玩家专属命令（balance/pay）改用 tellraw 可点击消息，由玩家本人点击执行
  解决 MCDR execute() 以控制台身份执行玩家命令无效的问题
- 价格表改为内存存储，不写入文件
- 默认关闭，需在 config.json 开启 economy
"""
import json as _json

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


# 简易价格表（内存存储，重启清空，可由 AI 通过 modify_custom_tools 修改）
_PRICE_LIST: dict = {}


def _send_clickable_cmd(source: CommandSource, label: str, command: str, hint: str = "") -> str:
    """向玩家发送一条可点击消息，玩家点击后以本人身份执行 command。"""
    server = source.get_server()
    if not source.is_player:
        return (
            f"该命令需由玩家本人执行（控制台无法代执行）。请让目标玩家在聊天栏输入：/{command}"
            + (f"\n说明：{hint}" if hint else "")
        )
    player = source.player
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


@register_tool(
    description="查询玩家经济余额。需要服务端安装 EssentialsX（或兼容 Vault 的经济插件）。不指定 player 时向调用玩家发送可点击消息由其本人点击执行 /balance（玩家专属）；指定 player 时直接执行 /balance <player>（控制台可执行，需 essentials.balance.others 权限）。若未安装经济插件，服务端会返回未知命令提示。",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "string",
                "description": "可选。要查询的玩家名。不填则查询调用者自己（仅玩家可用，会发送可点击消息）。"
            }
        }
    }
)
def get_balance(source: CommandSource, ai_prefix: str, player: str = None):
    server = source.get_server()
    if not player:
        # 查自己余额：balance 无参是玩家专属命令，用可点击消息让玩家本人执行
        if not source.is_player:
            return "控制台查询自己余额无意义（控制台无账户）。请指定 player 参数查询他人余额。"
        source.reply(f"{ai_prefix}正在准备查询你的余额...")
        return _send_clickable_cmd(source, "点击查询余额", "balance", "若提示未知命令，说明服务端未安装经济插件")
    # 查他人余额：/balance <player> 控制台可执行（需 essentials.balance.others 权限）
    source.reply(f"{ai_prefix}正在查询 {player} 的余额...")
    server.execute(f"balance {player}")
    return f"已发送查询 {player} 余额的指令，结果请查看聊天栏。若提示未知命令，说明服务端未安装经济插件；若提示无权限，需 essentials.balance.others 权限。"


@register_tool(
    description="玩家之间转账。需要服务端安装 EssentialsX（或兼容 Vault 的经济插件）。pay 是玩家专属命令，会向调用玩家发送可点击消息由其本人点击执行。",
    parameters={
        "type": "object",
        "properties": {
            "to_player": {
                "type": "string",
                "description": "收款玩家名"
            },
            "amount": {
                "type": "number",
                "description": "转账金额（必须 > 0）"
            }
        },
        "required": ["to_player", "amount"]
    }
)
def pay_player(source: CommandSource, ai_prefix: str, to_player: str, amount: float):
    if amount <= 0:
        return f"转账金额必须 > 0，你输入的是 {amount}"
    source.reply(f"{ai_prefix}正在准备向 {to_player} 转账 {amount}...")
    return _send_clickable_cmd(
        source, "点击转账", f"pay {to_player} {amount}",
        "点击后将以本人身份发起转账，请关注聊天栏确认是否成功。若提示未知命令，说明服务端未安装经济插件。"
    )


@register_tool(
    description="查询或设置物品价格表。本插件维护一个本地价格表（内存），方便玩家问价、AI 报价。重启后清空。",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["query", "set", "list", "remove"],
                "description": "操作：query=查询单品价格，set=设置单品价格（管理员），list=列出全部价格，remove=删除单品价格（管理员）"
            },
            "item": {
                "type": "string",
                "description": "物品 ID 或名称（如 'diamond'、'minecraft:netherite_ingot'）。query/set/remove 必填。"
            },
            "price": {
                "type": "number",
                "description": "set 时的价格（单价）。仅 set 时使用。"
            }
        },
        "required": ["action"]
    }
)
def price_list(source: CommandSource, ai_prefix: str, action: str, item: str = None, price: float = None):
    if action == "query":
        if not item:
            return "query 操作必须指定 item"
        item_lower = item.lower()
        for k, v in _PRICE_LIST.items():
            if item_lower in k.lower():
                return f"物品 {k} 的价格: {v}"
        return f"未找到物品 {item} 的价格记录。可用 price_list(action='list') 查看全部"
    elif action == "list":
        if not _PRICE_LIST:
            return "价格表为空"
        lines = [f"{k}: {v}" for k, v in _PRICE_LIST.items()]
        return "当前价格表:\n" + "\n".join(lines)
    elif action == "set":
        if not item or price is None:
            return "set 操作必须指定 item 和 price"
        if price < 0:
            return "价格不能为负"
        if ":" not in item:
            item = "minecraft:" + item
        _PRICE_LIST[item] = price
        return f"已设置 {item} 的价格为 {price}"
    elif action == "remove":
        if not item:
            return "remove 操作必须指定 item"
        if ":" not in item:
            item = "minecraft:" + item
        if item in _PRICE_LIST:
            del _PRICE_LIST[item]
            return f"已删除 {item} 的价格记录"
        return f"价格表中没有 {item}"
    return f"未知操作: {action}"
