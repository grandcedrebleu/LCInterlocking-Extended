# LCInterlocking Extended

**Version 1.2.1**

LCInterlocking Extended is a maintained FreeCAD workbench based on the original
LCInterlocking project by execuc.

Repository:
https://github.com/grandcedrebleu/LCInterlocking-Extended

## What Extended adds

This distribution adds a configurable **through-cut margin** to MultiJoin operations.

From version 1.1.0, its Python packages and FreeCAD GUI command IDs are namespaced so it can coexist safely with the standard LCInterlocking addon.

From version 1.2.0, Extended also accepts derived single-solid geometry whose planar
faces have been altered by Cut, Pocket, other boolean operations, Slice and Slice Apart.

Default value:

- 0.10 mm on each side of the contact plane
- 0.20 mm total extension of the boolean cutting solid

The purpose is to prevent the very thin residual face ("skin") that can remain at the
bottom of a slot when the cutting solid ends exactly on the opposite face.

## Derived geometry support

Version 1.2.0 removes the historical four-edge-face limitation for planar laser-cut parts.
LCInterlocking Extended can work from the final Shape of a single solid produced by
Part/PartDesign boolean operations and by individual Slice Apart / CompoundFilter results.

Supported workflows include Cut, Fuse, Common, Pocket, BooleanFragments, Slice and
Slice Apart, provided the selected result resolves to one valid solid. Multi-solid
containers are rejected explicitly instead of guessing which solid to use.

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
