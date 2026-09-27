from check_geometry_cadquery import *
# Minimal application bindings: execute the REAL feature proxy and geometry.
# Qt visual interaction and FreeCAD undo engine are not emulated by this test.
class Dialog: pass
sys.modules['FreeCADGui']=types.SimpleNamespace(addCommand=lambda *a:None)
sys.modules['PySide']=types.SimpleNamespace(QtGui=types.SimpleNamespace(QDialog=Dialog),QtCore=object())
sys.modules['FreeCAD'].Console=types.SimpleNamespace(PrintError=print)
from lcie_panel.finger_oblique import FingerProxy,count_for_width
class Quantity:
 def __init__(self,v):self.Value=v
class Obj:
 def __init__(self):object.__setattr__(self,'PropertiesList',[]);object.__setattr__(self,'kinds',{})
 def addProperty(self,kind,name,*args):
  self.PropertiesList.append(name);self.kinds[name]=kind;setattr(self,name,False if kind.endswith('Bool') else None);return self
 def setEditorMode(self,*a):pass
 def __setattr__(self,name,value):
  kind=self.__dict__.get('kinds',{}).get(name,'')
  if value is not None and (kind.endswith('Length') or kind.endswith('Angle')):value=Quantity(value)
  if kind.endswith('Enumeration') and isinstance(value,list):value=value[0]
  object.__setattr__(self,name,value)
a,fa,b,fb=case(60,3,5)
a.getElement=lambda n:fa;b.getElement=lambda n:fb
Wrap.isNull=lambda self:False
sys.modules['Part'].getShape=lambda obj,name,needSubElement=False,transform=True: obj.Shape.getElement(name) if needSubElement else obj.Shape
obj=Obj();FingerProxy(obj)
obj.PanelA=(types.SimpleNamespace(Shape=a,getParentGeoFeatureGroup=lambda:None),['Face1']);obj.PanelB=(types.SimpleNamespace(Shape=b,getParentGeoFeatureGroup=lambda:None),['Face1'])
obj.ResultA=types.SimpleNamespace(Shape=None);obj.ResultB=types.SimpleNamespace(Shape=None)
obj.SizingMode='Largeur souhaitée';obj.RequestedWidth=10
obj.Proxy.execute(obj)
assert obj.BandCount==7
assert abs(obj.BandWidth.Value-72/7)<1e-6
obj.RequestedWidth=12;obj.Proxy.execute(obj)
assert obj.BandCount==6 and abs(obj.BandWidth.Value-12)<1e-6
obj.SizingMode='Nombre de bandes';obj.BandCount=8;obj.Proxy.execute(obj)
assert obj.BandCount==8 and abs(obj.BandWidth.Value-9)<1e-6
assert obj.ResultA.Shape.common(obj.ResultB.Shape).Volume<1e-5
assert count_for_width(72,100)==2 and count_for_width(72,.01)==100
try:count_for_width(72,0)
except ValueError:pass
else:raise AssertionError('width zero accepted')
print('Feature proxy: width 10 -> 7 bands; width 12 -> 6; count 8 -> 9 mm; limits: PASS')
# A link need not expose the same Shape API as a Part feature. Ensure the
# production proxy obtains geometry via Part.getShape and keeps occurrences.
class Link:
 def __init__(self,label):self.Label=label
 def getParentGeoFeatureGroup(self):return None
 @property
 def Shape(self):raise AssertionError('Direct Link.Shape access bypasses resolver')
la,lb=Link('A'),Link('B')
geometry={la:(a,fa),lb:(b,fb)}
calls=[]
def resolve(link,name,needSubElement=False,transform=True):
 assert transform is True
 calls.append((link,needSubElement))
 return geometry[link][int(needSubElement)]
sys.modules['Part'].getShape=resolve
obj.PanelA=(la,['Face1']);obj.PanelB=(lb,['Face1'])
obj.Proxy.execute(obj)
assert obj.Status.startswith('Calcul géométrique OK'),obj.Status
assert calls==[(la,False),(la,True),(lb,False),(lb,True)]
assert obj.PanelA[0] is la and obj.PanelB[0] is lb
assert obj.ResultA.Shape.common(obj.ResultB.Shape).Volume<1e-5
print('Link resolver boundary and occurrence references: PASS (native FreeCAD API not emulated)')

from lcie_panel.finger_oblique import is_direct_face
mapped_a=';#1d:3;:G;XTR;:H146:7,F.Face3'
mapped_b=';#d:2;:G;XTR;:H144:7,F.Face2'
for name in ('Face1',mapped_a,mapped_b):assert is_direct_face(name),name
for name in ('Edge1','Face0','Face','Face2junk','Body.Face2','Link.Face3','Body.'+mapped_a):
 assert not is_direct_face(name),name
received=[]
def resolve_mapped(link,name,needSubElement=False,transform=True):
 received.append((link,name))
 return resolve(link,name,needSubElement,transform)
sys.modules['Part'].getShape=resolve_mapped
obj.PanelA=(la,[mapped_a]);obj.PanelB=(lb,[mapped_b]);obj.Proxy.execute(obj)
assert obj.Status.startswith('Calcul géométrique OK'),obj.Status
assert received==[(la,mapped_a),(la,mapped_a),(lb,mapped_b),(lb,mapped_b)]
assert obj.PanelA[1][0]==mapped_a and obj.PanelB[1][0]==mapped_b
print('Exact user mapped face names accepted and preserved; non-face/nested names rejected: PASS')
