"""Dedicated parametric command for oblique fingers. LGPL-2.1-or-later."""
import os
import re
import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtGui, QtCore
try:
    from PySide import QtWidgets
except ImportError:
    QtWidgets = QtGui
from lcie_lasercut.finger_oblique import build, frame


def is_direct_face(name):
    """Accept legacy FaceN and FreeCAD mapped element names, not object paths.

    Keep the original name unchanged for Part.getShape and PropertyLinkSub.
    """
    return bool(re.fullmatch(r'(?:;[^.]*\.)?Face[1-9][0-9]*',name))


def panel_geometry(obj, face_name):
    """Resolve the selected occurrence, including LinkTransform, exactly once.

    Part.getShape applies the link chain and its placement. Never additionally
    apply LinkedObject.Placement or LinkPlacement to the returned geometry.
    Only root objects and direct face selections are supported here.
    """
    if obj.getParentGeoFeatureGroup() or not is_direct_face(face_name):
        raise ValueError('Utiliser un panneau ou un Link directement à la racine du document.')
    shape = Part.getShape(obj, face_name, needSubElement=False, transform=True)
    face = Part.getShape(obj, face_name, needSubElement=True, transform=True)
    if shape.isNull() or face.isNull():
        raise ValueError('La géométrie du panneau ou du Link est vide.')
    return shape, face


def count_for_width(length,width):
    if width <= 0:
        raise ValueError('La largeur souhaitée doit être positive.')
    return max(2,min(100,int(length/width+0.5)))


def ensure_parameters(obj):
    if 'SizingMode' not in obj.PropertiesList:
        obj.addProperty('App::PropertyEnumeration','SizingMode','Doigts')
        obj.SizingMode = ['Nombre de bandes','Largeur souhaitée']
    if 'RequestedWidth' not in obj.PropertiesList:
        obj.addProperty('App::PropertyLength','RequestedWidth','Doigts',
                        'Largeur cible ; les bandes sont réparties régulièrement.').RequestedWidth = 10


class FingerViewProvider:
    def __init__(self,vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
    def attach(self,vobj): self.Object = vobj.Object
    def getIcon(self):
        return os.path.join(os.path.dirname(__file__),'..','icons','finger_oblique.svg')
    def claimChildren(self): return self.Object.Group
    def doubleClicked(self,vobj):
        edit_dialog(vobj.Object)
        return True
    def dumps(self): return None
    def loads(self,state): pass


class ParameterDialog(QtWidgets.QDialog):
    def __init__(self,obj):
        super(ParameterDialog,self).__init__(Gui.getMainWindow())
        self.obj = obj
        self.setWindowTitle('Doigts croisés — paramètres')
        self.setMinimumWidth(510)
        layout = QtWidgets.QVBoxLayout(self)
        self.geometry = QtWidgets.QLabel()
        self.geometry.setWordWrap(True)
        layout.addWidget(self.geometry)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)
        self.mode = QtWidgets.QComboBox()
        self.mode.addItems(['Nombre de bandes','Largeur souhaitée'])
        self.mode.setCurrentIndex(1 if str(obj.SizingMode)=='Largeur souhaitée' else 0)
        form.addRow('Répartition',self.mode)
        self.count = QtWidgets.QSpinBox()
        self.count.setRange(2,100); self.count.setValue(obj.BandCount)
        form.addRow('Nombre total de bandes',self.count)
        self.width = self.length_spin(obj.RequestedWidth.Value,0.01,10000)
        form.addRow('Largeur souhaitée des bandes',self.width)
        self.oa = self.length_spin(obj.OverhangA.Value,0,1000)
        self.ob = self.length_spin(obj.OverhangB.Value,0,1000)
        self.gap = self.length_spin(obj.FitGap.Value,0,100)
        form.addRow('Dépassement A',self.oa)
        form.addRow('Dépassement B',self.ob)
        form.addRow('Jeu entre doigts (hors trait laser)',self.gap)
        self.invert = QtWidgets.QCheckBox('Inverser les doigts A / B')
        self.invert.setChecked(obj.Invert);form.addRow(self.invert)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True);layout.addWidget(self.summary)
        self.status = QtWidgets.QLabel('Clique sur Aperçu pour calculer ces réglages.')
        self.status.setWordWrap(True);layout.addWidget(self.status)
        buttons = QtWidgets.QHBoxLayout();layout.addLayout(buttons)
        preview = QtWidgets.QPushButton('Aperçu')
        accept = QtWidgets.QPushButton('Valider')
        cancel = QtWidgets.QPushButton('Annuler')
        for button in (preview,accept,cancel):buttons.addWidget(button)
        preview.clicked.connect(self.preview)
        accept.clicked.connect(self.validate)
        cancel.clicked.connect(self.reject)
        self.mode.currentIndexChanged.connect(self.changed)
        for spin in (self.count,self.width,self.oa,self.ob,self.gap):
            spin.valueChanged.connect(self.changed)
        self.invert.toggled.connect(self.changed)
        self.changed()
        try:
            a,an = obj.PanelA; b,bn = obj.PanelB
            da=frame(*panel_geometry(a,an[0]))
            db=frame(*panel_geometry(b,bn[0]))
            import math
            angle=math.degrees(math.acos(min(1.0,abs(da[3].dot(db[3])))))
            self.geometry.setText('A : %s — %.3f mm\nB : %s — %.3f mm\nAngle aigu entre plans : %.2f°' %
                (a.Label,da[4][2][1]-da[4][2][0],b.Label,db[4][2][1]-db[4][2][0],angle))
        except Exception as exc:
            self.geometry.setText(str(exc))

    def length_spin(self,value,minimum,maximum):
        spin=QtWidgets.QDoubleSpinBox()
        spin.setDecimals(3);spin.setRange(minimum,maximum)
        spin.setSingleStep(0.1);spin.setSuffix(' mm');spin.setValue(value)
        return spin

    def changed(self,*args):
        by_width=self.mode.currentIndex()==1
        self.count.setEnabled(not by_width);self.width.setEnabled(by_width)
        if by_width:
            self.summary.setText('Le nombre de bandes est calculé à l’aperçu. La largeur réelle est ajustée à la longueur du raccord.')
        else:self.show_counts(self.count.value())
        self.status.setText('Réglages modifiés : clique sur Aperçu ou Valider.')

    def show_counts(self,n):
        na=(n+1)//2 if not self.invert.isChecked() else n//2
        nb=n-na
        self.summary.setText('%d bandes : A = %d doigts / %d encoches ; B = %d doigts / %d encoches.' %
                             (n,na,nb,nb,na))

    def preview(self):
        o=self.obj
        try:
            o.SizingMode=self.mode.currentText()
            o.BandCount=self.count.value();o.RequestedWidth=self.width.value()
            o.OverhangA=self.oa.value();o.OverhangB=self.ob.value()
            o.FitGap=self.gap.value();o.Invert=self.invert.isChecked()
            o.touch();o.Document.recompute()
            if o.ResultA.Shape.isNull() or o.ResultB.Shape.isNull():
                raise ValueError(o.Status)
            o.PanelA[0].ViewObject.Visibility=False
            o.PanelB[0].ViewObject.Visibility=False
            o.ResultA.ViewObject.Visibility=True;o.ResultB.ViewObject.Visibility=True
            self.count.blockSignals(True);self.count.setValue(o.BandCount);self.count.blockSignals(False)
            self.show_counts(o.BandCount)
            self.status.setText('Aperçu calculé — largeur réelle des bandes : %.3f mm (avant jeu).'%o.BandWidth.Value)
            return True
        except Exception as exc:
            self.status.setText('Calcul impossible : '+str(exc))
            return False

    def validate(self):
        if self.preview():self.accept()


