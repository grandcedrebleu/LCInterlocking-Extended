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
        "LCInterlocking with configurable through-cut margin "
        "and isolated Python namespace for safe coexistence"
    )
    child("version").text = version

    maint = child("maintainer")
    if maint is not None:
        maint.text = "grandcedrebleu"

    author = child("author")
    if author is not None:
        author.text = "execuc and LCInterlocking Extended contributors"

    repository_url = "https://github.com/grandcedrebleu/LCInterlocking-Extended"

    for url in root.findall("p:url", ns):
        url_type = url.attrib.get("type")
        if url_type == "repository":
            url.text = repository_url
            url.set("branch", "dist")
        elif url_type in ("readme", "documentation"):
            url.text = repository_url

    freecadmin = child("freecadmin")
    if freecadmin is None:
        freecadmin = ET.SubElement(root, f"{{{ns['p']}}}freecadmin")
    freecadmin.text = "1.1.1"

    # v1.1+: Extended is technically isolated and can coexist with upstream.
    # Remove old replacement/conflict declarations from earlier builds.
    for tag in ("conflict", "replace"):
        for node in list(root.findall(f"p:{tag}", ns)):
            if (node.text or "").strip() == "LCInterlocking":
                root.remove(node)

    tree.write(path, encoding="utf-8", xml_declaration=True)

def write_extended_readme(dist, version):
    readme = f"""# LCInterlocking Extended

**Version {version}**

LCInterlocking Extended is a maintained FreeCAD workbench based on the original
LCInterlocking project by execuc.

Repository:
https://github.com/grandcedrebleu/LCInterlocking-Extended

## What Extended adds

This distribution adds a configurable **through-cut margin** to MultiJoin operations.

From version 1.1.0, its Python packages and FreeCAD GUI command IDs are namespaced so it can coexist safely with the standard LCInterlocking addon.

Default value:

- 0.10 mm on each side of the contact plane
- 0.20 mm total extension of the boolean cutting solid

The purpose is to prevent the very thin residual face ("skin") that can remain at the
bottom of a slot when the cutting solid ends exactly on the opposite face.

## Installation

Install **LCInterlocking Extended** from FreeCAD's Addon Manager.

FreeCAD determines the correct user `Mod` directory for the running FreeCAD version.
No Windows, Linux or macOS installation path is hard-coded.

## Upstream

Based on LCInterlocking 1.5.1:
https://github.com/execuc/LCInterlocking

## Maintenance

The complete installable workbench in this branch is generated automatically from a
pinned upstream LCInterlocking revision.

The maintenance source, guarded patching logic and compatibility documentation are
kept on the `main` branch of this repository.

## License

LGPL-2.1-or-later, matching the upstream LCInterlocking project.
"""
    (dist / "README.md").write_text(readme, encoding="utf-8")


