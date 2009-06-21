import unittest
from tegakidb.hwdb.models import CharacterSet

class CharacterSetTestCase(unittest.TestCase):
    def setUp(self):
        self.ascii = CharacterSet.objects.create(name="ascii", 
                                                 lang="en",
                                                 description="Ascii",
                                                 characters="0..FF")
        self.fake = CharacterSet.objects.create(name="fake", 
                                                lang="en",
                                                description="fake",
                                                characters="9,A..F,11,12")

    def testGetArrayFromString(self):
        self.assertEquals(CharacterSet.get_array_from_string("0..FF"),
                          [[0,0xFF]])
        self.assertEquals(CharacterSet.get_array_from_string("9,A..F,11,12"),
                          [0x9, [0xA,0xF], 0x11, 0x12])

    def testContains(self):
        for i in range(0,256):
            self.assertTrue(self.ascii.contains(i))
        for i in range(257,500):
            self.assertFalse(self.ascii.contains(i))

        for i in range(0,9):
            self.assertFalse(self.fake.contains(i))
        for i in range(9,16):
            self.assertTrue(self.fake.contains(i))
        self.assertFalse(self.fake.contains(0x10))
        self.assertTrue(self.fake.contains(0x11))
        self.assertTrue(self.fake.contains(0x12))
        for i in range(19, 200):
            self.assertFalse(self.fake.contains(i))

    def testLength(self):
        self.assertEquals(len(self.ascii), 256)
        self.assertEquals(len(self.fake), 9)

    def testGetRandom(self):
        for i in range(1000):
            self.assertTrue(self.ascii.contains(self.ascii.get_random()))

        for i in range(1000):
            self.assertTrue(self.fake.contains(self.fake.get_random()))
