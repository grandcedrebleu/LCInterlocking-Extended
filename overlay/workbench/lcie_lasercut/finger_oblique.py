"""Oblique open-edge fingers; LGPL-2.1-or-later.

Prototype: rectangular solid panels, two selected end faces.
All coordinates are document coordinates. Cutters are prisms normal to each
panel, so the output retains straight (2D laser) edges through its thickness.
"""
import math
import FreeCAD as App
import Part

EPS = 1e-7
END_SNAP_TOLERANCE = 0.10  # mm: bridge small axial discrepancies at joint ends


def unit(v):
    if v.Length < EPS:
        raise ValueError('Direction de longueur nulle.')
    return v / v.Length


def prism(origin, x, y, z, x0, x1, y0, y1, z0, z1):
    pts = [origin+x*a+y*b+z*z0 for a,b in
           [(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)]]
    return Part.Face(Part.makePolygon(pts)).extrude(z*(z1-z0))


def frame(shape, face):
    if len(shape.Solids) != 1 or not shape.isValid():
        raise ValueError('Choisir un panneau valide constitué d’un seul solide.')
    if any(not isinstance(f.Surface, Part.Plane) for f in shape.Faces):
        raise ValueError('Les faces doivent être planes.')
    n = unit(face.normalAt(0, 0))
    broad = max(shape.Faces, key=lambda f: f.Area)
    z = unit(broad.normalAt(0, 0))
    if abs(n.dot(z)) > 1e-6:
        raise ValueError('Sélectionner un chant, pas une grande face du panneau.')
    y = unit(z.cross(n))
    o = face.CenterOfMass
    coords = [( (v.Point-o).dot(n), (v.Point-o).dot(y), (v.Point-o).dot(z))
              for v in shape.Vertexes]
    limits = [(min(p[k] for p in coords), max(p[k] for p in coords)) for k in range(3)]
    # Existing fingers on other ends are allowed, provided the panel remains
    # a constant-thickness extrusion and the selected end is a full rectangle.
    thickness = limits[2][1]-limits[2][0]
    tol = max(1e-5,shape.Volume*1e-6)
    envelope = broad.extrude(-z*thickness)
    if shape.cut(envelope).Volume > tol or envelope.cut(shape).Volume > tol:
        raise ValueError('Le panneau doit avoir une épaisseur constante, sans biseau ni poche partielle.')
    expected_area = (limits[1][1]-limits[1][0])*thickness
    if len(face.Vertexes) != 4 or abs(face.Area-expected_area) > max(1e-5,expected_area*1e-6):
        raise ValueError('Choisir un chant terminal rectangulaire entier, pas un doigt déjà découpé.')
    if limits[0][1] > 1e-5:
        raise ValueError('Le chant sélectionné doit être une face extérieure terminale.')
    return o,n,y,z,limits


def extend(shape, face, data, other, other_data, overhang):
    o,x,y,z,lim = data
    span = max(shape.BoundBox.DiagonalLength, other.BoundBox.DiagonalLength,
               (shape.BoundBox.Center-other.BoundBox.Center).Length)*4 + 100
    slab = prism(o,x,y,z,-span,span,-span,span,lim[2][0],lim[2][1])
    oo,ox,oy,oz,ol = other_data
    other_slab = prism(oo,ox,oy,oz,-span,span,ol[1][0],ol[1][1],ol[2][0],ol[2][1])
    crossing = other_slab.common(slab)
    if crossing.isNull() or crossing.Volume < EPS:
        raise ValueError('Les plans des panneaux ne se croisent pas dans leur zone utile.')
    reach = max((v.Point-o).dot(x) for v in crossing.Vertexes)
    if reach < -max(lim[2][1]-lim[2][0], 1)*10:
        raise ValueError('Chant trop éloigné du croisement : choisir le chant proche de la jonction.')
    length = reach + overhang
    if length <= lim[0][0] + EPS:
        raise ValueError("Le dépassement demandé supprimerait tout le panneau.")
    if length < -EPS:
        keep = prism(o,x,y,z,lim[0][0]-0.1,length,
                     lim[1][0]-0.1,lim[1][1]+0.1,lim[2][0]-0.1,lim[2][1]+0.1)
        return shape.common(keep).removeSplitter()
    if length < EPS:
        return shape.copy()
    # Small inward overlap makes the union robust to coincident surfaces.
    f = face.copy()
    f.translate(x*(-1e-5))
    return shape.fuse(f.extrude(x*(length+1e-5))).removeSplitter()


