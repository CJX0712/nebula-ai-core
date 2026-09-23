# P0 门禁：扫描仓库中是否把 emoji 当作功能图标
# 作者: 晨星
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# 覆盖主要 emoji / 符号平面；功能图标用 emoji 即判违规
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F02F"
    "\U0001F0A0-\U0001F0FF\U0001F100-\U0001F64F\U0001F680-\U0001F6FF"
    "\U0001FA70-\U0001FAFF\uFE00-\uFE0F\u200D\u20E3]"
)

EXTS = {
    ".py",
    ".md",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".vue",
    ".json",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    hits: list[str] = []
    for p in root.rglob("*"):
        if any(part in SKIP for part in p.parts):
            continue
        if p.suffix.lower() not in EXTS or not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in EMOJI_RE.finditer(line):
                hits.append(f"{p.relative_to(root)}:{i}: {m.group()!r}")
    if hits:
        print(json.dumps({"status": "FAIL", "hits": hits}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": "OK", "message": "无 emoji 功能图标"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
