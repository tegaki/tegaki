# -*- coding: utf-8 -*-

# Copyright (C) 2008 The Tegaki project contributors
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

from math import sqrt, hypot, atan2, pi

def euclidean_distance(v1, v2):
    assert(len(v1) == len(v2))

    return sqrt(sum([(v2[i] - v1[i]) ** 2 for i in range(len(v1))]))
  
def cartesian_to_polar(x, y):
    """
    Cartesian to polar coordinates conversion.
    r is the distance to the point.
    teta is the angle to the point between 0 and 2 pi.
    """
    r = hypot(x, y)
    teta = atan2(y, x) + pi
    return (r, teta)