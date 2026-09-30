---
name: ffmpeg-video-processing
description: 用 FFmpeg 裁剪、统一格式、合并短剧 clip、处理字幕和验证视频，保留原片并按指定顺序输出成片；在剪辑或批量视频格式处理时使用。
---

# 视频处理

## 目标与边界
只处理用户指定本地媒体；输出新文件。先探测流、时长、分辨率、帧率和音轨，再选 copy 或重编码，不盲拼不同规格视频。

## 输入与输出
输入按集／clip 排序的文件和目标规格。输出成片、新片段、命令记录和验收结果。

## 执行
1. 用 `ffmpeg-install` 找可用路径。先 ffprobe JSON；无 ffprobe 时用 FFmpeg 解码和日志辅助核对，不能称元数据已完整探测。
2. 脚本 `scripts/media.py` 默认打印 argv，`--execute` 执行，`--ffmpeg` 可指定路径：

```text
python <技能目录>/scripts/media.py normalize --input <视频> --output <新mp4> --width 720 --height 1280 --fps 24 --execute
python <技能目录>/scripts/media.py trim --input <视频> --output <新mp4> --start 2 --duration 5 --execute
python <技能目录>/scripts/media.py concat --input <片段1> <片段2> --output <新mp4> --execute
python <技能目录>/scripts/media.py check --input <成片> --execute
```

3. normalize 保持内容比例缩放并补边、统一 SAR、帧率、H.264/yuv420p 和 AAC；混合有声／无声素材时先补静音轨，再合并。concat 默认要求同规格，列表严格按传入顺序，不按字符串猜集号。
4. 精准 trim 重编码；`-c copy` 快裁可能停在关键帧，按用户是否要求逐帧精确决定。字幕／转场／横竖重构见 [进阶配方](references/recipes.md)。
5. 合成前检查接缝位置、轴线、音量、黑帧、字幕安全区；完成后完整解码、核对总时长和抽看每个连接点。

## 验收与恢复
脚本拒绝覆盖输出和以输入文件作输出；命令失败非零退出。失败产物可能存在，检查后写新路径再跑，不能自动覆盖用户文件。最终 approved 需观看，不仅工具退出成功。

## 来源与限制
依据 [技能合集](https://bytedance.larkoffice.com/wiki/BdgQwEQPHi0EXckhyiOcT8cnn4c) 的工具能力重建；[FFmpeg 官方文档](https://ffmpeg.org/ffmpeg.html) 为命令依据。
