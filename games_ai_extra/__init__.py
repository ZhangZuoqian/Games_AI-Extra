from mcdreforged.api.all import *
import importlib
import os
import zipfile

from games_ai.register_extra_plugin import register_self
from games_ai.external_skills_loader import register_skills

_all_tools = [
    'carpet',
    'location_plguin',
    'where2go_plugin',
    'whitelist_api',
    'web_search',
    # 扩展模块（默认关闭，按需在 config.json 开启）
    'bot_group',
    'technical_server',
    'survival_server',
    'economy',
    'chat_log',
]

_all_skills = {
    'carpet.md': "Read this skill before spawning, controlling, or killing Carpet fake players (bots)",
    'bot_group.md': "Read this skill before using batch fake player operations (group spawn/kill/action)",
    'technical.md': "Read this skill before using technical server tools (TPS/MSPT, Carpet rules, forceload, entity management, death log, etc.)",
    'survival.md': "Read this skill before using survival server tools (teleport, player info, weather/time, backup, etc.)",
    'economy.md': "Read this skill before using economy tools (balance, pay, price list)",
    'chat_log.md': "Read this skill before searching or clearing chat logs",
}

DEFAULT_CONFIG = {
    "carpet": True,
    "location_plguin": False,
    "where2go_plugin": True,
    "whitelist_api": True,
    "web_search": True,
    # 扩展模块默认关闭，需管理员在 config.json 手动开启
    "bot_group": True,
    "technical_server": False,
    "survival_server": False,
    "economy": False,
    "chat_log": False,
}

PLUGIN_METADATA = {
    "id": "games_ai_extra",
    "version": "0.3.1",
    "name": "GamesAI Extra",
    "description":{
        "zh_cn": "GamesAI的功能性扩展",
        "en_us": "Functional extension for GamesAI",
        "zh_tw": "GamesAI的功能性擴展"
    },
    "author": ["man8in", "yello"],
    "dependencies": {
        "mcdreforged": ">=2.15.0",
        "games_ai": ">=0.6.4"
    }
}

# 当前配置缓存，供 on_user_info 事件监听器判断模块是否启用
_CURRENT_CONFIG: dict = {}


def on_load(server: PluginServerInterface, old):
    global _CURRENT_CONFIG
    register_self(PLUGIN_METADATA.get("id", "games_ai_extra"))

    # 确保假人自动索敌脚本已部署到服务器 scripts/ 目录（Carpet/scarpet 加载）
    _ensure_bot_combat_script(server)

    # Register skill files
    # Supports both extracted directory (dev) and packed .mcdr zip (distribution)
    _plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for skill, description in _all_skills.items():
        _skill_content: str | None = None

        if os.path.isfile(_plugin_root):
            # Packed as .mcdr zip — read skill from inside the archive
            try:
                with zipfile.ZipFile(_plugin_root, "r") as zf:
                    _skill_content = zf.read(f"skills/{skill}").decode("utf-8")
            except (KeyError, zipfile.BadZipFile):
                continue
        else:
            # Extracted directory — read skill from filesystem
            _skill_path = os.path.join(_plugin_root, "skills", skill)
            try:
                with open(_skill_path, mode="r", encoding="utf-8") as f:
                    _skill_content = f.read()
            except FileNotFoundError:
                continue

        if _skill_content is not None:
            register_skills(
                file_name=skill,
                description=description,
                content=_skill_content,
            )
        else:
            server.logger.warning(f"{skill} skill file not found, skipping skill registration")

    config = server.load_config_simple(
        file_name="config.json",
        default_config=DEFAULT_CONFIG,
        in_data_folder=True
    )
    _CURRENT_CONFIG = config

    for project, state in config.items():
        if state and project in _all_tools:
            try:
                importlib.import_module(f"games_ai_extra.games_ai_tools.{project}")
            except Exception as e:
                server.logger.error(f"[games_ai_extra] Failed to load tool module {project}: {e}")


def _ensure_bot_combat_script(server: PluginServerInterface):
    """确保服务器 scripts/bot_combat.sc 存在（假人自动索敌脚本，由 Carpet/scarpet 加载）。

    打包模式从 .mcdr 压缩包读取，开发模式从文件系统读取；服务器 scripts/ 目录下
    已存在同名脚本时跳过（以服务器上的版本为准）。
    """
    try:
        working_dir = server.get_mcdr_config().get('working_directory', 'server')
        scripts_dir = os.path.join(os.getcwd(), working_dir, 'scripts')
        target = os.path.join(scripts_dir, 'bot_combat.sc')
        if os.path.exists(target):
            return
        os.makedirs(scripts_dir, exist_ok=True)
        _plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if os.path.isfile(_plugin_root):
            # 打包为 .mcdr zip — 从压缩包内读取
            with zipfile.ZipFile(_plugin_root, 'r') as zf:
                content = zf.read('games_ai_extra/scripts/bot_combat.sc')
        else:
            # 解压目录（开发模式）— 从文件系统读取
            with open(os.path.join(_plugin_root, 'games_ai_extra', 'scripts', 'bot_combat.sc'), 'rb') as f:
                content = f.read()
        with open(target, 'wb') as f:
            f.write(content)
        server.logger.info('[games_ai_extra] bot_combat.sc 已写入服务器 scripts/ 目录')
    except Exception as e:
        server.logger.warning(f'[games_ai_extra] 写入 bot_combat.sc 失败: {e}')


# 事件监听
# MCDR 没有 on_player_death / on_player_chat 事件，统一用 on_user_info 解析：
# - 玩家死亡由服务端输出死亡消息（info.is_from_server）触发
# - 玩家聊天由玩家发言（info.is_player）触发
# 死亡消息的解析/匹配逻辑统一放在 technical_server 模块（try_record_death），
# 事件监听只负责按配置转发，避免解析逻辑散落在入口模块。


def on_user_info(server, info):
    """统一信息事件：解析玩家聊天与死亡广播。

    MCDR 不提供独立的 player_death / player_chat 事件，需在 on_user_info 中
    按 info 来源（玩家发言 / 服务端广播）自行解析。
    """
    try:
        if info.is_player:
            # 玩家聊天 → 记录到 chat_log（若启用）
            if _CURRENT_CONFIG.get("chat_log", False):
                try:
                    from games_ai_extra.games_ai_tools.chat_log import _append_chat_record
                    _append_chat_record(info.player, info.content)
                except Exception as e:
                    server.logger.warning(f"[games_ai_extra] 聊天记录失败: {e}")
        elif info.is_from_server:
            # 服务端消息 → 判断是否为死亡广播（若 technical_server 启用）
            if _CURRENT_CONFIG.get("technical_server", False):
                try:
                    from games_ai_extra.games_ai_tools.technical_server import try_record_death
                    try_record_death(server, info.content)
                except Exception as e:
                    server.logger.warning(f"[games_ai_extra] 死亡记录失败: {e}")
    except Exception as e:
        try:
            server.logger.warning(f"[games_ai_extra] on_user_info 处理失败: {e}")
        except Exception:
            pass
