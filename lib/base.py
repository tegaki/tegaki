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
import sys
import glob
import shutil
import ghmm
import math

class ModelException(Exception):
    pass

def my_import(name):
    """
    Similar to __import__() except that x.y.z returns z instead of x.
    """
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def load_model_module(model):
    if os.path.isdir(model):
        model_init = os.path.join(model, "__init__.py")
      
        if os.path.exists(model_init):
            module = model.replace("/", ".")

            return my_import(module)

    return None

def load_model_modules(path="models"):
    dic = {}
  
    for name in os.listdir(path):
        model = os.path.join(path, name)

        module = load_model_module(model)

        if module:
            dic[name] = module
        
    return dic

def get_model_list(path="models"):
    return [name for name in os.listdir(path) \
            if os.path.isdir(os.path.join(path, name))]

def get_pyc_files(folder):
    pyc_files = []
    
    for name in os.listdir(folder):
        full_path = os.path.join(folder, name)
        if os.path.isdir(full_path):
            pyc_files += get_pyc_files(full_path)
        elif full_path.endswith(".pyc"):
            pyc_files.append(full_path)
            
    return pyc_files

def clean_model_folder(model_folder):
    feature_folder = os.path.join(model_folder, "features")
    hmm_folder = os.path.join(model_folder, "hmms")

    for folder in (feature_folder, hmm_folder, ):
        if os.path.exists(folder):
            shutil.rmtree(folder)

    for pyc_file in get_pyc_files(model_folder):
        os.unlink(pyc_file)

def array_sample(arr, rate):
    n = int(round(1 / rate))
    
    return [arr[i] for i in range(0, len(arr), n)]

def array_flatten(l, ltypes=(list, tuple)):
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                if not len(l):
                    break
            else:
                l[i:i+1] = list(l[i])
        i += 1
    return l

def array_reshape(arr, n):
    newarr = []
    subarr = []
    
    i = 0
    
    for ele in arr:
        subarr.append(ele)
        i += 1

        if i % n == 0 and i != 0:
            newarr.append(subarr)
            subarr = []
            
    return newarr

def array_split(seq, p):
    newseq = []
    n = len(seq) / p    # min items per subsequence
    r = len(seq) % p    # remaindered items
    b,e = 0, n + min(1, r)  # first split
    for i in range(p):
        newseq.append(seq[b:e])
        r = max(0, r-1)  # use up remainders
        b,e = e, e + n + min(1, r)  # min(1,r) is always 0 or 1

    return newseq

def array_mean(arr):
    return float(sum(arr)) / float(len(arr))

def array_variance(arr):
    mean = array_mean(arr)
    return array_mean([(val - mean) ** 2 for val in arr])

def array_mean_vector(vectors):
    """
    Calculate the means of vector components.
    This assumes that all vectors have the same number of dimensions.
    Ex: array_mean_vector([ [1,2], [3,4] ]) returns [2, 3]
    """
    assert(len(vectors) > 0)

    n_dimensions = len(vectors[0])

    mean_vector = []

    for i in range(n_dimensions):
        arr = [vector[i] for vector in vectors]
        mean_vector.append(array_mean(arr))
        
    return mean_vector

def array_variance_vector(vectors):
    """
    Calculate the variances of vector components.
    This assumes that all vectors have the same number of dimensions.
    """
    assert(len(vectors) > 0)

    n_dimensions = len(vectors[0])

    variance_vector = []

    for i in range(n_dimensions):
        arr = [vector[i] for vector in vectors]
        variance_vector.append(array_variance(arr))
        
    return variance_vector

def array_covariance_matrix(vectors, non_diagonal=False):
    """
    Calculate the covariance matrix for vectors.
    If non_diagonal is True, non-diagonal values are also calculated.
    """
    assert(len(vectors) > 0)

    n_dimensions = len(vectors[0])

    cov_matrix = []

    for i in range(n_dimensions):
        for j in range(n_dimensions):
            if i == j:
                # diagonal value: COV(X,X) = VAR(X)
                arr = [vector[i] for vector in vectors]
                cov_matrix.append(array_variance(arr))
            else:
                # non-diagonal value
                if non_diagonal:
                    # COV(X,Y) = E(XY) - E(X)E(Y)
                    arr_x = [vector[i] for vector in vectors]
                    arr_y = [vector[j] for vector in vectors]
                    arr_xy = array_mul(arr_x, arr_y)
                    
                    mean_xy = array_mean(arr_xy)
                    
                    mean_x = array_mean(arr_x)
                    mean_y = array_mean(arr_y)

                    cov_matrix.append(mean_xy - mean_x * mean_y)
                else:
                    # X and Y indep => COV(X,Y) = 0
                    cov_matrix.append(0.0)

    return cov_matrix

def array_add(arr1, arr2):
    """
    Add arr1 and arr2 element by element.
    Ex: array_add([1,2], [3,4)) returns [4, 6].
    """
    assert(len(arr1) == len(arr1))

    newarr = []

    for i in range(len(arr1)):
        newarr.append(arr1[i] + arr2[i])

    return newarr

def array_mul(arr1, arr2):
    """
    Multiply arr1 and arr2 element by element.
    Ex: array_mul([1,2], [3,4)) returns [3, 8].
    """
    assert(len(arr1) == len(arr1))

    newarr = []

    for i in range(len(arr1)):
        newarr.append(arr1[i] * arr2[i])

    return newarr
    
def euclidean_distance(v1, v2):
    assert(len(v1) == len(v2))

    return math.sqrt(sum([(v2[i] - v1[i]) ** 2 for i in range(len(v1))]))
  
def cartesian_to_polar(x, y):
    """
    Cartesian to polar coordinates conversion.
    r is the distance to the point.
    teta is the angle to the point between 0 and 2 pi.
    """
    r = math.hypot(x, y)
    teta = math.atan2(y, x) + math.pi
    return (r, teta)

def stderr_print(*args):
    sys.stderr.write("".join([str(arg) for arg in args]) + "\n")
