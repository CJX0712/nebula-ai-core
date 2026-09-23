# 测试公共 fixtures
# 作者: 晨星
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from nebula.core.config import Settings  # noqa: E402
from nebula.core.factory import build_system  # noqa: E402

SAMPLE = ROOT / "samples" / "sample.md"


@pytest.fixture
def system():
    return build_system(Settings())
