# -*- coding: utf-8 -*-

# Copyright (C) 2009 Mathieu Blondel
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

    def get_model(self):
        return self._model

    def set_model(self, model):
        self._model = model

    # To be implemented by child class
    def recognize(self, model, writing, n=10):
        """
        Recognizes writing using model and returns n candidates.
        """
        raise NotImplementedError

try:
    import zinnia

    class ZinniaRecognizer(Recognizer):

        def __init__(self):
            Recognizer.__init__(self)
            self._recognizer = zinnia.Recognizer()

        @classmethod
        def get_available_models(cls):
            if "available_models" in cls.__dict__:
                return cls.available_models
            else:
                cls.__dict__["available_models"] = \
                                       ZinniaRecognizer._get_available_models()
                return cls.__dict__["available_models"]

        @staticmethod
        def _get_available_models():
            available_models = SortedDict()

            pers_dir = os.path.join(os.environ['HOME'], ".tegaki", "models",
                                    "zinnia")

            # FIXME: use $prefix defined in setup
            for directory in ("/usr/local/share/tegaki/models/zinnia/",
                              "/usr/share/tegaki/models/zinnia/",
                              pers_dir):

                if not os.path.exists(directory):
                    continue

                models = glob.glob(os.path.join(directory, "*.model"))

                for model in models:
                    meta = model.replace(".model", ".meta")

                    if not os.path.exists(meta):
                        continue

                    meta = ZinniaRecognizer._read_meta_file(meta)

                    if not meta.has_key("name") or \
                       not meta.has_key("shortname"):
                        continue

                    meta["model"] = model

                    available_models[meta["name"]] = meta

            return available_models

        @staticmethod
        def _read_meta_file( meta_file):
            f = open(meta_file)
            ret = {}
            for line in f.readlines():
                key, value = [s.strip() for s in line.strip().split("=")]
                ret[key] = value
            f.close()
            return ret

        def set_model(self, model_name):
            if not model_name in ZinniaRecognizer.get_available_models():
                raise RecognizerError, "Model does not exist"

            Recognizer.set_model(self, model_name)

            model = ZinniaRecognizer.get_available_models()[model_name]["model"]

            if not self._recognizer.open(model):
                raise RecognizerError, "Could not open model"

        def recognize(self, writing, n=10):
            s = zinnia.Character()

            s.set_width(writing.get_width())
            s.set_height(writing.get_height())

            strokes = writing.get_strokes()
            for i in range(len(strokes)):
                stroke = strokes[i]

                for x, y in stroke:
                    s.add(i, x, y)

            result = self._recognizer.classify(s, n)
            size = result.size()

            return [(result.value(i), result.score(i)) \
                        for i in range(0, (size - 1))]

except ImportError:
    pass

if __name__ == "__main__":
    import sys
    from tegaki.character import Character

    recognizer = sys.argv[1] # name of recognizer
    model = sys.argv[2] # name of .model file
    char = Character()
    char.read(sys.argv[3])
    writing = char.get_writing() # path of .xml file

    recognizers = Recognizer.get_available_recognizers()
    print "Available recognizers", recognizers

    if not recognizer in recognizers:
        raise "Not an available recognizer"

    recognizer_klass = recognizers[recognizer]
    recognizer = recognizer_klass()

    models = recognizer_klass.get_available_models()
    print "Available models", models

    if not model in models:
        raise "Not an available model"

    recognizer.set_model(model)

    print recognizer.recognize(writing)