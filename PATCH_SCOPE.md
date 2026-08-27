# Patch scope

Only these upstream implementation files are altered by the 1.0.0 build:

- `lasercut/helper.py`
- `panel/multiplejoins.py`
- `package.xml` (distribution metadata only)

Everything else is copied unmodified from the pinned LCInterlocking upstream reference.

The build is guarded: expected source anchors must occur exactly once. If upstream
changes those areas, the build stops and requires review.
