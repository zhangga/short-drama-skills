# 短剧创作 Skills 功能复刻

已按飞书《AI短剧漫剧创作 Skills 大合集》重建全部 **15 个 skills**，包含创作流程、配套脚本、原创接口示例和测试。原文未提供完整技能源码，因此这是功能复刻；增强内容和实现范围见 [评估报告](docs/流程评估.md)。

技能保存在本仓库的 `.agents/skills`，按项目使用，无需安装进全局技能目录。

## 开始使用

先克隆仓库：

```sh
git clone https://github.com/zhangga/short-drama-skills.git
cd short-drama-skills
```

在 Codex 中把本目录作为工作目录打开，再显式调用 `$novel-to-video` 或下表中的单项技能。Codex 支持从工作目录的 `.agents/skills` 加载项目技能；更新未显示时可重启。依据：[OpenAI 官方技能文档](https://developers.openai.com/codex/skills/)。

第一次可直接发：

```text
$novel-to-video 创作一部原创都市悬疑短剧，9:16、二维漫画风，先做1集60秒。
主角搬入新家，发现自己的备用钥匙出现在陌生邻居手里。
先完成故事、大纲、剧本、人物与场景设定、文字分镜和生成提示词；这次不调用付费后端。
作品保存在本目录 outputs/雨夜钥匙 下。
```

已有素材可指定阅读范围、总集数、目标时长和后端；已有项目可说“`$novel-to-video 继续 outputs/作品名，从账本里未完成的 clip 续做`”。推荐先验证一个 10–15 秒样片，再扩展整集。

## 15 个技能

| 技能 | 用途 | 实现与依赖 |
|---|---|---|
| [novel-to-video](.agents/skills/novel-to-video/SKILL.md) | 故事到短剧的总流程 | 创作／审核／编排；项目初始化与哈希账本脚本 |
| [character-design](.agents/skills/character-design/SKILL.md) | 人物卡与三视图 | Agent 创作提示词，实际出图走选定图像后端 |
| [text-storyboard](.agents/skills/text-storyboard/SKILL.md) | 时间轴文字分镜 | Agent 写镜头，脚本校验时序和资产引用 |
| [generate-film-video-prompt](.agents/skills/generate-film-video-prompt/SKILL.md) | clip 视频指令 | 保留人物映射、动作、摄影、光线与声音 |
| [generate-image-by-seedream](.agents/skills/generate-image-by-seedream/SKILL.md) | Ark Seedream 图片 | REST 请求打包与基础提交，需要 ARK_API_KEY／模型权限 |
| [generate-video-by-seedance](.agents/skills/generate-video-by-seedance/SKILL.md) | Ark Seedance 视频 | 异步创建与查询，需账号；视频下载由后续流程完成 |
| [jimeng-skill](.agents/skills/jimeng-skill/SKILL.md) | 即梦 Dreamina CLI | 使用真实 CLI 帮助适配；当前本机未安装／未实测 |
| [nano-banana-pro](.agents/skills/nano-banana-pro/SKILL.md) | Gemini 图像 | 基础 Interactions REST；需要 GEMINI_API_KEY／模型权限 |
| [novel-reader](.agents/skills/novel-reader/SKILL.md) | 超长小说阅读与资产抽取 | 字符分块／提交后推进进度；语义理解由 Agent 完成 |
| [storyboard-prompt-generator](.agents/skills/storyboard-prompt-generator/SKILL.md) | 静态分镜、首尾关键帧 | 图像提示词与构图／连续性检查 |
| [doc-to-txt](.agents/skills/doc-to-txt/SKILL.md) | 文档转 UTF-8 TXT | DOCX 标准库；PDF 需 pdftotext/pypdf；DOC 需 antiword/LibreOffice |
| [ffmpeg-install](.agents/skills/ffmpeg-install/SKILL.md) | 定位／配置 FFmpeg | doctor 只读检查；安装按真实系统环境处理 |
| [ffmpeg-video-processing](.agents/skills/ffmpeg-video-processing/SKILL.md) | 视频剪辑／合成 | FFmpeg 实际执行，默认预览参数 |
| [ffmpeg-audio-processing](.agents/skills/ffmpeg-audio-processing/SKILL.md) | 提音／混音／响度 | FFmpeg 实际执行及两遍测量配方 |
| [ffmpeg-image-processing](.agents/skills/ffmpeg-image-processing/SKILL.md) | 首尾帧／缩放／拼图 | FFmpeg 实际执行 |

## 本地验证与后端配置

脚本最低 Python 3.10，基础逻辑仅用标准库。系统上已有 imageio_ffmpeg 时可复用其 FFmpeg；不自动安装。测试中的图片检查用 Pillow，技能正常执行不强制 Pillow。

```powershell
python -m unittest discover -s tests -v
python .agents/skills/ffmpeg-install/scripts/doctor.py
python .agents/skills/text-storyboard/scripts/validate_storyboard.py examples/雨夜钥匙/storyboard.json --assets examples/雨夜钥匙/assets.json
```

生成脚本默认仅写离线请求，不需要凭据。为实际选定的账号配置 `ARK_API_KEY` 或 `GEMINI_API_KEY` 环境变量，并传入有权限的模型 ID；不要把密钥写入作品文件或聊天。当前模型／规格须参照技能里的官方链接核对，`--execute` 才会提交远程请求。

FFmpeg 可通过 `DRAMA_FFMPEG` 指定路径，ffprobe 独立通过 `DRAMA_FFPROBE` 指定。本机验证时 FFmpeg 可用、ffprobe 缺失；已实测完整解码与处理，尚未实测 ffprobe 元数据校验。

查看 [验证记录](docs/验证记录.md) 和 [原创示例](examples/雨夜钥匙/创作简报与剧本.md)。这些验证没有付费生成 AI 图片／视频，也没有创建实际成片。