def patch_workbench_identity(dist):
    """Give Extended a unique visible label and Python workbench class."""
    initgui = dist / "InitGui.py"
    if not initgui.exists():
        raise RuntimeError("InitGui.py not found in generated upstream workbench.")

    text = initgui.read_text(encoding="utf-8")

    patterns = [
        (
            r'(?m)^(\s*MenuText\s*=\s*)["\']Laser cut Interlocking["\'](\s*)$',
            r'\1"Laser cut Interlocking Extended"\2',
        ),
        (
            r'(?m)^(\s*MenuText\s*=\s*)["\']Laser Cut Interlocking["\'](\s*)$',
            r'\1"Laser Cut Interlocking Extended"\2',
        ),
    ]

    total = 0
    for pattern, replacement in patterns:
        text, count = re.subn(pattern, replacement, text)
        total += count
    if total != 1:
        raise RuntimeError(
            "InitGui workbench label: expected exactly one visible MenuText anchor, "
            f"found {total}. Upstream changed: review before releasing."
        )

    class_pattern = r'(?m)^class\s+LCInterlockingWorkbench\s*\(Workbench\)\s*:'
    text, count = re.subn(
        class_pattern,
        'class LCInterlockingExtendedWorkbench(Workbench):',
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError(
            "InitGui class: expected exactly one LCInterlockingWorkbench declaration."
        )

    add_pattern = r'Gui\.addWorkbench\(LCInterlockingWorkbench\(\)\)'
    text, count = re.subn(
        add_pattern,
        'Gui.addWorkbench(LCInterlockingExtendedWorkbench())',
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError(
            "InitGui registration: expected exactly one upstream workbench registration."
        )

    initgui.write_text(text, encoding="utf-8")


def _rewrite_imports_in_file(path):
    """Rewrite known upstream package imports to Extended-only names."""
    text = path.read_text(encoding="utf-8")
    original = text

    # Safe and common form: from panel.foo import X / from lasercut.foo import X
    text = re.sub(r'(?m)^(\s*)from\s+lasercut(?=\.|\s+import\b)',
                  r'\1from lcie_lasercut', text)
    text = re.sub(r'(?m)^(\s*)from\s+panel(?=\.|\s+import\b)',
                  r'\1from lcie_panel', text)

    # Exact package imports, preserving the local variable name expected by code.
    text = re.sub(r'(?m)^(\s*)import\s+lasercut\s*(#.*)?$',
                  r'\1import lcie_lasercut as lasercut \2', text)
    text = re.sub(r'(?m)^(\s*)import\s+panel\s*(#.*)?$',
                  r'\1import lcie_panel as panel \2', text)

    if text != original:
        path.write_text(text, encoding="utf-8")


def namespace_python_modules(dist):
    """Isolate Extended from the upstream workbench's top-level Python names."""
    # Rewrite imports before renaming directories.
    for py in dist.rglob("*.py"):
        _rewrite_imports_in_file(py)

    # Root command modules are imported by name from InitGui.py and would also collide.
    root_modules = {
        "ExportPanel.py": "LCIE_ExportPanel.py",
        "MakeBoxPanel.py": "LCIE_MakeBoxPanel.py",
        "MakeRoundedBoxPanel.py": "LCIE_MakeRoundedBoxPanel.py",
    }

    initgui = dist / "InitGui.py"
    text = initgui.read_text(encoding="utf-8")
    for old_name, new_name in root_modules.items():
        old_mod = old_name[:-3]
        new_mod = new_name[:-3]
        pattern = rf'(?m)^(\s*)import\s+{re.escape(old_mod)}\s*$'
        text, count = re.subn(pattern, rf'\1import {new_mod}', text)
        if count != 1:
            raise RuntimeError(
                f"InitGui root import {old_mod}: expected exactly one anchor, found {count}."
            )
    initgui.write_text(text, encoding="utf-8")

    for old_name, new_name in root_modules.items():
        old = dist / old_name
        new = dist / new_name
        if not old.exists():
            raise RuntimeError(f"Expected upstream root module not found: {old_name}")
        old.rename(new)

    renames = {
        "lasercut": "lcie_lasercut",
        "panel": "lcie_panel",
    }
    for old_name, new_name in renames.items():
        old = dist / old_name
        new = dist / new_name
        if not old.is_dir():
            raise RuntimeError(f"Expected upstream package not found: {old_name}")
        old.rename(new)

    # Reject any unsafe imports left behind. Failing the build is safer than silently
    # producing an addon that can collide with the standard LCInterlocking workbench.
    unsafe = []
    unsafe_pattern = re.compile(
        r'(?m)^\s*(?:from\s+(?:lasercut|panel)(?:\.|\s)|'
        r'import\s+(?:lasercut|panel)(?:\.|\s|$))'
    )
    for py in dist.rglob("*.py"):
        content = py.read_text(encoding="utf-8")
        if unsafe_pattern.search(content):
            unsafe.append(str(py.relative_to(dist)))
    if unsafe:
        raise RuntimeError(
            "Unsafe upstream imports remain after namespacing: " + ", ".join(unsafe)
        )


def namespace_gui_commands(dist):
    """Prefix global FreeCAD GUI command IDs so both workbenches can coexist."""
    command_pattern = re.compile(
        r'(?:Gui|FreeCADGui)\.addCommand\(\s*["\']([^"\']+)["\']'
    )
    command_ids = set()
    for py in dist.rglob("*.py"):
        command_ids.update(command_pattern.findall(py.read_text(encoding="utf-8")))

    if not command_ids:
        raise RuntimeError("No FreeCAD GUI command IDs found; upstream structure changed.")

    # Replace exact Python string literals matching registered command IDs.
    # This covers both addCommand() registration and toolbar/menu command lists.
    for py in dist.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        original = text
        for cmd in sorted(command_ids, key=len, reverse=True):
            prefixed = "LCIE_" + cmd
            text = text.replace(f'"{cmd}"', f'"{prefixed}"')
            text = text.replace(f"'{cmd}'", f"'{prefixed}'")
        if text != original:
            py.write_text(text, encoding="utf-8")

    # Validate that every registered command now has our prefix.
    remaining = []
    for py in dist.rglob("*.py"):
        for cmd in command_pattern.findall(py.read_text(encoding="utf-8")):
            if not cmd.startswith("LCIE_"):
                remaining.append((str(py.relative_to(dist)), cmd))
    if remaining:
        raise RuntimeError(f"Unnamespaced GUI commands remain: {remaining}")

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
    patch_workbench_identity(DIST)
    namespace_python_modules(DIST)
    namespace_gui_commands(DIST)
    update_package(DIST / "package.xml", version)
    write_extended_readme(DIST, version)

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
