---
name: generate-video-by-seedance
description: 通过火山方舟 Ark Seedance API 创建视频任务、查询状态并取得生成视频；在用户指定 Seedance/Ark 生视频或恢复已有该后端任务时使用。
---

# Seedance 视频任务

## 目标与边界
把生成视为异步任务。创建、查询、下载和媒体审核分别记录；生成请求 ID 不等于视频完成。

## 输入与输出
输入 prompt 文件、用户可用的实际模型 ID、时长比例和参考文件。`ARK_API_KEY` 从环境读取；输出离线请求包，执行后保存供应商 task_id／状态。基础脚本支持文生视频和图片参考；视频／音频参考与高级编辑按当前官方说明组装。

## 执行
1. 读 [创建 API](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh&redirect=1)，核对选定模型支持的时长、分辨率、参考模式和音频能力。不要把产品 UI、不同代模型或即梦的能力直接套到 Ark。
2. `scripts/api.py` 离线打包：

```text
python <技能目录>/scripts/api.py --kind seedance --model <模型ID> --prompt-file <prompt.txt> --duration 15 --ratio 9:16 --resolution 720p --out <新请求目录> [--reference <本地图> ...] [--reference-role reference_image] [--audio]
```

3. reference-role 可为 reference_image/first_frame/last_frame；基础脚本为所有图片设置同一种 role，需要首尾混合时依官方文档分别组装 content，不能把两张图都标 first_frame。检查后端是否支持对应模式。
4. 用户授权该后端生成后加 `--execute`。创建前保存请求，返回 task_id 后立刻保存。若提交超时，标 unknown 并核查供应商记录，不自动重发。
5. 查询只做 GET：`api.py --kind seedance --poll <任务ID> --out <新查询目录> --execute`。一次查询后保存状态；排队长时给任务 ID 与续做方式，不长时间无上限轮询。默认查询不会再次创建任务。
6. 成功后从响应的 `content.video_url` 获取视频，及时保存至作品目录。可用现有下载工具；下载地址仅来自刚查询的任务，不能把无关网页链接当产物。用 FFmpeg 解码／ffprobe 核对实际时长，再观看动作、空间、声音和接缝。

## 验收与恢复
failed/canceled/expired 为终态；succeeded 后仍须下载和观看，批准后才纳入剪辑。缺凭据时交付请求包。选择其他后端需说明切换，不能把手工视频冒称 Seedance 结果。

## 来源与限制
Seedance 工作流参考：[技能合集](https://bytedance.larkoffice.com/wiki/BdgQwEQPHi0EXckhyiOcT8cnn4c)。基础 REST 适配未进行付费线上实测，模型限制需每次使用时核对。
