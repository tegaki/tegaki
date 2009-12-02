# -*- coding: utf-8 -*-

# Copyright (C) 2008-2009 The Tegaki project contributors
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
import imp
from cStringIO import StringIO

from tegaki.engine import Engine
from tegaki.dictutils import SortedDict

class TrainerError(Exception):
    """
    Raised when something went wrong in a Trainer.
    """
    pass

class Trainer(Engine):
    """
    Base Trainer class.

    A trainer can train models based on sample data annotated with labels.
    """

    def __init__(self):
        pass
   
    @classmethod
    def get_available_trainers(cls):
        """
        Return trainers installed on the system.

        @rtype: dict
        @return: a dict where keys are trainer names and values \
                 are trainer classes
        """
        if not "available_trainers" in cls.__dict__:
            cls._load_available_trainers()
        return cls.available_trainers

    @classmethod
    def _load_available_trainers(cls):
        cls.available_trainers  = SortedDict()

        for directory in cls._get_search_path("engines"):
            if not os.path.exists(directory):
                continue

            for f in glob.glob(os.path.join(directory, "*.py")):
                if f.endswith("__init__.py") or f.endswith("setup.py"):
                    continue

                module_name = os.path.basename(f).replace(".py", "")
                module_name += "trainer"
                module = imp.load_source(module_name, f)

                try:
                    name = module.TRAINER_CLASS.TRAINER_NAME
                    cls.available_trainers[name] = module.TRAINER_CLASS
                except AttributeError:
                    pass         

    def set_options(self, options):
        """
        Process trainer/model specific options.

        @type options: dict
        @param options: a dict where keys are option names and values are \
                        option values
        """
        pass

    # To be implemented by child class
    def train(self, character_collection, meta, path=None):
        """
        Train a model.

        @type character_collection: L{CharacterCollection}
        @param character_collection: collection containing training data

        @type meta: dict
        @param meta: meta dict obtained with L{Engine.read_meta_file}

        @type path: str
        @param path: path to the ouput model \
                     (if None, the personal directory is assumed)

        The meta dict needs the following keys:
            - name: full name (mandatory)
            - shortname: name with less than 3 characters (mandatory)
            - language: model language (optional)
        """
        raise NotImplementedError

    def _check_meta(self, meta):
        if not meta.has_key("name") or not meta.has_key("shortname"):
            raise TrainerError, "meta must contain a name and a shortname"

    def _write_meta_file(self, meta, meta_file):
        io = StringIO()
        for k,v in meta.items():
            io.write("%s = %s\n" % (k,v))

        if os.path.exists(meta_file):
            f = open(meta_file)
            contents = f.read() 
            f.close()
            # don't rewrite the file if same
            if io.getvalue() == contents:
                return

        f = open(meta_file, "w")
        f.write(io.getvalue())
        f.close()
