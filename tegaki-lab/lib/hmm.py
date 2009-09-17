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
from math import sqrt
try:
    import cPickle as pickle
except ImportError:
    import pickle
from tegaki.arrayutils import *

class _Pickable:

    @classmethod
    def from_file(cls, input_file):
        f = open(input_file)
        ret = pickle.load(f)
        f.close()
        return ret

    def write(self, output_file):
        if os.path.exists(output_file):
            os.unlink(output_file)

        f = open(output_file, "w")
        pickle.dump(self, f)
        f.close()

class Sequence(list, _Pickable):
    pass

class SequenceSet(list, _Pickable):
    pass

class MultivariateHmm(object, _Pickable):

    def __init__(self, A, B, pi):
        self.A = A
        self.B = B
        self.pi = pi

try:
    import ghmm

    DOMAIN = ghmm.Float()

    class _GhmmBase(object):

        def _get_hmm(self, hmm):
            return ghmm.HMMFromMatrices(DOMAIN,
                            ghmm.MultivariateGaussianDistribution(DOMAIN),
                            hmm.A, hmm.B, hmm.pi)    

    class GhmmBaumWelchTrainer(_GhmmBase):

        def train(self, hmm, sset):
            sset = [array_flatten(s) for s in sset]
            hmm_ = self._get_hmm(hmm)
            hmm_.baumWelch(ghmm.SequenceSet(DOMAIN, sset))
            hmm.A, hmm.B, hmm.pi = hmm_.asMatrices()

    class GhmmViterbiCalculator(_GhmmBase):

        def viterbi(self, hmm, obj):
            hmm_ = self._get_hmm(hmm)

            if isinstance(obj, SequenceSet):
                obj = [array_flatten(s) for s in obj]
                obj = ghmm.SequenceSet(DOMAIN, obj)
                res = hmm_.viterbi(obj)
                # ghmm returns a scalar even though a sequence set was passed
                # if length == 1 but we want an array
                if len(obj) == 1:
                    res = [[res[0]], [res[1]]]
            else:
                obj = ghmm.EmissionSequence(DOMAIN, array_flatten(obj))
                res = hmm_.viterbi(obj)
    
            return res

except ImportError:
    pass

import platform

if platform.system() == "Java": # Jython 2.5

    import java
    from java.util import ArrayList

    from be.ac.ulg.montefiore.run.jahmm import ObservationVector
    from be.ac.ulg.montefiore.run.jahmm import OpdfMultiGaussian
    from be.ac.ulg.montefiore.run.jahmm import Hmm
    from be.ac.ulg.montefiore.run.jahmm.learn import BaumWelchLearner
    from be.ac.ulg.montefiore.run.jahmm.learn import BaumWelchScaledLearner
    from be.ac.ulg.montefiore.run.jahmm import ViterbiCalculator

    class _JahmmBase(object):

        def _get_hmm(self, hmm):
            """
            Gets the internal HMM as a Jahmm object.
            """
            opdfs = []
            for means, covmatrix in hmm.B:
                covmatrix = array_split(covmatrix, int(sqrt(len(covmatrix))))
                opdfs.append(OpdfMultiGaussian(means, covmatrix))

            return Hmm(hmm.pi, hmm.A, ArrayList(opdfs))

        def _vectors_to_observations(self, vectors):
            arr = [ObservationVector(v) for v in vectors]
            return ArrayList(arr)

        def _sset_to_array_list(self, sset):
            obs_set = ArrayList()
            for seq in sset:
                obs_set.add(self._vectors_to_observations(seq))
            return obs_set

    class JahmmBaumWelchTrainer(_JahmmBase):

        def _update_hmm(self, hmm, hmm_):
            """
            Updates the internal HMM from a Jahmm object.
            """
            hmm.pi = [hmm_.getPi(i) for i in range(hmm_.nbStates())]

            hmm.A = []
            for i in range(hmm_.nbStates()):
                arr = []
                for j in range(hmm_.nbStates()):
                    arr.append(hmm_.getAij(i, j))
                hmm.A.append(arr)

            opdfs = [hmm_.getOpdf(i) for i in range(hmm_.nbStates())]
            hmm.B = []
            for opdf in opdfs:
                means = opdf.mean().tolist()
                covmatrix = [a.tolist() for a in opdf.covariance()]
                covmatrix = array_flatten(covmatrix)
                hmm.B.append([means, covmatrix])

        def train(self, hmm, sset):
            hmm_ = self._get_hmm(hmm)
            learner = BaumWelchScaledLearner()

            obs_set = self._sset_to_array_list(sset)

            try:
                hmm_ = learner.learn(hmm_, obs_set)
                self._update_hmm(hmm, hmm_)
            except java.lang.IllegalArgumentException:
                print "Couldn't train HMM"

    class JahmmViterbiCalculator(_JahmmBase):

        def _viterbi(self, seq, hmm_):
            calc = ViterbiCalculator(self._vectors_to_observations(seq), hmm_)
            return calc.stateSequence().tolist(), calc.lnProbability()

        def viterbi(self, hmm, obj):
            hmm_ = self._get_hmm(hmm)

            if isinstance(obj, SequenceSet):
                res = [self._viterbi(seq, hmm_) for seq in obj]
                all_paths = [res[i][0] for i in range(len(res))]
                all_logp = [res[i][1] for i in range(len(res))]
                return all_paths, all_logp
            else:
                return self._viterbi(obj, hmm_)
