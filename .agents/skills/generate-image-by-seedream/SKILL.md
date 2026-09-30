---
name: generate-image-by-seedream
description: 通过火山方舟 Ark 的 Seedream 图片 API 生成或编辑短剧人物、场景和道具图；在用户指定 Seedream/Ark 生图或需要对接该后端时使用。
---

# Seedream 生图／编辑

## 目标与边界
使用用户有权限调用的模型和账号。保留请求与结果；不把 Seedream、即梦 CLI 或其他图像服务混为同一个接口。

## 输入与输出
输入 prompt 文件、实际模型 ID／接入点 ID、尺寸、可选本地参考图与输出目录。依赖 `ARK_API_KEY` 环境变量；Python 3.10+ 标准库即可。输出请求包，执行后输出图片和状态文件。

## 执行
1. 当前接口见 [官方图片 API](https://docs.volcengine.com/docs/ark/image-generation-api?lang=en)。先确认选定模型的尺寸、参考数量和可用参数；模型排序沿用用户选择，不硬编码原文的个人偏好。
2. `scripts/api.py` 默认只打包离线请求。`--model` 必填；参考图编码为 data URI；响应选 b64_json，避免图像下载地址过期。打包命令：

```text
python <技能目录>/scripts/api.py --kind seedream --model <模型ID> --prompt-file <prompt.txt> --size 2K --out <新请求目录> [--reference <本地图> ...]
```

3. 用户已要求此后端生成且计费范围明确时，加 `--execute` 真正提交；只要求制作技能或提示词时不执行。脚本执行前保存 submitted 状态，失败不自动重新 POST。
4. 检查状态文件与实际媒体。比较画风、人物锁定特征、三视图布局／场景空间，审看通过后登记项目资产。脚本下载成功仍只是 generated。

## 验收与恢复
图片能解码、比例尺寸正确、参考目标没有混淆。脚本响应解析失败、超时等写 unknown 或 failed，保留请求；不要因没有本地图片就盲目重复计费。无凭据时离线打包仍可完成，清楚说明未调用后端。

## 来源与限制
Seedream 工作流参考：[技能合集](https://bytedance.larkoffice.com/wiki/BdgQwEQPHi0EXckhyiOcT8cnn4c)，接口按官方资料核对。脚本支持基础文生图／多参考编辑；流式、图层等高级功能不在当前脚本范围内。
