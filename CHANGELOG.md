# Changelog

## 1.0.0 - 2026-08-27

Baseline: upstream LCInterlocking 1.5.1.

### Added
- `CutThroughMargin` property on MultiJoin, default 0.10 mm.
- `Marge traversante` editor in the MultiJoin dialog.
- Propagation of the margin to preview and final join generation.
- Through-cut extension of the slot tool on both sides of the contact plane.
- Guarded build process tied to an explicit upstream reference.
- Compatibility and maintenance documentation.
- Regression diagnostic macros retained from the original investigation.

### Maintenance policy
A new Extended release must be built and tested whenever the pinned LCInterlocking
baseline or supported FreeCAD version changes.
