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

import glob
import os

from dictutils import SortedDict

class TrainerError(Exception):
    pass

class Trainer:

    def __init__(self):
        pass
   
    @staticmethod
    def get_available_trainers():
        trainers = SortedDict()

        try:
            trainers["zinnia"] = ZinniaTrainer
        except NameError:
            pass

        return trainers   

    # To be implemented by child class
    def train(self, character_collection, meta):
        """
        character_collection: a tegaki.character.CharacterCollection object
        meta: a dictionary containing the following keys
            - name: full name (mandatory)
            - shortname: name with less than 3 characters (mandatory)
            - language: model language (optional)
            - path: output path (optional)
        """
        raise NotImplementedError

    def _check_meta(self, meta):
        if not meta.has_key("name") or not meta.has_key("shortname"):
            raise TrainerError, "meta must contain a name and a shortname"

    def _write_meta_file(self, meta, meta_file):
        f = open(meta_file, "w")
        for k,v in meta.items():
            f.write("%s = %s\n" % (k,v))
        f.close()

try:
    import zinnia

    class ZinniaTrainer(Trainer):

        def __init__(self):
            Trainer.__init__(self)

        def train(self, charcol, meta):
            self._check_meta(meta)

            trainer = zinnia.Trainer()
            zinnia_char = zinnia.Character()

            for set_name in charcol.get_set_list():
                for character in charcol.get_characters(set_name):      
                    if (not zinnia_char.parse(character.to_sexp())):
                        raise TrainerError, zinnia_char.what()
                    else:
                        trainer.add(zinnia_char)

            if "path" in meta:
                path = meta["path"]
            else:
                path = os.path.join(os.environ['HOME'], ".tegaki", "models",
                                    "zinnia", meta["name"] + ".model")

            meta_file = path.replace(".model", ".meta")
            
            trainer.train(path)
            self._write_meta_file(meta, meta_file)

except ImportError:
    pass

