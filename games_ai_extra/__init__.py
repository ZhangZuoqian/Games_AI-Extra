from mcdreforged.api.all import *
import importlib

__all__ = ['carpet']

def on_load(server: PluginServerInterface, old):
    DEFAULT_CONFIG = {
        "carpet": True
    }

    config = server.load_config_simple(
        file_name="config.json",
        default_config=DEFAULT_CONFIG,
        in_data_folder=True
    )

    for project, state in config.items():
        if state and project in __all__:
            importlib.import_module(f"games_ai_extra.games_ai_tools.{project}")
