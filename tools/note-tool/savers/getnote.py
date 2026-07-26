"""
Get笔记（得到大脑）API 客户端
管理笔记：列表、详情、保存
"""
import os
import requests

GETNOTE_API_KEY = os.environ.get("GETNOTE_API_KEY", "")
GETNOTE_CLIENT_ID = os.environ.get("GETNOTE_CLIENT_ID", "")
GETNOTE_BASE_URL = "https://openapi.biji.com/open/api/v1"


def _headers() -> dict:
    return {
        "Authorization": GETNOTE_API_KEY,
        "X-Client-ID": GETNOTE_CLIENT_ID,
        "Content-Type": "application/json",
    }


def _check_config():
    if not GETNOTE_API_KEY or not GETNOTE_CLIENT_ID:
        return False
    return True


def list_notes(cursor: str = "") -> dict:
    """
    获取笔记列表
    
    Args:
        cursor: 翻页游标，首次不传
    
    Returns:
        {"success": bool, "notes": [...], "cursor": str, "has_more": bool, "total": int, "error": str}
    """
    if not _check_config():
        return {"success": False, "error": "未配置 GETNOTE_API_KEY 或 GETNOTE_CLIENT_ID"}

    params = {}
    if cursor:
        params["cursor"] = cursor

    try:
        r = requests.get(
            f"{GETNOTE_BASE_URL}/resource/note/list",
            headers=_headers(),
            params=params,
            timeout=15,
        )
        data = r.json()
        if data.get("success"):
            d = data["data"]
            return {
                "success": True,
                "notes": d.get("notes", []),
                "cursor": d.get("cursor", ""),
                "has_more": d.get("has_more", False),
                "total": d.get("total", 0),
            }
        else:
            err = data.get("error", {})
            return {"success": False, "error": err.get("message", str(data))}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_note(note_id: str) -> dict:
    """
    获取笔记详情
    
    Args:
        note_id: 笔记 ID
    
    Returns:
        {"success": bool, "note": {...}, "error": str}
    """
    if not _check_config():
        return {"success": False, "error": "未配置 GETNOTE_API_KEY 或 GETNOTE_CLIENT_ID"}

    try:
        r = requests.get(
            f"{GETNOTE_BASE_URL}/resource/note/detail",
            headers=_headers(),
            params={"id": note_id},
            timeout=15,
        )
        data = r.json()
        if data.get("success"):
            return {"success": True, "note": data["data"]["note"]}
        else:
            err = data.get("error", {})
            return {"success": False, "error": err.get("message", str(data))}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_to_getnote(content: dict, markdown: str) -> dict:
    """
    将笔记内容保存到 Get笔记
    """
    if not _check_config():
        return {"success": False, "error": "未配置 GETNOTE_API_KEY 或 GETNOTE_CLIENT_ID"}

    # 构建笔记标题
    title = content.get("title", "").strip()
    if not title:
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
            headers=_headers(),
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
            err = data.get("error", {})
            return {"success": False, "error": err.get("message", str(data)), "code": err.get("code", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}
