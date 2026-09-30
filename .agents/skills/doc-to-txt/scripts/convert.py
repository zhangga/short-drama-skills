"""Convert local DOCX/PDF/DOC/TXT to new UTF-8 text; no installation or OCR."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_text(path):
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    paragraphs = []
    for paragraph in root.iter(W + "p"):
        parts = []
        for child in paragraph.iter():
            if child.tag == W + "t":
                parts.append(child.text or "")
            elif child.tag == W + "tab":
                parts.append("\t")
            elif child.tag in (W + "br", W + "cr"):
                parts.append("\n")
        paragraphs.append("".join(parts))
    return "\n".join(paragraphs), "stdlib-docx-main-body"


def extract(path, encoding="utf-8-sig"):
    path = Path(path).resolve(strict=True)
    extension = path.suffix.lower()
    if extension == ".txt":
        return path.read_bytes().decode(encoding), "strict-text-decode"
    if extension == ".docx":
        return docx_text(path)
    if extension == ".pdf":
        executable = shutil.which("pdftotext")
        if executable:
            process = subprocess.run([executable, "-layout", "-enc", "UTF-8", str(path), "-"],
                                     check=True, capture_output=True)
            return process.stdout.decode("utf-8"), "pdftotext-layout"
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise ValueError("PDF requires existing pdftotext or pypdf") from error
        return "\n\f\n".join(page.extract_text() or "" for page in PdfReader(path).pages), "pypdf"
    if extension == ".doc":
        antiword = shutil.which("antiword")
        if antiword:
            result = subprocess.run([antiword, "-m", "UTF-8.txt", str(path)], check=True, capture_output=True)
            return result.stdout.decode("utf-8"), "antiword"
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            raise ValueError("DOC requires existing antiword or LibreOffice")
        with tempfile.TemporaryDirectory() as work:
            profile = (Path(work) / "profile").as_uri()
            subprocess.run([soffice, "-env:UserInstallation=" + profile, "--headless", "--convert-to", "docx",
                            "--outdir", work, str(path)], check=True, capture_output=True)
            text, _ = docx_text(Path(work) / (path.stem + ".docx"))
            return text, "libreoffice-to-docx"
    raise ValueError("Supported formats: DOC, DOCX, PDF, TXT")


def convert(source, out, encoding="utf-8-sig"):
    out = Path(out)
    if out.exists():
        raise FileExistsError("Output already exists")
    text, tool = extract(source, encoding)
    if not text.strip():
        raise ValueError("Empty text; scanned documents may require OCR")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return {"output": str(out.resolve()), "characters": len(text), "tool": tool,
            "requires_content_review": True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source")
    p.add_argument("--out", required=True)
    p.add_argument("--encoding", default="utf-8-sig")
    args = p.parse_args()
    try:
        print(json.dumps(convert(args.source, args.out, args.encoding), ensure_ascii=False))
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
