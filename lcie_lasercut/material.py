#!/usr/bin/env python

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 execuc                                             *
# *                                                                         *
# *   This file is part of LCInterlocking module.                           *
# *   LCInterlocking module is free software; you can redistribute it and/or*
# *   modify it under the terms of the GNU Lesser General Public            *
# *   License as published by the Free Software Foundation; either          *
# *   version 2.1 of the License, or (at your option) any later version.    *
# *                                                                         *
# *   This module is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU     *
# *   Lesser General Public License for more details.                       *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this library; if not, write to the Free Software   *
# *   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,            *
# *   MA  02110-1301  USA                                                   *
# *                                                                         *
# ***************************************************************************

import FreeCAD
import Part
import collections
from lcie_lasercut.helper import ObjectProperties, sort_quad_vertex, biggest_area_faces, sort_area_shape_list, compare_value


class MaterialProperties(ObjectProperties):

    _allowed = ('type', 'thickness', 'thickness_tolerance', 'hole_width_tolerance',
                'laser_beam_diameter', 'name', 'label', 'link_name',
                # For cross Part
                'dog_bone', 'node_type', 'node_thickness') #'freecad_object_index'
    TYPE_LASER_CUT = 1
    NODE_NO = "No node"
    NODE_SINGLE_SHORT = 'Single short'
    NODE_SINGLE_LONG = 'Single long'
    NODE_DUAL_SHORT = 'Dual short'

    def __init__(self, **kwargs):
        super(MaterialProperties, self).__init__(**kwargs)
        self.freecad_object = None
        #if not hasattr(self, 'freecad_object_index'):
        #    raise ValueError("Must defined freecad object")
        if not hasattr(self, 'type'):
            self.type = self.TYPE_LASER_CUT
        if not hasattr(self, 'thickness'):
            self.thickness = 5.0
            try:
                #self.thickness = retrieve_thickness_from_biggest_face(self.freecad_object)
                self.thickness = retrieve_thickness_from_biggest_face(kwargs['freecad_object'])
                # FreeCAD.Console.PrintError("found : %f\n" % self.thickness)
            except ValueError as e:
                FreeCAD.Console.PrintError(e)
        if not hasattr(self, 'thickness_tolerance'):
            self.thickness_tolerance = 0.1 * self.thickness
        if not hasattr(self, 'laser_beam_diameter'):
            self.laser_beam_diameter = self.thickness / 15.0
        if not hasattr(self, 'new_name'):
            self.new_name = "%s_tab" % kwargs['freecad_object'].Label
        if not hasattr(self, 'hole_width_tolerance'):
            self.hole_width_tolerance = 0.0
        # For cross part
        if not hasattr(self, 'dog_bone'):
            self.dog_bone = True
        if not hasattr(self, 'node_type'):
            self.node_type = self.NODE_NO
        if not hasattr(self, 'node_thickness'):
            self.node_thickness = 0.05 * self.thickness
        if not hasattr(self, 'link_name'):
            self.link_name = ""

    def recomputeInit(self, freecad_obj):
        self.freecad_object = freecad_obj
        thickness = retrieve_thickness_from_biggest_face(freecad_obj)
        if compare_value(thickness, self.thickness) is False:
            FreeCAD.Console.PrintError("Recomputed thickness for %s is different (%f != %f)\n" % (self.name, thickness, self.thickness))


# Prendre la normal la plus présente en terme de surface (biggest_area_faces)
# appliquer  une transformation pour orienter la normal vers Z
# l'éppaiseur et le Zlength du boundedbox (ce sera donc l'éppaisseur max)
def retrieve_thickness_from_bounded_box():
    return None


# Prend les deux premiere faces ayant la même normal (géré exception !! si une seule face)
# Pour chaque face recupere les points et calcule la plus petite distance entre chaque point
# de la premiere face et ceux de la deuxième face. La distance la plus petite est l'éppaisseur estimé.
def retrieve_thickness_from_biggest_face(freecad_object):
    """Estimate sheet thickness from the final Shape, independent of feature history.

    The upstream implementation matches vertices between two quadrilateral faces.
    That fails as soon as Cut/Pocket/Boolean/Slice operations alter face topology.
    Extended instead evaluates projection spans along planar face normals and uses
    the smallest stable span of the resulting solid as the sheet thickness.
    """
    shape = freecad_object.Shape
    if shape is None or shape.isNull():
        raise ValueError("Object has no valid Shape")

    solids = list(shape.Solids)
    if len(solids) > 1:
        raise ValueError(
            "LCInterlocking Extended requires a single solid; "
            "select one Slice Apart result or one individual solid"
        )
    if len(solids) == 1:
        shape = solids[0]

    vertices = [vertex.Point for vertex in shape.Vertexes]
    if len(vertices) < 4:
        raise ValueError("Not enough vertices to determine material thickness")

    normals = []
    for face in shape.Faces:
        try:
            normal = face.normalAt(0, 0)
        except Exception:
            continue
        if normal.Length < 1e-9:
            continue
        normal.normalize()

        # One representative for each parallel/anti-parallel direction.
        if not any(normal.cross(existing).Length < 1e-5 for existing in normals):
            normals.append(normal)

    spans = []
    for normal in normals:
        projections = [point.dot(normal) for point in vertices]
        span = max(projections) - min(projections)
        if span > 1e-7:
            spans.append(span)

    if not spans:
        raise ValueError("Unable to determine material thickness from final Shape")

    # For planar laser-cut parts, thickness is the smallest global extent measured
    # along a face-normal direction. Cuts, pockets and slicing do not change it.
    return min(spans)

