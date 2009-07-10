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

class RecognizerError(Exception):
    pass

class Recognizer:

    def __init__(self):
        self._model = None
   
    @staticmethod
    def get_available_recognizers():
        recognizers = SortedDict()

        try:
            recognizers["zinnia"] = ZinniaRecognizer
        except NameError:
            pass

        return recognizers   

    @staticmethod
    def get_all_available_models():
        """
        Returns a flat list of available models from all recognizers.
        """
        all_models = []
        for r_name, klass in Recognizer.get_available_recognizers().items():
            for model_name, meta in klass.get_available_models().items():
                all_models.append([r_name, model_name, meta])
        return all_models

    @classmethod
    def get_available_models(cls):
        if "available_models" in cls.__dict__:
            return cls.available_models
        else:
            # change ZinniaRecognizer to zinnia
            name = cls.__name__.replace("Recognizer", "").lower()
            cls.__dict__["available_models"] = cls._get_available_models(name)
            return cls.__dict__["available_models"]

    @staticmethod
    def _get_available_models(recognizer):
        available_models = SortedDict()

        try:
            # UNIX
            homedir = os.environ['HOME']
        except KeyError:
            # Windows
            homedir = os.environ['USERPROFILE']

        # FIXME: use $prefix defined in setup
        for directory in (os.path.join("/usr/local/share/tegaki/models/",
                                       recognizer),
                          os.path.join("/usr/share/tegaki/models/",
                                       recognizer),
                          # for Maemo
                          os.path.join("/media/mmc1/tegaki/models/",
                                       recognizer),
                          os.path.join("/media/mmc2/tegaki/models/",
                                       recognizer),
                          # personal directory
                          os.path.join(homedir, ".tegaki", "models",
                                       recognizer)):

            if not os.path.exists(directory):
                continue

            meta_files = glob.glob(os.path.join(directory, "*.meta"))

            for meta_file in meta_files:
                meta = Recognizer._read_meta_file(meta_file)

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

    @staticmethod
    def _read_meta_file(meta_file):
        f = open(meta_file)
        ret = {}
        for line in f.readlines():
            try:
                key, value = [s.strip() for s in line.strip().split("=")]
                ret[key] = value
            except ValueError:
                continue
        f.close()
        return ret

    def get_model(self):
        return self._model

    def set_model(self, model_name):
        """
        Sets a model with a model available on the system.
        model_name must exist for that recognizer.
        """
        if not model_name in self.__class__.get_available_models():
            raise RecognizerError, "Model does not exist"

        self._model = model_name

        path = self.__class__.get_available_models()[model_name]["path"]

        if not self._recognizer.open(path):
            raise RecognizerError, "Could not open model" 

    def set_model_from_file(self, path):
        if not self._recognizer.open(path):
            raise RecognizerError, "Could not open model" 

    # To be implemented by child class
    def recognize(self, writing, n=10):
        """
        Recognizes writing and returns n candidates.
        A model must be set with set_model() beforehand.
        """
        raise NotImplementedError

try:
    import zinnia

    class ZinniaRecognizer(Recognizer):

        def __init__(self):
            Recognizer.__init__(self)
            self._recognizer = zinnia.Recognizer()

        def recognize(self, writing, n=10):
            s = zinnia.Character()

            s.set_width(writing.get_width())
            s.set_height(writing.get_height())

            strokes = writing.get_strokes()
            for i in range(len(strokes)):
                stroke = strokes[i]

                for x, y in stroke:
                    s.add(i, x, y)

            result = self._recognizer.classify(s, n+1)
            size = result.size()

            return [(result.value(i), result.score(i)) \
                        for i in range(0, (size - 1))]

except ImportError:
    pass

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