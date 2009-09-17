# -*- coding: utf-8 -*-

# Copyright (C) 2008-2009 The Tegaki project contributors
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

# Contributors to this file:
# - Mathieu Blondel

import xml.parsers.expat
import cStringIO
import gzip as gzipm
try:
    import bz2 as bz2m
except ImportError:
    pass
from math import floor, atan, sin, cos, pi
import os
import re

try:
    # lxml is used for DTD validation
    # for server-side applications, it is recommended to install it
    # for desktop applications, it is optional
    from lxml import etree
except ImportError:
    pass

from tegaki.mathutils import euclidean_distance
from tegaki.dictutils import SortedDict

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

    def get_coordinates(self):
        return (self.x, self.y)

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

    def to_sexp(self):
        return "(%d %d)" % (self.x, self.y)

    def __eq__(self, othr):
        if not isinstance(othr, Point):
            return False

        for key in self.KEYS:
            if self[key] != othr[key]:
                return False

        return True

    def __ne__(self, othr):
        return not(self == othr)

    def copy_from(self, p):
        self.clear()
        for k in p.keys():
            if p[k] is not None:
                self[k] = p[k]

    def copy(self):
        return Point(**self)

class Stroke(list):

    def __init__(self):
        list.__init__(self)
        self._is_smoothed = False

    def get_coordinates(self):
        return [(p.x, p.y) for p in self]

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

    def to_sexp(self):
        return "(" + "".join([p.to_sexp() for p in self]) + ")"

    def __eq__(self, othr):
        if not isinstance(othr, Stroke):
            return False

        if len(self) != len(othr):
            return False

        for i in range(len(self)):
            if self[i] != othr[i]:
                return False

        return True

    def __ne__(self, othr):
        return not(self == othr)

    def copy_from(self, s):
        self.clear()
        self._is_smoothed = s.get_is_smoothed()
        for p in s:
            self.append_point(p.copy())

    def copy(self):
        c = Stroke()
        c.copy_from(self)
        return c

    def get_is_smoothed(self):
        return self._is_smoothed

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

        offset = int(floor(len(weights) / 2.0))
        wsum = sum(weights)

        for n in range(times):
            s = self.copy()

            for i in range(offset, len(self) - offset):
                self[i].x = 0
                self[i].y = 0

                for j in range(len(weights)):
                    self[i].x += weights[j] * s[i + j - offset].x
                    self[i].y += weights[j] * s[i + j - offset].y

                self[i].x = int(round(self[i].x / wsum))
                self[i].y = int(round(self[i].y / wsum))
        
        self._is_smoothed = True

    def clear(self):
        while len(self) != 0:
            del self[0]
        self._is_smoothed = False

    def downsample(self, n):
        """
        Downsample by keeping only 1 sample every n samples.
        """
        if len(self) == 0:
            return

        new_s = Stroke()
        for i in range(len(self)):
            if i % n == 0:
                new_s.append_point(self[i])

        self.copy_from(new_s)

    def downsample_threshold(self, threshold):
        """
        Downsample by removing consecutive samples for which
        the euclidean distance is inferior to threshold.
        """
        if len(self) == 0:
            return

        new_s = Stroke()
        new_s.append_point(self[0])

        last = 0
        for i in range(1, len(self) - 2):
            u = [self[last].x, self[last].y]
            v = [self[i].x, self[i].y]

            if euclidean_distance(u, v) > threshold:
                new_s.append_point(self[i])
                last = i

        new_s.append_point(self[-1])

        self.copy_from(new_s)

    def upsample(self, n):
        """
        'Artificially' increase sampling by adding n linearly spaced points
        between consecutive points.
        """
        self._upsample(lambda d: n)

    def upsample_threshold(self, threshold):
        """
        'Artificially' increase sampling, using threshold to determine
        how many samples to add between consecutive points.
        """
        self._upsample(lambda d: int(floor(float(d) / threshold - 1)))

    def _upsample(self, func):
        """
        'Artificially' increase sampling, using func(distance) to determine how
        many samples to add between consecutive points.
        """
        if len(self) == 0:
            return

        new_s = Stroke()

        for i in range(len(self)- 1):
            x1, y1 = [self[i].x, self[i].y]
            x2, y2 = [self[i+1].x, self[i+1].y]

            new_s.append_point(self[i])

            dx = x2 - x1
            dy = y2 - y1

            if dx == 0:
                alpha = pi / 2
                cosalpha = 0.0
                sinalpha = 1.0
            else:
                alpha = atan(float(abs(dy)) / abs(x2 - x1))
                cosalpha = cos(alpha)
                sinalpha = sin(alpha)

            d = euclidean_distance([x1, y1], [x2, y2])
            signx = cmp(dx, 0)
            signy = cmp(dy, 0)

            n = func(d)

            for j in range(1, n+1):
                dx = cosalpha * 1.0 / (n + 1) * d
                dy = sinalpha * 1.0 / (n + 1) * d
                new_s.append_point(Point(x=int(x1+j*dx*signx), 
                                         y=int(y1+j*dy*signy)))

        new_s.append_point(self[-1])

        self.copy_from(new_s)

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

    def insert_stroke(self, i, stroke):
        self._strokes.insert(i, stroke)

    def remove_stroke(self, i):
        if self.get_n_strokes() - 1 >= i:
            del self._strokes[i]

    def remove_last_stroke(self):
        if self.get_n_strokes() > 0:
            del self._strokes[-1]

    def replace_stroke(self, i, stroke):
        if self.get_n_strokes() - 1 >= i:
            self.remove_stroke(i)
            self.insert_stroke(i, stroke)

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

    def downsample(self, n):
        """
        Downsample by keeping only 1 sample every n samples.
        """
        for s in self._strokes:
            s.downsample(n)

    def downsample_threshold(self, threshold):
        """
        Downsample by removing consecutive samples for which
        the euclidean distance is inferior to threshold.
        """
        for s in self._strokes:
            s.downsample_threshold(threshold)

    def upsample(self, n):
        """
        'Artificially' increase sampling by adding n linearly spaced points
        between consecutive points.
        """
        for s in self._strokes:
            s.upsample(n)

    def upsample_threshold(self, threshold):
        """
        'Artificially' increase sampling, using threshold to determine
        how many samples to add between consecutive points.
        """
        for s in self._strokes:
            s.upsample_threshold(threshold)

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

    def to_sexp(self):
        return "((width %d)(height %d)(strokes %s))" % \
            (self._width, self._height, 
             "".join([s.to_sexp() for s in self._strokes]))                    
         
    def __str__(self):
        return str(self.get_strokes(full=True))

    def __eq__(self, othr):
        if not isinstance(othr, Writing):
            return False

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

    def copy_from(self, w):
        self.clear()
        self.set_width(w.get_width())
        self.set_height(w.get_height())
        
        for s in w.get_strokes(True):
            self.append_stroke(s.copy())

    def copy(self):
        c = Writing()
        c.copy_from(self)
        return c

    def smooth(self):
        for stroke in self._strokes:
            stroke.smooth()

