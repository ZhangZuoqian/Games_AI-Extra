# Contributing to GamesAI Extra

Thank you for considering contributing to GamesAI Extra! This guide explains how to add new **tools** and **skills** to the plugin.

## Ways to Contribute

GamesAI Extra provides two types of extensions for the [GamesAI](https://github.com/PengZixuan30/Games_AI) plugin:

- **Tools** — Python functions registered with `@register_tool()` that the AI can call via `!!ask`
- **Skills** — Markdown guides registered with `register_skills()` that the AI reads before performing specific tasks

## Project Structure

```
games_ai_extra/
├── __init__.py            # Plugin entry: version, config, skill registration
├── games_ai_tools/
│   ├── carpet.py          # Carpet fake player (bot) tools
│   ├── location_plguin.py # Location Marker waypoint tools
│   └── where2go_plugin.py # Where2Go waypoint tools
skills/
└── carpet.md              # Carpet fake player control skill
```

## Adding a New Tool

Tools are Python functions decorated with `@register_tool()`. Each tool is part of a **module** (a `.py` file in `games_ai_tools/`) that can be enabled or disabled via `config.json`.

### Step 1: Create the tool module

Create a new `.py` file in `games_ai_extra/games_ai_tools/`. Use the existing modules as templates:

```python
# games_ai_extra/games_ai_tools/my_module.py
from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool, register_bot_tool


@register_tool(
    description="Brief description of what this tool does for the AI",
    parameters={
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string",
                "description": "What this parameter is for"
            }
        },
        "required": ["param_name"]
    }
)
@register_bot_tool()  # Optional — makes tool available to Mineflayer Bot
def my_tool(source: CommandSource, ai_prefix: str, param_name: str):
    server = source.get_server()
    source.reply(f"{ai_prefix}Running my tool...")
    # Tool logic here
    return "Result string returned to the AI"
```

### Step 2: Register the module

1. Add the module name to `__all__` in `games_ai_extra/__init__.py`:
   ```python
   __all__ = ['carpet', 'location_plguin', 'where2go_plugin', 'my_module']
   ```

2. Add a default config entry in the `DEFAULT_CONFIG` dict:
   ```python
   DEFAULT_CONFIG = {
       "carpet": True,
       "location_plguin": False,
       "where2go_plugin": True,
       "my_module": True,          # <-- add your module
   }
   ```

### Tool Function Signature

Every tool function **must** follow this signature:

```python
def tool_name(source: CommandSource, ai_prefix: str, ...) -> str:
```

- `source` — the MCDR command source (provides `get_server()`, `is_player`, `player`, etc.)
- `ai_prefix` — the AI's name prefix for reply formatting
- Additional parameters — defined in the `parameters` dict of `@register_tool()`
- Return value — a string that is sent back to the AI as the tool result

### `@register_tool()` Parameters

| Parameter | Required | Description |
|-----------|:--------:|-------------|
| `description` | Yes | Tells the AI what the tool does. Be detailed and specific. |
| `parameters` | No | JSON Schema defining the tool's arguments (OpenAI function calling format). |
| `tr_key` | No | Translation key for MCDR i18n support (used by built-in GamesAI tools). |

### `@register_bot_tool()`

Add this decorator to make the tool available to the **Mineflayer autonomous Bot controller**. Without it, the tool can only be used through `!!ask` by the chat AI. Only add this for tools that are safe for autonomous bot execution.

## Adding a New Skill

Skills are Markdown files that guide the AI's behavior for specific tasks. They are registered programmatically in `on_load()` via the `register_skills()` API.

### Step 1: Create the skill file

Create a `.md` file in the `skills/` directory:

```markdown
# My Skill Title

Brief description of what this skill covers.

---

## Core Principles

> ⚠️ **Read this skill before performing XYZ!** Call `read_skills("my_skill.md")`.

...

## Tool Reference

| Tool | Purpose |
|------|---------|
| `tool_a` | Description |

...

## Typical Workflows

### Scenario A
...

## Important Notes

- Key rule 1
- Key rule 2
```

Use `skills/carpet.md` as a reference for the expected format and level of detail.

### Step 2: Register the skill

Add a `register_skills()` call in `games_ai_extra/__init__.py` inside `on_load()`, following the existing `carpet.md` pattern:

```python
# Register my skill
_skill_path = os.path.join(_plugin_root, "skills", "my_skill.md")
try:
    if os.path.isfile(_plugin_root):
        with zipfile.ZipFile(_plugin_root, "r") as zf:
            content = zf.read("skills/my_skill.md").decode("utf-8")
    else:
        with open(_skill_path, mode="r", encoding="utf-8") as f:
            content = f.read()
    register_skills(
        file_name="my_skill.md",
        description="Read this skill before performing XYZ operations",
        content=content,
    )
except (FileNotFoundError, KeyError, zipfile.BadZipFile):
    server.logger.warning("my_skill.md not found, skipping skill registration")
```

> [!IMPORTANT]
> Always support **both** reading modes: extracted directory (development) and packed `.mcdr` zip (distribution). See the existing code for the full pattern.

### Skill Guidelines

- Use **English** for skill content (the AI reads these files directly)
- Be **prescriptive** — tell the AI exactly what to do, not just what's possible
- Include **workflows** with step-by-step examples
- Use **blockquotes** (`>`) for important warnings and rules
- Keep the skill **focused** on one topic/domain

## Updating README

When adding a new module or skill, update all three README files:

- `README.md` (English)
- `README.zh-CN.md` (Simplified Chinese)
- `README.zh-TW.md` (Traditional Chinese)

Add the new tool table or skill entry in the appropriate section, and update the **What's New** section with the version change.

## Version Bumping

Update the version number in these files:

- `mcdreforged.plugin.json` — `"version"` field
- `games_ai_extra/__init__.py` — `PLUGIN_METADATA["version"]`

## Pull Request Checklist

- [ ] New tool module created in `games_ai_tools/`
- [ ] Module registered in `__all__` and `DEFAULT_CONFIG`
- [ ] `@register_tool()` decorator with clear `description` and `parameters`
- [ ] `@register_bot_tool()` added if the tool is bot-safe
- [ ] New skill file created in `skills/` (if applicable)
- [ ] Skill registered via `register_skills()` in `on_load()`
- [ ] Both zip and filesystem reading modes supported for skill files
- [ ] All three README files updated
- [ ] Version bumped in `mcdreforged.plugin.json` and `__init__.py`

## Questions?

[Open an issue](https://github.com/PengZixuan30/Games_AI-Extra/issues/new) or join the [GamesAI QQ Group](https://qm.qq.com/q/jDQQaUPNmw).
