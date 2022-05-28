# -*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin
from django.db.models.signals import pre_save
from django.utils import simplejson

from django.contrib.auth.models import User
from tegakidb.users.models import TegakiUser
from tegakidb.utils.models import Language

import random
#from random import randint
from datetime import datetime
import re
sets = set #wanna use set as a class variable

class CharacterSet(models.Model):
    name = models.CharField(max_length=30)
    lang = models.ForeignKey(Language)
    description = models.CharField(max_length=255)
    # characters is a string representation of character code lists
    ## and/or character code ranges.
    ## e.g. 8,10..15,17 is equivalent to 8,10,11,12,13,14,15,17
    # internally we won't use ranges, its more convenient to use built-in sets
    characters = models.TextField()
    user = models.ForeignKey(User,blank=True, null=True)
    public = models.BooleanField(default=True) 
    set = None
    def __init__(self, *args, **kwargs):
        super(CharacterSet, self).__init__(*args, **kwargs)
        #print "in init"
        #print self.characters, len(self.characters)
        #print self.set
        try: 
            self.set = sets(simplejson.loads(self.characters))
        except:
            #print "no json yet"
            pass
        #print self.set
        #print "leaving init"

    @staticmethod
    def get_array_from_string(s):
        """
        Returns an an array representation of the string representation.
        e.g. "8,A..F,11" => [0x8, [0x10,0xF], 0x11]

        raises ValueError if the input is not valid.
        """
        if not isinstance(s, str) and not isinstance(s, str):
            raise ValueError

        ret = []
        for ele in s.strip().split(","):
            arr = [int(x, 16) for x in ele.strip().split("..")]
            if len(arr) == 1:
                ret.append(arr[0])
            else:
                ret.append(arr)
        return ret

    @staticmethod
    def get_set_from_range_string(s):
        """
        Returns a set representation of the string representation.
        e.g. "8,A..F,11" => Set([0x8, 0x10, 0xE, 0xF, 0x11])

        raises ValueError if the input is not valid.
        """
        if not isinstance(s, str) and not isinstance(s, str):
            raise ValueError

        retset = sets()
        for ele in s.strip().split(","):
            arr = [int(x, 16) for x in ele.strip().split("..")]
            if len(arr) == 1:
                retset.add(arr[0])
            else:
                for i in range(arr[0], arr[1]):
                    retset.add(i)
        return retset


    @staticmethod
    def get_set_with_filter(s, filter="\u0400-\u9fff"):
        """
        Returns an array of characters (unicode ordinals) found in the input string
        filtered by the given filter.
        default usage
        CharacterSet.get_set_with_filter(u"我是一个人。你也是一个好人")
        will return
        [19968, 20320, 20010, 26159, 25105, 20154, 22909, 20063]
        the default filter will grab anything in the CJK codepoints
        """
        matches = re.findall("[%s]+" % filter, s)
        range = sets()
        #print "in set with filter", u"[%s]+" % filter
        #print matches
        for m in matches:
            #print m.encode("utf-8")
            #print ord(m)
            for c in m:
                range.add(ord(c))
        #print range
        return range
        
    def save_string(self):
        """
        Saves the current set into the string representation
        """
        #print "saving a string:", self.set
        self.characters = str(repr(self.set)[4:-1])

    def display_characters(self):
        """
        Display all the characters in the set
        """
        s = ""
        for c in self.set:
            s = s + "%s,"%chr(c)
        s = s[:-1]
        return s

    def __subtract__(first, second):
        """
        Subtract two CharacterSets
        """
        return first.difference(second)
        #if not self.set:
        #    self.set = CharacterSet.get_set_from_string(self.characters)

        #self.set = self.set.difference(other_set)
        #self.save_string()
        #for ele in other_set:
        #    if isinstance(ele, int):
        #        if self.contains(ele):
        #            self.remove_element(ele)

    def __add__(first, second):
        """
        Add two CharacterSets
        """
        return first.union(second)

    def contains(self, char_code):
        """
        Returns whether a given character code belongs to the character set
        or not.
        """
        #if not self.arr:
        #    self.arr = CharacterSet.get_set_from_string(self.characters)
        return char_code in self.set

        # FIXME: replaces linear search with binary search
        #        (get_array_from_string must return a sorted array)
        """for ele in arr:
            if isinstance(ele, int): # individual character code
                if ele == char_code:
                    return True
            elif isinstance(ele, list): # character code range
                #if ele[0] <= char_code and char_code <= ele[1]:
                #    return True
                return in_range(ele, list)
        return False"""

    def __len__(self):
        """
        Returns the number of characters in the character set.
        """
        return len(self.set)
        #if not self.arr:
        #   arr = CharacterSet.get_set_from_string(self.characters)
        """
        length = 0
        for ele in arr:
            if isinstance(ele, int): # individual character code
                length += 1
            elif isinstance(ele, list): # character code range
                length += ele[1] - ele[0] + 1
        return length
        """

    #def get_list(self):
        """
        Returns the character set as a python list
        """
        #return CharacterSet.get_array_from_string(self.characters)


    def get_random(self):
        """
        Returns a random character code from the set.
        Character codes are equally probable.
        """
        #if not self.arr:
        #    self.arr = CharacterSet.get_set_from_string(self.characters)
        #i = randint(0, len(self.set)-1)
        #return repr(self.set)[i]
        return random.sample(self.set, 1)[0]
        """
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
        """


    def __unicode__(self):
        return self.name

def handle_cs_save(sender, instance, signal, *args, **kwargs):
    """
    Save the set into the character string for the database
    """
    try:
        a = sender.objects.get(pk=instance._get_pk_val())
        a.save_string()
    except:
        print("umm")
    #instance.save_string()
pre_save.connect(handle_cs_save, sender=CharacterSet)

admin.site.register(CharacterSet)

class Character(models.Model):
    lang = models.ForeignKey(Language)
    str = models.IntegerField()
    n_correct_handwriting_samples = models.IntegerField(default=0)
    n_handwriting_samples = models.IntegerField(default=0)
    
    def __unicode__(self):      #this is the display name
        return chr(self.str)#.encode("UTF-8") 

    def utf8(self):
        return chr(self.str)

admin.site.register(Character)


#TODO: create choices for each of the enum fields
class HandWritingSample(models.Model):
    character = models.ForeignKey(Character)
    user = models.ForeignKey(User)
    character_set = models.ForeignKey(CharacterSet)
    data = models.TextField()
    compressed = models.IntegerField(default=0) #(NON_COMPRESSED=0, GZIP=1, BZ2=2)
    date = models.DateTimeField(default=datetime.today())
    n_proofread = models.IntegerField(default=0)
    proofread_by = models.ManyToManyField(TegakiUser, related_name='tegaki_user', blank=True)
    device_used = models.IntegerField(default=0) #(MOUSE, TABLET, PDA)
    model = models.BooleanField(default=False)
    stroke_order_incorrect = models.BooleanField(default=False)
    stroke_number_incorrect = models.BooleanField(default=False)
    wrong_stroke = models.BooleanField(default=False)
    wrong_spacing = models.BooleanField(default=False)
    client = models.TextField(blank=True)

    def __unicode__(self):      #this is the display name
        return self.character.__unicode__()

admin.site.register(HandWritingSample)
