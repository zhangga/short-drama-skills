"""Local production ledger. Approval is a recorded human/Agent review decision."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

STATES = ["planned", "submitted", "unknown", "succeeded", "approved", "rejected", "failed"]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, data):
    path = Path(path)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".ledger-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def file_info(root, value):
    path = Path(value)
    path = (path if path.is_absolute() else root / path).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Asset path must be a file within the project root")
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def initialize(root, title, ratio, style):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    for directory in ["source", "角色", "场景", "道具", "单集制作/EP001", "exports"]:
        (root / directory).mkdir(parents=True)
    write(root / "project.json", {"schema_version": "1.0", "title": title,
          "ratio": ratio, "style": style, "target_clip_seconds": 15, "episodes": ["EP001"]})
    write(root / "assets.json", {"schema_version": "1.0", "assets": []})
    write(root / "ledger.json", {"schema_version": "1.0", "tasks": {}, "history": []})
    return {"root": str(root), "initialized": True}


def record(root, task, status, inputs, output=None, task_id=None):
    root = Path(root).resolve(strict=True)
    if status not in STATES or not task.strip():
        raise ValueError("Invalid task/status")
    entry = {"status": status, "inputs": [file_info(root, p) for p in inputs]}
    if output:
        entry["output"] = file_info(root, output)
    elif status in ("succeeded", "approved"):
        raise ValueError("succeeded/approved requires an actual output file")
    if task_id:
        entry["task_id"] = task_id
    ledger = read(root / "ledger.json")
    if task in ledger["tasks"]:
        ledger["history"].append({"id": task, **ledger["tasks"][task]})
    ledger["tasks"][task] = entry
    write(root / "ledger.json", ledger)
    return {"id": task, **entry}


def status(root):
    root = Path(root).resolve(strict=True)
    ledger = read(root / "ledger.json")
    report = []
    for task, entry in ledger["tasks"].items():
        problems = []
        for item in entry.get("inputs", []):
            try:
                if file_info(root, item["path"])["sha256"] != item["sha256"]:
                    problems.append("stale input: " + item["path"])
            except (OSError, ValueError):
                problems.append("missing/invalid input: " + item["path"])
        output = entry.get("output")
        if output:
            try:
                if file_info(root, output["path"])["sha256"] != output["sha256"]:
                    problems.append("changed output: " + output["path"])
            except (OSError, ValueError):
                problems.append("missing/invalid output: " + output["path"])
        report.append({"id": task, "status": entry["status"], "task_id": entry.get("task_id"), "problems": problems})
    return {"tasks": report}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("init")
    a.add_argument("--root", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--ratio", default="9:16")
    a.add_argument("--style", required=True)
    a = sub.add_parser("status")
    a.add_argument("--root", required=True)
    a = sub.add_parser("record")
    a.add_argument("--root", required=True)
    a.add_argument("--id", required=True)
    a.add_argument("--status", choices=STATES, required=True)
    a.add_argument("--inputs", nargs="*", default=[])
    a.add_argument("--output")
    a.add_argument("--task-id")
    args = p.parse_args()
    try:
        if args.command == "init":
            data = initialize(args.root, args.title, args.ratio, args.style)
        elif args.command == "record":
            data = record(args.root, args.id, args.status, args.inputs, args.output, args.task_id)
        else:
            data = status(args.root)
        print(json.dumps(data, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
