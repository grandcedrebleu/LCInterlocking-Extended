from check_geometry_cadquery import *
a,fa,b,fb=case(90,5,5)
b.translate(V(0,0,-.08));fb.translate(V(0,0,-.08))
out,_,_=build(a,fa,b,fb)
def inside(s,p):return any(x.s.isInside(V(*p),1e-7) for x in s.Solids)
assert not inside(out[0],(4,0,71.99)), 'Peau terminale A présente'
assert not inside(out[1],(0,4,-.07)), 'Peau terminale B présente'
assert inside(out[0],(-30,0,71.99)), 'Corps A altéré'
print('Décalage axial 0,08 mm : extrémités ouvertes, corps préservé : OK')
