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
from tegaki.arrayutils import *
import models.basic.model

class Model(models.basic.model.Model):
    """
    Title: basic_latin
    """

    def __init__(self, *args):
        models.basic.model.Model.__init__(self, *args)

        self.N_STATES_PER_STROKE = 8
        self.TRAIN_CORPORA = ["latin-writer1"]
        self.EVAL_CORPORA = self.TRAIN_CORPORA

        self.ROOT = os.path.join("models", "basic_latin")
        self.update_folder_paths()

    def get_feature_vectors(self, writing):
        """
        Get deltax and deltay as feature vectors.
        """
        return models.basic.model.Model.get_feature_vectors(self,
                                                            writing,
                                                            normalize=True)
        