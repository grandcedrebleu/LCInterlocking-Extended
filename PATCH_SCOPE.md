# Patch scope

LCInterlocking Extended 1.2.1 is generated from the pinned LCInterlocking upstream
baseline and applies only reviewed, guarded changes.

Upstream implementation areas altered by the generated build:

- `lasercut/helper.py`
  - through-cut margin support;
  - generalized local-axis detection for planar faces with any edge count;
  - non-mutating vector handling while constructing the local frame.
- `lasercut/material.py`
  - thickness detection from final single-solid geometry instead of matching quad vertices.
- `panel/toolwidget.py`
  - safe handling of selection changes while parameter widgets are not yet instantiated.
- `panel/multiplejoins.py`
  - through-cut margin property and editor propagation.
- `package.xml`
  - distribution metadata only.

The derived-geometry and related UI-stability patch is applied after Python package
namespacing by `scripts/patch_derived_geometry.py` to the generated Extended package.

Intended supported derived geometry includes Part/PartDesign boolean results and
individual Slice Apart / CompoundFilter results, provided the selected object resolves
to one valid solid. Multi-solid containers are rejected explicitly.

Everything else is copied unmodified from the pinned LCInterlocking upstream reference.
The build is guarded and must stop for review if expected source anchors change.
