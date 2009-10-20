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

try:
    import cPickle as pickle
except ImportError:
    import pickle

from random import random, randint, choice

from tegaki.character import *

def writing_to_xml(writing):
    character = Character()
    character.set_utf8("?")
    character.set_writing(writing)
    return character.to_xml()

def writing_to_json(writing):
    character = Character()
    character.set_utf8("?")
    character.set_writing(writing)
    return character.to_json() 

def xml_to_writing(xml):
    character = Character()
    character.read_string(xml)
    return character.get_writing()

def random_choose(objects):
    """
    Choose an object randomly in the list, remove it from the list 
    and return it.
    """
    if len(objects) == 1:
        i = 0
    else:
        i = randint(0, len(objects) - 1)
    obj = objects[i]
    del objects[i]
    return obj

def load_object(path):
    f = open(path)
    ret = pickle.load(f)
    f.close()
    return ret

def save_object(path, obj, del_first=False):
    if del_first and os.path.exists(path):
        os.unlink(path)

    f = open(path, "w")
    pickle.dump(obj, f)
    f.close()

def sort_files_by_numeric_id(files, reverse=False):
    """This only works with files having the form somenumber.ext"""
    def mycmp(a,b):
        a = os.path.basename(a)
        a = a[0:a.index(".")]
        b = os.path.basename(b)
        b = b[0:b.index(".")]
        return cmp(int(a), int(b))
    files.sort(mycmp, reverse=reverse)

def remove_duplicates(l):
    """
    Remove duplicates from a list and preserve order. 
    Elements from the list must be hashable.
    """
    d = {}
    ret = []
    for e in l:
        if not e in d:
            ret.append(e)
            d[e] = 1
    return ret
           
if __name__ == "__main__":
    assert(remove_duplicates(["b", "a", "b", 12, "z", 16, 12]) == \
           ["b", "a", 12, "z", 16])