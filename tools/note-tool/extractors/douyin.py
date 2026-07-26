"""
抖音内容提取器
"""
import re
import json
import requests


def extract_video_id(url: str) -> str:
    """从抖音链接中提取视频ID"""
    # 处理短链接
    if "v.douyin.com" in url:
        r = requests.head(url, allow_redirects=True, timeout=10)
        url = r.url
    
    # 格式: https://www.douyin.com/video/xxxxxxxxx
    match = re.search(r'/video/(\d+)', url)
    if match:
        return match.group(1)
    
    # 格式: https://www.douyin.com/note/xxxxxxxxx
    match = re.search(r'/note/(\d+)', url)
    if match:
        return match.group(1)
    
    raise ValueError(f"无法从链接中提取视频ID: {url}")


def extract_content(video_id: str) -> dict:
    """从抖音页面提取视频内容"""
    url = f"https://www.douyin.com/video/{video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
    }
    
    r = requests.get(url, headers=headers, timeout=15)
    html = r.text
    
    result = {
        "title": "",
        "desc": "",
        "images": [],
        "video_url": "",
        "tags": [],
        "author": "",
        "source": "douyin",
    }
    
    # 方法1: 提取 <script id="RENDER_DATA"> 中的 JSON
    render_match = re.search(
        r'<script id="RENDER_DATA"[^>]*type="application/json"[^>]*>([^<]+)</script>',
        html
    )
    if render_match:
        try:
            import urllib.parse
            render_data = urllib.parse.unquote(render_match.group(1))
            data = json.loads(render_data)
            result = _parse_render_data(data, result)
        except (json.JSONDecodeError, Exception):
            pass
    
    # 方法2: 提取 <script type="application/ld+json"> (结构化数据)
    if not result["desc"]:
        ld_match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>',
            html, re.DOTALL
        )
        if ld_match:
            try:
                ld_data = json.loads(ld_match.group(1))
                if isinstance(ld_data, dict):
                    result["title"] = result["title"] or ld_data.get("name", "")
                    result["desc"] = result["desc"] or ld_data.get("description", "")
            except json.JSONDecodeError:
                pass
    
    # 方法3: 从 meta 标签提取
    if not result["title"]:
        title_match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html)
        if title_match:
            result["title"] = title_match.group(1)
    
    if not result["desc"]:
        desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
        if desc_match:
            result["desc"] = desc_match.group(1)
    
    # 提取作者信息
    author_match = re.search(r'<p[^>]+class="[^"]*nickname[^"]*"[^>]*>([^<]+)</p>', html)
    if author_match:
        result["author"] = author_match.group(1).strip()
    
    return result


def _parse_render_data(data: dict, result: dict) -> dict:
    """递归解析 RENDER_DATA JSON 中的视频信息"""
    
    def search(obj, depth=0):
        if depth > 10:
            return
        if isinstance(obj, dict):
            # 查找描述文本
            for key in ["desc", "title", "description"]:
                if key in obj and isinstance(obj[key], str) and obj[key]:
                    if key == "title" or key == "desc":
                        result["title"] = result["title"] or obj[key].strip()
                    if key == "description":
                        result["desc"] = result["desc"] or obj[key].strip()
            
            # 查找标签
            if "textExtra" in obj and isinstance(obj["textExtra"], list):
                for item in obj["textExtra"]:
                    if isinstance(item, dict) and "hashtagName" in item:
                        result["tags"].append(item["hashtagName"])
            
            # 查找作者
            if "author" in obj and isinstance(obj["author"], dict):
                result["author"] = result["author"] or obj["author"].get("nickname", "")
            
            # 查找视频封面
            if "video" in obj and isinstance(obj["video"], dict):
                play_addr = obj["video"].get("playAddr", {})
                if isinstance(play_addr, dict):
                    url_list = play_addr.get("urlList", [])
                    if url_list:
                        result["video_url"] = url_list[0]
            
            # 继续递归
            for v in obj.values():
                search(v, depth + 1)
        
        elif isinstance(obj, list):
            for item in obj:
                search(item, depth + 1)
    
    search(data)
    return result


def get_note(url: str) -> dict:
    """统一的接口：输入抖音链接，返回结构化笔记内容"""
    video_id = extract_video_id(url)
    content = extract_content(video_id)
    content["video_id"] = video_id
    content["url"] = url
    return content
