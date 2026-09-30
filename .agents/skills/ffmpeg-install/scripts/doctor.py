"""Read-only FFmpeg/ffprobe discovery; does not install or alter PATH."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def discover(explicit=None):
    ffmpeg = explicit or os.environ.get("DRAMA_FFMPEG") or shutil.which("ffmpeg")
    if not ffmpeg:
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
    ffprobe = os.environ.get("DRAMA_FFPROBE") or shutil.which("ffprobe")
    if ffmpeg and not ffprobe:
        candidate = Path(ffmpeg).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if candidate.is_file():
            ffprobe = str(candidate)
    result = {}
    for name, path in [("ffmpeg", ffmpeg), ("ffprobe", ffprobe)]:
        if not path:
            result[name] = {"available": False}
            continue
        process = subprocess.run([str(path), "-version"], capture_output=True, text=True, timeout=15)
        result[name] = {"available": process.returncode == 0, "path": str(Path(path).resolve()),
                        "version": process.stdout.splitlines()[0] if process.stdout else process.stderr[:200]}
    result["installed_or_settings_changed"] = False
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ffmpeg")
    args = p.parse_args()
    try:
        result = discover(args.ffmpeg)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ffmpeg"]["available"] else 1
    except (OSError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
