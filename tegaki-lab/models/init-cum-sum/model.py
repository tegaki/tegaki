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
import math

from tegaki.arrayutils import *
from tegaki.mathutils import *
import models.basic.model as base_model

class Model(base_model.Model):
    
    def __init__(self, *args):
        base_model.Model.__init__(self, *args)

        self.SAMPLING = 0.5
        self.N_STATES_PER_STROKE = 3
        self.N_DIMENSIONS = 2

        self.TRAIN_CORPORA = ["japanese-learner1", "japanese-native1"]
        self.EVAL_CORPORA = ["japanese-learner1", "japanese-native1"]

        self.ROOT = os.path.join("models", "init-cum-sum")
        self.update_folder_paths()

    def get_consecutive_distances(self, seq):
        dists = []
        for i in range(len(seq)-1):
            vect = seq[i]
            next_vect = seq[i+1]
            dists.append(euclidean_distance(vect, next_vect))
        return dists # contains N-1 distances for a sequence of size N

    def get_initial_state_alignment(self, n_states, sset):
        # the idea of this segmentation is to assign more states
        # to portions that vary a lot
        # it doesn't work well for characters with a high degree of stationarity

        all_segments = [[] for i in range(n_states)]

        for seq in sset:
            dists = self.get_consecutive_distances(seq)
            cum_sum = sum(dists)
            step = cum_sum / n_states

            curr_state = 0
            curr_cum_sum = 0
            
            all_segments[0].append(seq[0])

            for i, dist in enumerate(dists):
                curr_cum_sum += dist
                if curr_cum_sum > (curr_state + 1) * step and \
                   curr_state < n_states - 1:
                    curr_state += 1
                all_segments[curr_state].append(seq[i+1])

        if [] in all_segments:
            # there was an empty segment, fall back to uniform segmentation
            all_segments = base_model.Model.get_initial_state_alignment(
                                self, n_states, sset)
       
        return all_segments

