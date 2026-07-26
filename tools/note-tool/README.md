# 笔记提取器 (Note Tool)

从抖音/小红书链接提取内容，用 AI 仿写为个人笔记，支持一键保存到 Get笔记（得到大脑）。

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

# 提取 + 保存到 Get笔记（得到大脑）
python3 note_tool.py https://www.xiaohongshu.com/explore/xxxxx --save

# 列出 Get笔记 最近笔记
python3 note_tool.py --list-getnote

# 从 Get笔记 读取并仿写为视频口播稿
python3 note_tool.py --from-getnote <note_id> --style "视频口播稿"

# 从 Get笔记 读取 → 仿写 → 存回 Get笔记
python3 note_tool.py --from-getnote <note_id> --style "公众号文章" --save

# 使用快捷脚本
./note.sh https://www.xiaohongshu.com/explore/xxxxx
```

## 配置

### DeepSeek API（用于 AI 仿写）

```bash
export DEEPSEEK_API_KEY="sk-your-key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
```

### Get笔记（可选，用于 --save 功能）

已从 `~/.hermes/.env` 自动读取配置，无需额外设置。

对应环境变量：
```bash
GETNOTE_API_KEY=gk_live_xxx
GETNOTE_CLIENT_ID=cli_xxx
```

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
├── savers/
│   └── getnote.py        # Get笔记 API 保存
└── notes/                # 生成的笔记输出目录
```
