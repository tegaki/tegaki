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

# Incomplete parser for the unipen version of the kuchibue database
# See http://www.tuat.ac.jp/~nakagawa/database/

import re
import os

from tegaki.character import Point, Stroke, Writing, Character
from tegaki.charcol import CharacterCollection

from .unipen import UnipenParser
from .shiftjis import SHIFT_JIS_TABLE

class KuchibueParser(UnipenParser):

    # The Kuchibue database has three major differences with Tegaki
    #
    # 1) (0, 0) is the left-bottom corner in the former while it's the top-
    #    left corner in the latter.
    # 2) the default screen size is 1280*960 for the former while it's
    #    1000 * 1000 for the latter
    # 3) the screen contains 152 boxes (19 columns, 8 rows) for the former
    #    while it contains only 1 for the latter

    def __init__(self):
        UnipenParser.__init__(self)
        self._labels = []
        self._characters = []
        self._char = None
        self._row = 0
        self._col = 0
        self._screen = None
        self._line = None

    def _handle_SEGMENT(self, args):
        seg_type, delimit, quality, label = args.split(" ")
        if seg_type == "SCREEN":
            self._screen = []
        elif seg_type == "LINE":
            self._screen.append(0) # number of characters in line
        elif seg_type == "CHARACTER":
            label = label.strip()[1:-1]
            if label.startswith("SJIS"):
                charcode = int("0" + label[4:], 16)
                try:
                    label = SHIFT_JIS_TABLE[charcode]
                except KeyError:
                    pass #print "missing character", hex(charcode)
                    
            self._labels.append(label)
            self._screen[-1] += 1

    def _handle_X_DIM(self, args):
        self.FRAME_WIDTH = int(args)

    def _handle_Y_DIM(self, args):
        self.FRAME_HEIGHT = int(args)

    def _get_int_pair_from_line(self, line):
        k, v = line.split(":")
        return [int(val) for val in v.strip().split(" ")]

    def _handle_PAD(self, args):
        lines = [l.strip() for l in args.split("\n")]
        for line in lines:
            if line.startswith("Input Resolution"):
                self.INPUT_RESOLUTION_WIDTH, self.INPUT_RESOLUTION_HEIGHT = \
                    self._get_int_pair_from_line(line)

    def _handle_DATA_INFO(self, args):
        lines = [l.strip() for l in args.split("\n")]
        for line in lines:
            if line.startswith("Frame start"):
                self.FRAME_START_X, self.FRAME_START_Y = \
                    self._get_int_pair_from_line(line)
            elif line.startswith("Frame  step"):
                self.FRAME_STEP_X, self.FRAME_STEP_Y = \
                    self._get_int_pair_from_line(line)  
            elif line.startswith("Frame count"):
                self.FRAME_COUNT_COL, self.FRAME_COUNT_ROW = \
                    self._get_int_pair_from_line(line)    

    def _handle_START_BOX(self, args):
        if self._char:
            self._characters.append(self._char)
            if self._col == self.FRAME_COUNT_COL - 1:
                self._col = 0
                if self._row == self.FRAME_COUNT_ROW - 1:
                    self._row = 0
                else:
                    self._row += 1
            else:
                self._col += 1

        self._char = Character()

    def handle_eof(self):
        if self._char:
            self._characters.append(self._char)

    def _get_coordinates(self, x, y):
        y = abs(y - self.INPUT_RESOLUTION_HEIGHT) # change basis
        x -= self.FRAME_START_X # remove the padding
        x -= self.FRAME_STEP_X * self._col # translate to the left
        x *= float(Writing.WIDTH) / self.FRAME_WIDTH # scale for x = 1000
        y -= (self.INPUT_RESOLUTION_HEIGHT - self.FRAME_START_Y) # padding
        y -= self.FRAME_STEP_Y * self._row # translate to the top
        y *= float(Writing.HEIGHT) / self.FRAME_HEIGHT # scale for y = 1000
        return (int(x), int(y))

    def _handle_PEN_DOWN(self, args):
        writing = self._char.get_writing()
        points = [[int(p_) for p_ in p.split(" ")] \
                    for p in args.strip().split("\n")]
        stroke = Stroke()
        for x, y in points:
            x, y = self._get_coordinates(x,y)
            #assert(x >= 0 and x <= 1000)
            #assert(y >= 0 and y <= 1000)
            stroke.append_point(Point(x,y))
        writing.append_stroke(stroke)

    def _handle_PEN_UP(self, args):
        writing = self._char.get_writing()
        x, y = [int(p) for p in args.strip().split(" ")]
        x, y = self._get_coordinates(x,y)
        strokes = writing.get_strokes()
        strokes[-1].append(Point(x,y))

def kuchibue_to_character_collection(path):
    parser = KuchibueParser()
    parser.parse_file(path)
    return parser.get_character_collection()

if __name__ == "__main__":
    import sys
    charcol = kuchibue_to_character_collection(sys.argv[1])
    print(charcol.to_xml())
