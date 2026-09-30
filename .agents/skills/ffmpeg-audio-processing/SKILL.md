---
name: ffmpeg-audio-processing
description: 用 FFmpeg 提取、裁剪、响度处理或混合配音与配乐，检查短剧音轨和同步；在配音、背景音乐或音量整理时使用。
---

# 音频处理

## 目标与边界
保留原音。先了解用户希望保留对白、环境声、音乐的关系，再处理，避免音效被当噪声删掉。

## 输入与输出
输入音视频和目标音轨规格，输出新音频／混合轨以及响度与同步检查。

## 执行
1. 检查是否有音轨、采样率、声道、时长和峰值；输出新文件。`scripts/media.py` 默认预览 argv，`--execute` 执行：

```text
python <技能目录>/scripts/media.py extract-audio --input <视频> --output <新wav> --execute
python <技能目录>/scripts/media.py audio-trim --input <音频> --output <新wav> --start 0 --duration 5 --execute
python <技能目录>/scripts/media.py loudness --input <音频> --output <新wav> --execute
python <技能目录>/scripts/media.py mix --input <对白wav> <配乐wav> --output <混合wav> --execute
```

2. extract-audio 输出 48kHz 双声道 PCM；mix 以第一轨时长为准，默认配乐音量 0.2，不能把默认比例当所有片子的最终混音。
3. loudness 为单遍快速预览，使用目标 I=-16 LUFS/TP=-1.5dB/LRA=11；交付需要稳定响度时按 [两遍测量](references/recipes.md) 回填实测参数，不宣称单遍结果是实测达标。
4. 按对白理解度听音，必要时降低配乐、做淡入淡出或侧链压低。降噪先试听；没有声纹／配音授权时不擅自克隆音色。
5. 与视频合轨前校准起点、时长和口型；用户未要求截尾时不要仅靠 -shortest 截掉重要对白。

## 验收与恢复
完整解码；听开头、高潮、接缝和结尾，检查无爆音、削波、声道反相及对白被淹没。保留未处理轨便于重新混音。

## 来源与限制
依据 [技能合集](https://bytedance.larkoffice.com/wiki/BdgQwEQPHi0EXckhyiOcT8cnn4c) 的音频工具能力重建；[滤镜文档](https://ffmpeg.org/ffmpeg-filters.html) 为参数依据。本技能不直接生成 TTS。