class _XmlBase(object):

    @classmethod
    def validate(cls, string):
        try:
            dtd = etree.DTD(cStringIO.StringIO(cls.DTD))
            root = etree.XML(string.strip())
            return dtd.validate(root)
        except etree.XMLSyntaxError:
            return False
        except NameError:
            # this means that the functionality is not available on that
            # system so you have to catch that exception if you want to
            # ignore it
            raise NotImplementedError
       
    def read(self, file, gzip=False, bz2=False, compresslevel=9):
        """
        raises ValueError if incorrect XML
        """
        parser = self._get_parser()
        try:
            if type(file) == str:
                if gzip:
                    file = gzipm.GzipFile(file, compresslevel=compresslevel)
                elif bz2:
                    try:
                        file = bz2m.BZ2File(file, compresslevel=compresslevel)
                    except NameError:
                        raise NotImplementedError
                else:
                    file = open(file)
                    
                parser.ParseFile(file)
                file.close()
            else:                
                parser.ParseFile(file)
        except (IOError, xml.parsers.expat.ExpatError):
            raise ValueError

    def read_string(self, string, gzip=False, bz2=False, compresslevel=9):
        if gzip:
            io = cStringIO.StringIO(string)
            io = gzipm.GzipFile(fileobj=io, compresslevel=compresslevel)
            string = io.read()
        elif bz2:
            try:
                string = bz2m.decompress(string)
            except NameError:
                raise NotImplementedError
            
        parser = self._get_parser()
        parser.Parse(string)

    def write(self, file, gzip=False, bz2=False, compresslevel=9):
        if type(file) == str:
            if gzip:
                file = gzipm.GzipFile(file, "w", compresslevel=compresslevel)
            elif bz2:
                try:
                    file = bz2m.BZ2File(file, "w", compresslevel=compresslevel)
                except NameError:
                    raise NotImplementedError
            else:            
                file = open(file, "w")
                
            file.write(self.to_xml())
            file.close()
        else:
            file.write(self.to_xml())

    def write_string(self, gzip=False, bz2=False, compresslevel=9):
        if bz2:
            try:
                return bz2m.compress(self.to_xml(), compresslevel=compresslevel)
            except NameError:
                raise NotImplementedError
        elif gzip:
            io = cStringIO.StringIO()
            f = gzipm.GzipFile(fileobj=io, mode="w",
                               compresslevel=compresslevel)
            f.write(self.to_xml())
            f.close()
            return io.getvalue()
        else:
            return self.to_xml()

    def _get_parser(self):
        parser = xml.parsers.expat.ParserCreate(encoding="UTF-8")
        parser.StartElementHandler = self._start_element
        parser.EndElementHandler = self._end_element
        parser.CharacterDataHandler = self._char_data
        self._first_tag = True
        return parser

