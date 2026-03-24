from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    gold_dir = raw / "_gold"
    if not gold_dir.exists():
        raise FileNotFoundError(f"Missing task-local gold directory: {gold_dir}")

    # 1. Copy input files to public/, excluding _gold
    for item in raw.iterdir():
        if item.name == "_gold":
            continue
        if item.is_file():
            shutil.copy2(item, public / item.name)
        elif item.is_dir():
            shutil.copytree(item, public / item.name, dirs_exist_ok=True)

    # 2. Copy canonical gold files to private/
    image_candidates = [p for p in gold_dir.iterdir() if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
    if len(image_candidates) != 1:
        raise ValueError(f"Expected exactly one gold image in {gold_dir}, found: {image_candidates}")

    image_src = image_candidates[0]
    Image.open(image_src).convert("RGB").save(private / "result.png", format="PNG")

    shutil.copy2(gold_dir / "plot.json", private / "plot.json")
    shutil.copy2(gold_dir / "result.npy", private / "result.npy")

    # 3. Create real sample files
    Image.new("RGB", (1, 1), color=(255, 255, 255)).save(public / "sample_result.png", format="PNG")

    sample_plot = {
        "type": "",
        "color": [],
        "figsize": [],
        "graph_title": "",
        "legend_title": "",
        "labels": [],
        "x_label": "",
        "y_label": "",
        "xtick_labels": [],
        "ytick_labels": [],
    }
    with open(public / "sample_plot.json", "w", encoding="utf-8") as f:
        json.dump(sample_plot, f, ensure_ascii=False, indent=2)

    np.save(public / "sample_result.npy", np.zeros((1, 1), dtype=float))
