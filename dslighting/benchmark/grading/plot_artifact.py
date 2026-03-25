from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Literal

import numpy as np
from PIL import Image, ImageColor

from dslighting.benchmark.grading.helpers import (
    reference_child_path,
    require_submission_dir,
    submission_child_path,
)

PLOT_IMAGE_NAME = "result.png"
PLOT_JSON_NAME = "plot.json"
PLOT_NUMPY_NAME = "result.npy"

FIG_KEYS = [
    "type",
    "color",
    "figsize",
    "graph_title",
    "legend_title",
    "labels",
    "x_label",
    "y_label",
    "xtick_labels",
    "ytick_labels",
]

_TAB_COLORS: dict[str, tuple[int, int, int]] = {
    "tab:blue": (31, 119, 180),
    "tab:orange": (255, 127, 14),
    "tab:green": (44, 160, 44),
    "tab:red": (214, 39, 40),
    "tab:purple": (148, 103, 189),
    "tab:brown": (140, 86, 75),
    "tab:pink": (227, 119, 194),
    "tab:gray": (127, 127, 127),
    "tab:olive": (188, 189, 34),
    "tab:cyan": (23, 190, 207),
}


@dataclass(frozen=True)
class _NormalizedColorField:
    kind: Literal["empty", "rgb", "categorical", "opaque"]
    items: tuple[Any, ...]


def _ratio(a: str, b: str) -> int:
    return int(round(100 * SequenceMatcher(None, a, b).ratio()))


def compare_image(result_path: Path, gold_path: Path, *, is_color: bool = True, check_size: bool = False) -> bool:
    if not result_path.exists() or not gold_path.exists():
        return False

    result_img = Image.open(result_path).convert("RGB" if is_color else "L")
    gold_img = Image.open(gold_path).convert("RGB" if is_color else "L")

    result_arr = np.array(result_img)
    gold_arr = np.array(gold_img)

    if gold_arr.ndim == 3 and result_arr.ndim != 3:
        return False

    if check_size:
        return result_arr.shape == gold_arr.shape and np.allclose(result_arr, gold_arr, atol=1e-2)

    resized = result_img.resize(gold_img.size)
    resized_arr = np.array(resized)
    return bool(np.allclose(resized_arr, gold_arr, atol=1e-2))


def scale_to_percentage(arr: np.ndarray) -> np.ndarray:
    total = np.sum(arr)
    if total == 0:
        return arr
    return arr / total


def compare_numpy(result_np: np.ndarray, gold_np: np.ndarray, tol: float = 1e-2, allow_scale: bool = True) -> bool:
    if result_np.ndim == 1 and gold_np.ndim == 2:
        if gold_np.shape[0] == 1:
            result_np = result_np.reshape(1, -1)
        elif gold_np.shape[1] == 1:
            result_np = result_np.reshape(-1, 1)
        else:
            result_np = result_np.reshape(-1, 1)
    elif result_np.ndim == 1:
        result_np = result_np.reshape(-1, 1)

    if gold_np.ndim == 1 and result_np.ndim == 2:
        if result_np.shape[0] == 1:
            gold_np = gold_np.reshape(1, -1)
        elif result_np.shape[1] == 1:
            gold_np = gold_np.reshape(-1, 1)
        else:
            gold_np = gold_np.reshape(-1, 1)
    elif gold_np.ndim == 1:
        gold_np = gold_np.reshape(-1, 1)

    if result_np.shape != gold_np.shape:
        return False

    # For single-row (1, N) arrays, sort along axis=1 (the values axis).
    # axis=0 sort is a no-op for 1 row, making order matter unintentionally.
    # For multi-row arrays (e.g. scatter (N, 2)), sort along axis=0 as before.
    sort_axis = 1 if result_np.shape[0] == 1 else 0
    result_sorted = np.sort(result_np, axis=sort_axis).reshape(result_np.shape)
    gold_sorted = np.sort(gold_np, axis=sort_axis).reshape(gold_np.shape)

    if np.allclose(result_sorted, gold_sorted, atol=tol, equal_nan=True):
        return True

    if allow_scale:
        result_scaled = scale_to_percentage(result_sorted)
        gold_scaled = scale_to_percentage(gold_sorted)
        if np.allclose(result_scaled, gold_scaled, atol=tol, equal_nan=True):
            return True

    return False


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool)


def _coerce_color_items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, tuple):
        value = list(value)
    if isinstance(value, list):
        if _looks_like_single_rgb_vector(value):
            return [value]
        return list(value)
    return [value]


def _looks_like_single_rgb_vector(value: list[Any]) -> bool:
    if len(value) not in {3, 4} or not all(_is_number(item) for item in value):
        return False

    numbers = [float(item) for item in value]
    if any(number < 0 for number in numbers):
        return False

    if any(not number.is_integer() for number in numbers):
        return True

    return max(numbers) > 20


