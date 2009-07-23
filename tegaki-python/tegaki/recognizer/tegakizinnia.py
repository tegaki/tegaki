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

from tegaki.recognizer import Recognizer, RecognizerError

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

    RECOGNIZER_CLASS = ZinniaRecognizer

except ImportError:
    pass

