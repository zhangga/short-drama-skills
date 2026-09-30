"""Unicode-safe chunks; progress advances only after an extraction file exists."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, obj, replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if not replace:
        with path.open("x", encoding="utf-8") as f:
            f.write(text)
        return
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".progress-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def source_state(source, state):
    source = Path(source).resolve(strict=True)
    raw = source.read_bytes()
    text = raw.decode("utf-8-sig")
    fingerprint = digest(raw)
    data = load(state) if Path(state).exists() else {
        "schema_version": "1.0", "source": str(source), "source_sha256": fingerprint,
        "cursor": 0, "total_characters": len(text),
    }
    if data.get("source_sha256") != fingerprint or data.get("source") != str(source):
        raise ValueError("Source changed; use a new progress file")
    cursor = data.get("cursor")
    if type(cursor) is not int or not 0 <= cursor <= len(text):
        raise ValueError("Invalid cursor")
    return text, data


def next_chunk(source, state, out, size=3000, end=None):
    text, progress = source_state(source, state)
    if not 1 <= size <= 30000:
        raise ValueError("Chunk size must be 1..30000")
    limit = len(text) if end is None else end
    start = progress["cursor"]
    if not start <= limit <= len(text):
        raise ValueError("Read end must be between cursor and text length")
    finish = min(start + size, limit)
    chunk = {
        "schema_version": "1.0", "source": progress["source"],
        "source_sha256": progress["source_sha256"], "start": start, "end": finish,
        "range_end": limit, "complete": start == limit,
        "context_before": text[max(0, start - 200):start], "text": text[start:finish],
    }
    save(out, chunk)
    return {"start": start, "end": finish, "complete": chunk["complete"], "out": str(out)}


def commit(source, state, chunk_path, result_path):
    text, progress = source_state(source, state)
    chunk = load(chunk_path)
    result = load(result_path)
    if not isinstance(result, dict) or result.get("schema_version") != "1.0":
        raise ValueError("Extraction must be a schema_version 1.0 JSON object")
    start, end = chunk.get("start"), chunk.get("end")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
        raise ValueError("Invalid chunk interval")
    if (start != progress["cursor"] or chunk.get("source_sha256") != progress["source_sha256"]
            or chunk.get("source") != progress["source"] or chunk.get("text") != text[start:end]):
        raise ValueError("Chunk does not match source/current progress")
    progress["cursor"] = end
    progress["last_extraction"] = {
        "start": start, "end": end, "path": str(Path(result_path).resolve()),
        "sha256": digest(Path(result_path).read_bytes()),
    }
    save(state, progress, replace=True)
    return {"cursor": end, "total_characters": len(text)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    for command in ("next", "commit"):
        p = subs.add_parser(command)
        p.add_argument("--source", required=True)
        p.add_argument("--state", required=True)
        if command == "next":
            p.add_argument("--out", required=True)
            p.add_argument("--size", type=int, default=3000)
            p.add_argument("--end", type=int)
        else:
            p.add_argument("--chunk", required=True)
            p.add_argument("--result", required=True)
    args = parser.parse_args()
    try:
        answer = (next_chunk(args.source, args.state, args.out, args.size, args.end)
                  if args.command == "next" else commit(args.source, args.state, args.chunk, args.result))
        print(json.dumps(answer, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
