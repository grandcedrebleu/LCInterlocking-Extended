# Compatibility

## LCInterlocking Extended 1.0.0

| Component | Version / status |
|---|---|
| LCInterlocking Extended | 1.0.0 |
| LCInterlocking upstream baseline | 1.5.1 |
| Installation method | FreeCAD Addon Manager |
| Through-cut margin tested | 0.100 mm per side |
| Validation date | 2026-08-27 |

## FreeCAD validation matrix

| FreeCAD | Extended | Upstream baseline | Addon Manager install | MultiJoin margin | Residual-skin regression | Status |
|---|---|---|---|---|---|---|
| 1.1.1 | 1.0.0 | LCInterlocking 1.5.1 | PASS | 0.100 mm | No residual skin | PASS |
| 1.1.3 | 1.0.0 | LCInterlocking 1.5.1 | PASS | 0.100 mm | No residual skin | PASS |

## Validated behavior

LCInterlocking Extended 1.0.0 was installed and functionally tested with FreeCAD
1.1.1 and FreeCAD 1.1.3 using the generated `dist` branch of the repository.

The following checks passed:

1. FreeCAD recognizes the addon as **LCInterlocking Extended**.
2. The workbench appears as **Laser Cut Interlocking Extended**.
3. MultiJoin exposes **Cut parameters → Marge traversante**.
4. The default value is **0.100 mm**.
5. Preview/final generation loads the Extended code successfully.
6. A real slot that previously produced a thin residual bottom face was regenerated.
7. No residual skin was observed.

## Exact FreeCAD build

Before publishing the final `v1.0.0` tag, replace the line below with the exact
information copied from **Help → About FreeCAD → Copy to clipboard**:

```text
Validated FreeCAD releases: 1.1.1 and 1.1.3
```

This information is intentionally not guessed.

## Future FreeCAD versions

No FreeCAD installation path is hard-coded in LCInterlocking Extended. Installation
is delegated to FreeCAD's Addon Manager, so version-specific user `Mod` directory
changes do not require changes to this project.

A new FreeCAD version is not automatically considered compatible merely because the
addon installs successfully.

For every FreeCAD major/minor release to be declared supported:

1. install LCInterlocking Extended using that FreeCAD instance;
2. confirm the workbench loads;
3. confirm `Marge traversante` is available;
4. run the residual-skin regression case;
5. test MultiJoin preview;
6. test final MultiJoin generation;
7. record the exact FreeCAD version/build here;
8. update the changelog if a new Extended release is required.

## Upstream LCInterlocking upgrades

The complete workbench is regenerated from the version pinned in `UPSTREAM`.

When upgrading the upstream baseline:

1. change the upstream `ref`;
2. run the guarded build;
3. investigate any failed patch anchor;
4. verify whether upstream has implemented an equivalent fix;
5. rebuild;
6. repeat all functional regression tests;
7. update this compatibility matrix.

A successful source build alone is not sufficient to declare compatibility.
