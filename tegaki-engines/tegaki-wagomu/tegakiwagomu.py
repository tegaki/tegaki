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

VERSION = '0.3.1'

import os
import struct
from array import array

from tegaki.recognizer import Results, Recognizer, RecognizerError
from tegaki.trainer import Trainer, TrainerError
from tegaki.arrayutils import array_flatten
from tegaki.dictutils import SortedDict
from tegaki.mathutils import euclidean_distance

VECTOR_DIMENSION_MAX = 4
INT_SIZE = 4
FLOAT_SIZE = 4
MAGIC_NUMBER = 0x77778888

# Features

FEATURE_EXTRACTION_FUNCTIONS = ["get_xy_features", "get_delta_features"]

def get_xy_features(writing):
    """
    Returns (x,y) for each point.
    """
    return [(x, y, 0.0, 0.0) for s in writing.get_strokes() for x,y in s]

get_xy_features.DIMENSION = 2

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

        # we add two floats to make it 16 bytes
        arr.append((deltax, deltay, 0.0, 0.0))

    return arr

get_delta_features.DIMENSION = 2

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

def argmin(arr):
    return arr.index(min(arr))

# File utils

def read_uints(f, n):
    return struct.unpack("@%dI" % n, f.read(n*4))

def read_uint(f):
    return read_uints(f, 1)[0]

def write_uints(f, *args):
    f.write(struct.pack("@%dI" % len(args), *args))
write_uint = write_uints

def read_floats(f, n):
    return struct.unpack("@%df" % n, f.read(n*4))

def read_float(f):
    return read_floats(f, 1)[0]

def write_floats(f, *args):
    f.write(struct.pack("@%df" % len(args), *args))
write_float = write_floats    

def get_padded_offset(offset, align):
    padding = (align - (offset % align)) % align
    return offset + ((align - (offset % align)) % align)

class _WagomuBase(object):

    def __init__(self):
        # The bigger the threshold, the fewer points the algorithm has to
        # compare. However, the fewer points, the more the character
        # quality deteriorates. 
        # The value is a distance in a 1000 * 1000 square
        self._downsample_threshold = 50

        self._feature_extraction_function = eval("get_delta_features")
        self._vector_dimension = self._feature_extraction_function.DIMENSION

        if isinstance(self, Recognizer):
            self._error = RecognizerError
        else:
            self._error = TrainerError

    def get_features(self, writing):
        writing.normalize()
        writing.downsample_threshold(self._downsample_threshold)
        flat = array_flatten(self._feature_extraction_function(writing))
        return [float(f) for f in flat]

    def set_options(self, opt):
        if "downsample_threshold" in opt:
            try:
                self._downsample_threshold = int(opt["downsample_threshold"])
            except ValueError:
                raise self._error, "downsample_threshold must be an integer"

        if "feature_extraction_function" in opt:
            if not opt["feature_extraction_function"] in \
                FEATURE_EXTRACTION_FUNCTIONS:
                raise self._error, "The feature function does not exist"
            else:
                self._feature_extraction_function = \
                    eval(opt["feature_extraction_function"])
                self._vector_dimension = \
                    self._feature_extraction_function.DIMENSION

        if "window_size" in opt:
            try:
                ws = int(opt["window_size"])
                if ws < 0: raise ValueError
                if isinstance(self, Recognizer):
                    self._recognizer.set_window_size(ws)
            except ValueError:
                raise self._error, "window_size must be a positive integer"    
       

# Recognizer

try:
    import wagomu

    class WagomuRecognizer(_WagomuBase, Recognizer):

        RECOGNIZER_NAME = "wagomu"

        def __init__(self):
            Recognizer.__init__(self)
            _WagomuBase.__init__(self)

            self._recognizer = wagomu.Recognizer()

        def open(self, path):
            ret = self._recognizer.open(path)
            if not ret: 
                raise RecognizerError, self._recognizer.get_error_message()

        def _recognize(self, writing, n=10):
            n_strokes = writing.get_n_strokes()
            feat = self.get_features(writing)
            nfeat = len(feat) 
            nvectors = nfeat / VECTOR_DIMENSION_MAX

            ch = wagomu.Character(nvectors, n_strokes)
            for i in range(nfeat):
                ch.set_value(i, feat[i])

            res = self._recognizer.recognize(ch, n)

            candidates = []
            for i in range(res.get_size()):
                utf8 = unichr(res.get_unicode(i)).encode("utf8")
                candidates.append((utf8, res.get_distance(i)))

            return Results(candidates)

    RECOGNIZER_CLASS = WagomuRecognizer

except ImportError:
    pass # no recognizer available here


# Trainer

