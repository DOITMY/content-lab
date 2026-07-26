#!/usr/bin/env python3
"""
笔记工具 - 从抖音/小红书链接提取内容并仿写为个人笔记

用法：
    python3 note_tool.py <小红书/抖音链接> [选项]

选项：
    --style TEXT     仿写风格 (默认: 个人学习笔记)
    --no-rewrite     只提取内容，不进行 AI 仿写
    --output DIR     输出目录 (默认: ./notes/)
    --cookie TEXT    小红书 cookie (可选，用于提取非公开笔记)
    --help           显示帮助
"""
import os
import sys
import argparse
from datetime import datetime

# 确保能导入 extractors 和 rewriters
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOL_DIR)

from extractors.xiaohongshu import get_note as get_xhs_note
from extractors.douyin import get_note as get_douyin_note
from rewriters.deepseek import rewrite_note


def detect_platform(url: str) -> str:
    """检测链接属于哪个平台"""
    url_lower = url.lower()
    if "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
        return "xiaohongshu"
    elif "douyin.com" in url_lower or "v.douyin.com" in url_lower or "iesdouyin.com" in url_lower:
        return "douyin"
    else:
        return "unknown"


def format_filename(title: str) -> str:
    """将标题格式化为文件名"""
    # 去掉非法字符
    invalid_chars = r'<>:"/\|?*'
    for c in invalid_chars:
        title = title.replace(c, '')
    title = title.strip()
    # 限制长度
    if len(title) > 50:
        title = title[:50]
    # 加时间戳前缀避免重名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{title}.md"


def run(url: str, style: str = "个人学习笔记", no_rewrite: bool = False, 
        output_dir: str = None, cookie: str = None) -> dict:
    """
    主执行流程
    """
    platform = detect_platform(url)
    print(f"🔍 检测到平台: {platform}")
    
    # 步骤1：提取内容
    print("📥 正在提取内容...")
    if platform == "xiaohongshu":
        content = get_xhs_note(url, cookie)
    elif platform == "douyin":
        content = get_douyin_note(url)
    else:
        print(f"❌ 不支持的链接: {url}")
        print("   目前支持: 小红书 (xiaohongshu.com) 和 抖音 (douyin.com)")
        sys.exit(1)
    
    print(f"   ✅ 标题: {content.get('title', '无')}")
    print(f"   ✅ 作者: {content.get('author', '未知')}")
    desc_preview = content.get('desc', '')[:80]
    print(f"   ✅ 内容: {desc_preview}{'...' if len(content.get('desc', '')) > 80 else ''}")
    
    # 步骤2：AI 仿写
    if no_rewrite:
        md_content = _format_raw(content)
        print("   ⏭️  跳过 AI 仿写")
    else:
        print("🤖 正在 AI 仿写笔记...")
        md_content = rewrite_note(content, style)
        print("   ✅ 仿写完成")
    
    # 步骤3：保存文件
    if output_dir is None:
        output_dir = os.path.join(TOOL_DIR, "notes")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = format_filename(content.get("title", "未命名笔记"))
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"\n📝 笔记已保存: {filepath}")
    
    return {
        "content": content,
        "markdown": md_content,
        "filepath": filepath,
    }


def _format_raw(content: dict) -> str:
    """不经过 AI，直接格式化为 Markdown"""
    source_name = "小红书" if content.get("source") == "xiaohongshu" else "抖音"
    
    md = []
    md.append(f"# {content.get('title', '无标题')}")
    md.append("")
    md.append(f"> **来源**：{source_name} | **作者**：{content.get('author', '未知')}")
    md.append(f"> **链接**：{content.get('url', '无')}")
    md.append("")
    
    if content.get("tags"):
        md.append(f"**标签**：{' '.join(['#' + t for t in content['tags']])}")
        md.append("")
    
    md.append("---")
    md.append("")
    
    if content.get("desc"):
        md.append("## 原文内容")
        md.append("")
        md.append(content["desc"])
    
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(
        description="从抖音/小红书链接提取内容并仿写为个人笔记",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 note_tool.py https://www.xiaohongshu.com/explore/xxxxx
  python3 note_tool.py https://www.douyin.com/video/xxxxx --style "观点评论"
  python3 note_tool.py https://www.xiaohongshu.com/explore/xxxxx --no-rewrite
        """,
    )
    parser.add_argument("url", help="小红书或抖音笔记/视频链接")
    parser.add_argument("--style", default="个人学习笔记", help="仿写风格 (默认: 个人学习笔记)")
    parser.add_argument("--no-rewrite", action="store_true", help="只提取内容，不进行 AI 仿写")
    parser.add_argument("--output", help="输出目录 (默认: ./notes/)")
    parser.add_argument("--cookie", help="小红书 cookie (可选)")
    
    args = parser.parse_args()
    
    run(args.url, args.style, args.no_rewrite, args.output, args.cookie)


if __name__ == "__main__":
    main()
