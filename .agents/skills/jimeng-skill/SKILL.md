---
name: jimeng-skill
description: 使用即梦 Dreamina CLI 生成图像、参考视频并查询已有任务；在用户选择即梦、dreamina 命令行或要恢复即梦排队任务时使用。
---

# 即梦 Dreamina CLI

## 目标与边界
对接当前本机 CLI 与登录态。即梦产品账号、会员、区域和模型权限独立于 Ark；不把另一个后端当静默替代品。

## 输入与输出
输入图像／视频 prompt 文件、已审参考资产、时长比例及用户选定模型。输出真实 CLI 请求、任务 ID、查询结果、媒体和对应元数据。

## 执行
1. 找命令：PowerShell `Get-Command dreamina`，其他环境 `command -v dreamina`。读取 `dreamina --help` 与要用子命令的 `--help`，按真实帮助选参数。
2. 未安装时从原文链接的 [即梦 CLI 体验指南](https://bytedance.larkoffice.com/wiki/FVTwwm0bGiishxkKOoScdHR2nsg) 核对官方安装入口和包名；读取可用权限，用户授权安装后执行。禁止猜一个同名 npm 包直接安装。
3. 登录沿用本机正常凭据；需要扫码时交给用户完成。权限／沙箱问题先检查账号、路径、执行边界；不能把“关闭沙箱”写成通用修复。
4. 当前 CLI 若提供 `multimodal2video`，先读其帮助。原文示例含 `--image/--prompt/--duration/--ratio/--model_version/--video_resolution`，仅作辨识线索，不保证当前版本仍一致。
5. prompt 从 UTF-8 文件读入变量；用数组或结构化调用传参，不拼接 shell 命令，不把正文中的反引号或 `$()` 当代码执行。人物、场景参考按明确编号映射。
6. 图像请求按实际生图子命令提交；视频请求按实际参考模式提交。保存 task_id，再用帮助里支持的查询命令恢复。没有该命令时记录手工交接方法，不编造 API。
7. 下载实际产物并做媒体与视觉验收；未完成任务保持 submitted/running，长排队结束本轮并给续做信息。用户要持续监控时再使用环境提供的自动化能力。

## 验收与恢复
保存精确模型、prompt、引用、参数、任务 ID 和输出位置。若 CLI 不可用，交付可审核 prompt 和请求清单并报告缺失依赖；不得虚报生成成功。重试先查询既有任务，避免重复扣费。

## 来源与限制
即梦工作流参考：[技能合集](https://bytedance.larkoffice.com/wiki/BdgQwEQPHi0EXckhyiOcT8cnn4c)。本套件交付时安装／登录／计费生成尚未实测；实际安装状态以本机检查为准。
