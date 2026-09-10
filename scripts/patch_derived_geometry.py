#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "LCInterlockingExtended"
HELPER = DIST / "lcie_lasercut" / "helper.py"
MATERIAL = DIST / "lcie_lasercut" / "material.py"
TOOLWIDGET = DIST / "lcie_panel" / "toolwidget.py"
README = DIST / "README.md"


def replace_function(text, name, replacement):
    pattern = re.compile(
        rf"(?ms)^def {re.escape(name)}\([^\n]*\):\n.*?(?=^def |\Z)"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            f"{name}: expected exactly one generated function, found {len(matches)}"
        )
    return text[:matches[0].start()] + replacement.rstrip() + "\n\n" + text[matches[0].end():]


def patch_helper():
    text = HELPER.read_text(encoding="utf-8")

    replacement = r'''def get_local_axis(face):
    """Return a stable local frame for any planar polygonal face.

    Upstream LCInterlocking assumes the selected face is a quadrilateral.  Boolean
    operations, PartDesign pockets and Slice Apart frequently add or split edges,
    while the resulting face is still perfectly planar and valid for laser-cut
    interlocking.  Extended derives the frame from all usable edge directions and
    computes the actual face spans by projection.
    """
    if face is None or len(face.Edges) < 2:
        raise ValueError("Selected face has insufficient geometry")

    try:
        normal_face = face.normalAt(0, 0)
    except Exception as ex:
        raise ValueError("Selected face is not suitable for interlocking: %s" % ex)

    if normal_face.Length < 1e-9:
        raise ValueError("Selected face has an invalid normal")

    # FreeCAD.Vector.normalize() and multiply() may mutate the vector instance.
    # Keep the face normal immutable throughout frame construction.
    x_local = FreeCAD.Vector(normal_face)
    x_local.normalize()

    # Candidate directions are chords of the face edges.  This deliberately avoids
    # any dependency on edge count or wire ordering.  Curved edges are harmless:
    # their chord is only used if it contributes a meaningful planar direction.
    candidates = []
    for edge in face.Edges:
        vertices = edge.Vertexes
        if len(vertices) < 2:
            continue
        vec = vertices[-1].Point.sub(vertices[0].Point)
        if vec.Length < 1e-7:
            continue

        # Remove numerical component normal to the face without mutating x_local.
        normal_component = FreeCAD.Vector(x_local)
        normal_component.multiply(vec.dot(x_local))
        projected = FreeCAD.Vector(vec)
        projected.sub(normal_component)
        if projected.Length < 1e-7:
            continue

        # Normalize a copy so the projected length remains available for ranking.
        direction = FreeCAD.Vector(projected)
        direction.normalize()

        # Cluster parallel/anti-parallel directions and retain representative span.
        found = False
        for item in candidates:
            if compare_freecad_vector_direction(direction, item[0], 1e-5):
                item[1] += projected.Length
                item[2] = max(item[2], projected.Length)
                found = True
                break
        if not found:
            candidates.append([direction, projected.Length, projected.Length])

    if len(candidates) < 2:
        raise ValueError("Unable to derive two in-plane directions from selected face")

    # The longitudinal direction is the most significant edge direction.  Prefer
    # maximum individual span, then accumulated edge length for deterministic ties.
    candidates.sort(key=lambda item: (item[2], item[1]), reverse=True)
    y_dir = candidates[0][0]

    # Select the strongest direction sufficiently transverse to Y.  Laser-cut sheet
    # faces are normally orthogonal, but this tolerates non-rectangular outlines.
    transverse = []
    for item in candidates[1:]:
        sine = y_dir.cross(item[0]).Length
        if sine > 0.25:
            transverse.append((sine, item[2], item[1], item[0]))
    if not transverse:
        raise ValueError("Unable to derive transverse direction from selected face")
    transverse.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)

    # Orthogonalize the secondary direction so the transformation remains rigid.
    z_dir = x_local.cross(y_dir)
    if z_dir.Length < 1e-9:
        raise ValueError("Degenerate local frame")
    z_dir.normalize()
    if y_dir.cross(z_dir).dot(x_local) < 0:
        z_dir = z_dir.negative()

    points = [vertex.Point for vertex in face.Vertexes]
    if len(points) < 3:
        raise ValueError("Selected face has insufficient vertices")

    y_proj = [point.dot(y_dir) for point in points]
    z_proj = [point.dot(z_dir) for point in points]
    y_span = max(y_proj) - min(y_proj)
    z_span = max(z_proj) - min(z_proj)

    if y_span < 1e-7 or z_span < 1e-7:
        raise ValueError("Selected face has a degenerate projected extent")

    y_local_not_normalized = FreeCAD.Vector(y_dir)
    y_local_not_normalized.multiply(y_span)
    z_local_not_normalized = FreeCAD.Vector(z_dir)
    z_local_not_normalized.multiply(z_span)
    return x_local, y_local_not_normalized, z_local_not_normalized
'''

    text = replace_function(text, "get_local_axis", replacement)
    HELPER.write_text(text, encoding="utf-8")


