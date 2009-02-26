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
import math

class Point(dict):

    KEYS = ("x", "y", "pressure", "xtilt", "ytilt", "timestamp")

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
        self.x = int(self.x * xrate)
        self.y = int(self.y * yrate)

    def move_rel(self, dx, dy):
        self.x = self.x + dx
        self.y = self.y + dy      

    def to_xml(self):
        attrs = []

        for key in self.KEYS:
            if self[key] is not None:
                attrs.append("%s=\"%s\"" % (key, str(self[key])))

        return "<point %s />" % " ".join(attrs)

    def to_json(self):
        attrs = []

        for key in self.KEYS:
            if self[key] is not None:
                attrs.append("\"%s\" : %d" % (key, int(self[key])))

        return "{ %s }" % ", ".join(attrs)

    def __eq__(self, othr):
        for key in self.KEYS:
            if self[key] != othr[key]:
                return False

        return True

    def __ne__(self, othr):
        return not(self == othr)

    def copy(self):
        return Point(**self)

class Stroke(list):

    def __init__(self):
        list.__init__(self)
        self._is_smoothed = False

    def get_duration(self):
        if len(self) > 0:
            if self[-1].timestamp is not None and self[0].timestamp is not None:
                return self[-1].timestamp - self[0].timestamp
        return None

    def append_point(self, point):
        self.append(point)

    def to_xml(self):
        s = "<stroke>\n"

        for point in self:
            s += "  %s\n" % point.to_xml()

        s += "</stroke>"

        return s

    def to_json(self):
        s = "{\"points\" : ["
        
        s += ",".join([point.to_json() for point in self])
        
        s += "]}"

        return s  

    def __eq__(self, othr):
        if len(self) != len(othr):
            return False

        for i in range(len(self)):
            if self[i] != othr[i]:
                return False

        return True

    def __ne__(self, othr):
        return not(self == othr)

    def copy(self):
        c = Stroke()
        for point in self:
            c.append_point(point.copy())
        return c

    def smooth(self):
        """
        Smoothing method based on a (simple) moving average algorithm. 
    
        Let p = p(0), ..., p(N) be the set points of this stroke, 
            w = w(-M), ..., w(0), ..., w(M) be a set of weights.
        
        This algorithm aims at replacing p with a set p' such as
        
            p'(i) = (w(-M)*p(i-M) + ... + w(0)*p(i) + ... + w(M)*p(i+M)) / S
        
        and where S = w(-M) + ... + w(0) + ... w(M). End points are not
        affected.
        """
        if self._is_smoothed:
            return

        weights = [1, 1, 2, 1, 1] # Weights to be used
        times = 3 # Number of times to apply the algorithm

        if len(self) < len(weights):
            return

        offset = int(math.floor(len(weights) / 2.0))
        wsum = sum(weights)

        for n in range(times):
            s = self.copy()

            for i in range(offset, len(self) - offset):
                self[i].x = 0
                self[i].y = 0

                for j in range(len(weights)):
                    self[i].x += weights[j] * s[i + j - offset].x
                    self[i].y += weights[j] * s[i + j - offset].y

                self[i].x = round(self[i].x / wsum)
                self[i].y = round(self[i].y / wsum)
        
        self._is_smoothed = True

