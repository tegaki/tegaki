#!/usr/bin/env python
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

from tegaki.charcol import CharacterCollection

from tegakitools.tomoe import tomoe_dict_to_character_collection
from tegakitools.kuchibue import kuchibue_to_character_collection
from tegakitools.kanjivg import kanjivg_to_character_collection

TYPE_CHARCOL, TYPE_CHARCOL_DB, TYPE_DIRECTORY, TYPE_TOMOE, TYPE_KANJIVG, TYPE_KUCHIBUE = \
range(6)

def _get_charcol(charcol_type, charcol_path):
    if charcol_type == TYPE_DIRECTORY:
        # charcol_path is actually a directory here
        return CharacterCollection.from_character_directory(charcol_path)

    elif charcol_type in (TYPE_CHARCOL, TYPE_CHARCOL_DB):
        return CharacterCollection(charcol_path)

    elif charcol_type == TYPE_TOMOE:
        return tomoe_dict_to_character_collection(charcol_path)

    elif charcol_type == TYPE_KUCHIBUE:
        return kuchibue_to_character_collection(charcol_path)

    elif charcol_type == TYPE_KANJIVG:
        return kanjivg_to_character_collection(charcol_path)
    

def get_aggregated_charcol(tuples, dbpath=None):
    """
    Create a character collection out of other character collections,
    character directories, tomoe dictionaries or kuchibue databases.

    tuples: a list of tuples (TYPE, path list)
    """

    # number of files for each character collection type
    n_files = [len(t[1]) for t in tuples]
    
    # we don't need to merge character collections if only one is provided
    # this can save a lot of time for large collections
    if sum(n_files) == 1 and dbpath is None:
        idx = n_files.index(1)
        return _get_charcol(tuples[idx][0], tuples[idx][1][0])

    if dbpath is not None and dbpath.endswith(".chardb"):
        if os.path.exists(dbpath):
            print "%s exists already." % dbpath
            print "Continuing will modify it..."
            answer = raw_input("Continue anyway? (y/N)")
            if answer == "y":
                print "Overwrite to concatenate collections together " + \
                      "in a new database"
                print "Don't overwrite to append new characters or "  + \
                      "filter (-i,-e,-m) existing database"
                answer = raw_input("Overwrite it? (y/N)")
                if answer == "y":
                    os.unlink(dbpath)
            else:
                exit()

        charcol = CharacterCollection(dbpath)
        #charcol.WRITE_BACK = False
        #charcol.AUTO_COMMIT = True
    else:
        charcol = CharacterCollection() # in memory db

    charcols = [_get_charcol(typ, path) \
                    for typ, paths in tuples for path in paths]

    charcol.merge(charcols)

    return charcol
