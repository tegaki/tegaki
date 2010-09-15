# -*- coding: utf-8 -*-

# Copyright (C) 2010 The Tegaki project contributors
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

import cStringIO
import gzip as gzipm
try:
    import bz2 as bz2m
except ImportError:
    pass

from tegaki.character import _IOBase

class CharacterStrokeDictionary(dict, _IOBase):
    """
    A dictionary used to map characters to their stroke sequences.
    This class supports strokes only to keep things simple.
    """

    def __init__(self, path=None):
        _IOBase.__init__(self, path)

    def get_characters(self):
        return self.keys()

    def get_strokes(self, char):
        if isinstance(char, str): char = unicode(char, "utf-8")
        return self[char]

    def set_strokes(self, char, strokes):
        if isinstance(char, str): char = unicode(char, "utf-8")

        for stroke_list in strokes:
            if not isinstance(stroke_list, list):
                raise ValueError

        self[char] = strokes

    def _parse_str(self, string):
        string = unicode(string, "utf-8")

        for line in string.strip().split("\n"):
            try:
                char, strokes = line.split("\t")
                strokes = strokes.strip()
                if len(strokes) == 0: continue
                strokes = strokes.split(" ")
                if not char in self: self[char] = []
                self[char].append(strokes)
            except ValueError:
                pass

    def _parse_file(self, file):
        self._parse_str(file.read())


    def to_str(self):
        s = ""
        for char, strokes in self.items():
            for stroke_list in strokes:
                s += "%s\t%s\n" % (char.encode("utf8"),
                                 " ".join(stroke_list).encode("utf8"))
        return s

