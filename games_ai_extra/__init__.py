from mcdreforged.api.all import *
import importlib
import os
import re as _re
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
        "games_ai": ">=0.6.4"
    }
}

# 当前配置缓存，供 on_user_info 事件监听器判断模块是否启用
_CURRENT_CONFIG: dict = {}


def on_load(server: PluginServerInterface, old):
    global _CURRENT_CONFIG
    register_self(PLUGIN_METADATA.get("id", "games_ai_extra"))

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


# 事件监听
# MCDR 没有 on_player_death / on_player_chat 事件，统一用 on_user_info 解析：
# - 玩家死亡由服务端输出死亡消息（info.is_from_server）触发
# - 玩家聊天由玩家发言（info.is_player）触发

# 死亡消息常见特征词（英文为主，覆盖 vanilla 死亡广播）
_DEATH_KEYWORDS = (
    "died", "was slain", "was shot", "fell", "drowned", "burned", "blew up",
    "was blown up", "hit the ground", "withered", "starved", "was struck",
    "was killed", "experienced kinetic energy", "went up in flames",
    "淹死", "烧死", "炸死", "饿死", "摔死", "掉落",
)

# 匹配死亡广播：玩家名（2-16字符，不含空格）+ 空格 + 死亡描述（以关键词开头）
# 用 {2,16} 排除 "I was slain..." 这类玩家聊天误判（"I" 为 1 字符），
# 同时允许 2 字符的中文玩家名（如"张三"）
_DEATH_PATTERN = _re.compile(
    r"^\S{2,16}\s+(?:" + "|".join(
        k.replace(" ", r"\s+") for k in _DEATH_KEYWORDS
    ) + r")",
    _re.IGNORECASE
)


def _try_record_death(server, content: str):
    """尝试从服务端消息中解析死亡事件并记录到死亡日志。

    先剥离颜色码，再用 _DEATH_PATTERN 正则精确匹配，避免玩家聊天含
    "died"/"死" 等词被误判为死亡广播。
    """
    try:
        from games_ai_extra.games_ai_tools.technical_server import on_player_death as _record
        # 剥离 Minecraft 颜色码：§ 后跟一个字符
        clean = _re.sub(r"§.", "", content).strip()
        if not clean or not _DEATH_PATTERN.match(clean):
            return
        # 取消息第一个词作为玩家名
        parts = clean.split(maxsplit=1)
        player = parts[0] if parts else "unknown"
        _record(server, player, clean)
    except Exception as e:
        try:
            server.logger.warning(f"[games_ai_extra] 死亡记录失败: {e}")
        except Exception:
            pass


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
                _try_record_death(server, info.content)
    except Exception as e:
        try:
            server.logger.warning(f"[games_ai_extra] on_user_info 处理失败: {e}")
        except Exception:
            pass
