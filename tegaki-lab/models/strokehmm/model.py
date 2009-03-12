# -*- coding: utf-8 -*-

# Copyright (C) 2009 Mathieu Blondel
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
import shutil
import pickle
from math import ceil
import gc

import numpy
import hcluster

from tegaki.arrayutils import *
from tegaki.mathutils import *

from models.basic.model import Model as BaseModel

from lib.dtw import dtw

class Model(BaseModel):
    """
    Title: strokehmm
    """

    def __init__(self, *args):
        BaseModel.__init__(self, *args)

        self.ALL = ["clean", "dtw", "cluster", "init", "sdict"]
        self.COMMANDS = self.ALL + ["pad", "find", "commands"]

        self.CLUSTER_MATRIX_SIZE = 1000 
        self.N_CLUSTERS = 50

        # one of 'single', 'complete', 'average', 'weighted'
        self.CLUSTERING_METHOD = "complete"

        self.STATE_MULTIPLIER = 5

        self.TRAIN_CORPORA = ["tomoe-ja-kanji"]
        self.EVAL_CORPORA = ["japanese-learner1", "japanese-native1"]
        self.ROOT = os.path.join("models", "strokehmm")
        self.update_folder_paths()

    ########################################
    # General utils...
    ########################################

    def update_folder_paths(self):
        BaseModel.update_folder_paths(self)
        self.DTW_ROOT = os.path.join(self.ROOT, "dtw")
        self.DTW_DATA = os.path.join(self.DTW_ROOT, "dtw.npy")
        self.CLUSTER_ROOT = os.path.join(self.ROOT, "cluster")
        self.CLUSTER_DATA = os.path.join(self.CLUSTER_ROOT, "cluster.pickle")
        self.DICT_ROOT = os.path.join(self.ROOT, "dict")
        self.DICT_DATA = os.path.join(self.DICT_ROOT, "cluster.pickle")

    ########################################
    # DTW...
    ########################################

    def get_first_n_strokes(self, n):
        """
        Returns a list of the first n Stroke objects.
        """
        strokes = []
        for char_code, xml_files in self.train_xml_files_dict.items():
            for xml_file in xml_files:
                character = self.get_character(xml_file)
                writing = character.get_writing()

                for stroke in writing.get_strokes(full=True):
                    strokes.append(stroke)
                    
                    if len(strokes) >= n:
                        return strokes
        return strokes

    def dtw(self):
        """Run Dynamic Time Warping on strokes"""

        # the purpose of this step is to build a distance matrix
        # between CLUSTER_MATRIX_SIZE stroke pairs using the DTW algorithm

        strokes = self.get_first_n_strokes(self.CLUSTER_MATRIX_SIZE)
        matrix_size = len(strokes)
        matrix = numpy.zeros((matrix_size, matrix_size))
        
        for i in range(matrix_size):
            for j in range(i, matrix_size):
                if i == j:
                    matrix[i, j] = 0.0
                else:
                    # dtw is performed on the x,y coordinates instead of
                    # the feature vectors, for now
                    matrix[i,j] = dtw(strokes[i].get_coordinates(), 
                                      strokes[j].get_coordinates(),
                                      euclidean_distance)

                    # The matrix is symmetrical
                    matrix[j,i] = matrix[i,j]

        if not os.path.exists(self.DTW_ROOT):
            os.makedirs(self.DTW_ROOT)

        numpy.save(self.DTW_DATA, matrix)

    ########################################
    # Cluster...
    ########################################

    def get_cluster_dict_from_array(self, arr):
        d = {}
        for stroke_id in range(len(arr)):
            cluster_id = arr[stroke_id] - 1 # first is 1
            if not d.has_key(cluster_id):
                d[cluster_id] = []
            d[cluster_id].append(stroke_id)
        return d

    def print_clusters(self, clusters):
        cluster_ids = clusters.keys()
        cluster_ids.sort()
        print "cluster\tstrokes"
        for cluster_id in cluster_ids:
            print "%d\t%s" % (cluster_id, 
                            ", ".join([str(i) for i in clusters[cluster_id]]))

    def cluster(self):
        """Cluster strokes"""

        # the purpose of this step is to cluster strokes using
        # the previously calculated distance matrix

        matrix = numpy.load(self.DTW_DATA)
        Y = hcluster.squareform(matrix)
        Z = hcluster.linkage(Y, method=self.CLUSTERING_METHOD)
        T = hcluster.fcluster(Z, 1.15)
        clusters = self.get_cluster_dict_from_array(T)

        if self.verbose:
            self.print_clusters(clusters)

        if not os.path.exists(self.CLUSTER_ROOT):
            os.makedirs(self.CLUSTER_ROOT)

        pickle.dump(clusters, open(self.CLUSTER_DATA, "w"))

    ########################################
    # Feature extraction...
    ########################################

    def get_stroke_feature_vectors(self, stroke, upsample=False):
        # Characters templates from Tomoe use straight lines and
        # thus have much fewer points than real handwriting.
        # The handwriting data in data/ was used to compute the average
        # distance between consecutive samples, which was found to be around 8
        # units in a 1000*1000 drawing area.
        if upsample:
            stroke.upsample_threshold(8) 
           
        coordinates = [(p.x,p.y) for p in stroke]
        coordinates = array_sample(coordinates, self.SAMPLING)

        vectors = numpy.zeros((len(coordinates) - 1, self.N_DIMENSIONS))

        for i in range(1, len(coordinates)):
            ((x1, y1), (x2, y2)) = (coordinates[i-1], coordinates[i])
            deltax = float(abs(x2 - x1))
            deltay = float(abs(y2 - y1))

            vectors[i-1] = [deltax, deltay]

        return vectors

    ########################################
    # Initialization...
    ########################################

    def get_initial_state_alignment(self, n_states, feature_vector_set):
        all_segments = [[] for i in range(n_states)]

        for seq in feature_vector_set:
            # Segments vectors uniformly. One segment per state.
            segments = array_split(list(seq), n_states)

            # Concatenate each segments[i] with the segments[i] obtained
            # at the previous iteration
            all_segments = array_add(all_segments, segments)

        return all_segments

    def get_emission_matrix(self, n_states, feature_vector_set):
        all_segments = self.get_initial_state_alignment(n_states, 
                                                        feature_vector_set)

        matrix = []

        for i in range(n_states):
            matrix.append([
            
                # the means of our multivariate gaussian
                array_mean_vector(all_segments[i]),
                
                # the covariance matrix of our multivariate gaussian
                array_covariance_matrix(all_segments[i],
                                        non_diagonal=self.NON_DIAGONAL)
                
            ])

        return matrix

    def get_initial_hmm(self, n_states, feature_vector_set):
        """
        Prepare an initial HMM. 1 HMM = 1 Cluster

        n_states: number of states for that particular HMM/Cluster
        feature_vector_set : an array of feature vectors for the strokes that
                             belong to that particular Cluster
        """
        pi = self.get_initial_state_probabilities(n_states)
        A = self.get_state_transition_matrix(n_states)
        B = self.get_emission_matrix(n_states, feature_vector_set)

        hmm = ghmm.HMMFromMatrices(
                    self.DOMAIN,
                    ghmm.MultivariateGaussianDistribution(self.DOMAIN),
                    A,
                    B,
                    pi)
        
        return hmm

    def get_fv_cumulated_distance(self, s):
        """
        Returns the cumulated distance of the stroke feature vectors.
        """
        return sum([euclidean_distance(s[i], s[i+1]) for i in \
                    range(len(s) -1)])

    def get_cluster_state_table(self, feature_vectors):
        """
        Estimate the number of states needed for each HMM.
        1 HMM = 1 Cluster

        The output of this method can be tweaked by modifying
        self.STATE_MULTIPLIER.

        Returns a dict: keys are cluster ids, values are state numbers
        """
        tbl = {}

        for cluster_id, fv_set in feature_vectors.items():
            tbl[cluster_id] = 0
            for fv in fv_set:
                tbl[cluster_id] += self.get_fv_cumulated_distance(fv)
            tbl[cluster_id] /= float(len(feature_vectors[cluster_id]))
        
        total = sum(tbl.values())
        avg = total / len(tbl)

        for cluster_id in tbl.keys():
            tbl[cluster_id] = int(ceil(float(tbl[cluster_id]) / avg * \
                                          self.STATE_MULTIPLIER))

        return tbl
    
    def get_clusters_feature_vector_sets(self, clusters):
        """
        Returns a dict: keys are cluster ids
                        values are sets of feature vectors
        """
        fv = {}
        s = self.get_first_n_strokes(self.CLUSTER_MATRIX_SIZE)
        for cid, stroke_ids in clusters.items():
            fv[cid] = [self.get_stroke_feature_vectors(s[i], upsample=True) \
                       for i in stroke_ids]
        return fv

    def train_hmm(self, hmm, feature_vector_set):
        sset = []
        for fv in feature_vector_set:
            # ghmm.SequenceSet expects flat arrays
            # e.g. [[x1,y1],[x2,y2]...] must be [x1,y1,x2,y2,...]
            sset.append(list(fv.flatten()))
        sset = ghmm.SequenceSet(self.DOMAIN, sset)
        hmm.baumWelch(sset)

    def init(self):
        """Init HMMs"""
        
        if not os.path.exists(self.INIT_HMM_ROOT):
            os.makedirs(self.INIT_HMM_ROOT)

        clusters = pickle.load(open(self.CLUSTER_DATA))
        feature_vectors = self.get_clusters_feature_vector_sets(clusters)
                
        state_tbl = self.get_cluster_state_table(feature_vectors)
        self.print_verbose("clusterid : state number")
        self.print_verbose(state_tbl)

        for cluster_id in clusters.keys():
            n_states = state_tbl[cluster_id]
            # Initialize the HMM with values calculated from
            # the features vectors
            hmm = self.get_initial_hmm(n_states, feature_vectors[cluster_id])
        
            # Train the initialized HMM with the same feature vectors
            self.train_hmm(hmm, feature_vectors[cluster_id])

            output_file = os.path.join(self.INIT_HMM_ROOT,
                                       "%d.xml" % cluster_id)

            self.print_verbose(output_file)

            if os.path.exists(output_file):
                os.unlink(output_file)

            hmm.write(output_file)

    ########################################
    # Stroke dictionary...
    ########################################

    def eval_sequence(self, seq, hmms):
        res = []
        
        for i in range(len(hmms)):
            logp = hmms[i].viterbi(seq)[1]
            res.append([i, logp])

        if seq.__class__.__name__ == ghmm.SequenceSet:
            res.sort(key=lambda x:array_mean(x[1]), reverse=True)
        else:
            res.sort(key=lambda x:x[1], reverse=True)

        return res

    def get_cluster_for_stroke(self, hmms, stroke):
        """
        Determine which cluster/HMM this stroke belongs to.
        """
        features = self.get_stroke_feature_vectors(stroke, upsample=True)
        
        seq = ghmm.EmissionSequence(self.DOMAIN,
                                    list(features.flatten()))

        # eval_sequence returns a list [cluster_id, logp] 
        # ordered by logp, and we want the most probable cluster_id
        return self.eval_sequence(seq, hmms)[0][0]
        
    def sdict(self):
        """Build stroke dictionary"""

        # the purpose of this step is to determine what strokes the 
        # characters are composed of
        files = self.get_initial_hmm_files()
        hmms = self.get_hmms_from_files(files)
        dic = {}

        i = 0
        for char_code, xml_files in self.train_xml_files_dict.items():
            # we use only the first file and we assume the stroke
            # order is correct
            xml_file = xml_files[0]

            character = self.get_character(xml_file)
            writing = character.get_writing()

            dic[char_code] = []

            for stroke in writing.get_strokes(full=True):
                dic[char_code].append(self.get_cluster_for_stroke(hmms, stroke))

            self.print_verbose("%d: %s" % (char_code, dic[char_code]))
            
            if i % 100 == 0:
                gc.collect()

            i += 1

        if not os.path.exists(self.DICT_ROOT):
            os.makedirs(self.DICT_ROOT)

        pickle.dump(dic, open(self.DICT_DATA, "w"))

    ########################################
    # Clean...
    ########################################

    def clean(self):
        BaseModel.clean(self)

        for path in (self.DTW_ROOT, self.CLUSTER_ROOT, self.DICT_ROOT):
            if os.path.exists(path):
                shutil.rmtree(path)
