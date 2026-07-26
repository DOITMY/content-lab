"""
DeepSeek AI 仿写笔记模块
"""
import os
import json
import requests


# 从环境变量读取 DeepSeek 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")


def rewrite_note(content: dict, style: str = "个人学习笔记") -> str:
    """
    使用 DeepSeek AI 将提取的内容仿写为个人笔记
    
    Args:
        content: 提取的笔记内容字典 (包含 title, desc, tags, author, source 等)
        style: 仿写风格 (个人学习笔记、观点评论、摘要总结等)
    
    Returns:
        仿写后的 Markdown 笔记文本
    """
    if not DEEPSEEK_API_KEY:
        return _fallback_format(content)
    
    # 构建 prompt
    prompt = _build_rewrite_prompt(content, style)
    
    # 调用 DeepSeek API
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个笔记助手。你的任务是将网络上的内容（小红书/抖音笔记）重新组织为高质量的个人学习笔记。"
                          "保持核心信息不变，但用自己的语言重新表达，加入个人的理解和归纳。\n\n"
                          "输出格式要求：\n"
                          "1. 使用 Markdown 格式\n"
                          "2. 用 ## 做标题分级\n"
                          "3. 核心观点用 **加粗** 标注\n"
                          "4. 如有列表用 - 符号\n"
                          "5. 开头标注来源\n"
                          "6. 结尾加上「💡 我的思考」小节，写出你对这个内容的观点或启发"
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    
    try:
        r = requests.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    
    except Exception as e:
        print(f"[警告] DeepSeek API 调用失败: {e}")
        print("[提示] 使用本地格式化作为后备方案")
        return _fallback_format(content)


def _build_rewrite_prompt(content: dict, style: str) -> str:
    """构建仿写提示词"""
    source_name = "小红书" if content.get("source") == "xiaohongshu" else "抖音"
    
    lines = [
        f"请将以下{source_name}内容仿写为[{style}]风格的个人笔记。\n",
        f"来源链接：{content.get('url', '无')}",
        f"作者：{content.get('author', '未知')}",
    ]
    
    if content.get("title"):
        lines.append(f"\n## 原标题\n{content['title']}")
    
    if content.get("desc"):
        lines.append(f"\n## 原文内容\n{content['desc']}")
    
    if content.get("tags"):
        lines.append(f"\n## 标签\n{'、'.join(content['tags'])}")
    
    lines.append(f"\n\n请按照以下结构输出：")
    lines.append("- 来源信息（标题、作者、链接）")
    lines.append("- 核心要点（提取原文 3-5 个关键观点）")
    lines.append("- 内容整理（用自己的语言重新组织）")
    lines.append("- 💡 我的思考（你的理解和启发）")
    
    return "\n".join(lines)


def _fallback_format(content: dict) -> str:
    """当 API 不可用时的后备格式"""
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
        md.append("")
    
    md.append("---")
    md.append("")
    md.append("## 💡 我的思考")
    md.append("")
    md.append("> *此处等待 AI 仿写优化，设置 DEEPSEEK_API_KEY 环境变量后自动生成*")
    
    return "\n".join(md)
