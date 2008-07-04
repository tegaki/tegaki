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

import unittest

from tegaki.maths import *

class MathTest(unittest.TestCase):

    def testEuclideanDistance(self):
        for v1, v2, expected in ( ( (2, 10, 12), (3, 10, 7), 5.0 ),
                                  ( (5, 5), (5, 5), 0.0)
                                ):

            res = round(euclidean_distance(v1, v2))
            self.assertEquals(res, expected)
