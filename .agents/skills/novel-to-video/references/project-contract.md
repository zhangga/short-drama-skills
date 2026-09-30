# 制作目录与数据接口

脚本使用 Python 3.10+ 标准库。路径相对于作品根，ID 为制作编号。

```text
作品/
  project.json
  创作简报.md
  剧情大纲.md
  剧本.md
  assets.json
  ledger.json
  source/
  角色/ 场景/ 道具/
  单集制作/EP001/
    storyboard.json
    文字分镜.md
    视频_Clip001.prompt.txt
    视频_Clip001.mp4
  exports/
```

`project.json` 保存 `schema_version="1.0"`、标题、比例、画风、目标 clip 时长。目标时长是规划初值，实际取决于后端。故事范围、受众、集数、预算和选用后端由 Agent 补入，不能假称脚本已自动理解故事。

`assets.json`：每个资产含 `asset_id/kind/name/description/locked_traits/source_location/source_excerpt/status/path/version`，kind 为 character/scene/prop；新增设定写 `creative_additions`。status 使用 planned/generated/approved/rejected，approved 需实际审看。人物别名合并到同一 ID；换装保留角色 ID 并使用独立版本。

`storyboard.json`：

```json
{
  "schema_version": "1.0", "episode_id": "EP001",
  "clips": [{
    "clip_id": "Clip001", "duration_seconds": 15,
    "shots": [{
      "shot_id": "S001", "start": 0, "end": 5,
      "scene_id": "scene001", "character_ids": ["char001"], "prop_ids": [],
      "action": "她推开门，停在门槛外。", "dialogue": "", "camera": "中景，固定",
      "lighting": "右侧窗光", "sound": "门轴轻响", "continuity": "右手仍握钥匙"
    }, {
      "shot_id": "S002", "start": 5, "end": 15,
      "scene_id": "scene001", "character_ids": ["char001"], "prop_ids": [],
      "action": "她低头看钥匙，再抬头望向空房。", "dialogue": "谁进来过？",
      "camera": "从手部特写缓慢上摇至面部", "lighting": "沿用窗光",
      "sound": "远处脚步声", "continuity": "停在同一门槛，钥匙在右手"
    }]
  }]
}
```

对多段视频，每个 clip 内时间从 0 开始，首尾衔接；禁止间隙、重叠、超时、非有限数和重复 ID。镜头动作的可执行性仍须语义审核。

请求记录：`request_id/provider/model/prompt_file/reference_paths/duration/ratio/task_id/status/output_path/input_sha256`。不保存密钥，不把后端简称当模型 ID。提交前保存请求，返回后立刻登记 task_id；提交超时写 unknown。仅此检查点不能保证供应商层面的幂等，必须查询后再决定是否重试。

`project.py record` 哈希输入与输出；`status` 返回 stale（输入变化）、missing、changed 等问题。脚本不自动删下游或判定故事质量；Agent 结合依赖重新制作。ready/approved 等状态不能替代媒体解码与观看。
