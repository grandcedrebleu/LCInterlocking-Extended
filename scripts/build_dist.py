#!/usr/bin/env python3
from pathlib import Path
import configparser
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_FILE = ROOT / "UPSTREAM"
WORK = ROOT / ".build"
DIST_ROOT = ROOT / "dist"
DIST = DIST_ROOT / "LCInterlockingExtended"

def read_upstream():
    data = {}
    for line in UPSTREAM_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly one upstream anchor, found {count}. "
            "Upstream changed: review before releasing."
        )
    return text.replace(old, new, 1)

def patch_helper(path):
    text = path.read_text(encoding="utf-8")

    pattern_depth = (
        r"(?m)^([ \t]*)corrected_length\s*=\s*"
        r"material_plane\.thickness(?:\s*#.*)?$"
    )

    matches = list(re.finditer(pattern_depth, text))

    if len(matches) != 1:
        raise RuntimeError(
            "helper depth: expected exactly one upstream anchor, "
            f"found {len(matches)}. Upstream changed: review before releasing."
        )

    indent = matches[0].group(1)

    replacement = (
        f'{indent}# Extended: force the boolean tool to cross both limiting faces.\n'
        f'{indent}hole_through_margin = max(\n'
        f'{indent}    0.0,\n'
        f'{indent}    float(getattr(tab_face, "cut_through_margin", 0.10))\n'
        f'{indent})\n'
        f'{indent}corrected_length = material_plane.thickness + '
        f'2.0 * hole_through_margin'
    )

    text = re.sub(pattern_depth, replacement, text, count=1)

    pattern_origin = (
        r"(?m)^([ \t]*)origin\s*=\s*"
        r"FreeCAD\.Vector\(0\.,\s*-\s*corrected_width_center,\s*"
        r"-corrected_height_center\)$"
    )

    matches = list(re.finditer(pattern_origin, text))

    if len(matches) != 1:
        raise RuntimeError(
            "helper origin: expected exactly one upstream anchor, "
            f"found {len(matches)}. Upstream changed: review before releasing."
        )

    indent = matches[0].group(1)

    replacement = (
        f'{indent}origin = FreeCAD.Vector(\n'
        f'{indent}    -hole_through_margin,\n'
        f'{indent}    -corrected_width_center,\n'
        f'{indent}    -corrected_height_center\n'
        f'{indent})'
    )

    text = re.sub(pattern_origin, replacement, text, count=1)

    path.write_text(text, encoding="utf-8")

def patch_multiplejoins(path):
    text = path.read_text(encoding="utf-8")

    old = """        obj.addProperty('App::PropertyPythonObject', 'namesMapping').namesMapping = {}
        obj.Proxy = self
"""
    new = """        obj.addProperty('App::PropertyPythonObject', 'namesMapping').namesMapping = {}
        obj.addProperty(
            'App::PropertyLength',
            'CutThroughMargin',
            'Laser cut',
            'Through-cut margin applied on each side of the contact plane'
        ).CutThroughMargin = 0.10
        obj.Proxy = self
"""
    text = replace_once(text, old, new, "MultiJoin property")

    old_preview = """            for tab in fp.faces.lst:
                cp_tab = copy.deepcopy(tab)
                freecad_obj = document.getObject(cp_tab.freecad_obj_name)
                freecad_face = document.getObject(cp_tab.freecad_obj_name).Shape.getElement(cp_tab.face_name)
                cp_tab.recomputeInit(freecad_obj, freecad_face)
                tabs.append(cp_tab)
"""

    new_preview = """            for tab in fp.faces.lst:
                cp_tab = copy.deepcopy(tab)
                freecad_obj = document.getObject(cp_tab.freecad_obj_name)
                freecad_face = document.getObject(cp_tab.freecad_obj_name).Shape.getElement(cp_tab.face_name)
                cp_tab.recomputeInit(freecad_obj, freecad_face)
                cp_tab.cut_through_margin = float(fp.CutThroughMargin.Value)
                tabs.append(cp_tab)
"""

    preview_count = text.count(old_preview)
    if preview_count != 2:
        raise RuntimeError(
            "preview/execute propagation: expected exactly two upstream anchors, "
            f"found {preview_count}. Upstream changed: review before releasing."
        )

    text = text.replace(old_preview, new_preview, 2)

    marker = """class MultipleJoins(TreePanel):
    def __init__(self, obj_join):
        super(MultipleJoins, self).__init__("Parts and tabs", obj_join)
        self.obj_join = obj_join
        self.parts_origin = copy.deepcopy(obj_join.parts)
        self.faces_origin = copy.deepcopy(obj_join.faces)
        self.obj_join.edit = True
"""
    replacement = """class MultipleJoins(TreePanel):
    def __init__(self, obj_join):
        if not hasattr(obj_join, "CutThroughMargin"):
            obj_join.addProperty(
                'App::PropertyLength',
                'CutThroughMargin',
                'Laser cut',
                'Through-cut margin applied on each side of the contact plane'
            )
            obj_join.CutThroughMargin = 0.10

        super(MultipleJoins, self).__init__("Parts and tabs", obj_join)
        self.obj_join = obj_join
        self.parts_origin = copy.deepcopy(obj_join.parts)
        self.faces_origin = copy.deepcopy(obj_join.faces)
        self.margin_origin = float(obj_join.CutThroughMargin.Value)

        from PySide import QtGui
        self.cut_margin_widget = QtGui.QWidget()
        self.cut_margin_widget.setWindowTitle("Cut parameters")
        layout = QtGui.QFormLayout(self.cut_margin_widget)
        self.cut_margin_spin = QtGui.QDoubleSpinBox(self.cut_margin_widget)
        self.cut_margin_spin.setRange(0.0, 10.0)
        self.cut_margin_spin.setDecimals(3)
        self.cut_margin_spin.setSingleStep(0.01)
        self.cut_margin_spin.setSuffix(" mm")
        self.cut_margin_spin.setValue(self.margin_origin)
        self.cut_margin_spin.setToolTip(
            "Through-cut extension on each side of the contact plane."
        )
        layout.addRow("Marge traversante :", self.cut_margin_spin)
        self.form.insert(0, self.cut_margin_widget)
        self.obj_join.edit = True
"""
    text = replace_once(text, marker, replacement, "MultiJoin editor")

    old_compute = """    def compute(self, preview, fast=False):
        self.save_items_properties()
        self.save_link_properties()
"""
    new_compute = """    def compute(self, preview, fast=False):
        self.save_items_properties()
        self.save_link_properties()
        self.obj_join.CutThroughMargin = float(self.cut_margin_spin.value())
"""
    text = replace_once(text, old_compute, new_compute, "MultiJoin save")

    path.write_text(text, encoding="utf-8")