class Character(_XmlBase):

    DTD = \
"""
<!ELEMENT character (utf8?,width?,height?,strokes)>
<!ELEMENT utf8 (#PCDATA)>
<!ELEMENT width (#PCDATA)>
<!ELEMENT height (#PCDATA)>
<!ELEMENT strokes (stroke+)>
<!ELEMENT stroke (point+)>
<!ELEMENT point EMPTY>

<!ATTLIST point x CDATA #REQUIRED>
<!ATTLIST point y CDATA #REQUIRED>
<!ATTLIST point timestamp CDATA #IMPLIED>
<!ATTLIST point pressure CDATA #IMPLIED>
<!ATTLIST point xtilt CDATA #IMPLIED>
<!ATTLIST point ytilt CDATA #IMPLIED>

"""

    def __init__(self):
        self._writing = Writing()
        self._utf8 = None

    def get_utf8(self):
        return self._utf8

    def get_unicode(self):
        return unicode(self.get_utf8(), "utf8")
        
    def set_utf8(self, utf8):
        self._utf8 = utf8

    def set_unicode(self, uni):
        self._utf8 = uni.encode("utf8")

    def get_writing(self):
        return self._writing

    def set_writing(self, writing):
        self._writing = writing       

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

    def to_sexp(self):
        return "(character (value %s)" % self._utf8 + \
                    self._writing.to_sexp()[1:-1]

    def __eq__(self, char):
        if not isinstance(char, Character):
            return False

        return self._utf8 == char.get_utf8() and \
               self._writing == char.get_writing()

    def __ne__(self, othr):
        return not(self == othr)

    def copy_from(self, c):
        self.set_utf8(c.get_utf8())
        self.set_writing(c.get_writing().copy())

    def copy(self):
        c = Character()
        c.copy_from(self)
        return c
        
    # Private...    

    def _start_element(self, name, attrs):
        self._tag = name

        if self._first_tag:
            self._first_tag = False
            if self._tag != "character":
                raise ValueError, "The very first tag should be <character>"

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
                        value = int(float(value))
                else:
                    value = None

                setattr(point, key, value)

            self._stroke.append_point(point)

    def _end_element(self, name):
        if name == "character":
            for s in ["_tag", "_stroke"]:
                if s in self.__dict__:
                    del self.__dict__[s]

        if name == "stroke":
            if len(self._stroke) > 0:
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

class CharacterCollection(_XmlBase):
    """
    A collection of characters is composed of sets.
    Each set can have zero, one, or more characters.
    """

    DTD = \
