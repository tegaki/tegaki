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

import numpy

def dtw(s, t, d):
    n = len(s)
    m = len(t)
    
    DTW = numpy.zeros((n, m))
   
    infinity = float('infinity')
    
    for i in range(1, m):
        DTW[0, i] = infinity
        
    for i in range(1, n):
        DTW[i, 0] = infinity
       
    for i in range(0, n):
        for j in range(0, m):
            cost = d(s[i], t[j])
            DTW[i, j] = cost + min(DTW[i-1, j], DTW[i, j-1], DTW[i-1, j-1])

    return DTW[n - 1, m - 1]