def edit_dialog(obj,transaction_open=False):
    doc=obj.Document
    if not transaction_open:doc.openTransaction('Modifier les doigts croisés')
    sources=[(o,o.ViewObject.Visibility) for o in (obj.PanelA[0],obj.PanelB[0])]
    results=[(o,o.ViewObject.Visibility) for o in (obj.ResultA,obj.ResultB)]
    try:
        ensure_parameters(obj)
        dialog=ParameterDialog(obj)
        run=getattr(dialog,'exec',None) or dialog.exec_
        if run()==QtWidgets.QDialog.Accepted:
            doc.commitTransaction()
            return True
        doc.abortTransaction()
        for o,visible in sources:
            o.ViewObject.Visibility=visible
        if not transaction_open:
            doc.recompute()
            for o,visible in results:o.ViewObject.Visibility=visible
        return False
    except Exception:
        doc.abortTransaction()
        for o,visible in sources:o.ViewObject.Visibility=visible
        raise


class FingerProxy:
    def __init__(self, obj):
        obj.addProperty('App::PropertyLinkSub','PanelA','Sources')
        obj.addProperty('App::PropertyLinkSub','PanelB','Sources')
        obj.addProperty('App::PropertyInteger','BandCount','Doigts','Nombre total de bandes alternées').BandCount = 6
        obj.addProperty('App::PropertyLength','OverhangA','Doigts','Prolongement minimal au-delà du croisement, panneau A').OverhangA = 3
        obj.addProperty('App::PropertyLength','OverhangB','Doigts','Prolongement minimal au-delà du croisement, panneau B').OverhangB = 3
        obj.addProperty('App::PropertyLength','FitGap','Doigts','Jeu géométrique total entre deux doigts voisins, hors trait laser').FitGap = 0.05
        obj.addProperty('App::PropertyBool','Invert','Doigts','Inverser les bandes conservées sur A et B')
        obj.addProperty('App::PropertyAngle','AcuteAngle','Résultat')
        obj.addProperty('App::PropertyLength','BandWidth','Résultat')
        obj.addProperty('App::PropertyString','Status','Résultat')
        obj.addProperty('App::PropertyLink','ResultA','Résultat')
        obj.addProperty('App::PropertyLink','ResultB','Résultat')
        for p in ('AcuteAngle','BandWidth','Status','ResultA','ResultB'):
            obj.setEditorMode(p,1)
        ensure_parameters(obj)
        obj.Proxy = self

    def execute(self,obj):
        if not obj.ResultA or not obj.ResultB:
            return
        try:
            a,anames = obj.PanelA
            b,bnames = obj.PanelB
            shape_a,face_a = panel_geometry(a,anames[0])
            shape_b,face_b = panel_geometry(b,bnames[0])
            ensure_parameters(obj)
            if obj.SizingMode == 'Largeur souhaitée':
                _,_,half = build(shape_a,face_a,shape_b,face_b,2,
                    obj.OverhangA.Value,obj.OverhangB.Value,0,obj.Invert)
                obj.BandCount = count_for_width(half*2,obj.RequestedWidth.Value)
            results,angle,width = build(shape_a,face_a,shape_b,face_b, obj.BandCount,
                obj.OverhangA.Value,obj.OverhangB.Value,obj.FitGap.Value,obj.Invert)
            obj.ResultA.Shape,obj.ResultB.Shape = results
            obj.AcuteAngle,obj.BandWidth = angle,width
            obj.Status = 'Calcul géométrique OK — prototype à valider au montage'
        except Exception as exc:
            obj.ResultA.Shape = Part.Shape()
            obj.ResultB.Shape = Part.Shape()
            obj.Status = str(exc)
            App.Console.PrintError('Doigts croisés : %s\n' % exc)

    def onDocumentRestored(self,obj):
        ensure_parameters(obj)
        if App.GuiUp:
            FingerViewProvider(obj.ViewObject)

    def dumps(self): return None
    def loads(self,state): pass


