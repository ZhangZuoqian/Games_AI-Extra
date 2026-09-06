"""RCON 执行辅助：优先用 RCON 同步获取命令输出，未开启/失败时回退。

MCDR 2.x 的 server.rcon 是 Rcon 对象：
- rcon.is_connected() -> bool
- rcon.send_command(cmd) -> str（同步返回服务器输出）

统一封装，供 economy / survival_server / technical_server 共用：
所有工具命令先走 RCON，能拿到响应就直接返回给 AI；RCON 未开启或
执行失败时返回 None，由调用方回退到 server.execute。
"""


def rcon_exec(server, command: str) -> str | None:
    """尝试用 RCON 同步执行命令。

    成功（连接可用且命令有输出）返回响应文本；RCON 不可用或执行
    失败返回 None，调用方应回退到 server.execute。
    """
    try:
        rcon = server.rcon
        if rcon is not None and rcon.is_connected():
            response = rcon.send_command(command)
            if response:
                return response
    except Exception as e:
        try:
            server.logger.warning(f"[games_ai_extra] RCON 执行失败，回退到 execute: {e}")
        except Exception:
            pass
    return None
