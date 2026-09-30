# 进阶剪辑配方

先定位当前 FFmpeg 并查看帮助。以下是参数形状；实际传递时用 argv 数组和独立文件，不把 prompt／路径拼成待执行 shell 字符串。

- 字幕：`-vf subtitles=<字幕文件>`；检查 libass 支持、字体存在、Windows 盘符／特殊字符的滤镜转义。先做短样片，确认中文与 9:16 安全区。无法可靠转义时把字幕及字体复制到临时目录使用简单相对名。
- 无声视频补音：用 `-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000`，明确映射原视频和静音轨，`-c:v copy -c:a aac -shortest`。此时 -shortest 的作用是截无限静音，不是截用户对白。
- 合并异规格：先分别 normalize 成同尺寸／SAR／帧率／编码／采样率／声道并确保均有音轨，再 concat。仅使用 concat demuxer 不会自动解决不匹配。
- 转场：`xfade` 的 offset 是上一段实际时长减转场时长；音频配 `acrossfade`。总时长应减掉各转场重叠，不能照简单时长求和。
- 变速：视频 `setpts=PTS/<倍率>`，音频 `atempo=<倍率>`，检查当前滤镜范围。两条轨分别处理再校准。
- 外部音轨替换：两个 `-i` 后明确 `-map 0:v:0 -map 1:a:0 -c:v copy -c:a aac`；截尾由编辑要求决定。

concat 清单的路径按 FFmpeg 格式转义，不是 shell 引号。脚本处理空格、中文和单引号；换行路径拒绝。列表顺序就是成片顺序。

元数据参考：`ffprobe -v error -show_streams -show_format -of json <成片>`。对无 ffprobe 的环境，先用 `media.py check` 完整解码；仍需观看故事／声音和接缝，不能把解码成功称为全部质量合格。

官方依据：[命令](https://ffmpeg.org/ffmpeg.html)、[滤镜](https://ffmpeg.org/ffmpeg-filters.html)、[容器与 concat](https://ffmpeg.org/ffmpeg-formats.html)。
