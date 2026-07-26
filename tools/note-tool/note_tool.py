#!/usr/bin/env python3
"""
笔记工具 - 从链接提取内容或从 Get笔记读取，AI 仿写为个人笔记

用法：
    python3 note_tool.py <小红书/抖音链接> [选项]
    python3 note_tool.py --list-getnote
    python3 note_tool.py --from-getnote <note_id> [选项]

选项：
    --style TEXT     仿写风格 (默认: 个人学习笔记)
                      可选: 个人学习笔记 / 视频口播稿 / 公众号文章 / 小红书种草文
    --no-rewrite     只提取内容，不进行 AI 仿写
    --output DIR     输出目录 (默认: ./notes/)
    --cookie TEXT    小红书 cookie (可选)
    --save           保存到 Get笔记（得到大脑）
    --list-getnote   列出 Get笔记 最近笔记
    --from-getnote   从 Get笔记 读取笔记进行仿写
    --help           显示帮助
"""
import os
import sys
import argparse
from datetime import datetime

# 自动读取 ~/.hermes/.env 中的环境变量
_HERMES_ENV = os.path.expanduser("~/.hermes/.env")
if os.path.exists(_HERMES_ENV):
    with open(_HERMES_ENV) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOL_DIR)

from extractors.xiaohongshu import get_note as get_xhs_note
from extractors.douyin import get_note as get_douyin_note
from rewriters.deepseek import rewrite_note
from savers.getnote import save_to_getnote, list_notes, get_note


def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
        return "xiaohongshu"
    elif "douyin.com" in url_lower or "v.douyin.com" in url_lower or "iesdouyin.com" in url_lower:
        return "douyin"
    else:
        return "unknown"


