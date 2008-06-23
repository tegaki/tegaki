# -*- coding: utf-8 -*-

# Copyright (C) 2008 Mathieu Blondel
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
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import xml.parsers.expat

class Point(dict):

    def __init__(self, x=None, y=None,
                       pressure=None, xtilt=None, ytilt=None,
                       timestamp=None):

        dict.__init__(self)

        self.x = x
        self.y = y

        self.pressure = pressure
        self.xtilt = xtilt
        self.ytilt = ytilt

        self.timestamp = timestamp

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError

    def __setattr__(self, attr, value):
        try:
            self[attr] = value
        except KeyError:
            raise AttributeError

class Stroke(list):

    def __init__(self):
        list.__init__(self)
        
        self.duration = None

    def get_duration(self):
        return self.duration

    def set_duration(self, duration):
        self.duration = duration

    def append_point(self, point):
        self.append(point)

class Writing(object):

    WIDTH = 1000
    HEIGHT = 1000

    def __init__(self):
        self.strokes = []

    def move_to(self, x, y):
        # For compatibility
        point = Point()
        point.x = x
        point.y = y

        self.move_to_point(point)

    def line_to(self, x, y):
        # For compatibility
        point = Point()
        point.x = x
        point.y = y
               
        self.line_to_point(point)
              
    def move_to_point(self, point):
        stroke = Stroke()
        stroke.append_point(point)

        self.append_stroke(stroke)
        
    def line_to_point(self, point):
        self.strokes[-1].append(point)

    def get_n_strokes(self):
        return len(self.strokes)

    def get_strokes(self, full=False):
        if not full:
            # For compatibility
            return [[(int(p.x), int(p.y)) for p in s] for s in self.strokes]
        else:
            return self.strokes

    def get_stroke_objects(self):
        return 

    def append_stroke(self, stroke):
        self.strokes.append(stroke)

    def remove_last_stroke(self):
        if self.get_n_strokes() > 0:
            del self.strokes[-1]

    def __str__(self):
        return str(self.get_strokes(full=True))

class Character(object):

    def __init__(self):
        self.writing = Writing()
        self.utf8 = None

    def get_utf8(self):
        return self.utf8
        
    def set_utf8(self, utf8):
        self.utf8 = utf8

    def get_writing(self):
        return self.writing

    def set_writing(self, writing):
        self.writing = writing

    def read(self, file):
        parser = self._get_parser()

        if type(file) == str:
            file = open(file)
            parser.ParseFile(file)
            file.close()
        else:
            parser.ParseFile(file)

    def read_string(self, string):
        parser = self._get_parser()
        parser.Parse(string)
        
    # Private...    

    def _start_element(self, name, attrs):
        self._tag = name

        if self._tag == "stroke":
            self._stroke = Stroke()

            if attrs.has_key("duration"):
                self._stroke.set_duration(attrs["duration"])
            
        elif self._tag == "point":
            point = Point()

            for key in ("x", "y", "pressure", "xtilt", "ytilt", "timestamp"):
                if attrs.has_key(key):
                    value = attrs[key]
                else:
                    value = None
                    
                setattr(point, key, value)

            self._stroke.append_point(point)

    def _end_element(self, name):
        if name == "stroke":
            self.writing.append_stroke(self._stroke)
            self._stroke = None

        self._tag = None

    def _char_data(self, data):
        if self._tag == "utf8":
            self.utf8 = data.encode("UTF-8")

    def _get_parser(self):
        parser = xml.parsers.expat.ParserCreate(encoding="UTF-8")
        parser.StartElementHandler = self._start_element
        parser.EndElementHandler = self._end_element
        parser.CharacterDataHandler = self._char_data
        return parser
