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
import glob

from tegaki.arrayutils import *
import models.basic.model

class Model(models.basic.model.Model):
    """
    Title: cartesian
    Feature vectors: (x, y)!
    """

    def __init__(self, *args):
        models.basic.model.Model.__init__(self, *args)

        self.SAMPLING = 0.5
        self.N_STATES_PER_STROKE = 3
        self.N_DIMENSIONS = 2

        self.TRAIN_CORPORA = ["japanese-learner1", "japanese-native1"]
        self.EVAL_CORPORA = ["japanese-learner1", "japanese-native1"]

        self.ROOT = os.path.join("models", "cartesian")
        self.update_folder_paths()

    ########################################
    # Feature extraction...
    ########################################

    def get_feature_vectors(self, writing):
        """
        Get cartesian coordinates.
        """
        strokes = writing.get_strokes()
        vectors = [(x,y) for stroke in strokes for x,y in stroke]
        vectors = array_sample(vectors, self.SAMPLING)
        return vectors
