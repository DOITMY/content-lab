"""
小红书内容提取器
"""
import re
import json
import requests


def extract_note_id(url: str) -> str:
    """从小红书链接中提取 note_id"""
    # 格式: https://www.xiaohongshu.com/explore/xxxxxxxxxx
    # 格式: https://xhslink.com/xxx (短链接)
    
    # 先处理短链接
    if "xhslink.com" in url:
        r = requests.head(url, allow_redirects=True, timeout=10)
        url = r.url
    
    # 从 URL 中提取 note_id
    match = re.search(r'/explore/([a-f0-9]+)', url)
    if match:
        return match.group(1)
    
    # 也支持 discover 格式
    match = re.search(r'/discover/item/([a-f0-9]+)', url)
    if match:
        return match.group(1)
    
    raise ValueError(f"无法从链接中提取笔记ID: {url}")


def extract_content(note_id: str, cookie: str = None) -> dict:
    """
    从小红书提取笔记内容
    使用 xhs 包（需要 cookie 登录）或直接 HTML 解析
    """
    try:
        from xhs import XhsClient
        
        if cookie:
            client = XhsClient(cookie=cookie)
        else:
            client = XhsClient()
        
        # 先从 HTML 页面提取（无需登录，对公开笔记有效）
        try:
            note_data = client.get_note_by_id_from_html(note_id)
            return _parse_note_data(note_data)
        except Exception:
            # 如果 HTML 方式失败，尝试 API 方式（需要 cookie）
            if cookie:
                note_data = client.get_note_by_id(note_id)
                return _parse_note_data(note_data)
            raise
    
    except ImportError:
        # 如果 xhs 包未安装，用直接请求方式
        return _extract_via_requests(note_id)


def _parse_note_data(note_data: dict) -> dict:
    """统一解析笔记数据"""
    result = {
        "title": "",
        "desc": "",
        "images": [],
        "video_url": "",
        "tags": [],
        "author": "",
        "source": "xiaohongshu",
    }
    
    # 尝试获取标题
    if "title" in note_data and note_data["title"]:
        result["title"] = note_data["title"]
    
    # 尝试获取描述（正文）
    if "desc" in note_data and note_data["desc"]:
        result["desc"] = note_data["desc"]
    
    # 尝试获取 display_title
    if "display_title" in note_data and note_data["display_title"]:
        if not result["title"]:
            result["title"] = note_data["display_title"]
    
    # 获取标签
    if "tag_list" in note_data:
        result["tags"] = [t.get("name", "") for t in note_data["tag_list"] if isinstance(t, dict)]
    
    # 获取作者
    if "user" in note_data and isinstance(note_data["user"], dict):
        result["author"] = note_data["user"].get("nickname", "")
    
    # 获取视频 URL
    if "video_url" in note_data and note_data["video_url"]:
        result["video_url"] = note_data["video_url"]
    
    # 获取图片
    if "img_urls" in note_data:
        result["images"] = note_data["img_urls"] if isinstance(note_data["img_urls"], list) else []
    
    # 如果没有标题，从 desc 截取
    if not result["title"] and result["desc"]:
        result["title"] = result["desc"][:50].strip()
    
    return result


def _extract_via_requests(note_id: str) -> dict:
    """通过直接请求 HTML 页面提取内容（备用方案）"""
    url = f"https://www.xiaohongshu.com/explore/{note_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.xiaohongshu.com/",
    }
    
    r = requests.get(url, headers=headers, timeout=15)
    html = r.text
    
    # 提取 window.__INITIAL_STATE__
    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})</script>', html, re.DOTALL)
    if not match:
        raise ValueError("无法解析页面数据，可能被反爬拦截")
    
    state_json = match.group(1).replace("undefined", '""')
    state = json.loads(state_json)
    
    # 从 state 树中提取笔记数据
    note_detail_map = state.get("note", {}).get("noteDetailMap", {})
    if note_id in note_detail_map:
        note_data = note_detail_map[note_id].get("note", {})
        return _parse_note_data(note_data)
    
    raise ValueError("页面中未找到笔记数据")


def get_note(url: str, cookie: str = None) -> dict:
    """统一的接口：输入小红书链接，返回结构化笔记内容"""
    note_id = extract_note_id(url)
    content = extract_content(note_id, cookie)
    content["note_id"] = note_id
    content["url"] = url
    return content
