from mcdreforged.api.all import *
import importlib
import os
import zipfile

from games_ai.register_extra_plugin import register_self
from games_ai.external_skills_loader import register_skills

__all__ = [
    'carpet',
    'location_plguin',
    'where2go_plugin',
    'bot_group',
    # 门控模块（默认关闭，按需开启）
    'technical_server',
    'survival_server',
    'economy',
    'chat_log',
]

PLUGIN_METADATA = {
    "id": "games_ai_extra",
    "version": "0.3.0",
    "name": "GamesAI Extra",
    "description":{
        "zh_cn": "GamesAI的功能性扩展",
        "en_us": "Functional extension for GamesAI",
        "zh_tw": "GamesAI的功能性擴展"
    },
    "author": ["man8in", "yello"],
    "dependencies": {
        "mcdreforged": ">=2.15.0",
        "games_ai": ">=0.6.1"
    }
}

# 需要注册的 skill 文件（文件名 -> 描述）
_SKILL_FILES = {
    "carpet.md": "Read this skill before spawning, controlling, or killing Carpet fake players (bots)",
    "bot_group.md": "Read this skill before using batch fake player operations (group spawn/kill/action)",
    "technical.md": "Read this skill before using technical server tools (TPS/MSPT, Carpet rules, forceload, entity management, etc.)",
    "survival.md": "Read this skill before using survival server tools (teleport, player info, weather/time, etc.)",
    "economy.md": "Read this skill before using economy tools (balance, pay, price list)",
    "chat_log.md": "Read this skill before searching or clearing chat logs",
}


def _read_skill_file(plugin_root: str, skill_name: str) -> str | None:
    """从解压目录或 .mcdr 压缩包读取 skill 文件内容"""
    if os.path.isfile(plugin_root):
        # 打包为 .mcdr 压缩包
        try:
            with zipfile.ZipFile(plugin_root, "r") as zf:
                return zf.read(f"skills/{skill_name}").decode("utf-8")
        except (KeyError, zipfile.BadZipFile):
            return None
    else:
        # 解压目录
        skill_path = os.path.join(plugin_root, "skills", skill_name)
        try:
            with open(skill_path, mode="r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None


# 保存当前配置，供事件监听器判断是否记录（门控）
_CURRENT_CONFIG: dict = {}


def on_load(server: PluginServerInterface, old):
    global _CURRENT_CONFIG
    register_self(server.get_self_metadata.id)

    # 注册所有 skill 文件
    _plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for skill_name, description in _SKILL_FILES.items():
        content = _read_skill_file(_plugin_root, skill_name)
        if content is not None:
            register_skills(
                file_name=skill_name,
                description=description,
                content=content,
            )
        else:
            server.logger.warning(f"{skill_name} skill file not found, skipping skill registration")

    DEFAULT_CONFIG = {
        "carpet": True,
        "location_plguin": False,
        "where2go_plugin": True,
        "bot_group": True,
        # 门控模块：默认全部关闭，需手动开启
        # technical_server 额外要求 carpet 也为 True 才会加载
        "technical_server": False,
        "survival_server": False,
        "economy": False,
        "chat_log": False,
    }

    config = server.load_config_simple(
        file_name="config.json",
        default_config=DEFAULT_CONFIG,
        in_data_folder=True
    )
    _CURRENT_CONFIG = config

    for project, state in config.items():
        if not state or project not in __all__:
            continue
        # 门控：technical_server 依赖 carpet，carpet 关闭时跳过
        if project == "technical_server" and not config.get("carpet", False):
            server.logger.warning("[games_ai_extra] technical_server 需要 carpet 同时开启，已跳过加载")
            continue
        importlib.import_module(f"games_ai_extra.games_ai_tools.{project}")


def on_player_death(server, player, message):
    """监听玩家死亡事件，记录到死亡日志（供 query_death_log 查询）。

    门控：仅当 technical_server 开启时才记录，避免无意义的处理。
    """
    if not _CURRENT_CONFIG.get("technical_server", False):
        return
    try:
        from games_ai_extra.games_ai_tools.technical_server import on_player_death as _record
        _record(server, player, message)
    except Exception as e:
        try:
            server.logger.warning(f"[games_ai_extra] 死亡事件记录失败: {e}")
        except Exception:
            pass


def on_player_chat(server, player, message, **kwargs):
    """监听玩家聊天事件，记录到聊天日志（供 search_chat_log 查询）。

    门控：仅当 chat_log 开启时才记录，避免无意义的处理。
    """
    if not _CURRENT_CONFIG.get("chat_log", False):
        return
    try:
        from games_ai_extra.games_ai_tools.chat_log import on_player_chat as _record
        _record(server, player, message, **kwargs)
    except Exception as e:
        try:
            server.logger.warning(f"[games_ai_extra] 聊天事件记录失败: {e}")
        except Exception:
            pass
