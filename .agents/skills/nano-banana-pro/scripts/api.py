"""Offline request packaging by default; --execute sends exactly one API request."""
import argparse
import base64
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

ENDPOINTS = {
    "seedream": "https://ark.cn-beijing.volces.com/api/v3/images/generations",
    "seedance": "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/interactions",
}


def image_type(raw):
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return "image/webp", ".webp"
    raise ValueError("Expected PNG/JPEG/WebP image bytes; decoding still requires media review")


def reference(path):
    raw = Path(path).read_bytes()
    mime, _ = image_type(raw)
    return mime, base64.b64encode(raw).decode("ascii")


def build(kind, model, prompt, references=(), size="2K", ratio="16:9", duration=15,
          resolution="720p", reference_role="reference_image", audio=False):
    if kind not in ENDPOINTS or not model.strip() or not prompt.strip():
        raise ValueError("kind, model and nonempty prompt are required")
    if ratio not in ("16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"):
        raise ValueError("Unsupported ratio")
    refs = [reference(path) for path in references]
    if kind == "seedream":
        payload = {"model": model, "prompt": prompt, "size": size, "response_format": "b64_json"}
        if refs:
            payload["image"] = ["data:" + mime + ";base64," + data for mime, data in refs]
    elif kind == "seedance":
        if type(duration) is not int or duration <= 0:
            raise ValueError("Positive integer duration required; verify model-specific limits")
        if reference_role not in ("reference_image", "first_frame", "last_frame"):
            raise ValueError("Invalid reference role")
        if reference_role != "reference_image" and len(refs) != 1:
            raise ValueError("This helper accepts exactly one first/last frame at a time")
        content = [{"type": "text", "text": prompt}]
        content.extend({"type": "image_url", "image_url": {"url": "data:" + mime + ";base64," + data},
                        "role": reference_role} for mime, data in refs)
        payload = {"model": model, "content": content, "duration": duration,
                   "ratio": ratio, "resolution": resolution, "generate_audio": bool(audio)}
    else:
        if ratio == "adaptive":
            raise ValueError("Gemini image requires a concrete aspect ratio")
        payload = {"model": model, "input": [{"type": "text", "text": prompt}] + [
            {"type": "image", "mime_type": mime, "data": data} for mime, data in refs],
            "response_format": {"type": "image", "aspect_ratio": ratio, "image_size": size}}
    return payload


def write_json(path, data):
    # Only used inside a newly reserved request folder; state is intentionally updated.
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def transmit(kind, payload=None, poll=None, timeout=120):
    key_name = "GEMINI_API_KEY" if kind == "gemini" else "ARK_API_KEY"
    key = os.environ.get(key_name)
    if not key:
        raise ValueError("Missing environment variable " + key_name)
    headers = {"Content-Type": "application/json"}
    headers["x-goog-api-key" if kind == "gemini" else "Authorization"] = key if kind == "gemini" else "Bearer " + key
    url = ENDPOINTS[kind]
    if poll:
        if kind != "seedance":
            raise ValueError("Polling is only implemented for Seedance")
        url += "/" + urllib.parse.quote(poll, safe="")
    raw = None if poll else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
    request = urllib.request.Request(url, data=raw, headers=headers, method="GET" if poll else "POST")
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def output_images(kind, response):
    if kind == "seedream":
        return [base64.b64decode(item["b64_json"], validate=True)
                for item in response.get("data", []) if item.get("b64_json")]
    if kind == "gemini":
        return [base64.b64decode(block["data"], validate=True)
                for step in response.get("steps", []) if step.get("type") == "model_output"
                for block in step.get("content", []) if block.get("type") == "image" and block.get("data")]
    return []


def execute_request(kind, payload, out, poll=None, transport=transmit):
    out = Path(out)
    key_name = "GEMINI_API_KEY" if kind == "gemini" else "ARK_API_KEY"
    if transport is transmit and not os.environ.get(key_name):
        write_json(out / "status.json", {"status": "blocked", "reason": "Missing " + key_name})
        raise ValueError("Missing " + key_name + "; offline request preserved")
    write_json(out / "status.json", {"status": "querying" if poll else "submitted", "task_id": poll})
    try:
        response = transport(kind, payload, poll)
        write_json(out / "response.json", response)
        if kind == "seedance":
            task = response.get("id") or poll
            if not task:
                raise ValueError("No task ID in Seedance response")
            state = {"status": response.get("status", "submitted"), "task_id": task,
                     "video_url": response.get("content", {}).get("video_url"),
                     "media_review": "pending"}
        else:
            images = output_images(kind, response)
            if not images:
                raise ValueError("No official image output; inspect saved response")
            names = []
            for index, raw in enumerate(images, 1):
                _, suffix = image_type(raw)
                name = "image_%03d" % index + suffix
                with (out / name).open("xb") as f:
                    f.write(raw)
                names.append(name)
            state = {"status": "succeeded", "images": names, "interaction_id": response.get("id"),
                     "media_review": "pending"}
        write_json(out / "status.json", state)
        return state
    except urllib.error.HTTPError as error:
        state = "failed" if 400 <= error.code < 500 and error.code != 408 else "unknown"
        write_json(out / "status.json", {"status": state, "http_status": error.code,
                                        "task_id": poll, "retry": "query/reconcile before new submission"})
        raise ValueError("API HTTP %s; details recorded without credentials" % error.code) from error
    except Exception as error:
        write_json(out / "status.json", {"status": "unknown", "task_id": poll,
                                        "reason": type(error).__name__, "retry": "inspect response/reconcile; do not auto-resubmit"})
        raise ValueError("Request outcome unknown; inspect saved status/response before retry") from error


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kind", choices=ENDPOINTS, required=True)
    p.add_argument("--model")
    p.add_argument("--prompt-file")
    p.add_argument("--reference", action="append", default=[])
    p.add_argument("--reference-role", default="reference_image")
    p.add_argument("--size", default="2K")
    p.add_argument("--ratio", default="16:9")
    p.add_argument("--duration", type=int, default=15)
    p.add_argument("--resolution", default="720p")
    p.add_argument("--audio", action="store_true")
    p.add_argument("--poll")
    p.add_argument("--out", required=True)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    try:
        if args.poll:
            if args.kind != "seedance":
                raise ValueError("--poll requires seedance")
            payload = None
        else:
            if not args.model or not args.prompt_file:
                raise ValueError("--model and --prompt-file required for creation")
            payload = build(args.kind, args.model, Path(args.prompt_file).read_text(encoding="utf-8-sig"),
                            args.reference, args.size, args.ratio, args.duration, args.resolution,
                            args.reference_role, args.audio)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=False)
        write_json(out / "request.json", {"schema_version": "1.0", "kind": args.kind,
                   "endpoint": ENDPOINTS[args.kind], "method": "GET" if args.poll else "POST",
                   "task_id": args.poll, "reference_paths": args.reference, "body": payload})
        write_json(out / "status.json", {"status": "planned", "network_called": False})
        if args.execute:
            result = execute_request(args.kind, payload, out, args.poll)
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(json.dumps({"out": str(out.resolve()), "status": "planned", "network_called": False}, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
