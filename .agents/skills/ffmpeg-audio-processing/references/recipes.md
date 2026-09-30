# 响度与对白混音

两遍 loudnorm 使用相同目标参数和原始输入：

1. 测量：`-af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null -`。从 stderr 保存 input_i/input_tp/input_lra/input_thresh/target_offset。
2. 正式处理：`loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=<input_i>:measured_TP=<input_tp>:measured_LRA=<input_lra>:measured_thresh=<input_thresh>:offset=<target_offset>:linear=true:print_format=json`。输出 48kHz 轨。
3. 对结果再次测量，结合听感报告实际响度和 true peak；极端输入可能触发动态模式，不能保证 linear=true 一定生效。目标值根据实际发布要求调整。

先以对白为基准混音。BGM 需要淡入淡出时用 `afade`，起止点按实际时长计算。对白出现时需自动压低音乐，可试 sidechaincompress，先保留副本试听，避免把喘息或关键环境声压没。

降噪如 `afftdn` 仅在确认持续背景噪声时小幅使用。无法区分对白与音乐时，普通 FFmpeg 不能完成人声分离，应明确需要另一个分离模型。

官方依据：[loudnorm、amix、sidechaincompress](https://ffmpeg.org/ffmpeg-filters.html)。
