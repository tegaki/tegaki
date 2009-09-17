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
import sys
import glob
import shutil
import tarfile
import datetime
import platform

from tegaki.character import *
from tegaki.arrayutils import *
from tegaki.mathutils import *
from tegaki.dictutils import SortedDict

from lib.exceptions import *
from lib.utils import *
from lib.hmm import Sequence, SequenceSet, MultivariateHmm
from lib import hmm

class Model(object):
    """
    Title: basic
    HMM: whole character
    Feature vectors: (dx, dy)
    Number of states: 3 per stroke
    Initialization: vectors distributed equally among states
    State transitions: 0.5 itself, 0.5 next state
    """

    def __init__(self, options):

        if platform.system() == "Java": # Jython 2.5
            self.Trainer = hmm.JahmmBaumWelchTrainer
            self.ViterbiCalculator = hmm.JahmmViterbiCalculator
        else:
            self.Trainer = hmm.GhmmBaumWelchTrainer
            self.ViterbiCalculator = hmm.GhmmViterbiCalculator

        self.ALL = ["clean", "fextract", "init", "train", "eval"]
        self.COMMANDS = self.ALL + ["pad", "find", "commands", "archive"]
    
        self.verbose = options.verbose
        self.options = options

        self.SAMPLING = 0.5
        self.N_STATES_PER_STROKE = 3
        self.N_DIMENSIONS = 2
        # whether to calculate non-diagonal values in the covariance matrix
        # or not
        self.NON_DIAGONAL = False

        self.TRAIN_CORPORA = ["japanese-learner1", "japanese-native1"]
        self.EVAL_CORPORA = ["japanese-learner1", "japanese-native1"]
        self.ROOT = os.path.join("models", "basic")
        self.update_folder_paths()

    ########################################
    # General utils...
    ########################################

    def stderr_print(self, *args):
        sys.stderr.write("".join([str(arg) for arg in args]) + "\n")

    def update_folder_paths(self):
        self.DATA_ROOT = "data"
        self.EVAL_ROOT = os.path.join(self.DATA_ROOT, "eval")
        self.TRAIN_ROOT = os.path.join(self.DATA_ROOT, "train")
        
        self.FEATURES_ROOT = os.path.join(self.ROOT, "features")
        self.TRAIN_FEATURES_ROOT = os.path.join(self.FEATURES_ROOT, "train")
        self.EVAL_FEATURES_ROOT = os.path.join(self.FEATURES_ROOT, "eval")

        self.HMM_ROOT = os.path.join(self.ROOT, "hmms")
        self.INIT_HMM_ROOT = os.path.join(self.HMM_ROOT, "init")
        self.TRAIN_HMM_ROOT = os.path.join(self.HMM_ROOT, "train")

        self.eval_char_dict = None
        self.train_char_dict = None

    def load_char_dicts(self):
        if not self.eval_char_dict:
            self.eval_char_dict = self.get_eval_char_dict()
        if not self.train_char_dict:
            self.train_char_dict = self.get_train_char_dict()
        self.print_verbose("Data loading done")

    def get_char_dict(self, directory, corpora):
        """
        Returns a dictionary with xml file list.
            keys are character codes.
            values are arrays of xml files.

        directory: root directory
        corpora: corpora list to restrict to
        """
        charcol = CharacterCollection()
        for file in glob.glob(os.path.join(directory, "*", "*")):
            corpus_name = file.split("/")[-2]
            # exclude data which are not in the wanted corpora
            if corpus_name not in corpora:
                continue

            if os.path.isdir(file):
                self.print_verbose("Loading dir %s" % file)
                charcol += CharacterCollection.from_character_directory(file)
            elif ".charcol" in file:
                self.print_verbose("Loading charcol %s" % file)
                gzip = False; bz2 = False
                if file.endswith(".gz"): gzip = True
                if file.endswith(".bz2"): bz2 = True
                charcol2 = CharacterCollection()
                charcol2.read(file, gzip=gzip, bz2=bz2)
                charcol += charcol2

        self.print_verbose("Grouping characters together...")
        dic = SortedDict()
        for set_name in charcol.get_set_list():
            for char in charcol.get_characters(set_name):
                charcode = ord(char.get_unicode())
                if not charcode in dic: dic[charcode] = []
                dic[charcode].append(char)

        return dic
                    
    def get_eval_char_dict(self):
        return self.get_char_dict(self.EVAL_ROOT, self.EVAL_CORPORA)

    def get_train_char_dict(self):
        return self.get_char_dict(self.TRAIN_ROOT, self.TRAIN_CORPORA)

    def get_character(self, char_path):
        char = Character()
        if char_path.endswith(".gz"):
            char.read(char_path, gzip=True)
        else:
             char.read(char_path)
        return char

    def get_sequence_set(self, file_path):
        return SequenceSet.from_file(file_path)

    def get_utf8_from_char_code(self, char_code):
        return unichr(int(char_code)).encode("utf8")

    def print_verbose(self, *args):
        if self.verbose:
            self.stderr_print(*args)

    ########################################
    # Feature extraction...
    ########################################

    def get_feature_vectors(self, writing, normalize=True):
        """
        Get deltax and deltay as feature vectors.
        """
        if normalize:
            writing.downsample_threshold(50)
            writing.normalize()
            
        strokes = writing.get_strokes()
        vectors = [(x,y) for stroke in strokes for x,y in stroke]
        #vectors = array_sample(vectors, self.SAMPLING)

        arr = []

        for i in range(1, len(vectors)):
            ((x1, y1), (x2, y2)) = (vectors[i-1], vectors[i])
            deltax = float(abs(x2 - x1))
            deltay = float(abs(y2 - y1))

            arr.append((deltax, deltay))

        return arr

    def fextract(self):
        """Extract features"""

        self.load_char_dicts()

        for dirname, char_dict in (("eval", self.eval_char_dict),
                                   ("train", self.train_char_dict)):
            
            for char_code, char_list in char_dict.items():
                output_dir = os.path.join(self.FEATURES_ROOT, dirname)

                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                sequence_set = []

                for character in char_list:

                    writing = character.get_writing()

                    char_features = self.get_feature_vectors(writing)

                    sequence_set.append(char_features)

                output_file = os.path.join(output_dir,
                                           str(char_code) + ".sset")

                self.print_verbose(output_file + " (%d chars)" % \
                                       len(sequence_set))

                sset = SequenceSet(sequence_set)
                sset.write(output_file)

    ########################################
    # Initialization...
    ########################################

    def get_train_feature_files(self):
        return glob.glob(os.path.join(self.TRAIN_FEATURES_ROOT, "*.sset"))

    def get_n_strokes(self, char_code):
        character = self.train_char_dict[char_code][0]
        return character.get_writing().get_n_strokes()

    def get_initial_state_probabilities(self, n_states):
        pi = [0.0] * n_states
        pi[0] = 1.0
        return pi

    def get_state_transition_matrix(self, n_states):
        matrix = []
        
        for i in range(n_states):
            # set all transitions to 0
            state = [0.0] * n_states
            
            if i == n_states - 1:
                # when the last state is reached,
                # the probability to stay in the state is 1
                state[n_states - 1] = 1.0
            else:
                # else, as an initial value, we set the prob to stay in
                # the same state to 0.5 and to jump to the next state to 0.5
                # the values will be updated by the training
                state[i] = 0.5
                state[i + 1] = 0.5

            matrix.append(state)
       
        return matrix

    def get_initial_state_alignment(self, n_states, sset):
        all_segments = [[] for i in range(n_states)]

        for seq in sset:
            # Segments vectors uniformly. One segment per state.
            segments = array_split(seq, n_states)

            # Concatenate each segments[i] with the segments[i] obtained
            # at the previous iteration
            all_segments = array_add(all_segments, segments)

        return all_segments

    def get_emission_matrix(self, n_states, sset):
        all_segments = self.get_initial_state_alignment(n_states, sset)

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

    def get_initial_hmm(self, sset):
        n_states = self.get_n_strokes(sset.char_code) * \
                   self.N_STATES_PER_STROKE

        pi = self.get_initial_state_probabilities(n_states)
        A = self.get_state_transition_matrix(n_states)
        B = self.get_emission_matrix(n_states, sset)

        hmm = MultivariateHmm(A, B, pi)
        
        return hmm
          

    def init(self):
        """Init HMMs"""

        self.load_char_dicts()

        feature_files = self.get_train_feature_files()

        if len(feature_files) == 0:
            raise ModelException, "No feature files found."
        
        if not os.path.exists(self.INIT_HMM_ROOT):
            os.makedirs(self.INIT_HMM_ROOT)

        for sset_file in feature_files:
            char_code = int(os.path.basename(sset_file[:-5]))

            sset = self.get_sequence_set(sset_file)
            sset.char_code = char_code

            hmm = self.get_initial_hmm(sset)

            output_file = os.path.join(self.INIT_HMM_ROOT,
                                       "%d.xml" % char_code)

            self.print_verbose(output_file)

            hmm.write(output_file)

    ########################################
    # Training...
    ########################################
    
    def get_initial_hmm_files(self):
        return glob.glob(os.path.join(self.INIT_HMM_ROOT, "*.xml"))

    def train(self):
        """Train HMMs"""
        initial_hmm_files = self.get_initial_hmm_files()

        if len(initial_hmm_files) == 0:
            raise ModelException, "No initial HMM files found."
        
        if not os.path.exists(self.TRAIN_HMM_ROOT):
            os.makedirs(self.TRAIN_HMM_ROOT)

        trainer = self.Trainer()
        
        for file in initial_hmm_files:
            char_code = int(os.path.basename(file).split(".")[0])
            hmm = MultivariateHmm.from_file(file)
            sset_file = os.path.join(self.TRAIN_FEATURES_ROOT,
                                     str(char_code) + ".sset")

            sset = self.get_sequence_set(sset_file)

            trainer.train(hmm, sset)

            output_file = os.path.join(self.TRAIN_HMM_ROOT,
                                       "%d.xml" % char_code)

            self.print_verbose(output_file)

            hmm.write(output_file)

    ########################################
    # Evaluation...
    ########################################    

    def get_eval_feature_files(self):
        return glob.glob(os.path.join(self.EVAL_FEATURES_ROOT, "*.sset"))

    def get_trained_hmm_files(self):
        return glob.glob(os.path.join(self.TRAIN_HMM_ROOT, "*.xml"))

    def eval_sequence(self, seq, hmms):
        res = []
        
        calculator = self.ViterbiCalculator()

        for hmm in hmms:
            logp = calculator.viterbi(hmm, seq)[1]
            res.append([hmm.char_code, logp])

        if str(seq.__class__.__name__) == "SequenceSet":
            # logp contains an array of log probabilities
            res.sort(key=lambda x:array_mean(x[1]), reverse=True)
        else:
            # logp contains a scalar
            res.sort(key=lambda x:x[1], reverse=True)

        return res

    def get_hmms_from_files(self, files):
        hmms = []
        
        for file in files:
            char_code = int(os.path.basename(file).split(".")[0])
            hmm = MultivariateHmm.from_file(file)
            hmm.char_code = char_code     
            hmms.append(hmm)
            
        return hmms

    def eval(self):
        """Evaluate HMMs"""
        trained_hmm_files = self.get_trained_hmm_files()

        if len(trained_hmm_files) == 0:
            raise ModelException, "No trained HMM files found."

        hmms = self.get_hmms_from_files(trained_hmm_files)
        
        n_total = 0
        n_match1 = 0
        n_match5 = 0
        n_match10 = 0
        char_codes = {}

        s = ""
        
        for file in self.get_eval_feature_files():
            char_code = int(os.path.basename(file).split(".")[0])
            char_codes[char_code] = 1
            sset = self.get_sequence_set(file)

            for seq in sset:
                res = [x[0] for x in self.eval_sequence(seq, hmms)][:10]

                if char_code in res:
                    n_match10 += 1 

                if char_code in res[:5]:
                    n_match5 += 1

                    position = str(res.index(char_code) + 1)
                    matches = ", ".join([self.get_utf8_from_char_code(x) \
                                            for x in res[:5]])
                else:
                    position = "X"
                    matches = ""

                if char_code == res[0]:
                    n_match1 += 1

                utf8 = self.get_utf8_from_char_code(char_code)

                s += "%s\t%s\t%s\n" % (utf8, position, matches)

                n_total += 1

            self.print_verbose(file)

        n_classes = len(char_codes.keys())

        self.stderr_print("%d characters (%d samples)" % \
                           (n_classes, n_total))
        self.stderr_print("match1: ",
                          float(n_match1)/float(n_total) * 100,
                          "%")
        self.stderr_print("match5: ",
                          float(n_match5)/float(n_total) * 100,
                          "%")
        self.stderr_print("match10: ",
                          float(n_match10)/float(n_total) * 100,
                          "%")
        
        self.print_verbose(s)

    ########################################
    # Writing pad...
    ########################################

    def find_writing(self, writing):
        seq = Sequence(self.get_feature_vectors(writing))
        trained_hmm_files = self.get_trained_hmm_files()

        if len(trained_hmm_files) == 0:
            raise ModelException, "No trained HMM files found."
        
        hmms = self.get_hmms_from_files(trained_hmm_files)
        res = [x[0] for x in self.eval_sequence(seq, hmms)][:10]
        return [self.get_utf8_from_char_code(x) for x in res]
       

    def pad(self):
        """Find characters using a pad"""
        from lib.writing_pad import WritingPad
        
        trained_hmm_files = self.get_trained_hmm_files()

        if len(trained_hmm_files) == 0:
            raise ModelException, "No trained HMM files found."
        
        pad = WritingPad(self.find_writing)
        pad.run()

    def find(self):
        """Find a character in XML format"""
        if self.options.stdin:
            lines = []

            while True:
                line = sys.stdin.readline()
                lines.append(line)
                
                if line.strip() == "</character>":
                    xml = "\n".join(lines)
                    writing = xml_to_writing(xml)
                    print " ".join(self.find_writing(writing))
                    lines = []

                if len(line) == 0:
                    break

    ########################################
    # Clean...
    ########################################

    def get_pyc_files(self, folder):
        pyc_files = []
        
        for name in os.listdir(folder):
            full_path = os.path.join(folder, name)
            if os.path.isdir(full_path):
                pyc_files += self.get_pyc_files(full_path)
            elif full_path.endswith(".pyc"):
                pyc_files.append(full_path)
                
        return pyc_files

    def clean(self):
        """Delete temporary files"""
        for folder in (self.FEATURES_ROOT, self.HMM_ROOT):
            if os.path.exists(folder):
                shutil.rmtree(folder)

        for pyc_file in self.get_pyc_files(self.ROOT):
            os.unlink(pyc_file)

    ########################################
    # Commands...
    ########################################
    def commands(self):
        """Display command list"""
        for cmd in self.COMMANDS:
            meth = getattr(self, cmd)
            print "- %s (%s)" % (cmd, meth.__doc__)

    ########################################
    # Archive...
    ########################################

    def archive(self):
        """Make a copy of the model in a tar.gz file"""
        if not os.path.exists("archives"):
            os.mkdir("archives")

        filename = os.path.basename(self.ROOT) + "-" + \
                  str(datetime.datetime.now()).replace(" ", "@") + ".tar.gz"
        path = os.path.join("archives", filename)
        targz = tarfile.open(path, mode="w:gz")
        targz.add(self.ROOT)
        targz.close()