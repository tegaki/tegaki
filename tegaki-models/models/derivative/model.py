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

from tegaki.array import *
import models.basic.model

class Model(models.basic.model.Model):
    """
    Feature vectors: derivative
    """

    def __init__(self, *args):
        models.basic.model.Model.__init__(self, *args)

        self.SAMPLING = 0.5
        self.N_STATES_PER_STROKE = 3
        self.N_DIMENSIONS = 2
        self.WINDOW_SIZE = 2

        self.ROOT = os.path.join("models", "derivative")
        self.update_folder_paths()

    ########################################
    # Feature extraction...
    ########################################

    def get_feature_vectors(self, writing):
        """
        Get derivative as feature vectors.
        Formula obtained from
        "An Online Handwriting Recognition System For Turkish"
        Esra Vural, Hakan Erdogan, Kemal Oflazer, Berrin Yanikoglu
        Sabanci University, Tuzla, Istanbul, Turkey
        """
        arr = []
        
        strokes = writing.get_strokes()

        sampling = int(1 / self.SAMPLING)

        for stroke in strokes:

            for i in range(self.WINDOW_SIZE,
                           len(stroke) - self.WINDOW_SIZE,
                           sampling):
            
                xnum = 0
                ynum = 0
            
                for teta in range(1, self.WINDOW_SIZE + 1):
                    xnum += (stroke[i+teta][0] - stroke[i-teta][0]) * teta
                    ynum += (stroke[i+teta][1] - stroke[i-teta][1]) * teta

                denom = 0

                for teta in range(1, self.WINDOW_SIZE + 1):
                    denom += teta ** 2

                denom *= 2

                xderivative = xnum / denom
                yderivative = ynum / denom

                arr.append([xderivative, yderivative])
                
        return arr    
