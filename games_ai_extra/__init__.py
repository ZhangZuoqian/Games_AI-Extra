from mcdreforged.api.all import *
import importlib
import os
import zipfile

from games_ai.register_extra_plugin import register_self
from games_ai.external_skills_loader import register_skills

__all__ = ['carpet', 'location_plguin', 'where2go_plugin', 'bot_group']

PLUGIN_METADATA = {
    "id": "games_ai_extra",
    "version": "0.2.0",
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


def on_load(server: PluginServerInterface, old):
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
    }

    config = server.load_config_simple(
        file_name="config.json",
        default_config=DEFAULT_CONFIG,
        in_data_folder=True
    )

    for project, state in config.items():
        if state and project in __all__:
            importlib.import_module(f"games_ai_extra.games_ai_tools.{project}")
