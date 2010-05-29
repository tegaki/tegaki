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

from tegaki.engine import Engine
from tegaki.dictutils import SortedDict

SMALL_HIRAGANA = {
"あ":"ぁ","い":"ぃ","う":"ぅ","え":"ぇ","お":"ぉ","つ":"っ",
"や":"ゃ","ゆ":"ゅ","よ":"ょ","わ":"ゎ"
}

SMALL_KATAKANA = {
"ア":"ァ","イ":"ィ","ウ":"ゥ","エ":"ェ","オ":"ォ","ツ":"ッ",
"ヤ":"ャ","ユ":"ュ","ヨ":"ョ","ワ":"ヮ"
}

class Results(list):
    """
    Object containing recognition results.
    """

    def get_candidates(self):
        return [c[0] for c in self]

    def get_scores(self):
        return [c[1] for c in self]

    def to_small_kana(self):
        cand = [SMALL_HIRAGANA[c] if c in SMALL_HIRAGANA else c \
                    for c in self.get_candidates()]
        cand = [SMALL_KATAKANA[c] if c in SMALL_KATAKANA else c \
                    for c in cand]
        return Results(zip(cand, self.get_scores()))

class RecognizerError(Exception):
    """
    Raised when something went wrong in a Recognizer.
    """
    pass

class Recognizer(Engine):
    """
    Base Recognizer class.

    A recognizer can recognize handwritten characters based on a model.

    The L{open} method should be used to load a model from an
    absolute path on the disk.

    The L{set_model} method should be used to load a model from its name.
    Two models can't have the same name within one recognizer.
    However, two models can be named the same if they belong to two different
    recognizers.

    Recognizers usually have a corresponding L{Trainer}.
    """

    def __init__(self):
        self._model = None
        self._lang = None
   
    @classmethod
    def get_available_recognizers(cls):
        """
        Return recognizers installed on the system.

        @rtype: dict
        @return: a dict where keys are recognizer names and values \
                 are recognizer classes
        """
        if not "available_recognizers" in cls.__dict__:
            cls._load_available_recognizers()
        return cls.available_recognizers

    @classmethod
    def _load_available_recognizers(cls):
        cls.available_recognizers  = SortedDict()

        for directory in cls._get_search_path("engines"):
            if not os.path.exists(directory):
                continue

            for f in glob.glob(os.path.join(directory, "*.py")):
                if f.endswith("__init__.py") or f.endswith("setup.py"):
                    continue

                module_name = os.path.basename(f).replace(".py", "")
                module_name += "recognizer"
                module = imp.load_source(module_name, f)

                try:
                    name = module.RECOGNIZER_CLASS.RECOGNIZER_NAME
                    cls.available_recognizers[name] = module.RECOGNIZER_CLASS
                except AttributeError:
                    pass       

    @staticmethod
    def get_all_available_models():
        """
        Return available models from all recognizers.

        @rtype: list
        @return: a list of tuples (recognizer_name, model_name, meta_dict)
        """
        all_models = []
        for r_name, klass in Recognizer.get_available_recognizers().items():
            for model_name, meta in klass.get_available_models().items():
                all_models.append([r_name, model_name, meta])
        return all_models

    @classmethod
    def get_available_models(cls):
        """
        Return available models for the current recognizer.

        @rtype; dict
        @return: a dict where keys are models names and values are meta dict
        """
        if "available_models" in cls.__dict__: 
            return cls.available_models
        else:
            name = cls.RECOGNIZER_NAME
            cls.available_models = cls._get_available_models(name)
            return cls.__dict__["available_models"]

    @classmethod
    def _get_available_models(cls, recognizer):
        available_models = SortedDict()

        for directory in cls._get_search_path("models"):
            directory = os.path.join(directory, recognizer)

            if not os.path.exists(directory):
                continue

            meta_files = glob.glob(os.path.join(directory, "*.meta"))

            for meta_file in meta_files:
                meta = Recognizer.read_meta_file(meta_file)

                if not meta.has_key("name") or \
                    not meta.has_key("shortname"):
                    continue

                model_file = meta_file.replace(".meta", ".model")
            
                if meta.has_key("path") and not os.path.exists(meta["path"]):
                    # skip model if specified path is incorrect
                    continue
                elif not meta.has_key("path") and os.path.exists(model_file):
                    # if path option is missing, assume the .model file
                    # is in the same directory
                    meta["path"] = model_file

                available_models[meta["name"]] = meta

        return available_models

    def open(self, path):
        """
        Open a model.

        @type path: str
        @param path: model path
        
        Raises RecognizerError if could not open.
        """
        raise NotImplementedError

    def set_options(self, options):
        """
        Process recognizer/model specific options.

        @type options: dict
        @param options: a dict where keys are option names and values are \
                        option values
        """
        pass

    def get_model(self):
        """
        Return the currently selected model.

        @rtype: str
        @return: name which identifies model uniquely on the system
        """
        return self._model

    def set_model(self, model_name):
        """
        Set the currently selected model.

        @type model_name: str
        @param model_name: name which identifies model uniquely on the system

        model_name must exist for that recognizer.
        """
        if not model_name in self.__class__.get_available_models():
            raise RecognizerError, "Model does not exist"

        self._model = model_name

        meta = self.__class__.get_available_models()[model_name]

        self.set_options(meta)

        if "language" in meta: self._lang = meta["language"]

        self.open(meta["path"])

    # To be implemented by child class
    def recognize(self, writing, n=10):
        """
        Recognizes handwriting.

        @type writing: L{Writing}
        @param writing: the handwriting to recognize

        @type n: int
        @param n: the number of candidates to return

        @rtype: list
        @return: a list of tuple (label, probability/distance)
        
        A model must be loaded with open or set_model() beforehand.
        """
        is_small = False
        if self._lang == "ja":
            is_small = writing.is_small()

        results = self._recognize(writing, n)

        if is_small:
            return results.to_small_kana()
        else:
            return results


if __name__ == "__main__":
    import sys
    from tegaki.character import Character

    recognizer = sys.argv[1] # name of recognizer
    model = sys.argv[2] # name of model file
    char = Character()
    char.read(sys.argv[3]) # path of .xml file
    writing = char.get_writing() 

    recognizers = Recognizer.get_available_recognizers()
    print "Available recognizers", recognizers

    if not recognizer in recognizers:
        raise Exception, "Not an available recognizer"

    recognizer_klass = recognizers[recognizer]
    recognizer = recognizer_klass()

    models = recognizer_klass.get_available_models()
    print "Available models", models

    if not model in models:
        raise Exception, "Not an available model"

    recognizer.set_model(model)

    print recognizer.recognize(writing)
