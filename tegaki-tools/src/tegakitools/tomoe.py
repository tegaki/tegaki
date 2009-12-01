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
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Contributors to this file:
# - Mathieu Blondel

from tegaki.character import Point, Stroke, Writing, Character, _XmlBase
from tegaki.charcol import CharacterCollection

class TomoeXmlDictionaryReader(_XmlBase):

    def __init__(self):
        self._charcol = CharacterCollection()

    def get_character_collection(self):
        return self._charcol

    def _start_element(self, name, attrs):
        self._tag = name

        if self._first_tag:
            self._first_tag = False
            if self._tag != "dictionary":
                raise ValueError, "The very first tag should be <dictionary>"

        if self._tag == "character":
            self._writing = Writing()

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
            char = Character()
            char.set_utf8(self._utf8)
            char.set_writing(self._writing)
            self._charcol.add_set(self._utf8)
            self._charcol.append_character(self._utf8, char)

            for s in ["_tag", "_stroke"]:
                if s in self.__dict__:
                    del self.__dict__[s]

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

def tomoe_dict_to_character_collection(path):
    reader = TomoeXmlDictionaryReader()
    gzip = False; bz2 = False
    if path.endswith(".gz"): gzip = True
    if path.endswith(".bz2"): bz2 = True
    reader.read(path, gzip=gzip, bz2=bz2)
    return reader.get_character_collection()