class Writing(object):

    # Default width and height of the canvas
    # If the canvas used to create the Writing object
    # has a different width or height, then
    # the methods set_width and set_height need to be used
    WIDTH = 1000
    HEIGHT = 1000

    NORMALIZE_PROPORTION = 0.7 # percentage of the drawing area
    NORMALIZE_MIN_SIZE = 0.1 # don't nornalize if below that percentage

    def __init__(self):
        self._width = Writing.WIDTH
        self._height = Writing.HEIGHT
        self.clear()

    def clear(self):
        self._strokes = []

    def get_duration(self):
        if self.get_n_strokes() > 0:
            if self._strokes[0][0].timestamp is not None and \
               self._strokes[-1][-1].timestamp is not None:
                return self._strokes[-1][-1].timestamp - \
                       self._strokes[0][0].timestamp
        return None

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
        self._strokes[-1].append(point)

    def get_n_strokes(self):
        return len(self._strokes)

    def get_n_points(self):
        return sum([len(s) for s in self._strokes])

    def get_strokes(self, full=False):
        if not full:
            # For compatibility
            return [[(int(p.x), int(p.y)) for p in s] for s in self._strokes]
        else:
            return self._strokes

    def append_stroke(self, stroke):
        self._strokes.append(stroke)

    def remove_last_stroke(self):
        if self.get_n_strokes() > 0:
            del self._strokes[-1]

    def resize(self, xrate, yrate):
        for stroke in self._strokes:
            if len(stroke) == 0:
                continue

            stroke[0].resize(xrate, yrate)
            
            for point in stroke[1:]:
                point.resize(xrate, yrate)

    def move_rel(self, dx, dy):
        for stroke in self._strokes:
            if len(stroke) == 0:
                continue

            stroke[0].move_rel(dx, dy)
            
            for point in stroke[1:]:
                point.move_rel(dx, dy)

    def size(self):
        xmin, ymin = 4294967296, 4294967296 # 2^32
        xmax, ymax = 0, 0
        
        for stroke in self._strokes:
            for point in stroke:
                xmin = min(xmin, point.x)
                ymin = min(ymin, point.y)
                xmax = max(xmax, point.x)
                ymax = max(ymax, point.y)

        return (xmin, ymin, xmax-xmin, ymax-ymin)

    def normalize(self):
        self.normalize_size()
        self.normalize_position()

    def normalize_position(self):
        x, y, width, height = self.size()

        dx = (self._width - width) / 2 - x
        dy = (self._height - height) / 2 - y

        self.move_rel(dx, dy)

    def normalize_size(self):
        # Note: you should call normalize_position() after normalize_size()
        x, y, width, height = self.size()

        
        if float(width) / self._width > Writing.NORMALIZE_MIN_SIZE:
            xrate = self._width * Writing.NORMALIZE_PROPORTION / width
        else:
            # Don't normalize if too thin in width
            xrate = 1.0


        if float(height) / self._height > Writing.NORMALIZE_MIN_SIZE:
            yrate = self._height * Writing.NORMALIZE_PROPORTION / height
        else:
            # Don't normalize if too thin in height
            yrate = 1.0
        
        self.resize(xrate, yrate)

    def get_width(self):
        return self._width
    
    def set_width(self, width):
        self._width = width

    def get_height(self):
        return self._height

    def set_height(self, height):
        self._height = height

    def to_xml(self):
        s = "<width>%d</width>\n" % self.get_width()
        s += "<height>%d</height>\n" % self.get_height()

        s += "<strokes>\n"

        for stroke in self._strokes:
            for line in stroke.to_xml().split("\n"):
                s += "  %s\n" % line

        s += "</strokes>"

        return s

    def to_json(self):
        s = "{ \"width\" : %d, " % self.get_width()
        s += "\"height\" : %d, " % self.get_height()
        s += "\"strokes\" : ["

        s += ", ".join([stroke.to_json() for stroke in self._strokes])

        s += "]}"

        return s

    def __str__(self):
        return str(self.get_strokes(full=True))

    def __eq__(self, othr):
        if self.get_n_strokes() != othr.get_n_strokes():
            return False

        if self.get_width() != othr.get_width():
            return False

        if self.get_height() != othr.get_height():
            return False

        othr_strokes = othr.get_strokes(full=True)

        for i in range(len(self._strokes)):
            if self._strokes[i] != othr_strokes[i]:
                return False
        
        return True

    def __ne__(self, othr):
        return not(self == othr)

    def copy(self):
        c = Writing()
        c.set_width(self.get_width())
        c.set_height(self.get_height())
        
        for stroke in self._strokes:
            c.append_stroke(stroke.copy())

        return c

    def smooth(self):
        for stroke in self._strokes:
            stroke.smooth()

class Character(object):

    def __init__(self):
        self._writing = Writing()
        self._utf8 = None

    def get_utf8(self):
        return self._utf8
        
    def set_utf8(self, utf8):
        self._utf8 = utf8

    def get_writing(self):
        return self._writing

    def set_writing(self, writing):
        self._writing = writing

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
                file = gzipm.GzipFile(file, "w", compresslevel=compresslevel)
            elif bz2:
                file = bz2m.BZ2File(file, "w", compresslevel=compresslevel)
            else:            
                file = open(file, "w")
                
            file.write(self.to_xml())
            file.close()
        else:
            file.write(self.to_xml())       

    def to_xml(self):
        s = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        
        s += "<character>\n"
        s += "  <utf8>%s</utf8>\n" % self._utf8

        for line in self._writing.to_xml().split("\n"):
            s += "  %s\n" % line
        
        s += "</character>"

        return s

    def to_json(self):
        s = "{"

        attrs = ["\"utf8\" : \"%s\"" % self._utf8,
                 "\"writing\" : " + self._writing.to_json()]

        s += ", ".join(attrs)

        s += "}"

        return s

    def __eq__(self, char):
        return self._utf8 == char.get_utf8() and \
               self._writing == char.get_writing()

    def __ne__(self, othr):
        return not(self == othr)

    def copy(self):
        c = Characters()
        c.set_utf8(self.get_utf8())
        c.set_writing(self.get_writing().copy())
        return c
        
    # Private...    

    def _start_element(self, name, attrs):
        self._tag = name

        if self._tag == "stroke":
            self._stroke = Stroke()
            
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

    def _get_parser(self):
        parser = xml.parsers.expat.ParserCreate(encoding="UTF-8")
        parser.StartElementHandler = self._start_element
        parser.EndElementHandler = self._end_element
        parser.CharacterDataHandler = self._char_data
        return parser