"""
<!ELEMENT character-collection (set*)>
<!ELEMENT set (character*)>

<!-- The name attribute identifies a set uniquely -->
<!ATTLIST set name CDATA #REQUIRED>

<!ELEMENT character (utf8?,width?,height?,strokes)>
<!ELEMENT utf8 (#PCDATA)>
<!ELEMENT width (#PCDATA)>
<!ELEMENT height (#PCDATA)>
<!ELEMENT strokes (stroke+)>
<!ELEMENT stroke (point+)>
<!ELEMENT point EMPTY>

<!ATTLIST point x CDATA #REQUIRED>
<!ATTLIST point y CDATA #REQUIRED>
<!ATTLIST point timestamp CDATA #IMPLIED>
<!ATTLIST point pressure CDATA #IMPLIED>
<!ATTLIST point xtilt CDATA #IMPLIED>
<!ATTLIST point ytilt CDATA #IMPLIED>
"""

    def __init__(self):
        self._characters = SortedDict()

    @staticmethod
    def from_character_directory(directory,
                                 extensions=["xml", "bz2", "gz"], 
                                 recursive=True):
        """
        Creates a character collection from a directory containing
        individual character files.
        """
        regexp = re.compile("\.(%s)$" % "|".join(extensions))
        charcol = CharacterCollection()
        
        for name in os.listdir(directory):
            full_path = os.path.join(directory, name)
            if os.path.isdir(full_path) and recursive:
                charcol += CharacterCollection.from_character_directory(
                               full_path, extensions)
            elif regexp.search(full_path):
                char = Character()
                gzip = False; bz2 = False
                if full_path.endswith(".gz"): gzip = True
                if full_path.endswith(".bz2"): bz2 = True
                
                try:
                    char.read(full_path, gzip=gzip, bz2=bz2)
                except ValueError:
                    continue # ignore malformed XML files

                utf8 = char.get_utf8()
                if utf8 is None: utf8 = "Unknown"

                charcol.add_set(utf8)
                if not char in charcol.get_characters(utf8):
                    charcol.append_character(utf8, char)
                
        return charcol

    def concatenate(self, other, check_duplicate=False):
        new = CharacterCollection()
        for charcol in (self, other):
            for set_name in charcol.get_set_list():
                new.add_set(set_name)
                characters = new.get_characters(set_name)
                for char in charcol.get_characters(set_name):
                    if not check_duplicate or not char in characters:
                        new.append_character(set_name, char)
        return new

    def __add__(self, other):
        return self.concatenate(other)
                   
    def add_set(self, set_name):
        if not self._characters.has_key(set_name):
            self._characters[set_name] = []

    def remove_set(self, set_name):
        if self._characters.has_key(set_name):
            del self._characters[set_name]

    def get_set_list(self):
        return self._characters.keys()

    def get_n_sets(self):
        return len(self.get_set_list())

    def get_characters(self, set_name):
        if self._characters.has_key(set_name):
            return self._characters[set_name]
        else:
            return []

    def get_all_characters(self):
        characters = []
        for k in self._characters.keys():
            characters += self._characters[k]
        return characters

    def get_total_n_characters(self):
        n = 0
        for k in self._characters.keys():
            n += len(self._characters[k])
        return n

    def set_characters(self, set_name, characters):
        self._characters[set_name] = characters

    def append_character(self, set_name, character):
        if not self._characters.has_key(set_name):
            self._characters[set_name] = []

        self._characters[set_name].append(character)

    def insert_character(self, set_name, i, character):
        if not self._characters.has_key(set_name):
            self._characters[set_name] = []
            self._characters[set_name].append(character)
        else:
            self._characters[set_name].insert(i, character)

    def remove_character(self, set_name, i):
        if self._characters.has_key(set_name):
            if len(self._characters[set_name]) - 1 >= i:
                del self._characters[set_name][i]

    def remove_last_character(self, set_name):
        if self._characters.has_key(set_name):
            if len(self._characters[set_name]) > 0:
                del self._characters[set_name][-1]

    def replace_character(self, set_name, i, character):
        if self._characters.has_key(set_name):
            if len(self._characters[set_name]) - 1 >= i:
                self.remove_character(set_name, i)
                self.insert_character(set_name, i, character)

    def _get_dict_from_text(self, text):
        text = text.replace(" ", "").replace("\n", "").replace("\t", "")
        dic = {}
        for c in text:
            dic[c] = 1
        return dic

    def include_characters_from_text(self, text):
        """
        Only keep characters found in text.
        """
        dic = self._get_dict_from_text(unicode(text, "utf8"))
        for set_name in self.get_set_list():
            i = 0
            for char in self.get_characters(set_name)[:]:
                if not char.get_unicode() in dic:
                    self.remove_character(set_name, i)
                else:
                    i += 1
        self.remove_empty_sets()

    def exclude_characters_from_text(self, text):
        """
        Exclude characters found in text.
        """
        dic = self._get_dict_from_text(unicode(text, "utf8"))
        for set_name in self.get_set_list():
            i = 0
            for char in self.get_characters(set_name)[:]:
                if char.get_unicode() in dic:
                    self.remove_character(set_name, i)
                else:
                    i += 1
        self.remove_empty_sets()

    def remove_samples(self, keep_at_most):
        for set_name in self.get_set_list():
            if len(self._characters[set_name]) > keep_at_most:
                self._characters[set_name] = \
                    self._characters[set_name][0:keep_at_most]

    def remove_empty_sets(self):
        for set_name in self.get_set_list():
            if len(self.get_characters(set_name)) == 0:
                self.remove_set(set_name)

    def to_xml(self):
        s = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        s += "<character-collection>\n"

        for set_name in self._characters.keys():
            s += "<set name=\"%s\">\n" % set_name

            for character in self._characters[set_name]:
                s += "  <character>\n"

                utf8 = character.get_utf8()
                if utf8:
                    s += "    <utf8>%s</utf8>\n" % utf8

                for line in character.get_writing().to_xml().split("\n"):
                    s += "    %s\n" % line
                
                s += "  </character>\n"

            s += "</set>\n"

        s += "</character-collection>\n"

        return s

    # Private...    

    def _start_element(self, name, attrs):
        self._tag = name

        if self._first_tag:
            self._first_tag = False
            if self._tag != "character-collection":
                raise ValueError, \
                      "The very first tag should be <character-collection>"

        if self._tag == "set":
            if not attrs.has_key("name"):
                raise ValueError, "<set> should have a name attribute"

            self._curr_set_name = attrs["name"].encode("UTF-8")
            self._curr_chars = []

        if self._tag == "character":
            self._curr_char = Character()
            self._curr_writing = self._curr_char.get_writing()
            self._curr_width = None
            self._curr_height = None
            self._curr_utf8 = None

        if self._tag == "stroke":
            self._curr_stroke = Stroke()
            
        elif self._tag == "point":
            point = Point()

            for key in ("x", "y", "pressure", "xtilt", "ytilt", "timestamp"):
                if attrs.has_key(key):
                    value = attrs[key].encode("UTF-8")
                    if key in ("pressure", "xtilt", "ytilt"):
                        value = float(value)
                    else:
                        value = int(float(value))
                else:
                    value = None

                setattr(point, key, value)

            self._curr_stroke.append_point(point)

    def _end_element(self, name):
        if name == "character-collection":
            for s in ["_tag", "_curr_char", "_curr_writing", "_curr_width",
                      "_curr_height", "_curr_utf8", "_curr_stroke",
                      "_curr_chars", "_curr_set_name"]:
                if s in self.__dict__:
                    del self.__dict__[s]
               
        if name == "set":
            self.set_characters(self._curr_set_name, self._curr_chars)

        if name == "character":
            if self._curr_utf8:
                self._curr_char.set_utf8(self._curr_utf8)
            if self._curr_width:
                self._curr_writing.set_width(self._curr_width)
            if self._curr_height:
                self._curr_writing.set_height(self._curr_height)
            self._curr_chars.append(self._curr_char)

        if name == "stroke":
            if len(self._curr_stroke) > 0:
                self._curr_writing.append_stroke(self._curr_stroke)
            self._stroke = None

        self._tag = None

    def _char_data(self, data):
        if self._tag == "utf8":
            self._curr_utf8 = data.encode("UTF-8")
        if self._tag == "width":
            self._curr_width = int(data)
        elif self._tag == "height":
            self._curr_height = int(data)
