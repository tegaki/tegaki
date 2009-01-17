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

class RecognizerError(Exception):
    pass

class Recognizer:

    def __init__(self):
        self._model = None
   
    @staticmethod
    def get_available_recognizers():
        recognizers = {}

        try:
            recognizers["zinnia"] = ZinniaRecognizer
        except NameError:
            pass

        return recognizers            

    def get_available_models(self):
        return self._available_models.keys()

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
            self._find_system_models()
            self._find_personal_models()

        def _find_system_models(self):
            self._available_models = {}

            for directory in ("/usr/local/lib/zinnia/model/tomoe/",
                              "/usr/lib/zinnia/model/tomoe/",
                              "/usr/local/share/tomoe/recognizer/",
                              "/usr/share/tomoe/recognizer/"):

                if os.path.exists(directory):
                    models = glob.glob(os.path.join(directory, "*.model"))

                    for model in models:
                        name = os.path.basename(model).replace(".model", "")
                        self._available_models[name] = model

        def _find_personal_models(self):
            # FIXME: search in for ex $HOME/.zinnia/models/
            pass

        def recognize(self, model, writing, n=10):
            s = zinnia.Character()
            r = zinnia.Recognizer()

            if not r.open(self._available_models[model]):
                raise RecognizerError, "Could not open model"

            s.set_width(writing.get_width())
            s.set_height(writing.get_height())

            strokes = writing.get_strokes()
            for i in range(len(strokes)):
                stroke = strokes[i]

                for x, y in stroke:
                    s.add(i, x, y)

            result = r.classify(s, n)
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

    recognizer = recognizers[recognizer]()

    models = recognizer.get_available_models()
    print "Available models", models

    if not model in models:
        raise "Not an available model"

    print recognizer.recognize(model, writing)