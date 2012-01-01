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
import hashlib

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
    """
    A point in a 2-dimensional space.
    """

    #: Attributes that a point can have.
    KEYS = ("x", "y", "pressure", "xtilt", "ytilt", "timestamp")

    def __init__(self, x=None, y=None,
                       pressure=None, xtilt=None, ytilt=None,
                       timestamp=None):
        """
        @type x: int
        @type y: int
        @type pressure: float
        @type xtilt: float
        @type ytilt: float
        @type timestamp: int
        @param timestamp: ellapsed time since first point in milliseconds
        """

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
        """
        Return (x,y) coordinates.

        @rtype: tuple of two int
        @return: (x,y) coordinates
        """
        return (self.x, self.y)

    def resize(self, xrate, yrate):
        """
        Scale point.

        @type xrate: float
        @param xrate: the x scaling factor
        @type yrate: float
        @param yrate: the y scaling factor
        """
        self.x = int(self.x * xrate)
        self.y = int(self.y * yrate)

    def move_rel(self, dx, dy):
        """
        Translate point.

        @type dx: int
        @param dx: relative distance from x
        @type dy: int
        @param yrate: relative distance from y
        """
        self.x = self.x + dx
        self.y = self.y + dy

    def to_xml(self):
        """
        Converts point to XML.

        @rtype: str
        """
        attrs = []

        for key in self.KEYS:
            if self[key] is not None:
                attrs.append("%s=\"%s\"" % (key, str(self[key])))

        return "<point %s />" % " ".join(attrs)

    def to_json(self):
        """
        Converts point to JSON.

        @rtype: str
        """
        attrs = []

        for key in self.KEYS:
            if self[key] is not None:
                attrs.append("\"%s\" : %d" % (key, int(self[key])))

        return "{ %s }" % ", ".join(attrs)

    def to_sexp(self):
        """
        Converts point to S-expressions.

        @rtype: str
        """
        return "(%d %d)" % (self.x, self.y)

    def __eq__(self, othr):
        if not othr.__class__.__name__ in ("Point", "PointProxy"):
            return False

        for key in self.KEYS:
            if self[key] != othr[key]:
                return False

        return True

    def __ne__(self, othr):
        return not(self == othr)

    def copy_from(self, p):
        """
        Replace point with another point.

        @type p: L{Point}
        @param p: the point to copy from
        """
        self.clear()
        for k in p.keys():
            if p[k] is not None:
                self[k] = p[k]

    def copy(self):
        """
        Return a copy of point.

        @rtype: L{Point}
        """
        return Point(**self)

    def __repr__(self):
        return "<Point (%s, %s) (ref %d)>" % (self.x, self.y, id(self))

class Stroke(list):
    """
    A sequence of L{Points<Point>}.
    """

    def __init__(self):
        list.__init__(self)
        self._is_smoothed = False

    def get_coordinates(self):
        """
        Return (x,y) coordinates.

        @rtype: a list of tuples
        """
        return [(p.x, p.y) for p in self]

    def get_duration(self):
        """
        Return the time that it took to draw the stroke.

        @rtype: int or None
        @return: time in millisecons or None if the information is not available
        """
        if len(self) > 0:
            if self[-1].timestamp is not None and self[0].timestamp is not None:
                return self[-1].timestamp - self[0].timestamp
        return None

    def append_point(self, point):
        """
        Append point to stroke.

        @type point: L{Point}
        """
        self.append(point)

    def append_points(self, points):
        self.extend(points)

    def to_xml(self):
        """
        Converts stroke to XML.

        @rtype: str
        """
        s = "<stroke>\n"

        for point in self:
            s += "  %s\n" % point.to_xml()

        s += "</stroke>"

        return s

    def to_json(self):
        """
        Converts stroke to JSON.

        @rtype: str
        """
        s = "{\"points\" : ["

        s += ",".join([point.to_json() for point in self])

        s += "]}"

        return s

    def to_sexp(self):
        """
        Converts stroke to S-expressions.

        @rtype: str
        """
        return "(" + "".join([p.to_sexp() for p in self]) + ")"

    def __eq__(self, othr):
        if not othr.__class__.__name__ in ("Stroke", "StrokeProxy"):
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
        """
        Replace stroke with another stroke.

        @type s: L{Stroke}
        @param s: the stroke to copy from
        """
        self.clear()
        self._is_smoothed = s.get_is_smoothed()
        for p in s:
            self.append_point(p.copy())

    def copy(self):
        """
        Return a copy of stroke.

        @rtype: L{Stroke}
        """
        c = Stroke()
        c.copy_from(self)
        return c

    def get_is_smoothed(self):
        """
        Return whether the stroke has been smoothed already or not.

        @rtype: boolean
        """
        return self._is_smoothed

    def smooth(self):
        """
        Visually improve the rendering of stroke by averaging points
        with their neighbours.

        The method is based on a (simple) moving average algorithm.

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
        """
        Remove all points from stroke.
        """
        while len(self) != 0:
            del self[0]
        self._is_smoothed = False

    def downsample(self, n):
        """
        Downsample by keeping only 1 sample every n samples.

        @type n: int
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

        @type threshod: int
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

        @type n: int
        """
        self._upsample(lambda d: n)

    def upsample_threshold(self, threshold):
        """
        'Artificially' increase sampling, using threshold to determine
        how many samples to add between consecutive points.

        @type threshold: int
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

    def __repr__(self):
        return "<Stroke %d pts (ref %d)>" % (len(self), id(self))

