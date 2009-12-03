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

__doctest__ = True

def array_sample(arr, rate):
    """
    Sample array.

    @type  arr: list/tuple/array
    @param arr: the list/tuple/array to sample
    @type rate: float
    @param rate: the rate (between 0 and 1.0) at which to sample
    @rtype: list
    @return: the sampled list

    >>> array_sample([1,2,3,4,5,6], 0.5)
    [1, 3, 5]
    """
    n = int(round(1 / rate))
    
    return [arr[i] for i in range(0, len(arr), n)]

def array_flatten(l, ltypes=(list, tuple)):
    """
    Reduce array of possibly multiple dimensions to one dimension.

    @type  l: list/tuple/array
    @param l: the list/tuple/array to flatten
    @rtype: list
    @return: the flatten list

    >>> array_flatten([[1,2,3], [4,5], [[7,8]]])
    [1, 2, 3, 4, 5, 7, 8]
    """
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
    """
    Reshape one-dimensional array to a list of n-element lists.

    @type  arr: list/tuple/array
    @param arr: the array to reshape
    @type  n: int
    @param n: the number of elements in each list
    @rtype: list
    @return: the reshaped array

    >>> array_reshape([1,2,3,4,5,6,7,8,9], 3)
    [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    """
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
    """
    Split an array into p arrays of about the same size.

    @type  seq: list/tuple/array
    @param seq: the array to split
    @type  p: int
    @param p: the split size
    @rtype: list
    @return: the split array

    >>> array_split([1,2,3,4,5,6,7], 3)
    [[1, 2, 3], [4, 5], [6, 7]]
    """
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
    """
    Calculate the mean of the elements contained in an array.

    @type  arr: list/tuple/array
    @rtype: float
    @return: mean

    >>> array_mean([100, 150, 300])
    183.33333333333334
    """
    return float(sum(arr)) / float(len(arr))

def array_variance(arr, mean=None):
    """
    Calculate the variance of the elements contained in an array.

    @type  arr: list/tuple/array
    @rtype: float
    @return: variance

    >>> array_variance([100, 150, 300])
    7222.2222222222226
    """
    if mean is None:
        mean = array_mean(arr)
    var = array_mean([(val - mean) ** 2 for val in arr])
    if var == 0.0:
        return 1.0
    else:
        return var

def array_mean_vector(vectors):
    """
    Calculate the mean of the vectors, element-wise.

    @type arr: list of vectors
    @rtype: list of floats
    @return: list of means

    >>> array_mean_vector([[10,20], [100, 200]])
    [55.0, 110.0]
    """
    assert(len(vectors) > 0)

    n_dimensions = len(vectors[0])

    mean_vector = []

    for i in range(n_dimensions):
        arr = [vector[i] for vector in vectors]
        mean_vector.append(array_mean(arr))
        
    return mean_vector

def array_variance_vector(vectors, means=None):
    """
    Calculate the variance of the vectors, element-wise.

    @type  arr: list of vectors
    @rtype: list of floats
    @return: list of variances

    >>> array_variance_vector([[10,20], [100, 200]])
    [2025.0, 8100.0]
    """
    assert(len(vectors) > 0)
    
    n_dimensions = len(vectors[0])

    if means is not None:
        assert(n_dimensions == len(means))
    else:
        means = array_mean_vector(vectors)

    variance_vector = []

    for i in range(n_dimensions):
        arr = [vector[i] for vector in vectors]
        variance_vector.append(array_variance(arr, means[i]))
        
    return variance_vector

def array_covariance_matrix(vectors, non_diagonal=False):
    """
    Calculate the covariance matrix of vectors.

    @type vectors: list of arrays
    @type non_diagonal: boolean
    @param non_diagonal: whether to calculate non-diagonal elements of the \
                         matrix or not

    >>> array_covariance_matrix([[10,20], [100, 200]])
    [2025.0, 0.0, 0.0, 8100.0]

    >>> array_covariance_matrix([[10,20], [100, 200]], non_diagonal=True)
    [2025.0, 4050.0, 4050.0, 8100.0]
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
    Add two arrays element-wise.

    >>> array_add([1,2],[3,4])
    [4, 6]
    """
    assert(len(arr1) == len(arr1))

    newarr = []

    for i in range(len(arr1)):
        newarr.append(arr1[i] + arr2[i])

    return newarr

def array_mul(arr1, arr2):
    """
    Multiply two arrays element-wise.

    >>> array_mul([1,2],[3,4])
    [3, 8]
    """
    assert(len(arr1) == len(arr1))

    newarr = []

    for i in range(len(arr1)):
        newarr.append(arr1[i] * arr2[i])

    return newarr

if __name__ == '__main__':
    import doctest
    doctest.testmod()