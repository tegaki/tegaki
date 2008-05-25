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

import lib.base as base


class BaseTest(unittest.TestCase):

    def testArrayFlatten(self):
        for arr, expected in (
                                ([[1,2], [3,4]], [1, 2, 3, 4]),
                                ([[]], [])
                             ):
            
            self.assertEquals(base.array_flatten(arr), expected)

    def testArrayReshape(self):
        for arr, expected, n in (
                                ([1, 2, 3, 4], [[1,2], [3,4]], 2),
                                ([], [], 2),
                                ([1, 2, 3], [[1, 2]], 2) # expected 4 values
                             ):
            
            self.assertEquals(base.array_reshape(arr, n), expected)


    def testArraySplit(self):
        arr = [[1,2], [3,4], [5,6], [7,8], [9, 10], [11, 12]]
        expected = [ [[1,2],[3,4]], [[5,6],[7, 8]], [[9,10],[11,12]] ]

        self.assertEquals(base.array_split(arr, 3), expected)

    def testArrayMean(self):
        arr = [1, 2, 3, 4]
        expected = 2.5

        self.assertEquals(base.array_mean(arr), expected)

    def testArrayVariance(self):
        arr = [1, 2, 3, 4]
        expected = 1.25

        self.assertEquals(base.array_variance(arr), expected)
        

        

