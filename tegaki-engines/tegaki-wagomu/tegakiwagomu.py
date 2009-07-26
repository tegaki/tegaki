# -*- coding: utf-8 -*-

# Copyright (C) 2009 The Tegaki project contributors
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
import struct
from array import array

from tegaki.recognizer import Recognizer, RecognizerError
from tegaki.trainer import Trainer, TrainerError
from tegaki.arrayutils import array_flatten
from tegaki.dictutils import SortedDict
from tegaki.mathutils import euclidean_distance

#######################
#       CONFIG        #
#######################

# the bigger the threshold, the fewer points the algorithm has to compare
# however, the fewer points, the more the character quality deteriorates
# The value is a distance in a 1000 * 1000 square
DOWNSAMPLE_THRESHOLD = 50

# Features used
FEATURE_EXTRACTION_FUNCTION = "get_delta_features"
FEATURE_VECTOR_DIMENSION = 2

#######################
#      END CONFIG     #
#######################

MAGIC_NUMBER = 0x7777 # All lucky 7s!

# Features

def get_xy_features(writing):
    """
    Returns (x,y) for each point.
    """
    return writing.get_strokes()

def get_delta_features(writing):   
    """
    Returns (delta x, delta y) for each point.
    """
    strokes = writing.get_strokes()
    vectors = [(x,y) for stroke in strokes for x,y in stroke]

    arr = []

    for i in range(1, len(vectors)):
        ((x1, y1), (x2, y2)) = (vectors[i-1], vectors[i])
        deltax = float(abs(x2 - x1))
        deltay = float(abs(y2 - y1))

        arr.append((deltax, deltay))

    return arr

FEATURE_EXTRACTION_FUNCTION = eval(FEATURE_EXTRACTION_FUNCTION)

# DTW

class DtwMatrix:
    # we use 1d-vector V instead of a n*m 2d-matrix M
    # M[i,j] can be accessed by V[k], k = j*n + i

    def __init__(self, n, m):
        self.a = array("f", [0.0] * (n*m))
        self.n = n
        self.m = m

    def __getitem__(self, p):
        return self.a[p[1] * self.n + p[0]]

    def __setitem__(self, p, value):
        self.a[p[1] * self.n + p[0]] = value

def dtw(s, t, d, f=euclidean_distance):
    """
    s; first sequence
    t: second sequence
    d: vector dimension
    f: distance function

    s and t are flat sequences of feature vectors of dimension d, so 
    their length should be multiple of d
    """    
    assert(len(s) % d == 0)
    assert(len(t) % d == 0)

    n = len(s) / d
    m = len(t) / d
   
    DTW = DtwMatrix(n, m)
   
    infinity = 4294967296 # 2^32
    
    for i in range(1, m):
        DTW[(0, i)] = infinity
        
    for i in range(1, n):
        DTW[(i, 0)] = infinity

    DTW[(0, 0)] = 0.0
       
    for i in range(1, n):
        # retrieve 1st d-dimension vector
        v1 = s[i*d:i*d+d]

        for j in range(1, m):
            # retrieve 2nd d-dimension vector
            v2 = t[j*d:j*d+d]
            # distance function
            cost = f(v1, v2)
            # DTW recursion step
            DTW[(i, j)] = cost + min(DTW[(i-1, j)],
                                     DTW[(i-1, j-1)],
                                     DTW[(i, j-1)])
       
    return DTW[(n-1, m-1)]

# Small utils

def get_features(writing):
    writing.normalize()
    writing.downsample_threshold(DOWNSAMPLE_THRESHOLD)
    flat = array_flatten(FEATURE_EXTRACTION_FUNCTION(writing))
    return [float(f) for f in flat]

def argmin(arr):
    return arr.index(min(arr))

def read_ushorts(f, n):
    return struct.unpack("@%dH" % n, f.read(n*2))

def read_ushort(f):
    return read_ushorts(f, 1)[0]

def write_ushorts(f, *args):
    f.write(struct.pack("@%dH" % len(args), *args))
write_ushort = write_ushorts

def read_ulongs(f, n):
    return struct.unpack("@%dL" % n, f.read(n*4))

def read_ulong(f):
    return read_ulongs(f, 1)[0]

def write_ulongs(f, *args):
    f.write(struct.pack("@%dL" % len(args), *args))
write_ulong = write_ulongs

def read_floats(f, n):
    return struct.unpack("@%df" % n, f.read(n*4))

def read_float(f):
    return read_floats(f, 1)[0]

def write_floats(f, *args):
    f.write(struct.pack("@%df" % len(args), *args))
write_float = write_floats    

# Recognizer

