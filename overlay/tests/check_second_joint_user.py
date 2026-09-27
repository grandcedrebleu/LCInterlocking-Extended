from check_geometry_cadquery import *
import zipfile
import tempfile
work=Path(tempfile.mkdtemp(prefix='lcie-test-'))
with zipfile.ZipFile(sys.argv[1]) as z:
 def read(n):
  p=work/(n+'.brp');p.write_bytes(z.read(n+'.Shape.brp'));return cq.Shape.importBrep(str(p))
 original=read('Extrude001');existing=read('LCIE_FingersB002');source=read('Extrude')
 link=source.translate((0,-4,0)).rotate((0,0,0),(1,0,0),60).translate((0,-31,72))
 face=original.Faces()[2]
 matches=[f for f in existing.Faces() if (f.Center()-face.Center()).Length<1e-5]
 assert len(matches)==1
 out,angle,pitch=build(Wrap(existing),Wrap(matches[0]),Wrap(link),Wrap(link.Faces()[1]))
 # Protect the half of the panel farthest from the new selected end.
 from lcie_lasercut.finger_oblique import frame,prism
 o,x,y,z,lim=frame(Wrap(existing),Wrap(matches[0]))
 protect=prism(o,x,y,z,lim[0][0]-1,lim[0][0]/2,lim[1][0]-1,lim[1][1]+1,lim[2][0]-1,lim[2][1]+1)
 old=Wrap(existing).common(protect);new=out[0].common(protect)
 assert old.cut(new).Volume<1e-5 and new.cut(old).Volume<1e-5
 assert out[0].common(out[1]).Volume<1e-5
 print('USER FILE: second joint valid; existing fingers preserved (symmetric difference <1e-5 mm3); no collision; angle',angle)
