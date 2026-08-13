"""经济系统工具集 - 余额查询、转账、价格查询

高效实现策略：
- 优先使用 Vault API（Bukkit 端经济），通过 MCDR 的 api 接口
- 不需要数据库，所有数据由 Vault 后端经济插件管理（EssentialsX Economy / iConomy 等）
"""
import json
import os

from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool


# 简易价格表（可由 AI 通过 modify_custom_tools 修改）
_PRICE_DB_FILE = os.path.join("config", "games_ai_extra", "price_list.json")


def _load_price_list() -> dict:
    if not os.path.isfile(_PRICE_DB_FILE):
        return {}
    try:
        with open(_PRICE_DB_FILE, mode="r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_price_list(data: dict):
    os.makedirs(os.path.dirname(_PRICE_DB_FILE), exist_ok=True)
    with open(_PRICE_DB_FILE, mode="w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _has_vault(server) -> bool:
    """检测服务端是否有 Vault 经济插件"""
    return server.get_plugin_metadata("vault") is not None or \
           server.get_plugin_metadata("Vault") is not None


@register_tool(
    description="查询玩家经济余额。需要服务端安装 Vault + 经济插件（如 EssentialsX Economy）。生电/生存服交易必备。",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "string",
                "description": "可选。要查询的玩家名。不填则查询调用者自己（仅玩家可用）。"
            }
        }
    }
)
def get_balance(source: CommandSource, ai_prefix: str, player: str = None):
    server = source.get_server()
    if not _has_vault(server):
        return "未检测到 Vault 经济插件，无法查询余额"
    if not player:
        if not source.is_player:
            return "控制台查询必须指定 player"
        player = source.player
    source.reply(f"{ai_prefix}正在查询 {player} 的余额...")
    # Vault 通过 essentials:balance 命令查询
    server.execute(f"balance {player}")
    return f"已发送查询 {player} 余额的指令，结果请查看聊天栏"


@register_tool(
    description="玩家之间转账。需要服务端安装 Vault + 经济插件。调用者必须是在线玩家。",
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
    server = source.get_server()
    if not _has_vault(server):
        return "未检测到 Vault 经济插件，无法转账"
    if not source.is_player:
        return "控制台无法发起转账，请由玩家发起"
    if amount <= 0:
        return f"转账金额必须 > 0，你输入的是 {amount}"
    source.reply(f"{ai_prefix}正在向 {to_player} 转账 {amount}...")
    server.execute(f"pay {to_player} {amount}")
    return f"已发送转账指令：向 {to_player} 转账 {amount}。请关注聊天栏确认是否成功"


@register_tool(
    description="查询或设置物品价格表。本插件维护一个本地价格表（JSON 文件），方便玩家问价、AI 报价。也可对接商店插件扩展。",
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
        prices = _load_price_list()
        # 模糊匹配
        item_lower = item.lower()
        for k, v in prices.items():
            if item_lower in k.lower():
                return f"物品 {k} 的价格: {v}"
        return f"未找到物品 {item} 的价格记录。可用 price_list(action='list') 查看全部"
    elif action == "list":
        prices = _load_price_list()
        if not prices:
            return "价格表为空"
        lines = [f"{k}: {v}" for k, v in prices.items()]
        return "当前价格表:\n" + "\n".join(lines)
    elif action == "set":
        if not item or price is None:
            return "set 操作必须指定 item 和 price"
        if price < 0:
            return "价格不能为负"
        prices = _load_price_list()
        if ":" not in item:
            item = "minecraft:" + item
        prices[item] = price
        _save_price_list(prices)
        return f"已设置 {item} 的价格为 {price}"
    elif action == "remove":
        if not item:
            return "remove 操作必须指定 item"
        prices = _load_price_list()
        if ":" not in item:
            item = "minecraft:" + item
        if item in prices:
            del prices[item]
            _save_price_list(prices)
            return f"已删除 {item} 的价格记录"
        return f"价格表中没有 {item}"
    return f"未知操作: {action}"
