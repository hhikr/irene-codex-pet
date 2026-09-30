"""Build the installable ZIP and checksum file for a tagged release."""
from __future__ import annotations

import hashlib
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION = "v1.0.0"
ZIP_NAME = f"Irene-Codex-Pet-{VERSION}.zip"
INCLUDED_ROOT_FILES = (
    "LICENSE",
    "NOTICE.md",
    "README.md",
    "RELEASE-NOTES.md",
    "第四版使用说明.md",
    "install.ps1",
    "pet.json",
    "preview.html",
    "preview-player.js",
)
EXCLUDED_PARTS = {".git", "dist", "research", "uninstalled-old-versions"}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    paths = [ROOT / name for name in INCLUDED_ROOT_FILES]
    paths.extend(path for path in (ROOT / "assets").rglob("*") if path.is_file())
    if any(not path.is_file() for path in paths):
        raise FileNotFoundError("A release file is missing.")
    paths.sort(key=lambda path: path.relative_to(ROOT).as_posix())
    if any(EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts) for path in paths):
        raise RuntimeError("A local or ignored directory entered the release package.")

    distribution = ROOT / "dist"
    distribution.mkdir(exist_ok=True)
    package = distribution / ZIP_NAME
    checksums = []
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(path, path.relative_to(ROOT).as_posix())
            checksums.append(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}")
    with zipfile.ZipFile(package) as archive:
        corrupt = archive.testzip()
        if corrupt is not None:
            raise RuntimeError(f"Invalid ZIP member: {corrupt}")
        names = set(archive.namelist())
        for required in ("install.ps1", "pet.json", "preview.html", "assets/native/walk.png"):
            if required not in names:
                raise RuntimeError(f"Required release file is missing: {required}")
    checksum_path = distribution / f"{ZIP_NAME}.sha256"
    checksum_path.write_text(f"{sha256(package)}  {ZIP_NAME}\n" + "\n".join(checksums) + "\n", encoding="utf-8")
    print(json.dumps({"zip": str(package), "bytes": package.stat().st_size, "sha256": sha256(package), "files": len(paths), "zip_integrity": "ok"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