class Writing(object):
    """
    A sequence of L{Strokes<Stroke>}.
    """

    #: Default width and height of the canvas
    #: If the canvas used to create the Writing object
    #: has a different width or height, then
    #: the methods set_width and set_height need to be used
    WIDTH = 1000
    HEIGHT = 1000

    NORMALIZE_PROPORTION = 0.7 # percentage of the drawing area
    NORMALIZE_MIN_SIZE = 0.1 # don't nornalize if below that percentage

    def __init__(self):
        self._width = Writing.WIDTH
        self._height = Writing.HEIGHT
        self.clear()

    def clear(self):
        """
        Remove all strokes from writing.
        """
        self._strokes = []

    def get_duration(self):
        """
        Return the time that it took to draw the strokes.

        @rtype: int or None
        @return: time in millisecons or None if the information is not available
        """
        if self.get_n_strokes() > 0:
            if self._strokes[0][0].timestamp is not None and \
               self._strokes[-1][-1].timestamp is not None:
                return self._strokes[-1][-1].timestamp - \
                       self._strokes[0][0].timestamp
        return None

    def move_to(self, x, y):
        """
        Start a new stroke at (x,y).

        @type x: int
        @type y: int
        """
        # For compatibility
        point = Point()
        point.x = x
        point.y = y

        self.move_to_point(point)

    def line_to(self, x, y):
        """
        Add point with coordinates (x,y) to the current stroke.

        @type x: int
        @type y: int
        """
        # For compatibility
        point = Point()
        point.x = x
        point.y = y

        self.line_to_point(point)

    def move_to_point(self, point):
        """
        Start a new stroke at point.

        @type point: L{Point}
        """
        stroke = Stroke()
        stroke.append_point(point)

        self.append_stroke(stroke)

    def line_to_point(self, point):
        """
        Add point to the current stroke.

        @type point: L{Point}
        """
        self._strokes[-1].append(point)

    def get_n_strokes(self):
        """
        Return the number of strokes.

        @rtype: int
        """
        return len(self._strokes)

    def get_n_points(self):
        """
        Return the total number of points.
        """
        return sum([len(s) for s in self._strokes])

    def get_strokes(self, full=False):
        """
        Return strokes.

        @type full: boolean
        @param full: whether to return strokes as objects or as (x,y) pairs
        """
        if not full:
            # For compatibility
            return [[(int(p.x), int(p.y)) for p in s] for s in self._strokes]
        else:
            return self._strokes

    def append_stroke(self, stroke):
        """
        Add a new stroke.

        @type stroke: L{Stroke}
        """
        self._strokes.append(stroke)

    def insert_stroke(self, i, stroke):
        """
        Insert a stroke at a given position.

        @type stroke: L{Stroke}
        @type i: int
        @param i: position at which to add the stroke (starts at 0)
        """
        self._strokes.insert(i, stroke)

    def remove_stroke(self, i):
        """
        Remove the ith stroke.

        @type i: int
        @param i: position at which to delete a stroke (starts at 0)
        """
        if self.get_n_strokes() - 1 >= i:
            del self._strokes[i]

    def remove_last_stroke(self):
        """
        Remove last stroke.

        Equivalent to remove_stroke(n-1) where n is the number of strokes.
        """
        if self.get_n_strokes() > 0:
            del self._strokes[-1]

    def replace_stroke(self, i, stroke):
        """
        Replace the ith stroke with a new stroke.

        @type i: int
        @param i: position at which to replace a stroke (starts at 0)
        @type stroke: L{Stroke}
        @param stroke: the new stroke
        """
        if self.get_n_strokes() - 1 >= i:
            self.remove_stroke(i)
            self.insert_stroke(i, stroke)

    def resize(self, xrate, yrate):
        """
        Scale writing.

        @type xrate: float
        @param xrate: the x scaling factor
        @type yrate: float
        @param yrate: the y scaling factor
        """
        for stroke in self._strokes:
            if len(stroke) == 0:
                continue

            stroke[0].resize(xrate, yrate)

            for point in stroke[1:]:
                point.resize(xrate, yrate)

    def move_rel(self, dx, dy):
        """
        Translate writing.

        @type dx: int
        @param dx: relative distance from current position
        @type dy: int
        @param yrate: relative distance from current position
        """
        for stroke in self._strokes:
            if len(stroke) == 0:
                continue

            stroke[0].move_rel(dx, dy)

            for point in stroke[1:]:
                point.move_rel(dx, dy)

    def size(self):
        """
        Return writing size.

        @rtype: (x, y, width, height)
        @return: (x,y) are the coordinates of the upper-left point
        """
        xmin, ymin = 4294967296, 4294967296 # 2^32
        xmax, ymax = 0, 0

        for stroke in self._strokes:
            for point in stroke:
                xmin = min(xmin, point.x)
                ymin = min(ymin, point.y)
                xmax = max(xmax, point.x)
                ymax = max(ymax, point.y)

        return (xmin, ymin, xmax-xmin, ymax-ymin)

    def is_small(self):
        """
        Return whether the writing is small or not.

        A writing is considered small when it is written in a corner.
        This is used in Japanese to detect small hiragana and katakana.

        Note: is_small() should be used before normalize().

        @rtype: boolean
        @return: whether the writing is small or not
        """
        x, y, w, h = self.size()
        # 0.44 and 0.56 are used instead of 0.5 to allow the character to go a
        # little bit beyond the corners
        return ((x+w <= self.get_width() * 0.56 and
                 y+h <= 0.56 * self.get_height()) or # top-left
                (x >= 0.44 * self.get_width() and
                 y+h <= 0.56 * self.get_height()) or # top-right
                (x+w <= self.get_width() * 0.56 and
                 y >= 0.44 * self.get_height()) or # bottom-left
                (x >= 0.44 * self.get_width() and
                 y >= 0.44 * self.get_height())) # bottom-right

    def normalize(self):
        """
        Call L{normalize_size} and L{normalize_position} consecutively.
        """
        self.normalize_size()
        self.normalize_position()

    def normalize_position(self):
        """
        Translate character so as to have the same amount of space to
        each side of the drawing box.

        It improves the quality of characters by making them
        more centered on the drawing box.
        """
        x, y, width, height = self.size()

        dx = (self._width - width) / 2 - x
        dy = (self._height - height) / 2 - y

        self.move_rel(dx, dy)

    def normalize_size(self):
        """
        Scale character to match a given, fixed size.

        This improves the quality of characters which are too big or too small.
        """

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

        @type n: int
        """
        for s in self._strokes:
            s.downsample(n)

    def downsample_threshold(self, threshold):
        """
        Downsample by removing consecutive samples for which
        the euclidean distance is inferior to threshold.

        @type threshod: int
        """
        for s in self._strokes:
            s.downsample_threshold(threshold)

    def upsample(self, n):
        """
        'Artificially' increase sampling by adding n linearly spaced points
        between consecutive points.

        @type n: int
        """
        for s in self._strokes:
            s.upsample(n)

    def upsample_threshold(self, threshold):
        """
        'Artificially' increase sampling, using threshold to determine
        how many samples to add between consecutive points.

        @type threshold: int
        """
        for s in self._strokes:
            s.upsample_threshold(threshold)

    def get_size(self):
        """
        Return the size of the drawing box.

        @rtype: tuple

        Not to be confused with size() which returns the size the writing.
        """
        return (self.get_width(), self.get_height())

    def set_size(self, w, h):
        self.set_width(w)
        self.set_height(h)

    def get_width(self):
        """
        Return the width of the drawing box.

        @rtype: int
        """
        return self._width

    def set_width(self, width):
        """
        Set the drawing box width.

        This is necessary if the points which are added were not drawn in
        1000x1000 drawing box.
        """
        self._width = width

    def get_height(self):
        """
        Return the height of the drawing box.

        @rtype: int
        """
        return self._height

    def set_height(self, height):
        """
        Set the drawing box height.

        This is necessary if the points which are added were not drawn in
        1000x1000 drawing box.
        """
        self._height = height

    def to_xml(self):
        """
        Converts writing to XML.

        @rtype: str
        """
        s = "<width>%d</width>\n" % self.get_width()
        s += "<height>%d</height>\n" % self.get_height()

        s += "<strokes>\n"

        for stroke in self._strokes:
            for line in stroke.to_xml().split("\n"):
                s += "  %s\n" % line

        s += "</strokes>"

        return s

    def to_json(self):
        """
        Converts writing to JSON.

        @rtype: str
        """
        s = "{ \"width\" : %d, " % self.get_width()
        s += "\"height\" : %d, " % self.get_height()
        s += "\"strokes\" : ["

        s += ", ".join([stroke.to_json() for stroke in self._strokes])

        s += "]}"

        return s

    def to_sexp(self):
        """
        Converts writing to S-expressions.

        @rtype: str
        """
        return "((width %d)(height %d)(strokes %s))" % \
            (self._width, self._height,
             "".join([s.to_sexp() for s in self._strokes]))

    def __eq__(self, othr):
        if not othr.__class__.__name__ in ("Writing", "WritingProxy"):
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


        self.clear()
        self._is_smoothed = s.get_is_smoothed()
        for p in s:
            self.append_point(p.copy())

    def copy_from(self, w):
        """
        Replace writing with another writing.

        @type w: L{Writing}
        @param w: the writing to copy from
        """
        self.clear()
        self.set_width(w.get_width())
        self.set_height(w.get_height())

        for s in w.get_strokes(True):
            self.append_stroke(s.copy())

    def copy(self):
        """
        Return a copy writing.

        @rtype: L{Writing}
        """
        c = Writing()
        c.copy_from(self)
        return c

    def smooth(self):
        """
        Smooth all strokes. See L{Stroke.smooth}.
        """
        for stroke in self._strokes:
            stroke.smooth()

    def __repr__(self):
        return "<Writing %d strokes (ref %d)>" % (self.get_n_strokes(),
                                                  id(self))

class _IOBase(object):
    """
    Class providing IO functionality to L{Character} and \
    L{CharacterCollection}.
    """

    def __init__(self, path=None):
        self._path = path

        if path is not None:
            gzip = True if path.endswith(".gz") or path.endswith(".gzip") \
                        else False
            bz2 = True if path.endswith(".bz2") or path.endswith(".bzip2") \
                       else False

            self.read(path, gzip=gzip, bz2=bz2)

    def read(self, file, gzip=False, bz2=False, compresslevel=9):
        """
        Read XML from a file.

        @type file: str or file
        @param file: path to file or file object

        @type gzip: boolean
        @param gzip: whether the file is gzip-compressed or not

        @type bz2: boolean
        @param bz2: whether the file is bzip2-compressed or not

        @type compresslevel: int
        @param compresslevel: compression level (see gzip module documentation)

        Raises ValueError if incorrect XML.
        """
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

                self._parse_file(file)
                file.close()
            else:
                self._parse_file(file)
        except (IOError, xml.parsers.expat.ExpatError):
            raise ValueError

    def read_string(self, string, gzip=False, bz2=False, compresslevel=9):
        """
        Read XML from string.

        @type string: str
        @param string: string containing XML

        Other parameters are identical to L{read}.
        """
        if gzip:
            io = cStringIO.StringIO(string)
            io = gzipm.GzipFile(fileobj=io, compresslevel=compresslevel)
            string = io.read()
        elif bz2:
            try:
                string = bz2m.decompress(string)
            except NameError:
                raise NotImplementedError

        self._parse_str(string)

    def write(self, file, gzip=False, bz2=False, compresslevel=9):
        """
        Write XML to a file.

        @type file: str or file
        @param file: path to file or file object

        @type gzip: boolean
        @param gzip: whether the file need be gzip-compressed or not

        @type bz2: boolean
        @param bz2: whether the file need be bzip2-compressed or not

        @type compresslevel: int
        @param compresslevel: compression level (see gzip module documentation)
        """
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

            file.write(self.to_str())
            file.close()
        else:
            file.write(self.to_str())

    def write_string(self, gzip=False, bz2=False, compresslevel=9):
        """
        Write XML to string.

        @rtype: str
        @return: string containing XML

        Other parameters are identical to L{write}.
        """
        if bz2:
            try:
                return bz2m.compress(self.to_str(), compresslevel=compresslevel)
            except NameError:
                raise NotImplementedError
        elif gzip:
            io = cStringIO.StringIO()
            f = gzipm.GzipFile(fileobj=io, mode="w",
                               compresslevel=compresslevel)
            f.write(self.to_str())
            f.close()
            return io.getvalue()
        else:
            return self.to_str()

    def save(self, path=None):
        """
        Save character to file.

        @type path: str
        @param path: path where to write the file or None if use the path \
                     that was given to the constructor

        The file extension is used to determine whether the file is plain,
        gzip-compressed or bzip2-compressed XML.
        """
        if [path, self._path] == [None, None]:
            raise ValueError, "A path must be specified"
        elif path is None:
            path = self._path

        gzip = True if path.endswith(".gz") or path.endswith(".gzip") \
                    else False
        bz2 = True if path.endswith(".bz2") or path.endswith(".bzip2") \
                       else False

        self.write(path, gzip=gzip, bz2=bz2)

class _XmlBase(_IOBase):
    """
    Class providing XML functionality to L{Character} and \
    L{CharacterCollection}.
    """

    @classmethod
    def validate(cls, string):
        """
        Validate XML against a DTD.

        @type string: str
        @param string: a string containing XML

        DTD must be an attribute of cls.
        """
        try:
            # first check whether etree is available or not
            etree
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

    def _parse_file(self, file):
        parser = self._get_parser()
        parser.ParseFile(file)

    def _parse_str(self, string):
        parser = self._get_parser()
        parser.Parse(string)

    def _get_parser(self):
        parser = xml.parsers.expat.ParserCreate(encoding="UTF-8")
        parser.StartElementHandler = self._start_element
        parser.EndElementHandler = self._end_element
        parser.CharacterDataHandler = self._char_data
        self._first_tag = True
        return parser

class Character(_XmlBase):
    """
    A handwritten character.

    A Character is composed of meta-data and handwriting data.
    Handwriting data are contained in L{Writing} objects.

    Building character objects
    ==========================

    A character can be built from scratch progmatically:

    >>> s = Stroke()
    >>> s.append_point(Point(10, 20))
    >>> w = Writing()
    >>> w.append_stroke(s)
    >>> c = Character()
    >>> c.set_writing(writing)

    Reading XML files
    =================

    A character can be read from an XML file:

    >>> c = Character()
    >>> c.read("myfile")

    Gzip-compressed and bzip2-compressed XML files can also be read:

    >>> c = Character()
    >>> c.read("myfilegz", gzip=True)

    >>> c = Character()
    >>> c.read("myfilebz", bz2=True)

    A similar method read_string exists to read the XML from a string
    instead of a file.

    For convenience, you can directly load a character by passing it the
    file to load. In that case, compression is automatically detected based on
    file extension (.gz, .bz2).

    >>> c = Character("myfile.xml.gz")

    The recommended extension for XML character files is .xml.

    Writing XML files
    =================

    A character can be saved to an XML file by using the write() method.

    >>> c.write("myfile")

    The write method has gzip and bz2 arguments just like read(). In addition,
    there is a write_string method which generates a string instead of a file.

    For convenience, you can save a character with the save() method.
    It automatically detects compression based on the file extension.

    >>> c.save("mynewfile.xml.bz2")

    If the Character object was passed a file when it was constructed,
    the path can ce omitted.

    >>> c = Character("myfile.gz")
    >>> c.save()

    >>> c = Character()
    >>> c.save()
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "tegaki/character.py", line 1238, in save
        raise ValueError, "A path must be specified"
    ValueError: A path must be specified

    """

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

    def __init__(self, path=None):
        """
        Creates a new Character.

        @type path: str or None
        @param path: path to file to load or None if empty character

        The file extension is used to determine whether the file is plain,
        gzip-compressed or bzip2-compressed XML.
        """
        self._writing = Writing()
        self._utf8 = None
        _XmlBase.__init__(self, path)

    def get_utf8(self):
        """
        Return the label of the character.

        @rtype: str
        """
        return self._utf8

    def get_unicode(self):
        """
        Return the label character.

        @rtype: unicode
        """
        return unicode(self.get_utf8(), "utf8")

    def set_utf8(self, utf8):
        """
        Set the label the character.

        @type utf8: str
        """
        self._utf8 = utf8

    def set_unicode(self, uni):
        """
        Set the label of the character.

        @type uni: unicode
        """
        self._utf8 = uni.encode("utf8")

    def get_writing(self):
        """
        Return the handwriting data of the character.

        @rtype: L{Writing}
        """
        return self._writing

    def set_writing(self, writing):
        """
        Set the handwriting data of the character.

        @type writing: L{Writing}
        """

        self._writing = writing

    def hash(self):
        """
        Return a sha1 digest for that character.
        """
        return hashlib.sha1(self.to_xml()).hexdigest()

    def to_str(self):
        return self.to_xml()

    def to_xml(self):
        """
        Converts character to XML.

        @rtype: str
        """
        s = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"

        s += "<character>\n"

        if self._utf8:
            s += "  <utf8>%s</utf8>\n" % self._utf8

        for line in self._writing.to_xml().split("\n"):
            s += "  %s\n" % line

        s += "</character>"

        return s

    def to_json(self):
        """
        Converts character to JSON.

        @rtype: str
        """
        s = "{"

        attrs = ["\"utf8\" : \"%s\"" % self._utf8,
                 "\"writing\" : " + self._writing.to_json()]

        s += ", ".join(attrs)

        s += "}"

        return s

    def to_sexp(self):
        """
        Converts character to S-expressions.

        @rtype: str
        """
        return "(character (value %s)" % self._utf8 + \
                    self._writing.to_sexp()[1:-1]

    def __eq__(self, char):
        if not char.__class__.__name__ in ("Character", "CharacterProxy"):
            return False

        return self._utf8 == char.get_utf8() and \
               self._writing == char.get_writing()

    def __ne__(self, othr):
        return not(self == othr)


        self.clear()
        self.set_width(w.get_width())
        self.set_height(w.get_height())

        for s in w.get_strokes(True):
            self.append_stroke(s.copy())

    def copy_from(self, c):
        """
        Replace character with another character.

        @type c: L{Character}
        @param c: the character to copy from
        """
        self.set_utf8(c.get_utf8())
        self.set_writing(c.get_writing().copy())

    def copy(self):
        """
        Return a copy of character.

        @rtype: L{Character}
        """
        c = Character()
        c.copy_from(self)
        return c

    def __repr__(self):
        return "<Character %s (ref %d)>" % (str(self.get_utf8()), id(self))

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

