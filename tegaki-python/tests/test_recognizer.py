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

from tegaki.recognizer import *

class ResultsTest(unittest.TestCase):

    def testToSmallKana(self):
        res = Results([("マ",1),("チ",2),("ユ",3),("ー",4)]).to_small_kana()
        res2 = Results([("ま",1),("ち",2),("ゆ",3),("ー",4)]).to_small_kana()
        self.assertEquals(res[2][0], "ュ")
        self.assertEquals(res2[2][0], "ゅ")
        