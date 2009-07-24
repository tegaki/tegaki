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

from array import array

from tegaki.mathutils import euclidean_distance

class DtwMatrix:
    # we use 1d-vector V instead of a n*m 2d-matrix M
    # M[i,j] can be accessed by V[k], k = j*n + i

    def __init__(self, n, m):
        self.a = array("f", [0.0] * (n*m))
        self.n = n
        self.m = m

    def __getitem__(self, p):
        return self.a[p[1] * self.n + p[0]]

    def __setitem__(self, p, value):
        self.a[p[1] * self.n + p[0]] = value

def dtw(s, t, d, f=euclidean_distance):
    """
    s; first sequence
    t: second sequence
    d: vector dimension
    f: distance function

    s and t are flat sequences of feature vectors of dimension d, so 
    their length should be multiple of d
    """    
    assert(len(s) % d == 0)
    assert(len(t) % d == 0)

    n = len(s) / d
    m = len(t) / d
   
    DTW = DtwMatrix(n, m)
   
    infinity = 4294967296 # 2^32
    
    for i in range(1, m):
        DTW[(0, i)] = infinity
        
    for i in range(1, n):
        DTW[(i, 0)] = infinity
       
    for i in range(0, n):
        # retrieve 1st d-dimension vector
        v1 = s[i*d:i*d+d]

        for j in range(0, m):
            # retrieve 2nd d-dimension vector
            v2 = t[j*d:j*d+d]
            # distance function
            cost = f(v1, v2)
            # DTW recursion step
            DTW[(i, j)] = cost + min(DTW[(i-1, j)],
                                     DTW[(i-1, j-1)],
                                     DTW[(i, j-1)])
       
    return DTW[(n-1, m-1)]