def _freeze_token(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_freeze_token(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_token(item) for item in value)
    if isinstance(value, float):
        return round(value, 8)
    return value


def _parse_rgb(value: Any) -> tuple[int, int, int] | None:
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None

        tab_color = _TAB_COLORS.get(normalized.lower())
        if tab_color is not None:
            return tab_color

        try:
            rgb = ImageColor.getrgb(normalized)
        except ValueError:
            return None

        return tuple(int(channel) for channel in rgb[:3])

    if isinstance(value, tuple):
        value = list(value)
    if isinstance(value, list) and len(value) in {3, 4} and all(_is_number(item) for item in value):
        channels = [float(item) for item in value[:3]]
        scale = 255.0 if channels and max(channels) <= 1.0 else 1.0
        rgb = tuple(
            int(round(min(255.0, max(0.0, channel * scale))))
            for channel in channels
        )
        return rgb

    return None


def _normalize_color_field(value: Any) -> _NormalizedColorField:
    items = _coerce_color_items(value)
    if not items:
        return _NormalizedColorField(kind="empty", items=())

    parsed_rgb = tuple(_parse_rgb(item) for item in items)
    if all(item is not None for item in parsed_rgb):
        return _NormalizedColorField(kind="rgb", items=tuple(parsed_rgb))

    if all(_is_number(item) for item in items):
        return _NormalizedColorField(
            kind="categorical",
            items=tuple(_freeze_token(item) for item in items),
        )

    return _NormalizedColorField(
        kind="opaque",
        items=tuple(str(_freeze_token(item)).strip().lower() for item in items),
    )


def _canonical_partition(items: tuple[Any, ...]) -> tuple[int, ...]:
    mapping: dict[Any, int] = {}
    partition: list[int] = []
    next_label = 0
    for item in items:
        if item not in mapping:
            mapping[item] = next_label
            next_label += 1
        partition.append(mapping[item])
    return tuple(partition)


def _color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    return float(np.sqrt(np.sum((np.array(c1) - np.array(c2)) ** 2)))


def _rgb_multiset_matches(
    result_colors: tuple[tuple[int, int, int], ...],
    gold_colors: tuple[tuple[int, int, int], ...],
    *,
    threshold: float = 15.0,
) -> bool:
    if len(result_colors) != len(gold_colors):
        if len(result_colors) == 1:
            return all(_color_distance(result_colors[0], gold) <= threshold for gold in gold_colors)
        if len(gold_colors) == 1:
            return all(_color_distance(color, gold_colors[0]) <= threshold for color in result_colors)
        return False

    remaining = list(gold_colors)
    for color in result_colors:
        candidates = [
            (_color_distance(color, gold), index)
            for index, gold in enumerate(remaining)
            if _color_distance(color, gold) <= threshold
        ]
        if not candidates:
            return False
        _, matched_index = min(candidates, key=lambda item: item[0])
        remaining.pop(matched_index)

    return not remaining


def compare_color_field(result_value: Any, gold_value: Any) -> bool:
    result = _normalize_color_field(result_value)
    gold = _normalize_color_field(gold_value)

    if result.kind == "empty" and gold.kind == "empty":
        return True
    if result.kind == "empty" or gold.kind == "empty":
        return False

    if result.kind == "rgb" and gold.kind == "rgb":
        return _rgb_multiset_matches(result.items, gold.items)

    if result.kind == "categorical" and gold.kind == "categorical":
        return _canonical_partition(result.items) == _canonical_partition(gold.items)

    if {result.kind, gold.kind} == {"categorical", "rgb"}:
        if len(result.items) != len(gold.items):
            return False
        return _canonical_partition(result.items) == _canonical_partition(gold.items)

    if result.kind == "opaque" and gold.kind == "opaque":
        return result.items == gold.items

    return False


def compare_plot_key(key: str, result: dict[str, Any], gold: dict[str, Any]) -> bool:
    key = key.lower()

    if key == "figsize":
        return list(result.get(key, [])) == list(gold.get(key, []))

    if key == "color":
        return compare_color_field(result.get(key, []), gold.get(key, []))

    if key == "type":
        return str(result.get(key, "")).lower() == str(gold.get(key, "")).lower()

    if key in {"graph_title", "x_label", "y_label", "legend_title"}:
        result_text = str(result.get(key, "")).lower()
        gold_text = str(gold.get(key, "")).lower()
        if not result_text and gold_text:
            return False
        return _ratio(result_text, gold_text) >= 90

    if key in {"labels", "xtick_labels", "ytick_labels"}:
        result_list = [str(x).lower() for x in result.get(key, [])]
        gold_list = [str(x).lower() for x in gold.get(key, [])]
        if len(result_list) != len(gold_list):
            return False
        return all(any(_ratio(x, y) > 95 for y in gold_list) for x in result_list)

    raise ValueError(f"Unsupported plot metadata key: {key}")


def compare_plot_json(result_json: Path, gold_json: Path, keys: list[str] | None = None) -> bool:
    if not result_json.exists() or not gold_json.exists():
        return False

    with open(result_json, "r", encoding="utf-8") as handle:
        result = json.load(handle)
    with open(gold_json, "r", encoding="utf-8") as handle:
        gold = json.load(handle)

    keys_to_compare = keys or list(gold.keys())
    return all(compare_plot_key(key, result, gold) for key in keys_to_compare)


def grade_plot_submission(request) -> float:
    require_submission_dir(request)

    result_image = submission_child_path(request, PLOT_IMAGE_NAME)
    gold_image = reference_child_path(request, PLOT_IMAGE_NAME)

    result_json = submission_child_path(request, PLOT_JSON_NAME)
    gold_json = reference_child_path(request, PLOT_JSON_NAME)

    result_npy = submission_child_path(request, PLOT_NUMPY_NAME)
    gold_npy = reference_child_path(request, PLOT_NUMPY_NAME)

    if compare_image(result_image, gold_image, is_color=True, check_size=False):
        return 1.0

    result_np = np.load(result_npy, allow_pickle=True)
    gold_np = np.load(gold_npy, allow_pickle=True)

    np_ok = compare_numpy(result_np, gold_np, tol=1e-2, allow_scale=True)
    json_ok = compare_plot_json(result_json, gold_json, keys=FIG_KEYS)

    return 1.0 if (np_ok and json_ok) else 0.0


__all__ = [
    "FIG_KEYS",
    "PLOT_IMAGE_NAME",
    "PLOT_JSON_NAME",
    "PLOT_NUMPY_NAME",
    "compare_color_field",
    "compare_image",
    "compare_numpy",
    "compare_plot_json",
    "compare_plot_key",
    "grade_plot_submission",
]
