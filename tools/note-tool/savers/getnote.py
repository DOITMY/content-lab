"""
Get笔记（得到大脑）API 保存模块
将笔记内容保存到用户的 Get笔记账号
"""
import os
import requests

GETNOTE_API_KEY = os.environ.get("GETNOTE_API_KEY", "")
GETNOTE_CLIENT_ID = os.environ.get("GETNOTE_CLIENT_ID", "")
GETNOTE_BASE_URL = "https://openapi.biji.com/open/api/v1"


def save_to_getnote(content: dict, markdown: str) -> dict:
    """
    将笔记内容保存到 Get笔记
    
    Args:
        content: 提取的原始内容字典
        markdown: AI 仿写后的 Markdown 文本
    
    Returns:
        API 响应结果
    """
    if not GETNOTE_API_KEY or not GETNOTE_CLIENT_ID:
        return {
            "success": False,
            "error": "未配置 GETNOTE_API_KEY 或 GETNOTE_CLIENT_ID\n请在 ~/.hermes/.env 中设置"
        }

    headers = {
        "Authorization": GETNOTE_API_KEY,
        "X-Client-ID": GETNOTE_CLIENT_ID,
        "Content-Type": "application/json",
    }

    # 构建笔记标题
    title = content.get("title", "").strip()
    if not title:
        # 从 markdown 第一行取标题
        for line in markdown.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                break
    if not title:
        title = f"未命名笔记 - {content.get('source', 'unknown')}"
    if len(title) > 100:
        title = title[:100]

    # 构建标签
    tags = content.get("tags", [])
    if isinstance(tags, list):
        tags = [t if isinstance(t, str) else t.get("name", "") for t in tags]
    # 添加来源标签
    source_tag = "抖音" if content.get("source") == "douyin" else "小红书"
    if source_tag not in tags:
        tags.insert(0, source_tag)

    payload = {
        "title": title,
        "content": markdown,
        "note_type": "plain_text",
        "tags": tags,
    }

    try:
        r = requests.post(
            f"{GETNOTE_BASE_URL}/resource/note/save",
            headers=headers,
            json=payload,
            timeout=30,
        )
        data = r.json()

        if data.get("success"):
            return {
                "success": True,
                "note_id": data.get("data", {}).get("note_id", ""),
                "title": title,
            }
        else:
            error = data.get("error", {})
            return {
                "success": False,
                "error": error.get("message", str(data)),
                "code": error.get("code", ""),
            }

    except Exception as e:
        return {"success": False, "error": str(e)}
