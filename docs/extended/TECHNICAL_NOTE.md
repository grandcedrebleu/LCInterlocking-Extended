# Residual slot skin — technical note

## Symptom

A slot whose cutting solid ended exactly on the opposite face could leave a very thin
residual face ("skin") after the OpenCASCADE boolean cut.

## Upstream 1.5.1 behavior

`lasercut/helper.py::tab_join_create_hole_on_plane()` creates a box whose X length is
exactly `material_plane.thickness` and whose origin is X=0.

## Extended behavior

Extended uses a margin `m`:

- origin X = `-m`
- box length = `material_plane.thickness + 2*m`

Default `m = 0.10 mm`.

This makes the boolean tool cross both limiting faces instead of being exactly
coincident with them.

## Scope

The margin changes only the penetration of the boolean cutting solid along its local
X axis. Width, laser compensation, tab spacing and material thickness definitions
retain upstream behavior.
