"""Local FFmpeg operations: preview argv by default, execute without a shell."""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

OPERATIONS = ["normalize", "trim", "concat", "check", "extract-audio", "audio-trim",
              "loudness", "mix", "first-frame", "last-frame", "resize", "crop", "sheet"]


def find_ffmpeg(explicit=None):
    path = explicit or os.environ.get("DRAMA_FFMPEG") or shutil.which("ffmpeg")
    if not path:
        try:
            import imageio_ffmpeg
            path = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError as error:
            raise ValueError("FFmpeg unavailable; use ffmpeg-install") from error
    resolved = Path(path).resolve(strict=True)
    if not resolved.is_file():
        raise ValueError("FFmpeg path is not a file")
    return str(resolved)


def input_paths(inputs):
    result = []
    for value in inputs:
        path = Path(value).resolve(strict=True)
        if not path.is_file() or "\n" in str(path) or "\r" in str(path):
            raise ValueError("Input must be a local file with a valid filename")
        result.append(str(path))
    return result


def concat_manifest(paths):
    return "ffconcat version 1.0\n" + "".join(
        "file '" + Path(path).as_posix().replace("'", "'\\''") + "'\n" for path in paths)


def build(args, playlist="<temporary-ffconcat>"):
    inputs = input_paths(args.input)
    multi = args.operation in ("concat", "mix", "sheet")
    if (not multi and len(inputs) != 1) or (multi and len(inputs) < 2) or (args.operation == "mix" and len(inputs) != 2):
        raise ValueError("Incorrect number of input files")
    out = None
    if args.operation != "check":
        if not args.output:
            raise ValueError("--output required")
        out = str(Path(args.output).resolve())
        if Path(out).exists() or out in inputs:
            raise FileExistsError("Output exists or is an input; choose a new path")
    for value in (args.width, args.height, args.fps):
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Dimensions and fps must be positive")
    if not math.isfinite(args.start) or args.start < 0 or not math.isfinite(args.duration) or args.duration <= 0:
        raise ValueError("Invalid trim timing")
    if args.x < 0 or args.y < 0:
        raise ValueError("Crop coordinates must be nonnegative")
    command = [find_ffmpeg(args.ffmpeg), "-hide_banner", "-loglevel", "error", "-nostdin", "-n"]
    op = args.operation
    if op == "concat":
        command += ["-f", "concat", "-safe", "0", "-i", playlist, "-map", "0:v:0", "-map", "0:a?", "-c", "copy", "-movflags", "+faststart"]
    elif op == "last-frame":
        command += ["-sseof", "-3", "-i", inputs[0], "-an", "-vf", "reverse", "-frames:v", "1"]
    else:
        for path in inputs:
            command += ["-i", path]
        if op == "check":
            command += ["-v", "error", "-xerror", "-map", "0:v?", "-map", "0:a?", "-f", "null", "-"]
        elif op == "normalize":
            if args.width % 2 or args.height % 2:
                raise ValueError("H.264 dimensions must be even")
            vf = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=%s"
                  % (args.width, args.height, args.width, args.height, args.fps))
            command += ["-map", "0:v:0", "-map", "0:a?", "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-movflags", "+faststart"]
        elif op in ("trim", "audio-trim"):
            command += ["-ss", str(args.start), "-t", str(args.duration)]
            if op == "trim":
                command += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart"]
            else:
                command += ["-vn", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
        elif op == "extract-audio":
            command += ["-vn", "-map", "0:a:0", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
        elif op == "loudness":
            command += ["-vn", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
        elif op == "mix":
            command += ["-filter_complex", "[1:a]volume=0.2[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[out]",
                        "-map", "[out]", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
        elif op == "first-frame":
            command += ["-an", "-frames:v", "1"]
        elif op == "resize":
            command += ["-vf", "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2"
                        % (args.width, args.height, args.width, args.height), "-frames:v", "1"]
        elif op == "crop":
            command += ["-vf", "crop=%d:%d:%d:%d" % (args.width, args.height, args.x, args.y), "-frames:v", "1"]
        elif op == "sheet":
            filters = ["[%d:v]scale=-1:%d,setsar=1[v%d]" % (i, args.height, i) for i in range(len(inputs))]
            filters.append("".join("[v%d]" % i for i in range(len(inputs))) + "hstack=inputs=%d[out]" % len(inputs))
            command += ["-filter_complex", ";".join(filters), "-map", "[out]", "-frames:v", "1"]
    if out:
        command.append(out)
    return command, inputs, out


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="operation", required=True)
    for op in OPERATIONS:
        q = sub.add_parser(op)
        q.add_argument("--input", nargs="+", required=True)
        q.add_argument("--output")
        q.add_argument("--ffmpeg")
        q.add_argument("--width", type=int, default=720)
        q.add_argument("--height", type=int, default=1280)
        q.add_argument("--fps", type=float, default=24)
        q.add_argument("--start", type=float, default=0)
        q.add_argument("--duration", type=float, default=5)
        q.add_argument("--x", type=int, default=0)
        q.add_argument("--y", type=int, default=0)
        q.add_argument("--execute", action="store_true")
    return p


def run(args):
    command, inputs, output = build(args)
    if not args.execute:
        result = {"executed": False, "argv": command}
        if args.operation == "concat":
            result["playlist_content"] = concat_manifest(inputs)
        return result
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drama-media-") as work:
        if args.operation == "concat":
            playlist = Path(work) / "input.ffconcat"
            playlist.write_text(concat_manifest(inputs), encoding="utf-8")
            command, inputs, output = build(args, str(playlist))
        process = subprocess.run(command, capture_output=True, text=True, errors="replace")
        if process.returncode:
            raise ValueError("FFmpeg failed (%d): %s" % (process.returncode, process.stderr[-2500:]))
    if output and (not Path(output).is_file() or not Path(output).stat().st_size):
        raise ValueError("FFmpeg returned without a nonempty output")
    return {"executed": True, "output": output, "inputs": inputs, "requires_visual_audio_review": True}


def main():
    try:
        print(json.dumps(run(parser().parse_args()), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
