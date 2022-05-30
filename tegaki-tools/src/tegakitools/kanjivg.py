#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009 The Tegaki project contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Contributors to this file:
# - Mathieu Blondel
# - Roger Braun
#
# -------------
# NOTES:
# 
# This will read the KanjiVG xml files you can find at 
# http://kanjivg.tagaini.net/.
# Search for "resolution" if you want to control how many points are being
# created for the tegaki-xml. 

from tegaki.character import Point, Stroke, Writing, Character, \
                             _XmlBase
from tegaki.charcol import CharacterCollection
from math import sqrt  

from pyparsing import *

import re, sys

class SVG_Point(Point):
    def add(self, point):
        return SVG_Point(self.x + point.x, self.y + point.y)

    def subtract(self, point):
        return SVG_Point(self.x - point.x, self.y - point.y)

    def dist(self, point):
        return sqrt((point.x - self.x) ** 2 + (point.y - self.y) ** 2)

    def multiply(self, number):
        return SVG_Point(self.x * number, self.y * number)

    def reflect(self, mirror):
        return mirror.add(mirror.subtract(self))
    

class SVG_Parser:

    def __init__(self, svg):
        # This replaces small "m"s at the beginning of a path by the equivalent
        # capital "M".
        # See http://groups.google.com/group/kanjivg/browse_thread/thread/3a85fb72dfd81ef9
        self._svg = re.sub("^m","M",svg)
        self._points = []

    def get_points(self):
        return self._points
    
    def linear_interpolation(self,a,b,factor):
        xr = a.x + ((b.x - a.x) * factor)
        yr = a.y + ((b.y - a.y) * factor)
        return SVG_Point(xr,yr)

    def make_curvepoint(self,c1,c2,p,current_cursor,factor):
        ab = self.linear_interpolation(current_cursor,c1,factor)
        bc = self.linear_interpolation(c1,c2,factor)
        cd = self.linear_interpolation(c2,p,factor)
        abbc = self.linear_interpolation(ab,bc,factor)
        bccd = self.linear_interpolation(bc,cd,factor)
        return self.linear_interpolation(abbc, bccd, factor)

    def length(self,c1,c2,p,current_cursor,points):
        length = current_cursor.dist(p)
        return length

    def make_curvepoints_array(self,c1,c2,p,current_cursor,distance):
        result = []
        l = self.length(c1,c2,p,current_cursor,10.0)
        points = l * distance
        factor = points
        for i in range(0, int(points)):
            self._points.append(self.make_curvepoint(c1,c2,p,current_cursor,i / factor)) 
        

    def parse(self):
        # Taken and (rather heavily) modified from http://annarchy.cairographics.org/svgtopycairo/
        dot = Literal(".")
        comma = Literal(",").suppress()
        floater = Combine(Optional("-") + Word(nums) + Optional(dot + Word(nums)))
        floater.setParseAction(lambda toks:float(toks[0]))
        couple = floater + Optional(comma) + floater
        M_command = "M" + Group(couple)
        C_command = "C" + Group(couple + Optional(comma) + couple + Optional(comma) + couple)
        L_command = "L" + Group(couple)
        Z_command = "Z"
        c_command = "c" + Group(couple + Optional(comma) + couple + Optional(comma) + couple)
        s_command = "s" + Group(couple + Optional(comma) + couple)
        S_command = "S" + Group(couple + Optional(comma) + couple)
        svgcommand = M_command | C_command | L_command | Z_command | c_command | s_command | S_command
        phrase = OneOrMore(Group(svgcommand)) 
        self._svg_array = phrase.parseString(self._svg)
        self.make_points()

    def resize(self,n):
        return n * 1000.0 / 109.0

    def make_points(self):
        current_cursor = SVG_Point(0,0)
  # ATTENTION: This is the place where you can change the resolution of the created xmls, i.e. how many points are generated. Higher value = More points
        resolution = 0.1
        for command in self._svg_array:
            if command[0] == "M":
                point = SVG_Point(self.resize(command[1][0]),self.resize(command[1][1]))
                self._points.append(point)
                current_cursor = point

            if command[0] == "c":
                c1 = SVG_Point(self.resize(command[1][0]),self.resize(command[1][1])).add(current_cursor) 
                c2 = SVG_Point(self.resize(command[1][2]),self.resize(command[1][3])).add(current_cursor)
                p  = SVG_Point(self.resize(command[1][4]),self.resize(command[1][5])).add(current_cursor)
                self.make_curvepoints_array(c1,c2,p,current_cursor,resolution)             
                current_cursor = self._points[-1]

            if command[0] == "C":
                c1 = SVG_Point(self.resize(command[1][0]),self.resize(command[1][1])) 
                c2 = SVG_Point(self.resize(command[1][2]),self.resize(command[1][3]))
                p  = SVG_Point(self.resize(command[1][4]),self.resize(command[1][5]))
                self.make_curvepoints_array(c1,c2,p,current_cursor,resolution)             
                current_cursor = self._points[-1]

            if command[0] == "s":
                c2 = SVG_Point(self.resize(command[1][0]),self.resize(command[1][1])).add(current_cursor) 
                p = SVG_Point(self.resize(command[1][2]),self.resize(command[1][3])).add(current_cursor)
                c1 = self._points[-2].reflect(current_cursor)
                self.make_curvepoints_array(c1,c2,p,current_cursor,resolution)             
                current_cursor = self._points[-1]     

            if command[0] == "S":
                c2 = SVG_Point(self.resize(command[1][0]),self.resize(command[1][1])) 
                p = SVG_Point(self.resize(command[1][2]),self.resize(command[1][3]))
                c1 = self._points[-2].reflect(current_cursor)
                self.make_curvepoints_array(c1,c2,p,current_cursor,resolution)             
                current_cursor = self._points[-1]     
    
