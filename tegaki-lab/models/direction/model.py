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
import math

from tegaki.arrayutils import *
from tegaki.mathutils import *
import models.basic.model

class Model(models.basic.model.Model):
    """
    Title: direction
    Feature vectors: (distance, angle)
        distance = euclidean distance between two consecutive samples.
        angle = angle of the current sample to the origin.
    """

    def __init__(self, *args):
        models.basic.model.Model.__init__(self, *args)

        self.SAMPLING = 0.5
        self.N_STATES_PER_STROKE = 3
        self.N_DIMENSIONS = 2

        self.TRAIN_CORPORA = ["japanese-learner1", "japanese-native1"]
        self.EVAL_CORPORA = ["japanese-learner1", "japanese-native1"]

        self.ROOT = os.path.join("models", "direction")
        self.update_folder_paths()

    ########################################
    # Feature extraction...
    ########################################

    def get_feature_vectors(self, writing):
        """
        Get (distance, angle).
        """
        strokes = writing.get_strokes()
        vectors = [(x,y) for stroke in strokes for x,y in stroke]
        vectors = array_sample(vectors, self.SAMPLING)

        arr = []

        for i in range(1, len(vectors)):
            ((x1, y1), (x2, y2)) = (vectors[i-1], vectors[i])

            distance = euclidean_distance((x1,y1), (x2,y2))
            r, teta = cartesian_to_polar(x2, y2)

            arr.append((distance, teta))

        return arr