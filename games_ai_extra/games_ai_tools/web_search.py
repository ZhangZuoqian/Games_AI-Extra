from mcdreforged.command.command_source import CommandSource
from games_ai.games_ai_tool import register_tool, register_bot_tool

import requests
from bs4 import BeautifulSoup as bs

MAX_RESULT_LENGTH = 4000

@register_tool(description="搜索Minecraft Wiki以获取相关信息, 请不要使用此方法搜索与Minecraft无关的东西。如果返回了Search results页面, 你可以通过先浏览此页面, 再进行一次精确查询", parameters={
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "要搜索的内容，例如某个物品、怪物、机制等的名称。"
        }
    },
    "required": ["query"]
})
@register_bot_tool()
def search_minecraft_wiki(source: CommandSource, ai_prefix: str, query: str):
    source.reply(f'{ai_prefix}{source.get_server().rtr("games_ai_extra.tools.searching_minecraft_wiki", query=query)}')
    lang = source.get_server().get_mcdr_language()
    if lang == "en_us":
        wiki_base = "https://minecraft.wiki/"
    else:
        wiki_base = "https://zh.minecraft.wiki/"
    try:
        response = requests.get(wiki_base, params={"search": query}, timeout=15)
    except requests.RequestException as e:
        return f"无法访问Minecraft Wiki: {e}"
    if response.status_code != 200:
        return f"无法访问Minecraft Wiki进行搜索，错误码:{response.status_code}，原因:{response.reason}"
    soup = bs(response.content.decode('utf-8'), "html.parser")
    # 搜索结果页：列出结果标题，供 AI 进行精确查询
    if soup.select_one(".mw-search-results") is not None or soup.select_one(".searchresults") is not None:
        result_links = soup.select(".mw-search-result-heading a")
        if not result_links:
            return f"没有找到与 '{query}' 相关的结果，可尝试更换关键词"
        titles = [a.get("title") or a.get_text(strip=True) for a in result_links[:10]]
        return f"以下是搜索 '{query}' 的结果（共 {len(titles)} 条）:\n" + "\n".join(titles)
    # 条目页：提取正文内容
    content = soup.select_one(".mw-parser-output")
    if content is None:
        text = soup.get_text(" ", strip=True)
    else:
        text = content.get_text("\n", strip=True)
    if len(text) > MAX_RESULT_LENGTH:
        text = text[:MAX_RESULT_LENGTH] + "\n...(内容过长，已截断，可再进行一次精确查询)"
    return f"以下是搜索内容 {query} 的结果:\n{text}"
