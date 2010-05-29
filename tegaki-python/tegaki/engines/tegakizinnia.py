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

import os

from tegaki.recognizer import Results, Recognizer, RecognizerError
from tegaki.trainer import Trainer, TrainerError

try:
    import zinnia    

    class ZinniaRecognizer(Recognizer):

        RECOGNIZER_NAME = "zinnia"

        def __init__(self):
            Recognizer.__init__(self)
            self._recognizer = zinnia.Recognizer()

        def open(self, path):
            ret = self._recognizer.open(path) 
            if not ret: raise RecognizerError, "Could not open!"

        def _recognize(self, writing, n=10):
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

            return Results([(result.value(i), result.score(i)) \
                               for i in range(0, (size - 1))])

    RECOGNIZER_CLASS = ZinniaRecognizer

    class ZinniaTrainer(Trainer):

        TRAINER_NAME = "zinnia"

        def __init__(self):
            Trainer.__init__(self)

        def train(self, charcol, meta, path=None):
            self._check_meta(meta)

            trainer = zinnia.Trainer()
            zinnia_char = zinnia.Character()

            for set_name in charcol.get_set_list():
                for character in charcol.get_characters(set_name):      
                    if (not zinnia_char.parse(character.to_sexp())):
                        raise TrainerError, zinnia_char.what()
                    else:
                        trainer.add(zinnia_char)

            if not path:
                if "path" in meta:
                    path = meta["path"]
                else:
                    path = os.path.join(os.environ['HOME'], ".tegaki", "models",
                                        "zinnia", meta["name"] + ".model")
            else:
                path = os.path.abspath(path)

            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            meta_file = path.replace(".model", ".meta")
            if not meta_file.endswith(".meta"): meta_file += ".meta"
            
            trainer.train(path)
            self._write_meta_file(meta, meta_file)

    TRAINER_CLASS = ZinniaTrainer

except ImportError:
    pass

