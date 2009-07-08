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

import os
import ghmm
import glob

from tegaki.arrayutils import *

import models.basic.model

class Model(models.basic.model.Model):
    """
    Title: 6dim
    Feature vectors: (x, y, delta x, delta y, delta2 x, delta2 y)
    """

    def __init__(self, *args):
        models.basic.model.Model.__init__(self, *args)

        self.SAMPLING = 0.5
        self.N_STATES_PER_STROKE = 3
        self.N_DIMENSIONS = 6
        self.NON_DIAGONAL = True

        self.TRAIN_CORPORA = ["japanese-learner1", "japanese-native1"]
        self.EVAL_CORPORA = ["japanese-learner1", "japanese-native1"]

        self.ROOT = os.path.join("models", "6dim")
        self.update_folder_paths()

    ########################################
    # Feature extraction...
    ########################################

    def get_feature_vectors(self, writing):
        """
        Get (x, y, delta x, delta y, delta2 x, delta2 y)

        delta x and delta y are the velocity up to a factor

        delta2 x and delta2 y are the acceleration up to a factor
        """
        strokes = writing.get_strokes()
        vectors = [[x,y] for stroke in strokes for x,y in stroke]
        vectors = array_sample(vectors, self.SAMPLING)

        # arr contains (delta x, delta y) pairs
        arr = []

        for i in range(1, len(vectors)):
            ((x1, y1), (x2, y2)) = (vectors[i-1], vectors[i])
            deltax = float(abs(x2 - x1))
            deltay = float(abs(y2 - y1))

            arr.append([deltax, deltay])

        # arr2 contains (delta2 x, delta2 y) pairs
        arr2 = []

        for i in range(1, len(arr)):
            ((x1, y1), (x2, y2)) = (arr[i-1], arr[i])
            delta2x = float(abs(x2 - x1))
            delta2y = float(abs(y2 - y1))

            arr2.append([delta2x, delta2y])

        # "vectors" contains 2 elements less than arr2
        # "arr" contains 1 element less than arr2
        ret = array_add(vectors[2:], arr[1:])
        ret = array_add(ret, arr2)
        
        return ret
