# Changelog

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
