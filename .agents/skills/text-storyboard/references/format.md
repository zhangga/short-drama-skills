# 分镜字段

JSON 为 UTF-8，`schema_version` 为 `1.0`，包含 `episode_id` 和 `clips` 数组。每 clip 含 `clip_id/duration_seconds/shots`；每 shot 含 `shot_id/start/end/scene_id/character_ids/prop_ids/action/dialogue/camera/lighting/sound/continuity`。

资产文件为 `{"schema_version":"1.0","assets":[{"asset_id":"char001","kind":"character"},{"asset_id":"scene001","kind":"scene"}]}`，可加 description、locked_traits 等资料。

人可读表格建议：镜号、秒段、场景与人物、景别／运镜、动作、对白、灯光、声音、连续性。必要的镜前／镜后状态写在表格下。

示例时间轴：15 秒分三镜 0–4、4–10、10–15。最后一镜若要求停留 3 秒，它的时间预算必须至少 3 秒；不能在 14–15 秒再要求定格 3 秒。

`python <技能目录>/scripts/validate_storyboard.py storyboard.json --assets assets.json` 返回 JSON 报告与非零失败码。未提供 assets 时仅校验结构，不声称核实了资产引用。有限非负时间、连续覆盖、每镜正时长、全局唯一镜号、合法 asset 类型是硬约束。对白超过约每秒 5 个字符或镜头普遍短于 1 秒时给警告，不能把该估计当配音实测。
