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

from tegaki.arrayutils import *
import models.basic.model

from lib.exceptions import *

class Model(models.basic.model.Model):
    """
    Title: prop-n-states
    Number of states: proportional to the number of observations
    """

    def __init__(self, *args):
        models.basic.model.Model.__init__(self, *args)

        self.SAMPLING = 0.5
        self.AVERAGE_N_STATES = 25
        self.N_DIMENSIONS = 2
        self.NON_DIAGONAL = True

        self.ROOT = os.path.join("models", "prop_n_states")
        self.update_folder_paths()


    def get_n_observations(self, sset):
        n_observations = sum([len(seq) for seq in sset])
        n_characters = len(sset)
        return (n_observations, n_characters)

    def get_initial_hmm(self, sset, avg_n_obs_per_char):
        obs, chars = self.get_n_observations(sset)

        n_obs = float(obs) / chars
        
        n_states = round(n_obs / avg_n_obs_per_char * self.AVERAGE_N_STATES)
        n_states = int(n_states)

        self.print_verbose("%s (%d): %d" % \
                            (self.get_utf8_from_char_code(sset.char_code),
                             sset.char_code,
                             n_states))
        
        pi = self.get_initial_state_probabilities(n_states)
        A = self.get_state_transition_matrix(n_states)
        B = self.get_emission_matrix(n_states, sset)

        hmm = ghmm.HMMFromMatrices(
                    self.DOMAIN,
                    ghmm.MultivariateGaussianDistribution(self.DOMAIN),
                    A,
                    B,
                    pi)
        
        return hmm
          

    def init(self):
        feature_files = self.get_train_feature_files()

        if len(feature_files) == 0:
            raise ModelException, "No feature files found."
        
        if not os.path.exists(self.INIT_HMM_ROOT):
            os.makedirs(self.INIT_HMM_ROOT)

        ssets = []

        # calculate the average number of observations for all characters
        n_observations = 0
        n_characters = 0
        
        for sset_file in feature_files:
            char_code = int(os.path.basename(sset_file[:-5]))
            
            sset = self.get_sequence_set(sset_file)
            sset.char_code = char_code
            ssets.append(sset)

            obs, chars = self.get_n_observations(sset)
            n_observations += obs
            n_characters += chars

        avg_n_obs_per_char = float(n_observations) / n_characters
            
        for sset in ssets:
            hmm = self.get_initial_hmm(sset, avg_n_obs_per_char)

            output_file = os.path.join(self.INIT_HMM_ROOT,
                                       "%d.xml" % sset.char_code)

            if os.path.exists(output_file):
                os.unlink(output_file)

            hmm.write(output_file)
            