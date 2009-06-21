from django.db import models
from django.contrib import admin

from random import randint

class CharacterSet(models.Model):
    name = models.CharField(max_length=30)
    lang = models.CharField(max_length=10)
    description = models.CharField(max_length=255)
    # characters is a string representation of character code lists
    # and/or character code ranges.
    # e.g. 8,10..15,17 is equivalent to 8,10,11,12,13,14,15,17
    characters = models.TextField() 

    @staticmethod
    def get_array_from_string(s):
        """
        Returns an an array representation of the string representation.
        e.g. "8,A..F,11" => [0x8, [0x10,0xF], 0x11]

        raises ValueError if the input is not valid.
        """
        if not isinstance(s, str):
            raise ValueError

        ret = []
        for ele in s.strip().split(","):
            arr = [int(x, 16) for x in ele.strip().split("..")]
            if len(arr) == 1:
                ret.append(arr[0])
            else:
                ret.append(arr)
        return ret

    def contains(self, char_code):
        """
        Returns whether a given character code belongs to the character set
        or not.
        """
        arr = CharacterSet.get_array_from_string(self.characters)
        # FIXME: replaces linear search with binary search
        #        (get_array_from_string must return a sorted array)
        for ele in arr:
            if isinstance(ele, int): # individual character code
                if ele == char_code:
                    return True
            elif isinstance(ele, list): # character code range
                if ele[0] <= char_code and char_code <= ele[1]:
                    return True
        return False

    def __len__(self):
        """
        Returns the number of characters in the character set.
        """
        arr = CharacterSet.get_array_from_string(self.characters)
        length = 0
        for ele in arr:
            if isinstance(ele, int): # individual character code
                length += 1
            elif isinstance(ele, list): # character code range
                length += ele[1] - ele[0] + 1
        return length

    def get_random(self):
        """
        Returns a random character code from the set.
        Character codes are equally probable.
        """
        i = randint(0, len(self)-1)
        arr = CharacterSet.get_array_from_string(self.characters)
        n = 0
        for ele in arr:
            if isinstance(ele, int): # individual character code
                if i == n:
                    return ele
                else:
                    n += 1
            elif isinstance(ele, list): # character code range
                range_len = ele[1] - ele[0] + 1
                if n <= i and i <= n + range_len - 1:
                    return ele[0] + i - n
                else:
                    n += range_len
        return None # should never be reached

admin.site.register(CharacterSet)

class HandWritingSample(models.Model):
    utf8 = models.CharField(max_length=2)
    pickled_char = models.TextField()
    xml = models.TextField()

admin.site.register(HandWritingSample)
