# Maintenance and upstream upgrades

## Principle

Never copy new upstream files manually over Extended.

The authoritative baseline is `UPSTREAM`. The complete workbench is regenerated.

## Upgrade procedure

1. Check the new upstream `package.xml` version.
2. Change `ref=` in `UPSTREAM` to the chosen tag/commit.
3. Run:
   `python scripts/build_dist.py`
4. If an anchor guard fails, inspect the upstream change before adapting the patcher.
5. Run static checks.
6. Test the residual-skin regression in the target FreeCAD version.
7. Test normal MultiJoin preview and final compute.
8. Update `COMPATIBILITY.md` and `CHANGELOG.md`.
9. Commit.
10. Tag the Extended release.
11. Build the release ZIP and publish it.

## Why guarded textual transforms

Only two upstream implementation areas are changed. Guarded transforms keep the
difference explicit and reviewable. If upstream later implements an equivalent fix,
the transform will stop matching and force a human review instead of double-applying
the workaround.

## Upstream contribution

If the correction is accepted upstream, Extended should either:
- drop the local patch and retain only any additional UX/tests, or
- be retired in favor of upstream LCInterlocking.