class FingerCommand:
    def GetResources(self):
        return {'MenuText':'Doigts croisés obliques (prototype)',
                'ToolTip':'Sélectionner avec Ctrl les deux chants terminaux de deux panneaux d’épaisseur constante.',
                'Pixmap':os.path.join(os.path.dirname(__file__),'..','icons','finger_oblique.svg')}

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        selection = Gui.Selection.getSelectionEx("",0)
        if len(selection)==1 and isinstance(getattr(selection[0].Object,"Proxy",None),FingerProxy):
            obj=selection[0].Object
            FingerViewProvider(obj.ViewObject)
            edit_dialog(obj)
            return
        if (len(selection) != 2 or any(len(s.SubElementNames) != 1 or
                not is_direct_face(s.SubElementNames[0]) for s in selection)):
            QtWidgets.QMessageBox.information(None,'Doigts croisés',
                'Sélectionne deux chants terminaux (Ctrl + clic), un sur chaque panneau d’épaisseur constante.')
            return
        if selection[0].Object == selection[1].Object:
            return
        if any(s.Object.getParentGeoFeatureGroup()
               for s in selection):
            QtWidgets.QMessageBox.information(None,'Doigts croisés',
                'Prototype : utiliser des panneaux directement à la racine du document, Links acceptés, sans conteneur placé.')
            return
        doc = App.ActiveDocument
        doc.openTransaction('Créer des doigts croisés obliques')
        try:
            obj = doc.addObject('App::DocumentObjectGroupPython','LCIE_ObliqueFingers')
            obj.Label = 'Doigts croisés obliques — prototype'
            FingerProxy(obj)
            a = doc.addObject('Part::Feature','LCIE_FingersA')
            b = doc.addObject('Part::Feature','LCIE_FingersB')
            a.Label,b.Label = 'Panneau A — doigts','Panneau B — doigts'
            obj.addObject(a); obj.addObject(b)
            obj.ResultA,obj.ResultB = a,b
            obj.PanelA = (selection[0].Object,[selection[0].SubElementNames[0]])
            obj.PanelB = (selection[1].Object,[selection[1].SubElementNames[0]])
            FingerViewProvider(obj.ViewObject)
            a.ViewObject.ShapeColor = (0.9,0.48,0.16)
            b.ViewObject.ShapeColor = (0.18,0.48,0.75)
            visibility = [(s.Object,s.Object.ViewObject.Visibility) for s in selection]
            if not edit_dialog(obj, transaction_open=True):
                for source,visible in visibility:
                    source.ViewObject.Visibility = visible
                return
            Gui.Selection.clearSelection(); Gui.Selection.addSelection(obj)
            Gui.activeDocument().activeView().viewAxonometric()
            Gui.activeDocument().activeView().fitAll()
        except Exception as exc:
            doc.abortTransaction()
            QtWidgets.QMessageBox.warning(None,'Doigts croisés',str(exc))


Gui.addCommand('LCIE_oblique_fingers',FingerCommand())