class WagomuTrainer(_WagomuBase, Trainer):

    TRAINER_NAME = "wagomu"

    def __init__(self):
        Trainer.__init__(self)
        _WagomuBase.__init__(self)

    def train(self, charcol, meta, path=None):
        self._check_meta(meta)

        if not path:
            if "path" in meta:
                path = meta["path"]
            else:
                path = os.path.join(os.environ['HOME'], ".tegaki", "models",
                                    "wagomu", meta["name"] + ".model")
        else:
            path = os.path.abspath(path)

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        meta_file = path.replace(".model", ".meta")
        if not meta_file.endswith(".meta"): meta_file += ".meta"
        
        self.set_options(meta)
        self._save_model_from_charcol(charcol, path)
        self._write_meta_file(meta, meta_file)

    def _get_representative_writing(self, writings):
        n_writings = len(writings)
        sum_ = [0] * n_writings
        features = [self.get_features(w) for w in writings]

        # dtw is a symmetric distance so d(i,j) = d(j,i)
        # we only need to compute the values on the right side of the
        # diagonale
        for i in range(n_writings):
            for j in range (i+1, n_writings):
                distance = dtw(features[i], features[j],
                                self._vector_dimension)
                sum_[i] += distance
                sum_[j] += distance
        
        i = argmin(sum_)

        return writings[i]

    def _save_model_from_charcol(self, charcol, output_path):
        chargroups = {} 

        n_chars = 0

        # get non-empty set list
        set_list = []
        for set_name in charcol.get_set_list():
            chars = charcol.get_characters(set_name)
            if len(chars) == 0: continue # empty set

            utf8 = chars[0].get_utf8()
            if utf8 is None: continue

            set_list.append(set_name)

        # each set may contain more than 1 sample per character
        # but we only need one ("the template") so we find the set
        # representative,  which we define as the sample which is, on
        # average, the closest to the other samples of that set
        for set_name in set_list:
            chars = charcol.get_characters(set_name)
            if len(chars) == 0: continue # empty set

            utf8 = chars[0].get_utf8()
            if utf8 is None: continue

            if len(chars) == 1 or len(chars) == 2:
                # take the first one if only 1 or 2 samples available
                writing = chars[0].get_writing()
            else:
                # we need to find the set representative
                writings = [c.get_writing() for c in chars]
                writing = self._get_representative_writing(writings)

            # artificially increase the number of points
            # this is useful when training data is made of straight lines
            # and thus has very few points
            writing.upsample_threshold(10)

            feat = self.get_features(writing)
            n_strokes = writing.get_n_strokes()

            if not n_strokes in chargroups: chargroups[n_strokes] = []
            chargroups[n_strokes].append((utf8, feat))

            print "%s (%d/%d)" % (utf8, n_chars+1, len(set_list))
            n_chars += 1

        stroke_counts = chargroups.keys()
        stroke_counts.sort()

        # Sort templates in stroke groups by length
        for sc in stroke_counts:
            chargroups[sc].sort(lambda x,y: cmp(len(x[1]),len(y[1])))

        # save model in binary format
        # this file is architecture dependent
        f = open(output_path, "wb")

        # magical number
        write_uint(f, MAGIC_NUMBER)

        # number of characters/templates
        write_uint(f, n_chars)

        # number of character groups
        write_uint(f, len(chargroups))

        # vector dimensionality
        write_uint(f, self._vector_dimension)

        # downsample threshold
        write_uint(f, self._downsample_threshold)

        strokedatasize = {}

        # character information
        for sc in stroke_counts:
            strokedatasize[sc] = 0

            for utf8, feat in chargroups[sc]:
                # unicode integer
                write_uint(f, ord(unicode(utf8, "utf-8")))
                
                # n_vectors
                write_uint(f, len(feat) / VECTOR_DIMENSION_MAX)

                strokedatasize[sc] += len(feat) * FLOAT_SIZE

        offset = 5 * INT_SIZE # header
        offset += n_chars * 2 * INT_SIZE # character information 
        offset += len(chargroups) * 4 * INT_SIZE # character group
        poffset = get_padded_offset(offset, VECTOR_DIMENSION_MAX * FLOAT_SIZE)
        pad = poffset - offset

        # character group information
        for sc in stroke_counts:
            # number of strokes
            write_uint(f, sc)
    
            # number of characters
            write_uint(f, len(chargroups[sc]))

            # offset from the start of the file
            write_uint(f, poffset)

            # padding
            f.write("".join(["\0"] * 4))

            poffset += strokedatasize[sc] 

        # padding
        if pad > 0:
            f.write("".join(["\0"] * pad))

        assert(f.tell() % (VECTOR_DIMENSION_MAX * FLOAT_SIZE) == 0)

        # stroke data
        for sc in stroke_counts:
            for utf8, feat in chargroups[sc]:
                assert(f.tell() % (VECTOR_DIMENSION_MAX * FLOAT_SIZE) == 0)

                # stroke data as flat list of vectors
                # e.g. [[x1, y1], [x2, y2]] is stored as [x1, y1, x2, y2]
                write_floats(f, *feat)

        f.close()
            
TRAINER_CLASS = WagomuTrainer

