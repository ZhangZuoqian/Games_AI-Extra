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
]

_all_skills = {
    'carpet.md': "Read this skill before spawning, controlling, or killing Carpet fake players (bots)",
}

DEFAULT_CONFIG = {
    "carpet": True,
    "location_plguin": False,
    "where2go_plugin": True,
    "whitelist_api": True,
    "web_search": True,
}

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
        "games_ai": ">=0.6.4"
    }
}

def on_load(server: PluginServerInterface, old):
    register_self(PLUGIN_METADATA.get("id", "games_ai_extra"))

    # Register carpet fake player control skill
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

    for project, state in config.items():
        if state and project in _all_tools:
            try:
                importlib.import_module(f"games_ai_extra.games_ai_tools.{project}")
            except Exception as e:
                server.logger.error(f"[games_ai_extra] Failed to load tool module {project}: {e}")
