# 笔记提取器 (Note Tool)

从抖音/小红书链接提取内容，用 AI 仿写为个人笔记。

## 安装依赖

```bash
pip install xhs requests
```

## 使用方法

```bash
# 提取小红书笔记并仿写
python3 note_tool.py https://www.xiaohongshu.com/explore/xxxxx

# 提取抖音视频并仿写
python3 note_tool.py https://www.douyin.com/video/xxxxx

# 自定义仿写风格
python3 note_tool.py https://www.xiaohongshu.com/explore/xxxxx --style "观点评论"

# 只提取原文，不仿写
python3 note_tool.py https://www.douyin.com/video/xxxxx --no-rewrite

# 使用快捷脚本
./note.sh https://www.xiaohongshu.com/explore/xxxxx
```

## 配置

需要设置 DeepSeek API 密钥（用于 AI 仿写）：

```bash
export DEEPSEEK_API_KEY="sk-your-key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
```

也可直接用 `note.sh` 脚本（已内置你的 API Key）。

## 目录结构

```
tools/note-tool/
├── note_tool.py          # 主程序
├── note.sh               # 快捷运行脚本
├── requirements.txt      # Python 依赖
├── extractors/
│   ├── xiaohongshu.py    # 小红书内容提取
│   └── douyin.py         # 抖音内容提取
├── rewriters/
│   └── deepseek.py       # DeepSeek AI 仿写
└── notes/                # 生成的笔记输出目录
```
