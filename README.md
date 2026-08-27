# LCInterlocking Extended

Maintained FreeCAD workbench distribution based on **execuc/LCInterlocking**, with a
configurable through-cut margin that prevents residual "skin" at the bottom of slots.

## Version

- LCInterlocking Extended: **1.0.0**
- Upstream baseline: **LCInterlocking 1.5.1**
- License: **LGPL-2.1-or-later**

## Why this repository is structured this way

The upstream workbench continues to evolve. Instead of maintaining an opaque copy of
every upstream file, this repository keeps:

1. the exact upstream reference in `UPSTREAM`;
2. a deterministic patcher in `scripts/build_dist.py`;
3. Extended-specific documentation and regression diagnostics in `overlay/`;
4. a GitHub Actions workflow that rebuilds the complete installable workbench.

The generated `dist/` tree is a **complete FreeCAD workbench**. That tree is what is
published for installation through FreeCAD's Addon Manager.

If the upstream source changes around one of the guarded patch anchors, the build
**fails deliberately**. That prevents a future FreeCAD/LCInterlocking update from
silently dropping or corrupting the correction.

## Functional change

For each MultiJoin, Extended adds:

- `CutThroughMargin` (`App::PropertyLength`), default **0.10 mm**;
- an editor labelled **Marge traversante**;
- propagation of that value to each tab/slot calculation;
- extension of the slot cutting solid on both sides of the contact plane.

With a 0.10 mm margin, the cutting solid is extended by 0.10 mm on each side,
i.e. 0.20 mm total.

## Build locally

A machine with Git and Python 3:

```bash
python scripts/build_dist.py
```

This clones the pinned upstream revision, applies the guarded changes and creates
`dist/LCInterlockingExtended`.

## GitHub publication model

- `main`: maintenance source, tests, patcher and documentation.
- `dist`: generated complete workbench tree for FreeCAD Addon Manager.
- tag `v1.0.0`: source release.
- release asset: `LCInterlockingExtended-1.0.0.zip`.

See `overlay/docs/MAINTENANCE.md`.

## FreeCAD installation

Once the repository is published and added to the FreeCAD Addon catalog, users install
**LCInterlocking Extended** from FreeCAD's Addon Manager. FreeCAD itself determines the
correct user `Mod` directory for the running FreeCAD version: no Windows path is encoded
in this project.

Until catalog inclusion, the generated `dist/LCInterlockingExtended` tree can be used
as a custom Addon Manager source or installed manually for testing.

## Attribution

Based on LCInterlocking by execuc. Original project:
https://github.com/execuc/LCInterlocking

The original code is licensed under LGPL-2.1-or-later.
