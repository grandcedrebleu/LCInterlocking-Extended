# Changelog

## 1.2.1 - 2026-09-10

### Fixed

- Prevented `get_local_axis()` from mutating the face normal while projecting edge vectors. This could collapse the local frame and raise `ValueError: Degenerate local frame` on valid derived faces, including a real `Slice Apart` result.
- Normalized copies of projected edge vectors so geometric ranking still uses the original projected edge length.
- Prevented the Parts and Tabs editor from calling `.value()` on a not-yet-created widget during selection changes (`'NoneType' object has no attribute 'value'`).

### Empirical status

- FreeCAD 1.1.3 installation through the custom `dist` repository is validated.
- A real single-solid `Slice Apart` child was correctly detected and its 10.0 mm material thickness was correctly measured by the 1.2.x final-Shape thickness logic.
- The corrected local-face frame and complete Join operation must be re-tested in FreeCAD before publishing a `v1.2.1` release tag.

## 1.2.0 - 2026-09-10

### Added

- Derived geometry support for laser-cut parts produced by boolean and split workflows.
- Generalized local-axis detection for planar faces with arbitrary edge counts.
- Thickness detection from the final single-solid Shape instead of matching vertices on quadrilateral faces.
- Intended support for:
  - Part Cut, Fuse and Common;
  - PartDesign Pocket and boolean-derived solids;
  - BooleanFragments;
  - Slice;
  - individual Slice Apart / CompoundFilter results.
- Explicit rejection of ambiguous multi-solid containers instead of selecting a solid implicitly.

### Preserved

- Configurable `CutThroughMargin` introduced by Extended.
- Default through-cut margin: **0.10 mm on each side** of the contact plane.
- Isolated Python namespace and GUI command IDs for coexistence with standard LCInterlocking.
- Pinned upstream baseline and guarded build process.

### Validation required before release tag

Test in FreeCAD with at least:

- one legacy rectangular-part MultiJoin regression case;
- one Part Cut result whose selected face has more than four edges;
- one Pocket/boolean-derived result;
- one individual Slice Apart result;
- verification that the 0.10 mm through-cut margin still removes residual bottom skin.

## 1.0.0 - 2026-08-27

First validated release of **LCInterlocking Extended**.

### Upstream baseline

- LCInterlocking upstream: **1.5.1**
- Upstream project: `execuc/LCInterlocking`

### Added

- `CutThroughMargin` property on MultiJoin.
- Default through-cut margin: **0.10 mm on each side** of the contact plane.
- User interface field:
  - **Cut parameters**
  - **Marge traversante**
- Propagation of the margin to:
  - MultiJoin preview generation;
  - final MultiJoin generation.
- Extension of the slot cutting solid across both limiting faces.
- Dedicated identity:
  - **LCInterlocking Extended**
  - **Laser Cut Interlocking Extended**
- FreeCAD Addon Manager compatible distribution via generated `dist` branch.
- Guarded build process tied to an explicit upstream LCInterlocking version.
- GitHub Actions generation of the complete installable workbench.
- Maintenance and compatibility documentation.
- Regression diagnostic macros retained from the original investigation.

### Functional validation

Validation performed on **2026-08-27** using the FreeCAD Addon Manager installation
of LCInterlocking Extended.

Validated behavior:

- Workbench appears in FreeCAD as **Laser Cut Interlocking Extended**.
- `Marge traversante` is visible in the MultiJoin interface.
- Default displayed value is **0.100 mm**.
- A real slot/interlocking case previously exhibiting a residual bottom skin was rebuilt.
- **Result: no residual skin observed.**

### FreeCAD version

The exact FreeCAD version/build used for this validation must be recorded in
`overlay/docs/COMPATIBILITY.md` before the final `v1.0.0` tag is published.

### Maintenance policy

A new Extended release must be reviewed and regression-tested whenever:

- the pinned LCInterlocking upstream baseline changes;
- a new FreeCAD major/minor version is declared supported;
- FreeCAD changes Python, Qt or OpenCASCADE behavior affecting the workbench.

The build must fail rather than silently apply the patch if guarded upstream anchors
no longer match.
