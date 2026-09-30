"""Offline behavioral tests. API transports are mocked; FFmpeg uses synthetic media."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import wave
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"


def module(skill, filename):
    name = skill.replace("-", "_") + "_" + filename.replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, SKILLS / skill / "scripts" / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


chunks = module("novel-reader", "read_chunks.py")
project = module("novel-to-video", "project.py")
storyboard = module("text-storyboard", "validate_storyboard.py")
convert = module("doc-to-txt", "convert.py")
api = module("generate-image-by-seedream", "api.py")
media = module("ffmpeg-video-processing", "media.py")


class ReadingTests(unittest.TestCase):
    def test_chunks_complete_chinese_and_commit_only_after_result(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            source, state = root / "小说.txt", root / "progress.json"
            original = ("小雨握住钥匙。\r\n🙂" * 400) + "结尾"
            source.write_bytes(original.encode("utf-8-sig"))
            parts = []
            for i in range(100):
                chunk = root / ("chunk%d.json" % i)
                chunks.next_chunk(source, state, chunk, size=3000)
                data = chunks.load(chunk)
                if data["complete"]:
                    break
                if i == 0:
                    self.assertFalse(state.exists())
                    with self.assertRaises(FileNotFoundError):
                        chunks.commit(source, state, chunk, root / "missing.json")
                    self.assertFalse(state.exists())
                result = root / ("result%d.json" % i)
                result.write_text('{"schema_version":"1.0","assets":[]}', encoding="utf-8")
                chunks.commit(source, state, chunk, result)
                parts.append(data["text"])
                with self.assertRaises(ValueError):
                    chunks.commit(source, state, chunk, result)
            self.assertEqual("".join(parts), original)
            self.assertEqual(chunks.load(state)["cursor"], len(original))
            source.write_text("新版本", encoding="utf-8")
            with self.assertRaises(ValueError):
                chunks.next_chunk(source, state, root / "changed.json")

    def test_read_range(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / "s.txt").write_text("一二三四五", encoding="utf-8")
            chunks.next_chunk(root / "s.txt", root / "p.json", root / "c.json", end=2)
            self.assertEqual(chunks.load(root / "c.json")["text"], "一二")


class LedgerTests(unittest.TestCase):
    def test_output_required_stale_hash_and_no_project_overwrite(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work) / "作品"
            project.initialize(root, "钥匙", "9:16", "漫画")
            with self.assertRaises(FileExistsError):
                project.initialize(root, "覆盖", "9:16", "漫画")
            (root / "input.txt").write_text("初稿", encoding="utf-8")
            with self.assertRaises(ValueError):
                project.record(root, "Clip001", "approved", ["input.txt"])
            (root / "output.txt").write_text("产物", encoding="utf-8")
            project.record(root, "Clip001", "submitted", ["input.txt"], task_id="fake-test-id")
            project.record(root, "Clip001", "approved", ["input.txt"], "output.txt")
            self.assertFalse(project.status(root)["tasks"][0]["problems"])
            (root / "input.txt").write_text("修订稿", encoding="utf-8")
            self.assertTrue(project.status(root)["tasks"][0]["problems"])
            outside = Path(work) / "outside.txt"
            outside.write_text("outside")
            with self.assertRaises(ValueError):
                project.file_info(root, outside)


class StoryboardTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples" / "雨夜钥匙" / "storyboard.json").read_text(encoding="utf-8"))
        self.assets = json.loads((ROOT / "examples" / "雨夜钥匙" / "assets.json").read_text(encoding="utf-8"))

    def test_valid_and_failure_modes(self):
        self.assertTrue(storyboard.validate(self.data, self.assets)["ok"])
        mutations = [
            ("start", 1), ("end", -1), ("end", float("nan")), ("end", True),
            ("scene_id", "unknown"), ("character_ids", ["scene001"]), ("action", None),
        ]
        for field, value in mutations:
            bad = copy.deepcopy(self.data)
            bad["clips"][0]["shots"][0][field] = value
            self.assertFalse(storyboard.validate(bad, self.assets)["ok"], field)
        bad = copy.deepcopy(self.data)
        bad["clips"][0]["shots"][1]["shot_id"] = bad["clips"][0]["shots"][0]["shot_id"]
        self.assertFalse(storyboard.validate(bad)["ok"])


class ConversionTests(unittest.TestCase):
    def test_docx_paragraph_table_order_and_output_protection(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            source = root / "剧本.docx"
            xml = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
            <w:p><w:r><w:t>开场中文</w:t></w:r></w:p>
            <w:tbl><w:tr><w:tc><w:p><w:r><w:t>表格对白</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
            <w:p><w:r><w:t>结尾</w:t></w:r></w:p></w:body></w:document>'''
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("word/document.xml", xml)
            out = root / "new.txt"
            convert.convert(source, out)
            self.assertEqual(out.read_text(encoding="utf-8"), "开场中文\n表格对白\n结尾")
            with self.assertRaises(FileExistsError):
                convert.convert(source, out)
            self.assertTrue(source.exists())

    def test_invalid_encoding_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as work:
            source = Path(work) / "gb.txt"
            source.write_bytes("中文".encode("gb18030"))
            with self.assertRaises(UnicodeDecodeError):
                convert.extract(source)
            self.assertEqual(convert.extract(source, "gb18030")[0], "中文")


class APITests(unittest.TestCase):
    def test_payloads_and_poll_are_distinct(self):
        self.assertEqual(api.build("seedream", "selected-model", "画角色")["response_format"], "b64_json")
        seedance = api.build("seedance", "selected-model", "推门", duration=5)
        self.assertEqual(seedance["content"][0]["text"], "推门")
        self.assertEqual(api.build("gemini", "selected-model", "画角色")["response_format"]["type"], "image")
        with self.assertRaises(ValueError):
            api.build("seedance", "model", "动作", duration=0)

    def test_no_auto_retry_on_timeout_and_task_id_persistence(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            calls = []
            def failed(*args):
                calls.append(args)
                raise TimeoutError("mock transport timeout")
            with self.assertRaises(ValueError):
                api.execute_request("seedance", {"model": "mock"}, root, transport=failed)
            self.assertEqual(len(calls), 1)
            self.assertEqual(json.loads((root / "status.json").read_text())["status"], "unknown")
            result = api.execute_request("seedance", None, root, "cgt-mock", transport=lambda *args: {"id": "cgt-mock", "status": "running"})
            self.assertEqual(result["task_id"], "cgt-mock")
            self.assertEqual(result["status"], "running")

    def test_gemini_does_not_return_thought_images(self):
        import base64
        data = base64.b64encode(b"test").decode()
        response = {"steps": [{"type": "thought", "summary": [{"type": "image", "data": data}]},
                              {"type": "model_output", "content": [{"type": "image", "data": data}]}]}
        self.assertEqual(api.output_images("gemini", response), [b"test"])

    def test_cli_offline_packaging_no_credentials(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            prompt = root / "prompt.txt"
            prompt.write_text("她推门，停住。", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SKILLS / "generate-video-by-seedance" / "scripts" / "api.py"),
                                     "--kind", "seedance", "--model", "offline-model", "--prompt-file", str(prompt),
                                     "--out", str(root / "request")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads((root / "request" / "status.json").read_text())["network_called"])


class MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.ffmpeg = media.find_ffmpeg()
        except (ValueError, OSError) as error:
            raise unittest.SkipTest(str(error))

    def test_real_ffmpeg_operations_and_first_last_frame(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            inputs = []
            for index, color in enumerate(["red", "blue"]):
                path = root / ("中文's clip%d.mp4" % index)
                result = subprocess.run([self.ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
                    "-f", "lavfi", "-i", "color=c=%s:s=160x90:r=24:d=1" % color,
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                inputs.append(path)
            def operation(op, sources, output=None, extra=()):
                argv = [op, "--input"] + [str(p) for p in sources]
                if output:
                    argv += ["--output", str(output)]
                argv += ["--execute"] + list(extra)
                return media.run(media.parser().parse_args(argv))
            joined = root / "joined.mp4"
            operation("concat", inputs, joined)
            operation("check", [joined])
            first, last = root / "first.png", root / "last.png"
            operation("first-frame", [joined], first)
            operation("last-frame", [joined], last)
            with Image.open(first) as image:
                pixel = image.convert("RGB").getpixel((80, 45))
                self.assertGreater(pixel[0], pixel[2] + 100)
            with Image.open(last) as image:
                pixel = image.convert("RGB").getpixel((80, 45))
                self.assertGreater(pixel[2], pixel[0] + 100)
            operation("normalize", [inputs[0]], root / "norm.mp4", ["--width", "80", "--height", "128"])
            operation("trim", [joined], root / "trim.mp4", ["--start", "0.2", "--duration", "0.5"])
            audio = root / "audio.wav"
            operation("extract-audio", [joined], audio)
            operation("audio-trim", [audio], root / "atrim.wav", ["--duration", "0.5"])
            with wave.open(str(root / "atrim.wav")) as wav:
                self.assertAlmostEqual(wav.getnframes() / wav.getframerate(), 0.5, places=2)
            operation("loudness", [audio], root / "loud.wav")
            operation("mix", [audio, audio], root / "mix.wav")
            resized = root / "resized.png"
            operation("resize", [first], resized, ["--width", "80", "--height", "128"])
            with Image.open(resized) as image:
                self.assertEqual(image.size, (80, 128))
            operation("crop", [first], root / "crop.png", ["--width", "40", "--height", "40"])
            operation("sheet", [first, last], root / "sheet.png", ["--height", "90"])
            with self.assertRaises(FileExistsError):
                operation("first-frame", [joined], first)


class PackageTests(unittest.TestCase):
    def test_provider_and_media_helpers_stay_self_contained_and_identical(self):
        for names, filename in [(["generate-image-by-seedream", "generate-video-by-seedance", "nano-banana-pro"], "api.py"),
                                (["ffmpeg-video-processing", "ffmpeg-audio-processing", "ffmpeg-image-processing"], "media.py")]:
            contents = [(SKILLS / name / "scripts" / filename).read_bytes() for name in names]
            self.assertTrue(all(text == contents[0] for text in contents))


if __name__ == "__main__":
    unittest.main()
