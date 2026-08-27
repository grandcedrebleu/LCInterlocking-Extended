# Compatibility

## 1.0.0 baseline

| Component | Baseline / status |
|---|---|
| LCInterlocking | 1.5.1 |
| FreeCAD | 1.1.x validation target |
| Python | supplied by FreeCAD |
| Qt | supplied by FreeCAD |
| OpenCASCADE | supplied by FreeCAD |

The build script validates the upstream source anchors before altering anything.
A successful source build does **not** by itself certify a new FreeCAD major/minor
version: the regression case must still be run in that FreeCAD version.

## Future FreeCAD versions

No FreeCAD installation path is hard-coded. Installation is delegated to FreeCAD's
Addon Manager.

For every new FreeCAD release:
1. install the generated Extended workbench through that FreeCAD instance;
2. run the representative slot regression;
3. verify MultiJoin preview and final generation;
4. record the result here;
5. publish a new patch/minor release if needed.
