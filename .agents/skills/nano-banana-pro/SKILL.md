---
name: nano-banana-pro
description: 使用 Google Gemini Nano Banana Pro 图像模型创作或编辑短剧视觉资产和多参考图；在用户指定 Nano Banana Pro/Gemini 3 Pro Image 时使用。
---

# Nano Banana Pro

## 目标与边界
调用用户选定的 Gemini 图像模型，不因为名称相似擅自切换到 Nano Banana 2 或其他供应商。角色和构图创意先由对应技能明确。

## 输入与输出
输入 prompt、实际 Gemini 模型 ID、比例、分辨率和可选本地参考图。依赖 `GEMINI_API_KEY` 环境变量；基础脚本走官方 Interactions REST，输出请求、状态和生成图。

## 执行
1. 核对 [官方图像指南](https://ai.google.dev/gemini-api/docs/image-generation) 与当前账号支持的模型标识；原文模型称呼不能替代实际 model ID。参考数量、分辨率和编辑能力服从模型当前限制。
2. 图像编辑先审看参考文件。列出每张图用途以及需要保留／更改的特征；多参考时说明谁是人物、谁是场景。
3. 使用 `scripts/api.py` 离线打包，不需 API key：

```text
python <技能目录>/scripts/api.py --kind gemini --model <实际模型ID> --prompt-file <prompt.txt> --ratio 16:9 --size 2K --out <新请求目录> [--reference <本地图> ...]
```

4. 在用户授权此后端生成的范围内加 `--execute`。参考图按 base64 与 MIME 放入 input；response_format 选择 image。不要把文字响应当图像，忽略 thought 中间图，仅保存 model_output 的正式图像。
5. 记录 interaction ID、模型、参数、图片来源和版本；每张产物审看后批准。多轮编辑需保留 previous_interaction_id 及实际历史；基础脚本是单轮，不伪称实现了历史编辑。

## 验收与恢复
无图像、被拦截或未知响应要明确失败，不输出假图片。超时不自动重发。已生成图的固有标记按服务规则保留，不承诺所有产物无水印。

## 来源与限制
Gemini 图像工作流参考：[技能合集](https://bytedance.larkoffice.com/wiki/BdgQwEQPHi0EXckhyiOcT8cnn4c)。脚本未做付费线上实测。
