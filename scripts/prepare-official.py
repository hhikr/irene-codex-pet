"""Normalize user-provided Spine filenames for a local browser renderer."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"default": "4009_irene", "synesthesia": "4009_irene_ambiencesynesthesia#3", "game": "4009_irene_game#3"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    args = parser.parse_args()
    records = {}
    for skin, folder in MODELS.items():
        destination = ROOT / "assets/official/source" / skin
        destination.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for extension in ("skel", "atlas", "png"):
            source = next((args.raw / folder).glob(f"*.{extension}"))
            data = source.read_bytes()
            hashes[source.name] = hashlib.sha256(data).hexdigest()
            if extension == "atlas":
                data = ("\n".join("model.png" if line.lower().endswith(".png") else line for line in data.decode("utf-8").splitlines()) + "\n").encode("utf-8")
            (destination / f"model.{extension}").write_bytes(data)
        records[skin] = {"source_model": folder, "spine_version": "3.8.99", "original_sha256": hashes, "atlas_change": "texture page renamed to model.png"}
    (ROOT / "assets/official/source/provenance.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