def projected_cutter(common, data, extended):
    # An OPEN notch must reach the extended end, not stop at the overlap.
    # With rectangular panels and parallel joint edges, the footprint is a
    # rectangle in (outward direction, joint axis).
    o,x,y,z,lim = data
    xs = [(v.Point-o).dot(x) for v in common.Vertexes]
    ys = [(v.Point-o).dot(y) for v in common.Vertexes]
    end = max((v.Point-o).dot(x) for v in extended.Vertexes)
    return prism(o,x,y,z,min(xs)-1e-7,end+0.1,
                 min(ys)-0.1,max(ys)+0.1,lim[2][0]-0.1,lim[2][1]+0.1)


def build(shape_a, face_a, shape_b, face_b, count=6, overhang_a=3.0,
          overhang_b=3.0, gap=0.05, invert=False):
    if int(count) != count or not 2 <= count <= 100:
        raise ValueError('Nombre de bandes : entier entre 2 et 100.')
    if any(not math.isfinite(v) or v < 0 for v in (overhang_a, overhang_b, gap)):
        raise ValueError('Dépassements et jeu : valeurs positives ou nulles.')
    da,db = frame(shape_a,face_a),frame(shape_b,face_b)
    axis = unit(da[3].cross(db[3]))
    angle = math.degrees(math.acos(min(1.0,abs(da[3].dot(db[3])))))
    if angle < 10:
        raise ValueError('Prototype : angle aigu entre plans au moins égal à 10 degrés.')
    if abs(abs(axis.dot(da[2]))-1) > 1e-6 or abs(abs(axis.dot(db[2]))-1) > 1e-6:
        raise ValueError('Les chants sélectionnés doivent suivre la ligne de croisement.')
    # Stable ordering of the bands, independent of outward normal signs.
    for component in (axis.z,axis.y,axis.x):
        if abs(component) > EPS:
            if component < 0: axis = -axis
            break
    a = extend(shape_a,face_a,da,shape_b,db,overhang_a)
    b = extend(shape_b,face_b,db,shape_a,da,overhang_b)
    common = a.common(b)
    if common.isNull() or common.Volume < EPS:
        raise ValueError('Aucun volume commun après prolongement des chants.')
    low = min(v.Point.dot(axis) for v in common.Vertexes)
    high = max(v.Point.dot(axis) for v in common.Vertexes)
    pitch = (high-low)/count
    if gap >= pitch*0.25:
        raise ValueError('Jeu trop grand par rapport à la largeur des doigts.')
    cutters = [projected_cutter(common,d,s) for d,s in zip((da,db),(a,b))]
    # Only a coordinate reference is needed here, not a mass centroid.
    # FreeCAD Part.Compound does not expose CenterOfMass.
    center = common.BoundBox.Center
    u = da[3]
    v = unit(axis.cross(u))
    span = max(a.BoundBox.DiagonalLength,b.BoundBox.DiagonalLength)*3+100
    results = [a,b]
    for i in range(count):
        target = (i + int(bool(invert)) + 1) % 2
        start = low+i*pitch-gap/2-1e-7
        stop = low+(i+1)*pitch+gap/2+1e-7
        # Bridge only small mismatches at the two OUTER ends, never internal
        # finger boundaries or intentionally longer panel edges.
        axial = [vertex.Point.dot(axis) for vertex in (a,b)[target].Vertexes]
        if i == 0 and low-min(axial) <= END_SNAP_TOLERANCE+EPS:
            start = min(start,min(axial)-0.1)
        if i == count-1 and max(axial)-high <= END_SNAP_TOLERANCE+EPS:
            stop = max(stop,max(axial)+0.1)
        band = prism(center,u,v,axis,-span,span,-span,span,
                     start-center.dot(axis),stop-center.dot(axis))
        cut = cutters[target].common(band)
        results[target] = results[target].cut(cut)
    results = [s.removeSplitter() for s in results]
    for s in results:
        if s.isNull() or not s.isValid() or len(s.Solids) != 1:
            raise ValueError('Résultat non valide ou panneau fragmenté : revoir les chants sélectionnés.')
    if results[0].common(results[1]).Volume > 1e-5:
        raise ValueError('Collision résiduelle entre les panneaux : résultat refusé.')
    return results, angle, pitch