def update_package(path, version):
    ns = {"p": "https://wiki.freecad.org/Package_Metadata"}
    ET.register_namespace("", ns["p"])
    tree = ET.parse(path)
    root = tree.getroot()
    def child(name):
        return root.find(f"p:{name}", ns)
    child("name").text = "LCInterlocking Extended"
    child("description").text = (
        "LCInterlocking with configurable through-cut margin to prevent residual slot skin"
    )
    child("version").text = version
    maint = child("maintainer")
    maint.text = "LCInterlocking Extended maintainers"
    author = child("author")
    if author is not None:
        author.text = "execuc and LCInterlocking Extended contributors"
    for url in root.findall("p:url", ns):
        if url.attrib.get("type") == "repository":
            # Replace after GitHub publication with the actual repository URL.
            url.text = "https://github.com/REPLACE_WITH_OWNER/LCInterlocking-Extended"
            url.set("branch", "dist")
        elif url.attrib.get("type") in ("readme", "documentation"):
            url.text = "https://github.com/REPLACE_WITH_OWNER/LCInterlocking-Extended"
    tree.write(path, encoding="utf-8", xml_declaration=True)

def main():
    cfg = read_upstream()
    repo = cfg["repository"]
    ref = cfg["ref"]
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    shutil.rmtree(WORK, ignore_errors=True)
    shutil.rmtree(DIST_ROOT, ignore_errors=True)
    WORK.mkdir(parents=True)
    DIST_ROOT.mkdir(parents=True)

    src = WORK / "upstream"
    subprocess.run(["git", "clone", "--depth", "1", "--branch", ref, repo, str(src)], check=True)

    shutil.copytree(src, DIST, ignore=shutil.ignore_patterns(".git", ".github"))
    patch_helper(DIST / "lasercut/helper.py")
    patch_multiplejoins(DIST / "panel/multiplejoins.py")
    update_package(DIST / "package.xml", version)

    # Extended documentation and diagnostic material
    overlay = ROOT / "overlay"
    shutil.copytree(overlay / "docs", DIST / "docs" / "extended", dirs_exist_ok=True)
    shutil.copytree(overlay / "tests", DIST / "test" / "extended", dirs_exist_ok=True)
    shutil.copy2(ROOT / "CHANGELOG.md", DIST / "CHANGELOG_EXTENDED.md")
    shutil.copy2(ROOT / "UPSTREAM", DIST / "UPSTREAM_EXTENDED")
    shutil.copy2(ROOT / "VERSION", DIST / "VERSION_EXTENDED")

    print(f"Built {DIST}")

if __name__ == "__main__":
    main()
