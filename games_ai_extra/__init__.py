from mcdreforged.api.all import *
import importlib
import os
import zipfile

from games_ai.register_extra_plugin import register_self
from games_ai.external_skills_loader import register_skills

__all__ = ['carpet', 'location_plguin', 'where2go_plugin']

PLUGIN_METADATA = {
    "id": "games_ai_extra",
    "version": "0.1.2",
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

def on_load(server: PluginServerInterface, old):
    register_self(server.get_self_metadata.id)

    # Register carpet fake player control skill
    # Supports both extracted directory (dev) and packed .mcdr zip (distribution)
    _plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _skill_content: str | None = None

    if os.path.isfile(_plugin_root):
        # Packed as .mcdr zip — read skill from inside the archive
        try:
            with zipfile.ZipFile(_plugin_root, "r") as zf:
                _skill_content = zf.read("skills/carpet.md").decode("utf-8")
        except (KeyError, zipfile.BadZipFile):
            _skill_content = None
    else:
        # Extracted directory — read skill from filesystem
        _skill_path = os.path.join(_plugin_root, "skills", "carpet.md")
        try:
            with open(_skill_path, mode="r", encoding="utf-8") as f:
                _skill_content = f.read()
        except FileNotFoundError:
            _skill_content = None

    if _skill_content is not None:
        register_skills(
            file_name="carpet.md",
            description="Read this skill before spawning, controlling, or killing Carpet fake players (bots)",
            content=_skill_content,
        )
    else:
        server.logger.warning("carpet.md skill file not found, skipping skill registration")

    DEFAULT_CONFIG = {
        "carpet": True,
        "location_plguin": False,
        "where2go_plugin": True,
    }

    config = server.load_config_simple(
        file_name="config.json",
        default_config=DEFAULT_CONFIG,
        in_data_folder=True
    )

    for project, state in config.items():
        if state and project in __all__:
            importlib.import_module(f"games_ai_extra.games_ai_tools.{project}")
