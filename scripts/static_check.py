#!/usr/bin/env python3
from pathlib import Path
import ast
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

ast.parse((ROOT / "scripts/build_dist.py").read_text(encoding="utf-8"))
assert (ROOT / "UPSTREAM").exists()
assert "ref=1.5.1" in (ROOT / "UPSTREAM").read_text(encoding="utf-8")
assert (ROOT / "overlay/docs/MAINTENANCE.md").exists()
print("Static checks: OK")
