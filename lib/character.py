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
import cStringIO
import gzip as gzipm
import bz2 as bz2m

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

    def resize(self, xrate, yrate):
        new_point = Point(**self)
        new_point.x = int(self.x * xrate)
        new_point.y = int(self.y * yrate)
        return new_point

    def to_xml(self):
        attrs = []

        for key in ("x", "y", "pressure", "xtilt", "ytilt", "timestamp"):
            if self[key]:
                attrs.append("%s=\"%s\"" % (key, str(self[key])))

        return "<point %s />" % " ".join(attrs)

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

    def to_xml(self):
        if self.duration:
            s = "<stroke duration=\"%d\">\n" % self.duration
        else:
            s = "<stroke>\n"

        for point in self:
            s += "  %s\n" % point.to_xml()

        s += "</stroke>"

        return s

    def __eq__(self, stroke):
        return self.duration == stroke.get_duration() and \
               list.__eq__(self, stroke)

class Writing(object):

    WIDTH = 1000
    HEIGHT = 1000

    def __init__(self):
        self.clear()

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

    def append_stroke(self, stroke):
        self.strokes.append(stroke)

    def remove_last_stroke(self):
        if self.get_n_strokes() > 0:
            del self.strokes[-1]

    def resize(self, xrate, yrate):
        new_writing = Writing()

        for stroke in self.strokes:
            point = stroke[0].resize(xrate, yrate)
            new_writing.move_to_point(point)
            
            for point in stroke[1:]:
                point = point.resize(xrate, yrate)
                new_writing.line_to_point(point)

        return new_writing

    def clear(self):
        self.strokes = []

    def to_xml(self):
        s = "<strokes>\n"

        for stroke in self.strokes:
            for line in stroke.to_xml().split("\n"):
                s += "  %s\n" % line

        s += "</strokes>"

        return s

    def __str__(self):
        return str(self.get_strokes(full=True))

    def __eq__(self, writing):
        return self.strokes == writing.get_strokes(full=True)

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

    def read(self, file, gzip=False, bz2=False, compresslevel=9):
        parser = self._get_parser()

        if type(file) == str:
            if gzip:
                file = gzipm.GzipFile(file, compresslevel=compresslevel)
            elif bz2:
                file = bz2m.BZ2File(file, compresslevel=compresslevel)
            else:
                file = open(file)
                
            parser.ParseFile(file)
            file.close()
        else:                
            parser.ParseFile(file)

    def read_string(self, string, gzip=False, bz2=False, compresslevel=9):
        if gzip:
            io = cStringIO.StringIO(string)
            io = gzipm.GzipFile(fileobj=io, compresslevel=compresslevel)
            string = io.read()
        elif bz2:
            string = bz2m.decompress(string)
            
        parser = self._get_parser()
        parser.Parse(string)

    def write(self, file, gzip=False, bz2=False, compresslevel=9):
        if type(file) == str:
            if gzip:
                file = GzipFile(file, "w", compresslevel=compresslevel)
            elif bz2:
                file = BZ2File(file, "w", compresslevel=compresslevel)
            else:            
                file = open(file, "w")
                
            file.write(self.to_xml())
            file.close()
        else:
            file.write(self.to_xml())       

    def to_xml(self):
        s = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        
        s += "<character>\n"
        s += "  <utf8>%s</utf8>\n" % self.utf8

        for line in self.writing.to_xml().split("\n"):
            s += "  %s\n" % line
        
        s += "</character>"

        return s

    def __eq__(self, char):
        return self.utf8 == char.get_utf8() and \
               self.writing == char.get_writing()
        
    # Private...    

    def _start_element(self, name, attrs):
        self._tag = name

        if self._tag == "stroke":
            self._stroke = Stroke()

            if attrs.has_key("duration"):
                self._stroke.set_duration(int(attrs["duration"]))
            
        elif self._tag == "point":
            point = Point()

            for key in ("x", "y", "pressure", "xtilt", "ytilt", "timestamp"):
                if attrs.has_key(key):
                    value = attrs[key].encode("UTF-8")
                    if key in ("pressure", "xtilt", "ytilt"):
                        value = float(value)
                    else:
                        value = int(value)
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
