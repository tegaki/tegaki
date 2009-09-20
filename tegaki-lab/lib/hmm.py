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
from math import sqrt, log
try:
    import cPickle as pickle
except ImportError:
    import pickle
from tegaki.arrayutils import *

def assert_almost_equals(a, b, eps=0.001):
    assert(abs(a-b) < eps)

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

    def get_n_states(self):
        return len(self.pi)

class ViterbiTrainer(object):
    """
    Supports left-right HMMs only for now.
    """

    def __init__(self, calculator, n_iterations=5, eps=0.0001,
                       non_diagonal=False):
        self._calculator = calculator
        self._n_iterations = n_iterations
        self._eps = abs(log(eps))
        self._non_diagonal = non_diagonal

    def train(self, hmm, sset):
        last_logp_avg = None

        for it in range(self._n_iterations):
            
            # contains vectors assigned to states
            containers = []
            for i in range(hmm.get_n_states()):
                containers.append([])

            # contains first state counts
            init = [0] * hmm.get_n_states()

            # contains outgoing transition counts
            out_trans = [0] * hmm.get_n_states()

            # contains transition counts
            trans_mat = []
            for i in range(hmm.get_n_states()):
                trans_mat.append([0] * hmm.get_n_states())

            logp_avg = 0

            for seq in sset:
                states, logp = self._calculator.viterbi(hmm, seq)
                logp_avg += logp
                assert(len(states) == len(seq))

                init[states[0]] += 1

                for i, state in enumerate(states):
                    containers[state].append(seq[i])
                    out_trans[state] += 1
                    
                    if i != len(states) - 1:
                        next_state = states[i+1]
                        trans_mat[state][next_state] += 1

            logp_avg /= float(len(sset))

            if last_logp_avg is not None:
                diff = abs(logp_avg - last_logp_avg)
                if  diff < self._eps:
                    #print "Viterbi training stopped on iteration %d" % it
                    break

            last_logp_avg = logp_avg

           # estimate observertion distribution
            opdfs = []
            for container in containers:
                if container == []:
                    # no vectors assigned to that state
                    # this means that the new HMM will have potentially
                    # fewer states
                    break

                means = array_mean_vector(container)
                covmatrix = array_covariance_matrix(container,
                                                    self._non_diagonal)
                opdfs.append([means, covmatrix])

            n_states = len(opdfs)

            # estimate initial state probabilities
            pi = [float(v) / len(sset) for v in init[0:n_states]]
            assert_almost_equals(sum(pi), 1.0)

            trans_mat = trans_mat[0:n_states]

            # estimate state transition probabilities
            for i in range(n_states): 
                for j in range(n_states):
                    if out_trans[i] > 0:
                        trans_mat[i][j] /= float(out_trans[i])

                trans_mat[i] = trans_mat[i][0:n_states]
                sum_= sum(trans_mat[i])

                if sum_ == 0:
                    trans_mat[i][-1] = 1.0
                else:
                    # normalize so that the sum of probabilities 
                    # always equals 1.0
                    for j in range(n_states):
                        trans_mat[i][j] /= sum_
               
                assert_almost_equals(sum(trans_mat[i]), 1.0)

            hmm.pi = pi
            hmm.A = trans_mat
            hmm.B = opdfs

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
                obj = [array_flatten(s[:]) for s in obj]
                obj = ghmm.SequenceSet(DOMAIN, obj)
                res = hmm_.viterbi(obj)
                # ghmm returns a scalar even though a sequence set was passed
                # if length == 1 but we want an array
                if len(obj) == 1:
                    res = [[res[0]], [res[1]]]
            else:
                obj = ghmm.EmissionSequence(DOMAIN, array_flatten(obj[:]))
                res = hmm_.viterbi(obj)
    
            return res

except ImportError:
    pass

try:
    from hydroml.hmm import Hmm
    from hydroml.distribution import MultivariateGaussianDistribution

    class _HydromlBase(object):

        def _get_hmm(self, hmm):
            opdfs = []
            for means, covmatrix in hmm.B:
                covmatrix = array_split(covmatrix, int(sqrt(len(covmatrix))))
                opdfs.append(MultivariateGaussianDistribution(means, covmatrix))

            return Hmm(hmm.pi, hmm.A, opdfs)

    class HydromlViterbiCalculator(_HydromlBase):

        def viterbi(self, hmm, obj):
            hmm_ = self._get_hmm(hmm)

            if isinstance(obj, SequenceSet):
                res = [hmm_.viterbi(seq) for seq in obj]
                all_paths = [res[i][0] for i in range(len(res))]
                all_logp = [res[i][1] for i in range(len(res))]
                return all_paths, all_logp
            else:
                return hmm_.viterbi(obj)

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