def patch_material():
    text = MATERIAL.read_text(encoding="utf-8")

    replacement = r'''def retrieve_thickness_from_biggest_face(freecad_object):
    """Estimate sheet thickness from the final Shape, independent of feature history.

    The upstream implementation matches vertices between two quadrilateral faces.
    That fails as soon as Cut/Pocket/Boolean/Slice operations alter face topology.
    Extended instead evaluates projection spans along planar face normals and uses
    the smallest stable span of the resulting solid as the sheet thickness.
    """
    shape = freecad_object.Shape
    if shape is None or shape.isNull():
        raise ValueError("Object has no valid Shape")

    solids = list(shape.Solids)
    if len(solids) > 1:
        raise ValueError(
            "LCInterlocking Extended requires a single solid; "
            "select one Slice Apart result or one individual solid"
        )
    if len(solids) == 1:
        shape = solids[0]

    vertices = [vertex.Point for vertex in shape.Vertexes]
    if len(vertices) < 4:
        raise ValueError("Not enough vertices to determine material thickness")

    normals = []
    for face in shape.Faces:
        try:
            normal = face.normalAt(0, 0)
        except Exception:
            continue
        if normal.Length < 1e-9:
            continue
        normal.normalize()

        # One representative for each parallel/anti-parallel direction.
        if not any(normal.cross(existing).Length < 1e-5 for existing in normals):
            normals.append(normal)

    spans = []
    for normal in normals:
        projections = [point.dot(normal) for point in vertices]
        span = max(projections) - min(projections)
        if span > 1e-7:
            spans.append(span)

    if not spans:
        raise ValueError("Unable to determine material thickness from final Shape")

    # For planar laser-cut parts, thickness is the smallest global extent measured
    # along a face-normal direction. Cuts, pockets and slicing do not change it.
    return min(spans)
'''

    text = replace_function(text, "retrieve_thickness_from_biggest_face", replacement)
    MATERIAL.write_text(text, encoding="utf-8")


def patch_toolwidget():
    text = TOOLWIDGET.read_text(encoding="utf-8")
    old = """    def get_properties(self):
        for widget_config in self.widget_list:
            if widget_config.type == float and not hasattr(widget_config, 'step'):
"""
    new = """    def get_properties(self):
        for widget_config in self.widget_list:
            # Selection changes can occur while an editor widget is still being
            # constructed or just after it has been removed. Such entries have no
            # live Qt widget to read and must simply be skipped.
            if widget_config.widget is None:
                continue
            if widget_config.type == float and not hasattr(widget_config, 'step'):
"""
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"toolwidget get_properties: expected exactly one generated anchor, found {count}"
        )
    TOOLWIDGET.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_readme():
    if not README.exists():
        return
    text = README.read_text(encoding="utf-8")
    marker = "## Installation\n"
    section = """## Derived geometry support\n\nVersion 1.2.0 removes the historical four-edge-face limitation for planar laser-cut parts.\nLCInterlocking Extended can work from the final Shape of a single solid produced by\nPart/PartDesign boolean operations and by individual Slice Apart / CompoundFilter results.\n\nSupported workflows include Cut, Fuse, Common, Pocket, BooleanFragments, Slice and\nSlice Apart, provided the selected result resolves to one valid solid. Multi-solid\ncontainers are rejected explicitly instead of guessing which solid to use.\n\n"""
    if section not in text:
        if marker not in text:
            raise RuntimeError("README installation marker not found")
        text = text.replace(marker, section + marker, 1)
    README.write_text(text, encoding="utf-8")


def validate():
    helper = HELPER.read_text(encoding="utf-8")
    material = MATERIAL.read_text(encoding="utf-8")
    toolwidget = TOOLWIDGET.read_text(encoding="utf-8")
    required = [
        (helper, "any planar polygonal face"),
        (helper, "for edge in face.Edges"),
        (helper, "normal_component = FreeCAD.Vector(x_local)"),
        (helper, "direction = FreeCAD.Vector(projected)"),
        (material, "requires a single solid"),
        (material, "return min(spans)"),
        (toolwidget, "if widget_config.widget is None:"),
    ]
    missing = [needle for text, needle in required if needle not in text]
    if missing:
        raise RuntimeError("Derived geometry patch validation failed: " + ", ".join(missing))

    forbidden = [
        "projected = vec.sub(x_local.multiply(vec.dot(x_local)))",
        "direction = projected.normalize()",
    ]
    present = [needle for needle in forbidden if needle in helper]
    if present:
        raise RuntimeError(
            "Unsafe mutating vector expressions remain: " + ", ".join(present)
        )


if __name__ == "__main__":
    if not HELPER.exists() or not MATERIAL.exists() or not TOOLWIDGET.exists():
        raise RuntimeError("Run scripts/build_dist.py before patch_derived_geometry.py")
    patch_helper()
    patch_material()
    patch_toolwidget()
    patch_readme()
    validate()
    print("Derived geometry support patch applied")
