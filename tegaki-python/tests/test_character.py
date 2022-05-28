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

import unittest
import os
import sys
import io
import minjson
import tempfile

from tegaki.character import Point, Stroke, Writing, Character

class CharacterTest(unittest.TestCase):

    def setUp(self):
        self.currdir = os.path.dirname(os.path.abspath(__file__))

        self.strokes = [[(210, 280), (213, 280), (216, 280), (220, 280), (223,
280), (226, 280), (230, 280), (233, 280), (236, 280), (243, 280), (246, 280),
(253, 280), (260, 280), (263, 280), (270, 283), (276, 283), (283, 286), (286,
286), (293, 290), (296, 290), (300, 290), (303, 290), (306, 290), (310, 290),
(313, 290), (316, 293), (320, 293), (320, 296), (320, 300), (316, 303), (316,
306), (316, 310), (316, 313), (313, 316), (313, 320), (310, 323), (310, 326),
(306, 330), (306, 333), (303, 340), (300, 346), (300, 350), (300, 356), (296,
360), (293, 366), (290, 366), (286, 373), (283, 376), (280, 380), (276, 386),
(273, 386), (273, 390), (270, 390), (270, 396), (266, 396), (263, 400), (260,
403), (256, 406), (253, 406), (253, 410), (250, 410), (250, 413), (246, 413),
(250, 413), (253, 413), (256, 413), (260, 413), (263, 413), (286, 423), (290,
423), (296, 423), (300, 423), (306, 426), (310, 426), (313, 426), (316, 426),
(316, 430), (320, 430), (323, 430), (326, 430), (326, 433), (330, 433), (333,
433), (333, 436), (336, 436), (336, 440), (336, 443), (336, 446), (336, 450),
(336, 453), (336, 456), (336, 460), (336, 463), (336, 466), (336, 470), (336,
476), (333, 480), (333, 483), (333, 486), (330, 490), (330, 496), (326, 496),
(326, 500), (326, 503), (323, 506), (323, 510), (320, 516), (316, 520), (316,
523), (313, 526), (310, 526), (306, 530), (306, 533), (303, 536), (300, 536),
(300, 540), (296, 546), (293, 546), (290, 553), (286, 556), (283, 556), (283,
560), (276, 563), (270, 566), (266, 566), (263, 573), (260, 573), (256, 576),
(253, 576), (250, 580), (250, 583), (246, 583), (243, 586), (240, 586), (240,
590), (236, 590), (233, 593), (230, 596), (226, 596), (220, 596), (220, 600),
(216, 600), (213, 600), (210, 603), (206, 603), (203, 603)], [(200, 276), (200,
280), (200, 283), (200, 286), (200, 290), (203, 293), (203, 296), (203, 300),
(206, 300), (206, 306), (206, 310), (206, 316), (206, 320), (210, 323), (210,
326), (210, 333), (210, 336), (210, 340), (210, 343), (210, 346), (213, 353),
(213, 356), (213, 360), (213, 363), (216, 363), (216, 370), (216, 373), (216,
376), (220, 380), (220, 386), (220, 393), (220, 396), (220, 400), (220, 403),
(220, 410), (220, 416), (220, 420), (220, 423), (220, 426), (220, 433), (220,
436), (220, 443), (220, 446), (220, 450), (220, 453), (220, 460), (220, 466),
(220, 470), (220, 473), (220, 476), (220, 483), (220, 486), (220, 490), (220,
493), (220, 496), (220, 500), (220, 503), (220, 506), (220, 510), (220, 513),
(220, 516), (220, 520), (220, 526), (220, 530), (223, 536), (223, 540), (223,
543), (223, 546), (223, 553), (223, 556), (223, 560), (223, 566), (223, 570),
(223, 573), (223, 576), (223, 580), (223, 583), (223, 590), (223, 593), (223,
596), (223, 603), (223, 606), (223, 613), (223, 616), (223, 620), (223, 626),
(223, 633), (223, 640), (223, 643), (223, 650), (223, 653), (223, 660), (223,
663), (223, 666), (223, 673), (223, 676), (223, 683), (223, 686), (223, 690),
(223, 693), (223, 696), (223, 700), (223, 706), (223, 710), (223, 713), (223,
720), (223, 723), (223, 726), (223, 730), (223, 736), (223, 740), (223, 746),
(223, 750), (223, 753), (223, 756), (223, 760), (223, 763), (223, 766), (223,
773), (223, 776), (223, 780)], [(493, 216), (493, 220), (496, 223), (496, 226),
(496, 230), (500, 233), (500, 236), (500, 240), (500, 243), (503, 246), (503,
250), (506, 253), (506, 256), (506, 260), (510, 263), (510, 266), (510, 270),
(510, 273)], [(370, 283), (373, 283), (376, 283), (380, 283), (386, 283), (390,
283), (400, 283), (403, 283), (413, 283), (423, 283), (426, 283), (436, 283),
(443, 283), (450, 283), (456, 283), (466, 283), (470, 283), (476, 283), (486,
283), (493, 283), (500, 283), (503, 283), (513, 283), (516, 283), (523, 283),
(526, 283), (533, 283), (536, 283), (540, 283), (546, 283), (550, 283), (583,
283), (586, 283), (593, 283), (596, 283), (600, 283), (606, 283), (610, 283),
(616, 283), (620, 283), (626, 283), (633, 283), (636, 283), (643, 283), (646,
283), (650, 283), (653, 283), (656, 283), (663, 283), (666, 283), (670, 283),
(673, 283), (676, 283), (680, 283), (683, 283), (686, 283), (690, 283), (693,
283), (696, 283), (700, 283), (703, 286)], [(530, 370), (536, 373), (540, 373),
(546, 373), (550, 373), (570, 380), (573, 380), (580, 380), (600, 386), (603,
386), (613, 386), (616, 386), (626, 386), (630, 386), (636, 386), (640, 386),
(646, 386), (650, 386), (653, 386), (656, 386), (656, 390), (656, 393), (660,
396), (660, 400), (660, 403), (660, 406), (663, 410), (663, 413), (663, 416),
(663, 420), (663, 423), (663, 426), (663, 430), (663, 433), (663, 436), (663,
440), (663, 446), (663, 450), (663, 456), (663, 460), (663, 463), (663, 470),
(663, 473), (663, 480), (663, 483), (663, 490), (660, 496), (660, 500), (660,
506), (660, 510), (660, 516), (656, 520), (656, 526), (656, 530), (656, 536),
(656, 543), (656, 546), (656, 553), (653, 556), (653, 563), (653, 566), (653,
570), (650, 573), (650, 576), (646, 583), (646, 586), (643, 590), (643, 593),
(640, 596), (640, 600), (636, 603), (636, 606), (633, 606), (633, 610), (630,
610), (626, 610), (623, 610), (623, 613), (620, 613), (616, 613), (613, 613),
(610, 613), (606, 613)], [(490, 293), (490, 296), (490, 300), (490, 303), (490,
306), (490, 310), (490, 316), (490, 320), (493, 323), (493, 330), (493, 336),
(493, 343), (493, 346), (493, 353), (493, 363), (493, 366), (493, 373), (493,
376), (493, 386), (493, 390), (493, 396), (493, 403), (493, 406), (493, 413),
(493, 416), (493, 423), (493, 426), (493, 433), (493, 436), (493, 443), (493,
453), (493, 456), (493, 463), (493, 470), (486, 490), (486, 520), (483, 530),
(483, 530), (483, 540), (480, 543), (480, 550), (480, 553), (476, 560), (476,
563), (476, 566), (476, 576), (476, 580), (473, 586), (473, 590), (460, 603),
(460, 606), (460, 613), (460, 620), (456, 626), (456, 636), (456, 640), (453,
646), (453, 650), (453, 656), (453, 660), (450, 666), (450, 673), (446, 676),
(443, 680), (443, 683), (443, 686), (440, 690), (440, 696), (436, 696), (436,
703), (433, 706), (433, 713), (430, 716), (430, 720), (426, 723), (426, 726),
(423, 730), (420, 736), (420, 740), (420, 743), (420, 746), (416, 746), (416,
750), (416, 753), (413, 756), (413, 760), (410, 760), (410, 763), (406, 763)]]

    def _testReadXML(self, char):
        self.assertEqual(char.get_utf8(), "防")

        self.assertEqual(self.strokes, char.get_writing().get_strokes())      
 

    def testConstructorAndSave(self):
        file_ = os.path.join(self.currdir, "data", "character.xml")

        for f in (file_, file_ + ".gzip", file_ + ".bz2", None):
            char = Character(f)
            if f:
                self._testReadXML(char) # check that it is correctly loaded

            files = list(map(tempfile.mkstemp, (".xml", ".xml.gz", ".xml.bz2")))
            output_paths = [path for fd,path in files]
            
            for path in output_paths:                
                try:
                    # check that save with a path argument works
                    char.save(path)
                    newchar = Character(path)
                    self.assertEqual(char, newchar)
                finally:
                    os.unlink(path)

                try:
                    # check that save with a path argument works
                    newchar.save()
                    newchar2 = Character(path)
                    self.assertEqual(char, newchar2)
                finally:
                    os.unlink(path)

        char = Character()
        self.assertRaises(ValueError, char.save)

                


    def testReadXMLFile(self):
        file = os.path.join(self.currdir, "data", "character.xml")
        char = Character()
        char.read(file)

        self._testReadXML(char)

    def testReadXMLGzipFile(self):
        file = os.path.join(self.currdir, "data", "character.xml.gzip")
        char = Character()
        char.read(file, gzip=True)

        self._testReadXML(char)

    def testReadXMLBZ2File(self):
        file = os.path.join(self.currdir, "data", "character.xml.bz2")
        char = Character()
        char.read(file, bz2=True)

        self._testReadXML(char)

    def testReadXMLString(self):
        file = os.path.join(self.currdir, "data", "character.xml")
        
        f = open(file)
        buf = f.read()
        f.close()
        
        char = Character()
        char.read_string(buf)

        self._testReadXML(char)

    def testReadXMLGzipString(self):
        file = os.path.join(self.currdir, "data", "character.xml.gzip")
        file = open(file)
        string = file.read()
        file.close()
        
        char = Character()
        char.read_string(string, gzip=True)

        self._testReadXML(char)

    def testReadXMLBZ2String(self):
        file = os.path.join(self.currdir, "data", "character.xml.bz2")
        file = open(file)
        string = file.read()
        file.close()
        
        char = Character()
        char.read_string(string, bz2=True)

        self._testReadXML(char)

    def _getPoint(self):
        point = Point()
        point.x = 1
        point.y = 2
        point.timestamp = 3
        return point

    def testPointToXML(self):
        point = self._getPoint()
        self.assertEqual(point.to_xml(), '<point x="1" y="2" timestamp="3" />')

    def testPointToJSON(self):
        point = self._getPoint()
        self.assertEqual(minjson.read(point.to_json()),
                          {'y': 2, 'timestamp': 3, 'x': 1})

    def _getStroke(self):
        point = Point()
        point.x = 1
        point.y = 2
        point.timestamp = 3
                
        point2 = Point()
        point2.x = 4
        point2.y = 5
        point2.pressure = 0.1

        stroke = Stroke()
        stroke.append_point(point)
        stroke.append_point(point2)
                
        return stroke

    def testStrokeToXML(self):
        stroke = self._getStroke()

        expected = """<stroke>
  <point x="1" y="2" timestamp="3" />
  <point x="4" y="5" pressure="0.1" />
</stroke>"""

        self.assertEqual(expected, stroke.to_xml())

    def testStrokeToJSON(self):
        stroke = self._getStroke()

        expected = {'points': [{'y': 2, 'timestamp': 3, 'x': 1}, {'y': 5,
'pressure': 0, 'x': 4}]}

        self.assertEqual(minjson.read(stroke.to_json()), expected)

    def _getWriting(self):
        point = Point()
        point.x = 1
        point.y = 2
        point.timestamp = 3
                
        point2 = Point()
        point2.x = 4
        point2.y = 5
        point2.pressure = 0.1

        stroke = Stroke()
        stroke.append_point(point)
        stroke.append_point(point2)
                
        writing = Writing()
        writing.append_stroke(stroke)
                
        return writing

    def testWritingToXML(self):
        writing = self._getWriting()

        expected = """<width>1000</width>
<height>1000</height>
<strokes>
  <stroke>
    <point x="1" y="2" timestamp="3" />
    <point x="4" y="5" pressure="0.1" />
  </stroke>
</strokes>"""

        self.assertEqual(expected, writing.to_xml())

    def testWritingToJSON(self):
        writing = self._getWriting()

        expected = {'width': 1000, 'height': 1000, 'strokes': [{'points':
[{'y': 2, 'timestamp': 3, 'x': 1}, {'y': 5, 'pressure': 0, 'x': 4}]}]}

        self.assertEqual(minjson.read(writing.to_json()), expected)

    def _getCharacter(self):
        writing = self._getWriting()

        char = Character()
        char.set_writing(writing)
        char.set_utf8("A")

        return char

    def testWriteXMLFile(self):
        char = self._getCharacter()

        io = io.StringIO()
        char.write(io)

        new_char = Character()
        new_char.read_string(io.getvalue())

        self.assertEqual(char, new_char)

    def testCharacterToJSON(self):
        char = self._getCharacter()

        expected = {'utf8': 'A', 'writing': {'width' : 1000, 
                    'height': 1000, 'strokes': [{'points': [{'y':
                    2, 'timestamp': 3, 'x': 1}, 
                    {'y': 5, 'pressure': 0, 'x': 4}]}]}}

        self.assertEqual(minjson.read(char.to_json()), expected)

    def testNewWriting(self):
        writing = Writing()

        writing.move_to(0,0)
        writing.line_to(1,1)
        writing.line_to(2,2)
        writing.line_to(3,3)

        writing.move_to(4,4)
        writing.line_to(5,5)

        writing.move_to(6,6)
        writing.line_to(7,7)
        writing.line_to(8,8)

        strokes = writing.get_strokes()
        expected = [ [(0, 0), (1,1), (2,2), (3,3)],
                     [(4,4), (5,5)],
                     [(6,6), (7,7), (8,8)] ]

        self.assertEqual(strokes, expected)

    def testDuration(self):
        point = Point()
        point.x = 1
        point.y = 2
        point.timestamp = 0
                
        point2 = Point()
        point2.x = 4
        point2.y = 5
        point2.timestamp = 5

        stroke = Stroke()
        stroke.append_point(point)
        stroke.append_point(point2)

        point3 = Point()
        point3.x = 1
        point3.y = 2
        point3.timestamp = 7
                
        point4 = Point()
        point4.x = 4
        point4.y = 5
        point4.timestamp = 10

        stroke2 = Stroke()
        stroke2.append_point(point3)
        stroke2.append_point(point4)
              
        self.assertEqual(stroke2.get_duration(), 3)

        writing = Writing()
        writing.append_stroke(stroke)
        writing.append_stroke(stroke2)
        
        self.assertEqual(writing.get_duration(), 10)

    def testPointEquality(self):
        p1 = Point(x=2, y=3)
        p2 = Point(x=2, y=3)
        p3 = Point(x=2, y=4)

        self.assertTrue(p1 == p2)
        self.assertFalse(p1 == p3)

    def testPointEqualityNone(self):
        p1 = Point(x=2, y=3)
        self.assertFalse(p1 == None)
        self.assertTrue(p1 != None)

    def testPointCopy(self):
        p1 = Point(x=2, y=3)
        p2 = p1.copy()

        self.assertTrue(p1 == p2)

    def testStrokeEquality(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = Stroke()
        s2.append_point(Point(x=2, y=3))
        s2.append_point(Point(x=3, y=4))

        s3 = Stroke()
        s3.append_point(Point(x=2, y=3))
        s3.append_point(Point(x=4, y=5))

        self.assertTrue(s1 == s2)
        self.assertFalse(s1 == s3)

    def testStrokeEqualityNone(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        self.assertFalse(s1 == None)
        self.assertTrue(s1 != None)

    def testStrokeCopy(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = s1.copy()

        self.assertTrue(s1 == s2)

    def testWritingEquality(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = Stroke()
        s2.append_point(Point(x=2, y=3))
        s2.append_point(Point(x=3, y=4))

        w1 = Writing()
        w1.append_stroke(s1)
        w1.append_stroke(s2)

        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = Stroke()
        s2.append_point(Point(x=2, y=3))
        s2.append_point(Point(x=3, y=4))

        w2 = Writing()
        w2.append_stroke(s1)
        w2.append_stroke(s2)

        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = Stroke()
        s2.append_point(Point(x=2, y=3))
        s2.append_point(Point(x=3, y=5))

        w3 = Writing()
        w3.append_stroke(s1)
        w3.append_stroke(s2)

        self.assertEqual(w1, w2)
        self.assertNotEqual(w1, w3)

    def testWritingEqualityNone(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = Stroke()
        s2.append_point(Point(x=2, y=3))
        s2.append_point(Point(x=3, y=4))

        w1 = Writing()
        w1.append_stroke(s1)
        w1.append_stroke(s2)

        self.assertTrue(w1 != None)
        self.assertFalse(w1 == None)

    def testCharacterEqualityNone(self):
        c = Character()
        self.assertTrue(c != None)
        self.assertFalse(c == None)        

    def testWritingCopy(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = Stroke()
        s2.append_point(Point(x=2, y=3))
        s2.append_point(Point(x=3, y=4))

        w1 = Writing()
        w1.append_stroke(s1)
        w1.append_stroke(s2)

        w2 = w1.copy()

        self.assertTrue(w1 == w2)

    def testGetNPoints(self):
        writing = self._getWriting()
        self.assertEqual(writing.get_n_points(), 2)

    def testRemoveStroke(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = Stroke()
        s2.append_point(Point(x=2, y=3))
        s2.append_point(Point(x=3, y=4))

        w = Writing()
        w.append_stroke(s1)
        w.append_stroke(s2)

        w.remove_stroke(1)
        
        self.assertEqual(w.get_strokes(), [[(2,3),(3,4)]])

    def testInsertStroke(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = Stroke()
        s2.append_point(Point(x=2, y=3))
        s2.append_point(Point(x=3, y=4))

        w = Writing()
        w.append_stroke(s1)
        w.append_stroke(s2)

        s3 = Stroke()      
        s3.append_point(Point(x=22, y=33))
        s3.append_point(Point(x=33, y=44))

        w.insert_stroke(1, s3)

        self.assertEqual(w.get_strokes(), [[(2,3),(3,4)], [(22,33),(33,44)],
                                            [(2,3),(3,4)]])    

    def testReplaceStroke(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))

        s2 = Stroke()
        s2.append_point(Point(x=2, y=3))
        s2.append_point(Point(x=3, y=4))

        w = Writing()
        w.append_stroke(s1)
        w.append_stroke(s2)  

        s3 = Stroke()      
        s3.append_point(Point(x=22, y=33))
        s3.append_point(Point(x=33, y=44))

        w.replace_stroke(1, s3)
        self.assertEqual(w.get_strokes(), [[(2,3),(3,4)],[(22,33),(33,44)]])

    def testClearStroke(self):
        s1 = Stroke()
        s1.append_point(Point(x=2, y=3))
        s1.append_point(Point(x=3, y=4))
        s1.clear()
        
        self.assertEqual(len(s1), 0)

    def testValidate(self):
        path = os.path.join(self.currdir, "data", "character.xml")
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
    <utf8>防</utf8>
    <strokes>
      <stroke>
      </stroke>
    </strokes>
"""

        try:
            self.assertTrue(Character.validate(buf))
            self.assertFalse(Character.validate(invalid))
            self.assertFalse(Character.validate(malformed))
        except NotImplementedError:
            sys.stderr.write("lxml missing!\n")
            pass

    def testToSexp(self):
        f = os.path.join(self.currdir, "data", "character.xml")
        char = Character()
        char.read(f)
        f = open(os.path.join(self.currdir, "data", "character.sexp"))
        sexp = f.read().strip()
        f.close()
        self.assertEqual(char.to_sexp(), sexp)

    def testIsSmall(self):
        for filename, res in (("small.xml", True),
                              ("small2.xml", True),
                              ("small3.xml", True),
                              ("small4.xml", True),
                              ("small5.xml", True),
                              ("non-small.xml", False)):
            f = os.path.join(self.currdir, "data", "small", filename)
            char = Character()
            char.read(f)
            self.assertEqual(char.get_writing().is_small(), res)

       