class KVGXmlDictionaryReader(_XmlBase):

    def __init__(self):
        self._charcol = CharacterCollection()

    def get_character_collection(self):
        return self._charcol

    def _start_element(self, name, attrs):
        self._tag = name

        if self._first_tag:
            self._first_tag = False
            if self._tag != "kanjivg":
                raise ValueError("The very first tag should be <kanjivg>")

        if self._tag == "kanji":
            self._writing = Writing()
            self._utf8 = chr(int(attrs["id"].split('_')[1], 16)).encode("UTF-8")

        if self._tag == "path":
            self._stroke = Stroke()
            if "d" in attrs:
                self._stroke_svg = attrs["d"].encode("UTF-8")
                svg_parser = SVG_Parser(self._stroke_svg) 
                svg_parser.parse()
                self._stroke.append_points(svg_parser.get_points())
            else:
                sys.stderr.write("Missing data in <path> element: " + self._utf8 + "\n")
    
            
    def _end_element(self, name):
        if name == "kanji":
            char = Character()
            char.set_utf8(self._utf8)
            char.set_writing(self._writing)
            self._charcol.add_set(self._utf8)
            self._charcol.append_character(self._utf8, char)
            for s in ["_tag", "_stroke"]:
                if s in self.__dict__:
                    del self.__dict__[s]

        if name == "path":
            self._writing.append_stroke(self._stroke)
            self._stroke = None

        self._tag = None

    def _char_data(self, data):
        if self._tag == "utf8":
            self._utf8 = data.encode("UTF-8")
        elif self._tag == "width":
            self._writing.set_width(int(data))
        elif self._tag == "height":
            self._writing.set_height(int(data))

def kanjivg_to_character_collection(path):
    reader = KVGXmlDictionaryReader()
    gzip = False; bz2 = False
    if path.endswith(".gz"): gzip = True
    if path.endswith(".bz2"): bz2 = True
    reader.read(path, gzip=gzip, bz2=bz2)
    return reader.get_character_collection()