def format_filename(title: str) -> str:
    invalid_chars = r'<>:"/\|?*'
    for c in invalid_chars:
        title = title.replace(c, '')
    title = title.strip()
    if len(title) > 50:
        title = title[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{title}.md"


def run(url: str, style: str = "个人学习笔记", no_rewrite: bool = False,
        output_dir: str = None, cookie: str = None, save: bool = False) -> dict:
    """从链接提取内容并仿写"""
    platform = detect_platform(url)
    print(f"🔍 检测到平台: {platform}")

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

    return _rewrite_and_save(content, style, no_rewrite, output_dir, save)


def run_from_getnote(note_id: str, style: str = "个人学习笔记", no_rewrite: bool = False,
                     output_dir: str = None, save: bool = False) -> dict:
    """从 Get笔记 读取并仿写"""
    print(f"📖 正在从 Get笔记 读取笔记 {note_id}...")
    result = get_note(note_id)
    if not result.get("success"):
        print(f"❌ 读取失败: {result.get('error', '未知错误')}")
        sys.exit(1)

    note = result["note"]
    title = note.get("title", "无标题") or "无标题"
    content_text = note.get("content", "") or ""
    note_type = note.get("note_type", "")
    tags = [t.get("name", "") for t in note.get("tags", [])]

    print(f"   ✅ 标题: {title}")
    print(f"   ✅ 类型: {note_type}")
    print(f"   ✅ 标签: {', '.join(tags) if tags else '无'}")
    preview = content_text[:100]
    print(f"   ✅ 内容: {preview}{'...' if len(content_text) > 100 else ''}")

    # 构建 content 字典供 rewriter 使用
    content = {
        "title": title,
        "desc": content_text,
        "tags": tags,
        "author": "Get笔记",
        "source": "getnote",
        "url": f"https://biji.com/note/{note_id}",
        "note_id": note_id,
    }

    return _rewrite_and_save(content, style, no_rewrite, output_dir, save)


def _rewrite_and_save(content: dict, style: str, no_rewrite: bool,
                      output_dir: str, save: bool) -> dict:
    """统一的仿写+保存流程"""
    # AI 仿写
    if no_rewrite:
        md_content = _format_raw(content)
        print("   ⏭️  跳过 AI 仿写")
    else:
        print("🤖 正在 AI 仿写...")
        md_content = rewrite_note(content, style)
        print("   ✅ 仿写完成")

    # 保存文件
    if output_dir is None:
        output_dir = os.path.join(TOOL_DIR, "notes")
    os.makedirs(output_dir, exist_ok=True)

    filename = format_filename(content.get("title", "未命名笔记"))
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n📝 笔记已保存: {filepath}")

    # 保存到 Get笔记
    if save:
        print("☁️  正在保存到 Get笔记...")
        result = save_to_getnote(content, md_content)
        if result.get("success"):
            print(f"   ✅ 已保存到 Get笔记 (note_id: {result['note_id']})")
        else:
            print(f"   ❌ 保存失败: {result.get('error', '未知错误')}")

    return {"content": content, "markdown": md_content, "filepath": filepath}


def _format_raw(content: dict) -> str:
    """不经过 AI，直接格式化为 Markdown"""
    source_map = {"xiaohongshu": "小红书", "douyin": "抖音", "getnote": "Get笔记"}
    source_name = source_map.get(content.get("source", ""), content.get("source", "未知"))

    md = []
    md.append(f"# {content.get('title', '无标题')}")
    md.append("")
    md.append(f"> **来源**：{source_name} | **作者**：{content.get('author', '未知')}")
    md.append(f"> **链接**：{content.get('url', '无')}")
    md.append("")

    if content.get("tags"):
        tags = content["tags"]
        if isinstance(tags, list):
            tags = [t if isinstance(t, str) else t.get("name", "") for t in tags]
        md.append(f"**标签**：{' '.join(['#' + t for t in tags if t])}")
        md.append("")

    md.append("---")
    md.append("")

    if content.get("desc"):
        md.append("## 原文内容")
        md.append("")
        md.append(content["desc"])

    return "\n".join(md)


def cmd_list_getnote():
    """列出 Get笔记 最近笔记"""
    print("📋 正在获取 Get笔记 笔记列表...")
    result = list_notes()
    if not result.get("success"):
        print(f"❌ 获取失败: {result.get('error', '未知错误')}")
        sys.exit(1)

    notes = result.get("notes", [])
    total = result.get("total", 0)
    print(f"\n共 {total} 条笔记，最近 {len(notes)} 条：\n")
    print(f"{'ID':<22} {'标题':<35} {'类型':<12} {'时间'}")
    print("-" * 90)
    for n in notes:
        note_id = n.get("note_id", "")
        title = (n.get("title", "") or "无标题")[:34]
        ntype = n.get("note_type", "")
        time = (n.get("created_at", "") or "")[:16]
        print(f"{note_id:<22} {title:<35} {ntype:<12} {time}")


def main():
    parser = argparse.ArgumentParser(
        description="从链接提取内容或从 Get笔记读取，AI 仿写为个人笔记",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 note_tool.py https://www.douyin.com/video/xxxxx --style "视频口播稿"
  python3 note_tool.py https://www.xiaohongshu.com/explore/xxxxx --save
  python3 note_tool.py --list-getnote
  python3 note_tool.py --from-getnote 1916675757309699464 --style "公众号文章"
        """,
    )
    parser.add_argument("url", nargs="?", help="小红书或抖音笔记/视频链接")
    parser.add_argument("--style", default="个人学习笔记",
                        help="仿写风格: 个人学习笔记/视频口播稿/公众号文章/小红书种草文 (默认: 个人学习笔记)")
    parser.add_argument("--no-rewrite", action="store_true", help="只提取内容，不进行 AI 仿写")
    parser.add_argument("--output", help="输出目录 (默认: ./notes/)")
    parser.add_argument("--cookie", help="小红书 cookie (可选)")
    parser.add_argument("--save", action="store_true", help="保存到 Get笔记（得到大脑）")
    parser.add_argument("--list-getnote", action="store_true", help="列出 Get笔记 最近笔记")
    parser.add_argument("--from-getnote", help="从 Get笔记 读取笔记进行仿写 (note_id)")

    args = parser.parse_args()

    # 模式1：列出 Get笔记 笔记
    if args.list_getnote:
        cmd_list_getnote()
        return

    # 模式2：从 Get笔记 读取
    if args.from_getnote:
        run_from_getnote(args.from_getnote, args.style, args.no_rewrite,
                         args.output, args.save)
        return

    # 模式3：从链接提取（默认）
    if not args.url:
        parser.print_help()
        sys.exit(1)

    run(args.url, args.style, args.no_rewrite, args.output, args.cookie, args.save)


if __name__ == "__main__":
    main()
