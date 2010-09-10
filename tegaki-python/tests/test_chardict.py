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

import unittest
import os
import sys
import StringIO
import minjson
import tempfile

from tegaki.chardict import CharacterStrokeDictionary

class CharacterStrokeDictionaryTest(unittest.TestCase):

    def setUp(self):
        self.currdir = os.path.dirname(os.path.abspath(__file__))
        self.txt = os.path.join(self.currdir, "data", "strokes_ja.txt")
        self.gz = os.path.join(self.currdir, "data", "strokes_ja.txt.gz")

    def testRead(self):
        cdict = CharacterStrokeDictionary(self.txt)
        cdictgz = CharacterStrokeDictionary(self.gz)

        for d in (cdict, cdictgz):
            self.assertEquals(len(d), 8)
            self.assertTrue(u"⺕" in d.get_characters())

    def testWrite(self):
        cdict = CharacterStrokeDictionary(self.txt)
        io = StringIO.StringIO()
        cdict.write(io)
        io.seek(0) # need to rewind the file
        cdict2 = CharacterStrokeDictionary()
        cdict2.read(io)
        self.assertEquals(cdict, cdict2)