try:
    import wagomu

    # Extension-based version
    class WagomuRecognizer(Recognizer):

        RECOGNIZER_NAME = "wagomu"

        def __init__(self):
            Recognizer.__init__(self)
            self._recognizer = wagomu.Recognizer()

        def open(self, path):
            ret = self._recognizer.open(path)
            if not ret: raise RecognizerError, recognizer.get_error_message()

        def recognize(self, writing, n=10):
            feat = get_features(writing)
            nfeat = len(feat) 
            nvectors = nfeat / self._recognizer.get_dimension()
            floatarr = wagomu.FloatArray(nfeat)

            for i in range(nfeat):
                floatarr[i] = feat[i]

            res = self._recognizer.recognize(floatarr, nvectors, n)

            candidates = []
            for i in range(res.get_size()):
                candidates.append((res.get_utf8(i), res.get_distance(i)))

            return candidates

except ImportError:
    # Pure python version
    class WagomuRecognizer(Recognizer):

        RECOGNIZER_NAME = "wagomu"

        def __init__(self):
            Recognizer.__init__(self)
            self._reprdict = SortedDict()
            self._dimension = None

        def open(self, path):
            f = open(path, "rb")

            magic_number = read_ushort(f)
            if magic_number != MAGIC_NUMBER:
                raise RecognizerError, "Incorrect model"

            n_characters = read_ulong(f)
            self._dimension = read_ushort(f)

            for i in range(n_characters):
                strlen = read_ushort(f)
                utf8 = f.read(strlen)
                n_vectors = read_ushort(f)
                feat = read_floats(f, n_vectors*self._dimension)
                self._reprdict[utf8] = feat

            f.close()

        def recognize(self, writing, n=10):
            feat = get_features(writing)

            results = []
            for utf8, template in self._reprdict.items():
                results.append((utf8, dtw(feat, template, self._dimension)))
            results.sort(cmp=lambda x,y: cmp(x[1],y[1]))

            candidates = []
            already = []
            # we don't just return the first n results because
            # a character may have several template variants (allographes)
            for utf8, dist in results:
                utf8 = utf8[0:-1] # remove \0 at the end
                if not utf8 in already:
                    candidates.append((utf8, dist))
                    already.append(utf8)
                if len(candidates) >= n:
                    break
            
            return candidates

RECOGNIZER_CLASS = WagomuRecognizer

# Trainer

class WagomuTrainer(Trainer):

    TRAINER_NAME = "wagomu"

    def __init__(self):
        Trainer.__init__(self)

    def train(self, charcol, meta, path=None):
        self._check_meta(meta)

        if not path:
            if "path" in meta:
                path = meta["path"]
            else:
                path = os.path.join(os.environ['HOME'], ".tegaki", "models",
                                    "wagomu", meta["name"] + ".model")

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        meta_file = path.replace(".model", ".meta")
        if not meta_file.endswith(".meta"): meta_file += ".meta"
        
        self._save_model_from_charcol(charcol, path)
        self._write_meta_file(meta, meta_file)

    def _get_representative_features(self, writings):
        n_writings = len(writings)
        sum_ = [0] * n_writings
        features = [get_features(w) for w in writings]

        # dtw is a symmetric distance so d(i,j) = d(j,i)
        # we only need to compute the values on the right side of the
        # diagonale
        for i in range(n_writings):
            for j in range (i+1, n_writings):
                distance = dtw(features[i], features[j],
                                FEATURE_VECTOR_DIMENSION)
                sum_[i] += distance
                sum_[j] += distance
        
        i = argmin(sum_)

        return features[i]

    def _save_model_from_charcol(self, charcol, output_path):
        # contains the set representative for each set
        reprdict = SortedDict() 

        # each set may contain more than 1 sample per character
        # but we only need one ("the template") so we find the set
        # representative,  which we define as the sample which is, on
        # average, the closest to the other samples of that set
        i = 1
        set_list = charcol.get_set_list()
        for set_name in set_list:
            chars = charcol.get_characters(set_name)
            if len(chars) == 0: continue # empty set

            utf8 = chars[0].get_utf8()
            if utf8 is None: continue

            if len(chars) == 1 or len(chars) == 2:
                # take the first one if only 1 or 2 samples available
                feat = get_features(chars[0].get_writing())
            else:
                # we need to find the set representative
                writings = [c.get_writing() for c in chars]
                feat = self._get_representative_features(writings)

            reprdict[set_name] = (utf8, feat)
            print "%s (%d/%d)" % (utf8, i, len(set_list))
            i += 1

        # save model in binary format
        # this file is architecture dependent
        f = open(output_path, "wb")

        # magical number
        write_ushort(f, MAGIC_NUMBER)

        # number of characters/templates
        write_ulong(f, len(reprdict))

        # vector dimensionality
        write_ushort(f, FEATURE_VECTOR_DIMENSION)

        for utf8, feat in reprdict.values():
            # char utf8's value stored in pascal-string 
            # (string prefixed by its length)
            utf8 += "\0"
            write_ushort(f, len(utf8))
            f.write(utf8)

            # number of vectors
            write_ushort(f, len(feat) / FEATURE_VECTOR_DIMENSION)

            # flat list of vectors
            # e.g. [[x1, y1], [x2, y2]] is stored as [x1, y1, x2, y2]
            write_floats(f, *[v for v in feat])

        f.close()
            
TRAINER_CLASS = WagomuTrainer

