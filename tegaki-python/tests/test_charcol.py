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

import unittest
import os
import sys
import StringIO

from tegaki.character import Point, Stroke, Writing, Character
from tegaki.charcol import CharacterCollection

class CharacterCollectionTest(unittest.TestCase):

    def setUp(self):
        self.currdir = os.path.dirname(os.path.abspath(__file__))      
        path = os.path.join(self.currdir, "data", "collection", "test.charcol")
        self.cc = CharacterCollection()
        self.cc.read(path)  
        f = os.path.join(self.currdir, "data", "character.xml")
        self.c = Character()
        self.c.read(f)

    def testValidate(self):
        path = os.path.join(self.currdir, "data", "collection", "test.charcol")
        f = open(path)
        buf = f.read()
        f.close()

        invalid = \
"""
<?xml version="1.0" encoding="UTF-8"?>
  <character>
    <utf8>防</utf8>
    <strokes>
      <stroke>
      </stroke>
    </strokes>
  </character>
"""

        malformed = \
"""
<?xml version="1.0" encoding="UTF-8"?>
  <character>
"""

        try:
            self.assertTrue(CharacterCollection.validate(buf))
            self.assertFalse(CharacterCollection.validate(invalid))
            self.assertFalse(CharacterCollection.validate(malformed))
        except NotImplementedError:
            sys.stderr.write("lxml missing!\n")
            pass

    def _testReadXML(self, charcol):
        self.assertEquals(charcol.get_set_list(), ["一", "三", "二", "四"])

        c = {}
        for k in ["19968_1", "19968_2", "19968_3", "19977_1", "19977_2",
                 "20108_1"]:
            c[k] = Character()
            c[k].read(os.path.join(self.currdir, "data", "collection", 
                      k + ".xml"))

        self.assertEquals(charcol.get_characters("一"),
                          [c["19968_1"], c["19968_2"], c["19968_3"]])
        self.assertEquals(charcol.get_characters("三"),
                          [c["19977_1"], c["19977_2"]])
        self.assertEquals(charcol.get_characters("二"),
                          [c["20108_1"]])
        self.assertEquals(charcol.get_characters("四"), [])
        self.assertEquals(charcol.get_all_characters(),
                          [c["19968_1"], c["19968_2"], c["19968_3"],
                           c["19977_1"], c["19977_2"], c["20108_1"]])

    def testReadXMLFile(self):
        self._testReadXML(self.cc)

    def testToXML(self):
        charcol2 = CharacterCollection()
        charcol2.read_string(self.cc.to_xml())
        self.assertEquals(self.cc.get_set_list(), charcol2.get_set_list())
        self.assertEquals(self.cc.get_all_characters(),
                          charcol2.get_all_characters())
  
    def testWriteGzipString(self):
        charcol2 = CharacterCollection()
        charcol2.read_string(self.cc.write_string(gzip=True), gzip=True)
        self.assertEquals(self.cc.get_set_list(), charcol2.get_set_list())
        self.assertEquals(self.cc.get_all_characters(),
                          charcol2.get_all_characters())

    def testWriteBz2String(self):
        charcol2 = CharacterCollection()
        charcol2.read_string(self.cc.write_string(bz2=True), bz2=True)
        self.assertEquals(self.cc.get_set_list(), charcol2.get_set_list())
        self.assertEquals(self.cc.get_all_characters(),
                          charcol2.get_all_characters())   

    def testAddSame(self):
        path = os.path.join(self.currdir, "data", "collection", "test.charcol")
        charcol = CharacterCollection()
        charcol.read(path)
        charcol2 = CharacterCollection()
        charcol2.read(path)
        charcol3 = charcol.concatenate(charcol2, check_duplicate=True)
        self.assertEquals(charcol3.get_set_list(), ["一", "三", "二", "四"])
        self.assertEquals(len(charcol3.get_characters("一")), 3)
        self.assertEquals(len(charcol3.get_characters("三")), 2)
        self.assertEquals(len(charcol3.get_characters("二")), 1)
        self.assertEquals(len(charcol3.get_characters("四")), 0)

    def testGetChars(self):
        all_ = self.cc.get_characters("一")
        self.assertEquals(self.cc.get_characters("一", limit=2), all_[0:2])
        self.assertEquals(self.cc.get_characters("一", offset=2), all_[2:])
        self.assertEquals(self.cc.get_characters("一", limit=1, offset=1),
                          all_[1:2])                          

    def testAdd(self):
        path = os.path.join(self.currdir, "data", "collection", "test.charcol")
        charcol = CharacterCollection()
        charcol.read(path)
        path2 = os.path.join(self.currdir, "data", "collection",
                             "test2.charcol")
        charcol2 = CharacterCollection()
        charcol2.read(path2)
        charcol3 = charcol + charcol2
        self.assertEquals(charcol3.get_set_list(), ["一", "三", "二", "四",
                                                    "a", "b", "c", "d"])
        self.assertEquals(len(charcol3.get_characters("一")), 3)
        self.assertEquals(len(charcol3.get_characters("三")), 2)
        self.assertEquals(len(charcol3.get_characters("二")), 1)
        self.assertEquals(len(charcol3.get_characters("四")), 0)
        self.assertEquals(len(charcol3.get_characters("a")), 3)
        self.assertEquals(len(charcol3.get_characters("b")), 2)
        self.assertEquals(len(charcol3.get_characters("c")), 1)
        self.assertEquals(len(charcol3.get_characters("d")), 0)

    def testFromCharDirRecursive(self):
        directory = os.path.join(self.currdir, "data")
        charcol = CharacterCollection.from_character_directory(directory,
                                                        check_duplicate=True)
        self.assertEquals(charcol.get_set_list(), ["防", "三", "一", "二"])
        self.assertEquals(len(charcol.get_characters("一")), 3)
        self.assertEquals(len(charcol.get_characters("三")), 2)
        self.assertEquals(len(charcol.get_characters("二")), 1)
        self.assertEquals(len(charcol.get_characters("防")), 1)

    def testFromCharDirNotRecursive(self):
        directory = os.path.join(self.currdir, "data")
        charcol = CharacterCollection.from_character_directory(directory,
                                        recursive=False, check_duplicate=True)
        self.assertEquals(charcol.get_set_list(), ["防"])
        self.assertEquals(len(charcol.get_characters("防")), 1)

    def testIncludeChars(self):
        self.cc.include_characters_from_text("一三")
        self.assertEquals(self.cc.get_set_list(), ["一", "三"])

    def testExcludeChars(self):
        self.cc.exclude_characters_from_text("三")
        self.assertEquals(self.cc.get_set_list(), ["一", "二"])

    def testProxy(self):
        char = self.cc.get_all_characters()[0]
        writing = char.get_writing()
        writing.normalize()
        strokes = writing.get_strokes(full=True)
        stroke = strokes[0]
        stroke.smooth()
        p = stroke[0]
        p.x = 10

        char2 = self.cc.get_all_characters()[0]
        self.assertEquals(char, char2)

    def testNoProxy(self):
        self.cc.WRITE_BACK = False

        char = self.cc.get_all_characters()[0]
        writing = char.get_writing()
        writing.normalize()
        strokes = writing.get_strokes(full=True)
        stroke = strokes[0]
        stroke.smooth()
        p = stroke[0]
        p.x = 10

        char2 = self.cc.get_all_characters()[0]
        self.assertNotEqual(char, char2)

        # manually update the object
        self.cc.update_character_object(char)

        char2 = self.cc.get_all_characters()[0]
        self.assertEquals(char, char2)

    def testAddSet(self):
        self.cc.add_set("toto")
        self.assertEquals(self.cc.get_set_list()[-1], "toto")

    def testRemoveSet(self):
        before = self.cc.get_set_list()
        self.cc.remove_set(before[-1])
        after = self.cc.get_set_list()
        self.assertEquals(len(before)-1, len(after))
        self.assertEquals(before[0:-1], after)

    def testGetNSets(self):
        self.assertEquals(len(self.cc.get_set_list()), self.cc.get_n_sets())
        self.assertEquals(4, self.cc.get_n_sets())

    def testGetTotalNCharacters(self):
        self.assertEquals(len(self.cc.get_all_characters()),
                          self.cc.get_total_n_characters())
        self.assertEquals(6, self.cc.get_total_n_characters())

    def testGetNCharacters(self):
        for set_name in self.cc.get_set_list():
            self.assertEquals(len(self.cc.get_characters(set_name)),
                              self.cc.get_n_characters(set_name))

        self.assertEquals(self.cc.get_n_characters("一"), 3)
        self.assertEquals(self.cc.get_n_characters("三"), 2)
        self.assertEquals(self.cc.get_n_characters("二"), 1)

    def testSetCharacters(self):
        before = self.cc.get_characters("一")[0:2]
        self.cc.set_characters("一", before)
        after = self.cc.get_characters("一")
        self.assertEquals(before, after)
    
    def testAppendCharacter(self):        
        len_before = len(self.cc.get_characters("一"))
        self.cc.append_character("一", self.c)
        len_after = len(self.cc.get_characters("一"))
        self.assertEquals(len_before + 1, len_after)
    
    def testInsertCharacter(self):
        before = self.cc.get_characters("一")[0]
        len_before = len(self.cc.get_characters("一"))
        self.cc.insert_character("一", 0, self.c)

        after = self.cc.get_characters("一")[0]
        self.assertNotEqual(before, after)
        len_after = len(self.cc.get_characters("一"))

        self.assertEqual(len_before+1, len_after)

    def testReplaceCharacter(self):
        before = self.cc.get_characters("一")[0]
        len_before = len(self.cc.get_characters("一"))
        self.cc.replace_character("一", 0, self.c)

        after = self.cc.get_characters("一")[0]
        self.assertNotEqual(before, after)
        len_after = len(self.cc.get_characters("一"))

        self.assertEqual(len_before, len_after)

    def testRemoveCharacter(self):
        before = self.cc.get_characters("一")[0]
        len_before = len(self.cc.get_characters("一"))
        self.cc.remove_character("一", 0)

        after = self.cc.get_characters("一")[0]
        self.assertNotEqual(before, after)
        len_after = len(self.cc.get_characters("一"))

        self.assertEqual(len_before-1, len_after)

    def testRemoveLastCharacter(self):
        before = self.cc.get_characters("一")[-1]
        len_before = len(self.cc.get_characters("一"))
        self.cc.remove_last_character("一")

        after = self.cc.get_characters("一")[-1]
        self.assertNotEqual(before, after)
        len_after = len(self.cc.get_characters("一"))

        self.assertEqual(len_before-1, len_after)

    def testRemoveSamples(self):
        self.cc.remove_samples(keep_at_most=2)
        self.assertEquals(self.cc.get_n_characters("一"), 2)
        self.assertEquals(self.cc.get_n_characters("三"), 2)
        self.assertEquals(self.cc.get_n_characters("二"), 1)

        self.cc.remove_samples(keep_at_most=1)
        self.assertEquals(self.cc.get_n_characters("一"), 1)
        self.assertEquals(self.cc.get_n_characters("三"), 1)
        self.assertEquals(self.cc.get_n_characters("二"), 1)

    def testRemoveEmptySets(self):
        self.cc.remove_empty_sets()
        self.assertEquals(self.cc.get_set_list(), ["一", "三", "二"])
