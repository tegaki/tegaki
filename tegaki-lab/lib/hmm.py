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

    class GhmmMultivariateHmm(MultivariateHmm):

        def __init__(self, *args):
            MultivariateHmm.__init__(self, *args)

        def _get_hmm(self):
            return ghmm.HMMFromMatrices(DOMAIN,
                            ghmm.MultivariateGaussianDistribution(DOMAIN),
                            self.A, self.B, self.pi)

        def bw_training(self, sset):
            sset = [array_flatten(s) for s in sset]
            hmm = self._get_hmm()
            hmm.baumWelch(ghmm.SequenceSet(DOMAIN, sset))
            self.A, self.B, self.pi = hmm.asMatrices()

        def viterbi(self, obj):
            hmm = self._get_hmm()

            if isinstance(obj, SequenceSet):
                obj = [array_flatten(s) for s in obj]
                obj = ghmm.SequenceSet(DOMAIN, obj)
            else:
                obj = ghmm.EmissionSequence(DOMAIN, array_flatten(obj))

            return hmm.viterbi(obj)

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

    class JahmmMultivariateHmm(MultivariateHmm):

        def __init__(self, *args):
            MultivariateHmm.__init__(self, *args)

        def _get_hmm(self):
            """
            Gets the internal HMM as a Jahmm object.
            """
            opdfs = []
            for means, covmatrix in self.B:
                covmatrix = array_split(covmatrix, int(sqrt(len(covmatrix))))
                opdfs.append(OpdfMultiGaussian(means, covmatrix))

            return Hmm(self.pi, self.A, ArrayList(opdfs))

        def _update_hmm(self, hmm):
            """
            Updates the internal HMM from a Jahmm object.
            """
            self.pi = [hmm.getPi(i) for i in range(hmm.nbStates())]

            self.A = []
            for i in range(hmm.nbStates()):
                arr = []
                for j in range(hmm.nbStates()):
                    arr.append(hmm.getAij(i, j))
                self.A.append(arr)

            opdfs = [hmm.getOpdf(i) for i in range(hmm.nbStates())]
            self.B = []
            for opdf in opdfs:
                means = opdf.mean().tolist()
                covmatrix = [a.tolist() for a in opdf.covariance()]
                covmatrix = array_flatten(covmatrix)
                self.B.append([means, covmatrix])

        def _vectors_to_observations(self, vectors):
            arr = [ObservationVector(v) for v in vectors]
            return ArrayList(arr)

        def _sset_to_array_list(self, sset):
            obs_set = ArrayList()
            for seq in sset:
                obs_set.add(self._vectors_to_observations(seq))
            return obs_set

        def bw_training(self, sset):
            hmm = self._get_hmm()
            learner = BaumWelchScaledLearner()

            obs_set = self._sset_to_array_list(sset)

            try:
                hmm = learner.learn(hmm, obs_set)
                self._update_hmm(hmm)
            except java.lang.IllegalArgumentException:
                print "Couldn't train HMM"

        def _viterbi(self, seq, hmm):
            calc = ViterbiCalculator(self._vectors_to_observations(seq), hmm)
            return calc.stateSequence().tolist(), calc.lnProbability()

        def viterbi(self, obj):
            hmm = self._get_hmm()

            if isinstance(obj, SequenceSet):
                res = [self._viterbi(seq, hmm) for seq in obj]
                all_paths = [res[i][0] for i in range(len(res))]
                all_logp = [res[i][1] for i in range(len(res))]
                return all_paths, all_logp
            else:
                return self._viterbi(obj, hmm)
