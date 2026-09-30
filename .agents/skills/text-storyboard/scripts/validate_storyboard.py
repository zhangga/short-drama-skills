"""Validate structural timing and optional typed asset references, not story quality."""
import argparse
import json
import math
from pathlib import Path
import sys


def load(path):
    def reject(value):
        raise ValueError("Non-finite JSON constant: " + value)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=reject)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate(data, assets=None):
    errors, warnings = [], []
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        return {"ok": False, "errors": ["Expected schema_version 1.0 object"], "warnings": []}
    if not isinstance(data.get("episode_id"), str) or not data["episode_id"].strip():
        errors.append("Missing episode_id")
    known = None
    if assets is not None:
        if not isinstance(assets, dict) or assets.get("schema_version") != "1.0" or not isinstance(assets.get("assets"), list):
            errors.append("Invalid assets document")
            known = {}
        else:
            known = {}
            for asset in assets["assets"]:
                if not isinstance(asset, dict) or not isinstance(asset.get("asset_id"), str):
                    errors.append("Invalid asset entry")
                    continue
                aid = asset["asset_id"]
                if aid in known:
                    errors.append("Duplicate asset: " + aid)
                if asset.get("kind") not in ("character", "scene", "prop"):
                    errors.append("Invalid asset kind: " + aid)
                known[aid] = asset.get("kind")
    clips = data.get("clips")
    if not isinstance(clips, list) or not clips:
        return {"ok": False, "errors": errors + ["No clips"], "warnings": warnings}
    clip_ids, shot_ids = set(), set()
    for clip in clips:
        if not isinstance(clip, dict):
            errors.append("Clip must be object")
            continue
        cid = clip.get("clip_id")
        if not isinstance(cid, str) or not cid.strip() or cid in clip_ids:
            errors.append("Missing/duplicate clip_id")
        else:
            clip_ids.add(cid)
        duration = clip.get("duration_seconds")
        if not number(duration) or duration <= 0:
            errors.append("Invalid clip duration")
            continue
        shots = clip.get("shots")
        if not isinstance(shots, list) or not shots:
            errors.append("Clip has no shots")
            continue
        cursor = 0
        for shot in shots:
            if not isinstance(shot, dict):
                errors.append("Shot must be object")
                continue
            sid = shot.get("shot_id")
            if not isinstance(sid, str) or not sid.strip() or sid in shot_ids:
                errors.append("Missing/duplicate shot_id")
            else:
                shot_ids.add(sid)
            start, end = shot.get("start"), shot.get("end")
            if not number(start) or not number(end) or start < 0 or end <= start:
                errors.append("Invalid shot interval: " + str(sid))
                continue
            if abs(start - cursor) > 1e-6:
                errors.append("Gap/overlap: " + str(sid))
            if end > duration + 1e-6:
                errors.append("Shot exceeds clip duration: " + str(sid))
            cursor = end
            for field in ["action", "camera", "dialogue", "lighting", "sound", "continuity"]:
                if not isinstance(shot.get(field), str):
                    errors.append("Missing text field " + field + ": " + str(sid))
            if end - start < 1:
                warnings.append("Short shot; check achievable motion: " + str(sid))
            if len(str(shot.get("dialogue", ""))) > (end - start) * 5:
                warnings.append("Dialogue may need more time: " + str(sid))
            references = []
            scene = shot.get("scene_id")
            if not isinstance(scene, str) or not scene:
                errors.append("Missing scene_id: " + str(sid))
            else:
                references.append((scene, "scene"))
            for field, kind in [("character_ids", "character"), ("prop_ids", "prop")]:
                refs = shot.get(field)
                if not isinstance(refs, list) or any(not isinstance(x, str) for x in refs):
                    errors.append("Invalid " + field + ": " + str(sid))
                    continue
                if len(refs) != len(set(refs)):
                    errors.append("Repeated reference: " + str(sid))
                references.extend((ref, kind) for ref in refs)
            if known is not None:
                for ref, kind in references:
                    if known.get(ref) != kind:
                        errors.append("Unknown/wrong-kind asset: " + ref)
        if abs(cursor - duration) > 1e-6:
            errors.append("Final shot does not reach clip end: " + str(cid))
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "asset_references_checked": known is not None}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("storyboard")
    p.add_argument("--assets")
    args = p.parse_args()
    try:
        result = validate(load(args.storyboard), load(args.assets) if args.assets else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    except (OSError, ValueError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
