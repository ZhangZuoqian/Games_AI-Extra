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
    # 门控模块（首次启动默认关闭，需管理员运行 !!gai_setup 配置后开启）
    'technical_server',
    'survival_server',
    'economy',
    'chat_log',
]

PLUGIN_METADATA = {
    "id": "games_ai_extra",
    "version": "0.3.2",
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

# 新增模块清单（仅这些受首次配置向导门控；原版模块不受影响）
_NEW_MODULES = ["technical_server", "survival_server", "economy", "chat_log"]
# 各新增模块的简短说明（用于向导提示）
_MODULE_DESC = {
    "technical_server": "生电服工具（TPS/MSPT、Carpet规则、强加载、实体清理、计分板、死亡日志）",
    "survival_server": "生存服工具（传送/家/领地/天气时间/备份，玩家命令用可点击消息）",
    "economy": "经济工具（余额/转账/价格表，依赖 EssentialsX）",
    "chat_log": "聊天记录搜索（内存存储，重启清空）",
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


# 保存当前配置与服务器实例，供事件监听器/向导命令使用
_CURRENT_CONFIG: dict = {}
_SETUP_DONE: bool = False
_SERVER_REF = None


def _is_admin(server, player) -> bool:
    """判定玩家是否为管理员（MCDR 权限等级 >= 3 视为管理员 ADMIN）"""
    try:
        return server.get_permission_level(player) >= 3
    except Exception:
        return False


def _notify_unconfigured(server, player):
    """向管理员玩家发送未配置提示（每次其上线时，若尚未完成配置则提示）"""
    if _SETUP_DONE:
        return
    try:
        server.tell(
            player,
            RText("§e[GamesAI Extra] §f检测到新增模块尚未配置。", RColor.yellow)
            + "\n§7请管理员运行 §e!!gai_setup §7选择开启哪些模块，配置后这些模块才会加载。"
        )
    except Exception:
        pass


def _print_setup_banner(server):
    """首次启动时在控制台输出未配置提示横幅"""
    server.logger.warning("═══════════════════════════════════════════════════════")
    server.logger.warning("[GamesAI Extra] 检测到首次启动，新增模块尚未配置")
    server.logger.warning("以下新增模块默认关闭，需管理员配置后才会加载：")
    for m in _NEW_MODULES:
        server.logger.warning(f"  - {m}: {_MODULE_DESC.get(m, '')}")
    server.logger.warning("请在 MCDR 控制台或游戏内执行：!!gai_setup")
    server.logger.warning("（管理员上线时也会收到提示）")
    server.logger.warning("═══════════════════════════════════════════════════════")


def _load_modules(server, config):
    """根据 config 加载已启用的模块"""
    for project, state in config.items():
        if not state or project not in __all__:
            continue
        # 门控：technical_server 依赖 carpet，carpet 关闭时跳过
        if project == "technical_server" and not config.get("carpet", False):
            server.logger.warning("[games_ai_extra] technical_server 需要 carpet 同时开启，已跳过加载")
            continue
        try:
            importlib.import_module(f"games_ai_extra.games_ai_tools.{project}")
        except Exception as e:
            server.logger.exception(f"[games_ai_extra] 加载模块 {project} 失败: {e}")


def on_load(server: PluginServerInterface, old):
    global _CURRENT_CONFIG, _SETUP_DONE, _SERVER_REF
    _SERVER_REF = server
    register_self(server.get_self_metadata.id)

    # 注册所有 skill 文件（skill 文件始终注册，与模块开关无关；模块不加载时 AI 也读不到对应工具）
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
        # 新增模块：默认全部关闭，首次需 !!gai_setup 配置
        "technical_server": False,
        "survival_server": False,
        "economy": False,
        "chat_log": False,
        # 配置向导完成标志（首次启动缺失 → 触发向导提示）
        "setup_done": False,
    }

    config = server.load_config_simple(
        file_name="config.json",
        default_config=DEFAULT_CONFIG,
        in_data_folder=True
    )
    _CURRENT_CONFIG = config
    _SETUP_DONE = bool(config.get("setup_done", False))

    # 注册 !!gai_setup 命令（仅管理员可用）
    server.register_command(
        Literal("!!gai_setup").runs(_cmd_setup_show).then(
            Literal("on").then(
                GreedyText("modules").runs(_cmd_setup_on)
            )
        ).then(
            Literal("off").then(
                GreedyText("modules").runs(_cmd_setup_off)
            )
        ).then(
            Literal("done").runs(_cmd_setup_done)
        ).then(
            Literal("status").runs(_cmd_setup_status)
        )
    )
    server.register_help_message("!!gai_setup", "配置 GamesAI Extra 新增模块开关（管理员）")

    if not _SETUP_DONE:
        # 首次启动：控制台提示，新增模块暂不加载（原版模块正常加载）
        _print_setup_banner(server)
        _load_modules(server, {k: v for k, v in config.items() if k not in _NEW_MODULES})
    else:
        # 已配置：按配置加载所有模块
        _load_modules(server, config)


# ── !!gai_setup 命令实现 ─────────────────────────────────

def _fmt_status() -> str:
    """格式化当前新增模块开关状态"""
    lines = ["§6[GamesAI Extra] 新增模块当前状态："]
    for m in _NEW_MODULES:
        st = "§a开启" if _CURRENT_CONFIG.get(m, False) else "§c关闭"
        lines.append(f"§7- {m} ({_MODULE_DESC.get(m, '')}): {st}")
    lines.append("§7setup_done = " + ("§a是" if _SETUP_DONE else "§c否"))
    return "\n".join(lines)


def _cmd_setup_show(source):
    if not _is_admin_source(source):
        source.reply("§c仅管理员可使用此命令")
        return
    source.reply(_fmt_status())
    source.reply("§7用法：")
    source.reply("§e  !!gai_setup on <模块名...>   §7开启指定模块（空格分隔，或用 all）")
    source.reply("§e  !!gai_setup off <模块名...>  §7关闭指定模块（空格分隔，或用 all）")
    source.reply("§e  !!gai_setup done             §7完成配置（新增模块将立即加载）")
    source.reply("§e  !!gai_setup status           §7查看当前状态")
    source.reply("§7可选模块：" + " ".join(_NEW_MODULES))


def _is_admin_source(source) -> bool:
    try:
        if source.is_console:
            return True
        if source.is_player:
            return source.get_server().get_permission_level(source.player) >= 3
        return False
    except Exception:
        return False


def _apply_module_change(source, modules: list, enable: bool):
    global _CURRENT_CONFIG
    server = source.get_server()
    if "all" in modules:
        norm = list(_NEW_MODULES)
        invalid = []
    else:
        norm = [m for m in modules if m in _NEW_MODULES]
        invalid = [m for m in modules if m not in _NEW_MODULES]
    if invalid:
        source.reply(f"§c未知模块：{invalid}。可选：" + " ".join(_NEW_MODULES) + " 或 all")
        return
    if not norm:
        source.reply("§c未指定模块。可选：" + " ".join(_NEW_MODULES) + " 或 all")
        return
    for m in norm:
        _CURRENT_CONFIG[m] = enable
        source.reply(f"§a{m} ({_MODULE_DESC.get(m, '')}) → {'开启' if enable else '关闭'}")
    # 立即写回配置文件
    try:
        server.save_config_simple(_CURRENT_CONFIG, file_name="config.json", in_data_folder=True)
    except Exception as e:
        source.reply(f"§c保存配置失败：{e}")
        return
    source.reply("§7配置已保存。运行 §e!!gai_setup done §7使新增模块立即生效（首次配置后才会加载）。")


def _cmd_setup_on(source, ctx):
    if not _is_admin_source(source):
        source.reply("§c仅管理员可使用此命令")
        return
    modules = ctx.get("modules", "").split()
    _apply_module_change(source, modules, enable=True)


def _cmd_setup_off(source, ctx):
    if not _is_admin_source(source):
        source.reply("§c仅管理员可使用此命令")
        return
    modules = ctx.get("modules", "").split()
    _apply_module_change(source, modules, enable=False)


def _cmd_setup_done(source):
    global _SETUP_DONE, _CURRENT_CONFIG
    if not _is_admin_source(source):
        source.reply("§c仅管理员可使用此命令")
        return
    server = source.get_server()
    _CURRENT_CONFIG["setup_done"] = True
    _SETUP_DONE = True
    try:
        server.save_config_simple(_CURRENT_CONFIG, file_name="config.json", in_data_folder=True)
    except Exception as e:
        source.reply(f"§c保存配置失败：{e}")
        return
    source.reply("§a配置完成！正在加载已开启的新增模块...")
    # 加载已开启的新增模块（原版模块在 on_load 已加载）
    _load_modules(server, {k: v for k, v in _CURRENT_CONFIG.items() if k in _NEW_MODULES})


def _cmd_setup_status(source):
    if not _is_admin_source(source):
        source.reply("§c仅管理员可使用此命令")
        return
    source.reply(_fmt_status())


# ── 事件监听 ─────────────────────────────────────────────
# MCDR 没有 on_player_death / on_player_chat 事件，统一用 on_user_info 解析
# 玩家死亡由服务端输出死亡消息（info.is_from_server）触发
# 玩家聊天由玩家发言（info.is_player）触发

import re as _re

# 死亡消息正则：匹配 "<player> ..." 或 "<player> fell from ..." 等服务端输出的死亡广播
# 服务端死亡广播格式多样，这里用宽松匹配：服务端消息中含已知玩家名
# 为避免误判，仅当 technical_server 开启且消息疑似死亡时记录

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


# 玩家死亡广播的常见特征词（中英文）
_DEATH_KEYWORDS = (
    "died", "was slain", "was shot", "fell", "drowned", "burned", "blew up",
    "was blown up", "hit the ground", "withered", "starved", "was struck",
    "was killed", "experienced kinetic energy", "went up in flames",
    "淹死", "烧死", "炸死", "饿死", "摔死", "掉落",
)

# 匹配死亡广播：玩家名（不含空格）+ 空格 + 死亡描述（以关键词开头）
# 格式："Steve was slain by Zombie" / "Steve fell from a high place" / "Steve 淹死了"
# 玩家名后直接跟死亡描述，不要求中间有额外词汇
# Minecraft 用户名长度 3-16，用 {3,16} 进一步排除 "I was slain..." 这类聊天
_DEATH_PATTERN = _re.compile(
    r"^\S{3,16}\s+(?:" + "|".join(
        k.replace(" ", r"\s+") for k in _DEATH_KEYWORDS
    ) + r")",
    _re.IGNORECASE
)


def _try_record_death(server, content: str):
    """尝试从服务端消息中解析死亡事件并记录到死亡日志。

    死亡广播格式：<玩家名> <死亡描述>，可能带 § 颜色码。
    先剥离颜色码，再用 _DEATH_PATTERN 正则精确匹配，避免玩家聊天含
    "died"/"死" 等词被误判为死亡广播。
    """
    try:
        from games_ai_extra.games_ai_tools.technical_server import on_player_death as _record
        # 剥离 Minecraft 颜色码：§ 后跟一个字符（§e、§r 等）
        clean = _re.sub(r"§.", "", content).strip()
        if not clean:
            return
        # 用正则精确匹配死亡广播格式（玩家名 + 死亡描述），
        # 比关键词包含更严格，减少误判
        if not _DEATH_PATTERN.match(clean):
            return
        # 取消息第一个词作为玩家名（死亡广播格式通常以玩家名开头）
        parts = clean.split(maxsplit=1)
        player = parts[0] if parts else "unknown"
        _record(server, player, clean)
    except Exception as e:
        try:
            server.logger.warning(f"[games_ai_extra] 死亡记录失败: {e}")
        except Exception:
            pass


def on_player_joined(server, player, info):
    """管理员上线时提示未配置项（仅首次配置未完成时）"""
    if _SETUP_DONE:
        return
    if _is_admin(server, player):
        _notify_unconfigured(server, player)
