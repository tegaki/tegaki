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

import os
import ghmm
import glob

import lib.base as base
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
        vectors = base.array_sample(vectors, self.SAMPLING)
        return vectors
