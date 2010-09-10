# -*- coding: utf-8 -*-

# Copyright (C) 2010 The Tegaki project contributors
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

import cStringIO
import gzip as gzipm
try:
    import bz2 as bz2m
except ImportError:
    pass

# FIXME: it should be impossible to share read, read_string, write and
# write_string with Character.

class CharacterStrokeDictionary(dict):
    """
    A dictionary used to map characters to their stroke sequences.
    This class supports strokes only to keep things simple.
    """

    def __init__(self, path=None):
        """
        Creates a new CharacterStrokeDictionary.

        @type path: str or None
        @param path: path to file to load or None if empty

        The file extension is used to determine whether the file is plain,
        gzip-compressed or bzip2-compressed XML.
        """
        self._path = path

        if path is not None:
            gzip = True if path.endswith(".gz") or path.endswith(".gzip") \
                        else False
            bz2 = True if path.endswith(".bz2") or path.endswith(".bzip2") \
                       else False

            self.read(path, gzip=gzip, bz2=bz2)

    def get_characters(self):
        return self.keys()

    def get_strokes(self, char):
        if isinstance(char, str): char = unicode(char, "utf-8")
        return self[char]

    def set_strokes(self, char, strokes):
        if isinstance(char, str): char = unicode(char, "utf-8")

        for stroke_list in strokes:
            if not isinstance(stroke_list, list):
                raise ValueError

        self[char] = strokes

    def _parse(self, string):
        string = unicode(string, "utf-8")

        for line in string.strip().split("\n"):
            try:
                char, strokes = line.split("\t")
                strokes = strokes.strip()
                if len(strokes) == 0: continue
                strokes = strokes.split(" ")
                if not char in self: self[char] = []
                self[char].append(strokes)
            except ValueError:
                pass

    def read(self, file, gzip=False, bz2=False, compresslevel=9):
        """
        Read strokes from a file.

        @type file: str or file
        @param file: path to file or file object

        @type gzip: boolean
        @param gzip: whether the file is gzip-compressed or not

        @type bz2: boolean
        @param bz2: whether the file is bzip2-compressed or not

        @type compresslevel: int
        @param compresslevel: compression level (see gzip module documentation)

        Raises ValueError if incorrect file
        """
        try:
            if type(file) == str:
                if gzip:
                    file = gzipm.GzipFile(file, compresslevel=compresslevel)
                elif bz2:
                    try:
                        file = bz2m.BZ2File(file, compresslevel=compresslevel)
                    except NameError:
                        raise NotImplementedError
                else:
                    file = open(file)

                s = file.read()
                file.close()
            else:
                s = file.read()

            self._parse(s)

        except (IOError,):
            raise ValueError

    def read_string(self, string, gzip=False, bz2=False, compresslevel=9):
        """
        Read strokes from string.

        @type string: str
        @param string: string containing XML

        Other parameters are identical to L{read}.
        """
        if gzip:
            io = cStringIO.StringIO(string)
            io = gzipm.GzipFile(fileobj=io, compresslevel=compresslevel)
            string = io.read()
        elif bz2:
            try:
                string = bz2m.decompress(string)
            except NameError:
                raise NotImplementedError

        self._parse(string)

    def to_str(self):
        s = ""
        for char, strokes in self.items():
            for stroke_list in strokes:
                s += "%s\t%s\n" % (char.encode("utf8"),
                                 " ".join(stroke_list).encode("utf8"))
        return s

    def write(self, file, gzip=False, bz2=False, compresslevel=9):
        """
        Write strokes to a file.

        @type file: str or file
        @param file: path to file or file object

        @type gzip: boolean
        @param gzip: whether the file need be gzip-compressed or not

        @type bz2: boolean
        @param bz2: whether the file need be bzip2-compressed or not

        @type compresslevel: int
        @param compresslevel: compression level (see gzip module documentation)
        """
        if type(file) == str:
            if gzip:
                file = gzipm.GzipFile(file, "w", compresslevel=compresslevel)
            elif bz2:
                try:
                    file = bz2m.BZ2File(file, "w", compresslevel=compresslevel)
                except NameError:
                    raise NotImplementedError
            else:
                file = open(file, "w")

            file.write(self.to_str())
            file.close()
        else:
            file.write(self.to_str())

    def write_string(self, gzip=False, bz2=False, compresslevel=9):
        """
        Write XML to string.

        @rtype: str
        @return: string containing XML

        Other parameters are identical to L{write}.
        """
        if bz2:
            try:
                return bz2m.compress(self.to_str(), compresslevel=compresslevel)
            except NameError:
                raise NotImplementedError
        elif gzip:
            io = cStringIO.StringIO()
            f = gzipm.GzipFile(fileobj=io, mode="w",
                               compresslevel=compresslevel)
            f.write(self.to_str())
            f.close()
            return io.getvalue()
        else:
            return self.to_str()

    def save(self, path=None):
        """
        Save dictionary to file.

        @type path: str
        @param path: path where to write the file or None if use the path \
                     that was given to the constructor

        The file extension is used to determine whether the file is plain,
        gzip-compressed or bzip2-compressed XML.
        """
        if [path, self._path] == [None, None]:
            raise ValueError, "A path must be specified"
        elif path is None:
            path = self._path

        gzip = True if path.endswith(".gz") or path.endswith(".gzip") \
                    else False
        bz2 = True if path.endswith(".bz2") or path.endswith(".bzip2") \
                       else False

        self.write(path, gzip=gzip, bz2=bz2)

