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
import tomoe
import shutil
import ghmm
import math

class ModelBase(object):

    def __init__(self, verbose=False):
        self.DATA_ROOT = "data"
        self.EVAL_ROOT = os.path.join(self.DATA_ROOT, "eval")
        self.TRAIN_ROOT = os.path.join(self.DATA_ROOT, "train")
        self.DOMAIN = ghmm.Float()
        
        self.verbose = verbose
        self.eval_xml_files_dict = self.get_eval_xml_files_dict()
        self.train_xml_files_dict = self.get_train_xml_files_dict()
        

    def get_xml_list_dict(self, directory):
        """
        Returns a dictionary with xml file list.
            keys are character codes.
            values are arrays of xml files.
        """
        dict = {}
        for file in glob.glob(os.path.join(directory, "*", "*", "*.xml")):
            char_code = int(os.path.basename(file)[:-4])
            if not dict.has_key(char_code):
                dict[char_code] = []
            dict[char_code].append(file)
        return dict
                    
    def get_eval_xml_files_dict(self):
        return self.get_xml_list_dict(self.EVAL_ROOT)

    def get_train_xml_files_dict(self):
        return self.get_xml_list_dict(self.TRAIN_ROOT)

    def get_tomoe_char(self, char_path):
        f = open(char_path, "r")
        xml = f.read()
        f.close()
        return tomoe.tomoe_char_new_from_xml_data(xml, len(xml))

    def get_sequence_set(self, file_path):
        return ghmm.SequenceSet(self.DOMAIN, file_path)

    def get_utf8_from_char_code(self, char_code):
        return unichr(int(char_code)).encode("utf8")

    def fextract(self):
        raise NotImplementedError

    def init(self):
        raise NotImplementedError

    def train(self):
        raise NotImplementedError

    def evaluation(self):
        raise NotImplementedError

    def writing_pad(self):
        raise NotImplementedError

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

def euclidean_distance(v1, v2):
    assert(len(v1) == len(v2))

    return math.sqrt(sum([(v2[i] - v1[i]) ** 2 for i in range(len(v1))]))  

def stderr_print(*args):
    sys.stderr.write("".join([str(arg) for arg in args]) + "\n")

def tomoe_writing_to_xml(tomoe_writing):
    tomoe_char = tomoe.Char()
    tomoe_char.set_utf8("?")
    tomoe_char.set_writing(tomoe_writing)
    return tomoe_char.to_xml()

def xml_to_tomoe_writing(xml):
    tomoe_char = tomoe.tomoe_char_new_from_xml_data(xml, len(xml))
    return tomoe_char.get_writing()