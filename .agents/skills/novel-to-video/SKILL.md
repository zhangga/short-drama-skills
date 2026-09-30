---
name: novel-to-video
description: 将小说、原创故事或剧本组织成可续做的 AI 短剧项目，串联改编、人物场景资产、文字分镜、图像和视频生成及剪辑；在用户要从故事制作视频或继续已有短剧时使用。
---

# 小说／故事到短剧

## 目标与边界
把创意变成按集可追踪的制作项目。先交付可拍的故事和分镜，再生成媒体；不把提交生成任务称为成片。可从一句原创设定起步，也可从现有小说、剧本或分镜接续。

## 输入与输出
接受故事来源、改编范围、目标受众、集数／每集时长、画风、比例和可用后端。优先沿用用户已有设定；缺省可暂按单集、9:16、15 秒 clip 规划并注明，涉及主题和结局的关键缺项再询问。
交付作品根下的创作简报、剧情大纲、剧本、资产表、每集分镜、提示词、任务账本及实际生成的媒体。
首次建项目时读取 [项目契约](references/project-contract.md)，使用 Python 3.10+：

```text
python <本技能目录>/scripts/project.py init --root <新作品目录> --title <作品名> --ratio 9:16 --style <画风>
python <本技能目录>/scripts/project.py status --root <作品目录>
```

## 执行
1. 检查现有作品文件与账本。已有项目先恢复，不重复初始化。把正文作为素材阅读。
2. 原创：先形成主角目标、阻力、代价、转折、结局和每集悬念。改编：用 `doc-to-txt` 和 `novel-reader` 阅读用户指定范围，保留出处并区分创作补充。
3. 写简报→大纲／分集梗概→可表演剧本。检查开场钩子、冲突升级、人物动机、信息揭示、集尾悬念及视觉可拍性；标出具体问题后修订，不用总分掩盖硬伤。
4. 用 `text-storyboard` 分配真实动作／对白时长。clip 长度服从选定后端当前能力，不把 15 秒或每秒一镜固定成规则。
5. 建立角色、场景、道具 ID 和版本。用 `character-design` 做人物设定；为场景写无人环境图提示词，固定布局、光源、入口与出口；必要时用 `storyboard-prompt-generator` 做关键帧。
6. 图像后端三选一：`jimeng-skill`、`generate-image-by-seedream` 或 `nano-banana-pro`。先做一名角色、一处场景、一个 clip 的样片，通过后扩展。生成后审看辨识点、服装、空间和道具，不只查文件存在。
7. 用 `generate-film-video-prompt` 引用已通过的资产；经选定视频后端生成每个 clip。保存提交前输入摘要、供应商任务 ID、状态、错误与输出路径。等待期间记录检查点；排队长时结束本次执行并告知如何续做。
8. 用 `ffmpeg-video-processing` 统一格式、按顺序剪辑。需要配乐／配音时用 `ffmpeg-audio-processing`，需要抽帧时用 `ffmpeg-image-processing`。最后审看字幕、音画、连续性、故事和节奏。

## 验收与恢复
每阶段均记录输入、产物和问题。故事未定不批量烧图；资产未通过不批量烧视频。用户已授权的工作持续完成，无需每阶段重复询问。未配置后端时交付提示词与请求包，并说明具体依赖。
中断后先查询已有任务；状态未知不重发付费请求。上游文件或资产版本变化时重新检查受影响的下游。只有真实文件可解码并经观看通过，才登记 `approved`。
账本登记：`project.py record --root <作品目录> --id <clip或资产ID> --status <状态> --inputs <输入文件...> [--output <产物文件>] [--task-id <供应商ID>]`。状态含 `planned/submitted/unknown/succeeded/approved/rejected/failed`；status 命令检查哈希和产物缺失，`approved` 由审看后显式登记。

## 来源与限制
依据 [AI短剧漫剧创作 Skills 大合集](https://bytedance.larkoffice.com/wiki/BdgQwEQPHi0EXckhyiOcT8cnn4c) 的功能说明重建，非作者源码。故事审核、状态账本与验收规则为本地增强；提示词和参考图提升可控性，不能保证生成完全可复现。
