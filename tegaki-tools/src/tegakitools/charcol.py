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

from tegaki.character import CharacterCollection

from tegakitools.tomoe import tomoe_dict_to_character_collection
from tegakitools.kuchibue import kuchibue_to_character_collection

TYPE_CHARCOL, TYPE_DIRECTORY, TYPE_TOMOE, TYPE_KUCHIBUE = range(4)

def get_aggregated_charcol(tuples):
    """
    Create a character collection out of other character collections,
    character directories, tomoe dictionaries or kuchibue databases.

    tuples: a list of tuples (TYPE, list)
    """
    charcol = CharacterCollection()

    for typ, files in tuples:
        if typ == TYPE_DIRECTORY:
            # files should actually contain a list of directories
            for d in files: 
                charcol += CharacterCollection.from_character_directory(d)

        elif typ == TYPE_CHARCOL:
            for charcol_path in files:
                _charcol = CharacterCollection()
                gzip = False; bz2 = False
                if charcol_path.endswith(".gz"): gzip = True
                if charcol_path.endswith(".bz2"): bz2 = True
                _charcol.read(charcol_path, gzip=gzip, bz2=bz2)
                charcol += _charcol

        elif typ == TYPE_TOMOE:
            for tomoe in files:
                charcol += tomoe_dict_to_character_collection(tomoe)

        elif typ == TYPE_KUCHIBUE:
            for kuchibue in files:
                charcol += kuchibue_to_character_collection(kuchibue)

    return charcol
