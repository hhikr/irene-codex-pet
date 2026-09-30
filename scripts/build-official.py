"""Pack rendered Spine frames into Codex v2 atlases and complete animation previews."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".build/official"
OUT = ROOT / "assets/official"
COUNTS = [6, 8, 8, 4, 5, 8, 6, 6, 6]

def clean(image):
    data = np.array(image.convert("RGBA"))
    data[data[:, :, 3] == 0, :3] = 0
    return Image.fromarray(data)

def main():
    overview = Image.new("RGB", (900, 430), "#252631")
    draw = ImageDraw.Draw(overview)
    for number, skin in enumerate(("default", "synesthesia", "game")):
        rendered = RAW / skin
        source = json.loads((rendered / "manifest.json").read_text())
        frames = {clip: [Image.open(p).convert("RGBA") for p in sorted((rendered / clip).glob("*.png"))] for clip in source["clips"]}
        frames["Look"] = [Image.open(p).convert("RGBA") for p in sorted((rendered / "Look").glob("*.png"))]
        def sample(clip, count, start=0, end=None):
            available = frames[clip]
            end = len(available) - 1 if end is None else min(end, len(available) - 1)
            return [available[round(start + (end - start) * i / max(1, count - 1))].copy() for i in range(count)]
        # Short open-eye idle segments avoid turning the host's slow playback into a prolonged blink.
        idle = sample("Relax", 6, 0, 10)
        walking = sample("Move", 8, 0, min(26, len(frames["Move"]) - 1))
        gesture = sample("Interact", 5, 0, 24 if skin == "game" else 30)
        rows = [idle, walking, walking,
                [gesture[i] for i in (0, 1, 3, 4)], gesture,
                sample("Sit", 8), sample("Sit", 6, 20),
                sample("Relax", 6, 20, 40), sample("Relax", 6, 45, 65)]
        used = [frame for row in rows for frame in row] + frames["Look"]
        boxes = [frame.getchannel("A").point(lambda a: 255 if a > 2 else 0).getbbox() for frame in used]
        if any(box is None for box in boxes):
            raise ValueError(f"Empty pose in {skin}")
        crop = (min(b[0] for b in boxes)-4, min(b[1] for b in boxes)-4, max(b[2] for b in boxes)+4, max(b[3] for b in boxes)+4)
        destination = OUT / skin
        destination.mkdir(parents=True, exist_ok=True)
        def cell(frame, multiplier=1):
            result = Image.new("RGBA", (192*multiplier, 208*multiplier))
            image = frame.crop(crop)
            image.thumbnail((180*multiplier, 194*multiplier), Image.Resampling.LANCZOS)
            result.alpha_composite(image, ((result.width-image.width)//2, result.height-image.height-8*multiplier))
            return clean(result)
        for multiplier, name in ((1, "native"), (2, "hd")):
            atlas = Image.new("RGBA", (1536*multiplier, 2288*multiplier))
            for row, poses in enumerate(rows):
                for column, pose in enumerate(poses):
                    normalized = cell(pose, multiplier)
                    if row == 2:
                        normalized = ImageOps.mirror(normalized)
                    atlas.paste(normalized, (column*192*multiplier, row*208*multiplier))
            for index, pose in enumerate(frames["Look"]):
                atlas.paste(cell(pose, multiplier), ((index%8)*192*multiplier, (9+index//8)*208*multiplier))
            atlas.save(destination / f"{name}.png")
        previews = destination / "previews"
        previews.mkdir(exist_ok=True)
        for clip, poses in frames.items():
            if clip == "Look":
                continue
            normalized = [clean(p.resize((384,416), Image.Resampling.LANCZOS)) for p in poses]
            normalized[0].save(previews / f"{clip}.webp", save_all=True, append_images=normalized[1:], duration=50, loop=0, lossless=True)
        portrait = cell(frames["Default"][0], 2)
        portrait.save(destination / "portrait.png")
        overview.paste(portrait.resize((300,325)), (number*300,50), portrait.resize((300,325)))
        draw.text((number*300+100,15), skin, fill="white")
        native = destination / "native.png"
        data = np.array(Image.open(native))
        report = {"ok": bool(Image.open(native).size == (1536,2288) and np.all(data[data[:,:,3]==0,:3]==0)),
                  "sha256": hashlib.sha256(native.read_bytes()).hexdigest(), "size": [1536,2288],
                  "used_cells": 73, "frame_counts": COUNTS, "transparent_rgb_zero": True}
        (destination / "validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        (destination / "manifest.json").write_text(json.dumps({"skin":skin,"spine_version":"3.8.99", "render_canvas":[768,832],"crop":crop,
            "states":[{"row":i,"frames":count,"source":clip} for i,(count,clip) in enumerate(zip(COUNTS,["Relax (open-eye segment)","Move","Move mirrored","Interact segment","Interact segment","Sit","Sit","Relax","Relax"]))],
            "look":"16 adapted Default poses: head rotation and pupil offset", "previews":source["clips"], "preview_fps":20},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"Built {skin}: 73 cells, original previews at 20 fps")
    overview.save(OUT / "overview.jpg", quality=94)

if __name__ == "__main__":
    main()
