"""Build the two installable editions and their checksum files."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v2.0.0"
COMMON = ("LICENSE", "NOTICE.md", "README.md", "RELEASE-NOTES.md", "preview-player.js")

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def package(edition, files, required):
    name = f"Irene-Codex-Pet-{edition}-{VERSION}.zip"
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    archive_path = output / name
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file in sorted(set(files)):
            archive.write(file, file.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert all(p in names for p in required)
        assert not any(p.startswith((".git/", ".build/", "research/", "node_modules/", "docs/")) or p.lower() in ("agent.md", "agents.md", "pat.txt") for p in names)
    (output / f"{name}.sha256").write_text(f"{sha256(archive_path)}  {name}\n", encoding="utf-8")
    print(json.dumps({"zip":name,"bytes":archive_path.stat().st_size,"files":len(names),"sha256":sha256(archive_path),"zip_integrity":"ok"}))

def main():
    common = [ROOT / p for p in COMMON]
    custom = common + [ROOT / p for p in ("install.ps1", "pet.json", "preview.html", "第四版使用说明.md")]
    custom += [p for p in (ROOT / "assets").rglob("*") if p.is_file() and "official" not in p.relative_to(ROOT).parts]
    custom.append(ROOT / "assets/official/overview.jpg")
    package("Custom", custom, ("install.ps1", "assets/native/walk.png"))
    official = common + [ROOT / p for p in ("install-official.ps1", "install-official.cmd", "preview-official.html", "官方小人使用说明.md")]
    official += [p for p in (ROOT / "assets/official").rglob("*") if p.is_file() and "source" not in p.relative_to(ROOT).parts]
    official.append(ROOT / "assets/official/source/provenance.json")
    package("Official", official, ("install-official.ps1", "assets/official/default/native.png", "assets/official/synesthesia/native.png", "assets/official/game/native.png"))

if __name__ == "__main__":
    main()
