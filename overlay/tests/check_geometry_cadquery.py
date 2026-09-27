"""Run the production geometry module against CadQuery/OpenCascade.
Small adapter only translates FreeCAD Part API calls; no replacement algorithm.
"""
import sys,types,math
from pathlib import Path
import cadquery as cq
V=cq.Vector
class Plane: pass
class Wrap:
 def __init__(self,s): self.s=s
 @property
 def Solids(self): return [Wrap(s) for s in self.s.Solids()]
 @property
 def Faces(self): return [Wrap(s) for s in self.s.Faces()]
 @property
 def Vertexes(self): return [types.SimpleNamespace(Point=V(*v.toTuple())) for v in self.s.Vertices()]
 @property
 def Surface(self): return Plane() if self.s.geomType()=='PLANE' else None
 @property
 def Area(self): return self.s.Area()
 @property
 def Volume(self): return self.s.Volume() if self.s.Solids() else 0
 @property
 def CenterOfMass(self):
  if isinstance(self.s,cq.Compound): raise AttributeError("'Part.Compound' object has no attribute 'CenterOfMass'")
  return self.s.Center()
 @property
 def BoundBox(self):
  b=self.s.BoundingBox()
  return types.SimpleNamespace(Center=V((b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,(b.zmin+b.zmax)/2),DiagonalLength=math.sqrt(b.xlen**2+b.ylen**2+b.zlen**2))
 def normalAt(self,*a): return self.s.normalAt()
 def common(self,o): return Wrap(self.s.intersect(o.s))
 def cut(self,o): return Wrap(self.s.cut(o.s))
 def fuse(self,o): return Wrap(self.s.fuse(o.s))
 def copy(self): return Wrap(self.s.copy())
 def translate(self,v): self.s=self.s.translate(v)
 def removeSplitter(self): return Wrap(self.s.clean())
 def isNull(self): return self.s.isNull()
 def isValid(self): return self.s.isValid()
 def extrude(self,v): return Wrap(cq.Solid.extrudeLinear(self.s.outerWire(),self.s.innerWires(),v))
sys.modules['FreeCAD']=types.SimpleNamespace(Vector=V)
sys.modules['Part']=types.SimpleNamespace(Plane=Plane,makePolygon=lambda pts:cq.Wire.makePolygon(pts),Face=lambda w:Wrap(cq.Face.makeFromWires(w)))
root = next((p for p in Path(__file__).resolve().parents if (p/'lcie_lasercut').is_dir()), Path(__file__).resolve().parents[1]/'prototype/LCInterlocking-Extended')
sys.path.insert(0,str(root))
from lcie_lasercut.finger_oblique import build

def case(angle,ta,tb):
 # Both bodies extend along negative local X, outgoing end at X=0.
 a=cq.Solid.makeBox(60,ta,72,V(-60,-ta/2,0))
 b=cq.Solid.makeBox(60,tb,72,V(-60,-tb/2,0)).rotate((0,0,0),(0,0,1),angle)
 na=V(1,0,0); nb=V(math.cos(math.radians(angle)),math.sin(math.radians(angle)),0)
 fa=max(a.Faces(),key=lambda f:f.normalAt().dot(na))
 fb=max(b.Faces(),key=lambda f:f.normalAt().dot(nb))
 return Wrap(a),Wrap(fa),Wrap(b),Wrap(fb)

if __name__=='__main__':
 results=[]
 for angle in [30,45,60,90,120,150]:
  for ta,tb in [(3,3),(5,5),(3,5)]:
   args=case(angle,ta,tb)
   out,acute,pitch=build(*args,count=6,overhang_a=3,overhang_b=4,gap=.05)
   assert all(s.Volume>0 and len(s.Solids)==1 and s.isValid() for s in out)
   assert out[0].common(out[1]).Volume<1e-5
   # Verify OPEN comb teeth at the outer tips, alternating on both panels.
   for k,(s,th,otherth,extra) in enumerate(zip(out,[ta,tb],[tb,ta],[3,4])):
    theta=math.radians(angle)
    reach=(otherth/2+th/2*abs(math.cos(theta)))/abs(math.sin(theta))
    direction=V(1,0,0) if k==0 else V(math.cos(theta),math.sin(theta),0)
    for band in range(6):
     point=direction*(reach+extra-.01)+V(0,0,(band+.5)*12)
     present=any(sol.s.isInside(point,1e-6) for sol in s.Solids)
     assert present == (band%2==k), (angle,ta,tb,k,band,'not open/alternating')
   results.append((angle,ta,tb,'PASS'))
   if angle==60 and ta==3 and tb==5 and Path('checks').is_dir():
    for i,s in enumerate(out): cq.exporters.export(s.s,'checks/result_%s.step'%i)
 print(results)

if __name__ == '__main__':
 args=list(case(60,3,5))
 for index in (0,2):
  args[index]=Wrap(cq.Compound.makeCompound([args[index].s]))
  assert not hasattr(args[index],'CenterOfMass')
 out,_,_=build(*args)
 assert all(s.isValid() and len(s.Solids)==1 for s in out)
 assert out[0].common(out[1]).Volume<1e-5
 print('Regression: compound sources and compound intersection: PASS')
