---
name: ffmpeg-image-processing
description: 用 FFmpeg 抽取短剧首尾帧、缩放裁剪或拼接参考图，准备媒体资产与连续性检查图；在确定性的图像格式处理或视频抽帧时使用。
---

# 图像处理／抽帧

## 目标与边界
处理像素、尺寸和帧，不承担角色重画或创意编辑。用户要增删人物／改风格等生成式编辑时，交给其选定的图像生成能力。

## 输入与输出
输入本地图片／视频、尺寸或帧要求；输出新图片和处理记录。

## 执行
1. 找 FFmpeg，核对图片格式、透明度和尺寸。保持比例；透明图尽量输出 PNG，转 JPEG 前由用户需求决定背景色。
2. `scripts/media.py` 默认打印 argv，`--execute` 真正执行：

```text
python <技能目录>/scripts/media.py first-frame --input <视频> --output <首帧png> --execute
python <技能目录>/scripts/media.py last-frame --input <视频> --output <尾帧png> --execute
python <技能目录>/scripts/media.py resize --input <图片> --output <新png> --width 720 --height 1280 --execute
python <技能目录>/scripts/media.py crop --input <图片> --output <新png> --x 0 --y 0 --width 300 --height 300 --execute
python <技能目录>/scripts/media.py sheet --input <图1> <图2> --output <拼图png> --height 300 --execute
```

3. last-frame 只在结尾约 3 秒解码并 reverse 取最后实际视频帧；不是估算时长后取可能为空的越界帧。不支持尾部 seek 的素材先按官方方案完整解码／探测后抽取。
4. resize 等比缩放补边；crop 核对主体与安全区；sheet 先统一图高再横排，适合审看对比，不将拼图替代单独人物参考。
5. 给文件语义命名并记录来源视频／帧位置。检查图片能解码、是否抽到黑场及是否保留关键道具。

## 验收与恢复
首尾帧必须对应实际素材；图片比例与用途匹配。输出路径已存在则停止；不改变原图，不把抽帧称作新生成画面。

## 来源与限制
依据 [技能合集](https://bytedance.larkoffice.com/wiki/BdgQwEQPHi0EXckhyiOcT8cnn4c) 的图像工具能力重建；[FFmpeg 官方文档](https://ffmpeg.org/ffmpeg.html) 为命令依据。
