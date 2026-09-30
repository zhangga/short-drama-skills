---
name: ffmpeg-install
description: 检查或配置 Windows、macOS、Linux 的 FFmpeg/ffprobe，优先复用已有二进制并验证编解码能力；在短剧媒体处理缺少 FFmpeg 或命令找不到时使用。
---

# FFmpeg 环境

## 目标与边界
先定位工具，再决定是否安装。复用系统、项目或已安装 imageio-ffmpeg 提供的 FFmpeg；不为命令不在 PATH 就重复安装。

## 输入与输出
输入操作系统、用户指定工具路径和需处理的媒体。输出 FFmpeg/ffprobe 路径、版本、编解码能力、可运行检查及缺项。

## 执行
1. `python <技能目录>/scripts/doctor.py [--ffmpeg <绝对路径>]` 查 PATH、`DRAMA_FFMPEG` 环境变量、可用 imageio_ffmpeg；ffprobe 独立查 PATH／同目录／`DRAMA_FFPROBE`。
2. doctor 检查可执行性与版本。处理前按实际需求查看 `-encoders/-decoders/-filters`，如 libx264、AAC、subtitles、loudnorm；版本号不是能力完整的保证。
3. 缺 FFmpeg 时读取 [官方入口](https://ffmpeg.org/download.html)。Windows 选择官方页面列出的发行包或已配置 winget 源；macOS 可用现有 Homebrew，Linux 可用对应发行版包管理器。先确定包来源、目标目录和系统修改范围，再按用户已授权的安装范围操作。
4. 优先项目内显式二进制路径；需修改 PATH 时限定作用范围并验证新进程可见。安装失败保留诊断，不能反复下载陌生包。
5. 用临时合成媒体验证所需编码／滤镜，避免拿用户原片做破坏性测试。ffprobe 缺失时说明元数据校验限制，可先用 FFmpeg 完整解码验证。

## 验收与恢复
目标工具可运行，关键能力可用。Python imageio 的 FFmpeg 通常不附带 ffprobe，分别报告。doctor 不安装软件或改系统设置。

## 来源与限制
依据 [技能合集](https://bytedance.larkoffice.com/wiki/BdgQwEQPHi0EXckhyiOcT8cnn4c) 的跨平台环境技能重建，安装渠道以当前官方资料为准。
