# -*- coding: utf-8 -*-

# Copyright (C) 2008 Mathieu Blondel
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

import os
import sys
import glob

import zinnia

from tegaki.character import *
from lib.exceptions import *

import models.basic.model

class Model(models.basic.model.Model):
    """
    Model using Support Vector Machines with the Zinnia library.
    """

    def __init__(self, *args):
        models.basic.model.Model.__init__(self, *args)

        self.TRAIN_CORPORA = ["japanese-learner1", "japanese-native1"]
        self.EVAL_CORPORA = ["japanese-learner1", "japanese-native1"]

        self.ROOT = os.path.join("models", "svm")
        self.update_folder_paths()

    ########################################
    # Feature extraction...
    ########################################

    def fextract(self):
        pass # nothing to do

    ########################################
    # Initialization...
    ########################################
    
    def init(self):
        pass # nothing to do

    ########################################
    # Training...
    ########################################

    def char_to_sexp(self, char):
        strokes_str = ""
        for stroke in char.get_writing().get_strokes():
            strokes_str += "("
            strokes_str += "".join(["(%d %d)" % (x,y) for x,y in stroke])
            strokes_str += ")"

        return "(character (value %s)(width 1000)(height 1000)(strokes %s))" % \
                    (char.get_utf8(), strokes_str)
        

    def train(self):
        trainer = zinnia.Trainer()
        zinnia_char = zinnia.Character()
            
        for char_code, xml_list in self.train_xml_files_dict.items():

            for xml_file in xml_list:
                character = self.get_character(xml_file)
                sexp = self.char_to_sexp(character)
                
                if (not zinnia_char.parse(sexp)):
                    print zinnia_char.what()
                    exit(1)
                else:
                    trainer.add(zinnia_char)

        path = os.path.join(self.ROOT, "model")
        trainer.train(path)
                
                    

    ########################################
    # Evaluation...
    ########################################
      
    def recognize(self, recognizer, writing):
        character = Character()
        character.set_utf8("?")
        character.set_writing(writing)
        sexp = self.char_to_sexp(character)

        zinnia_char = zinnia.Character()

        if (not zinnia_char.parse(sexp)):
            print zinnia_char.what()
            exit(1)

        results = recognizer.classify(zinnia_char, 10)

        return [results.value(i) for i in range(0, (results.size() - 1))]

    def eval(self):   
        path = os.path.join(self.ROOT, "model")

        if not os.path.exists(path):
            raise ModelException, "No model found."
        
        n_total = 0
        n_match1 = 0
        n_match5 = 0
        n_match10 = 0

        s = ""

        recognizer = zinnia.Recognizer()
        recognizer.open(path)
        
        for char_code, xml_list in self.eval_xml_files_dict.items():
            for xml_file in xml_list:
                utf8 = self.get_utf8_from_char_code(char_code)
                character = self.get_character(xml_file)
                res = self.recognize(recognizer, character.get_writing())

                if utf8 in res:
                    n_match10 += 1 

                if utf8 in res[:5]:
                    n_match5 += 1

                    position = str(res.index(utf8) + 1)
                    matches = ", ".join(res[:5])
                else:
                    position = "X"
                    matches = ""

                if utf8 == res[0]:
                    n_match1 += 1

                n_total += 1

                s += "%s\t%s\t%s\n" % (utf8, position, matches)

            

        self.stderr_print("match1: ",
                          float(n_match1)/float(n_total) * 100,
                          "%")
        self.stderr_print("match5: ",
                          float(n_match5)/float(n_total) * 100,
                          "%")
        self.stderr_print("match10: ",
                          float(n_match10)/float(n_total) * 100,
                          "%")
        
        self.print_verbose(s)

    ########################################
    # Writing pad...
    ########################################

    def find_writing(self, writing):

        path = os.path.join(self.ROOT, "model")

        if not os.path.exists(path):
            raise ModelException, "No model found."

        recognizer = zinnia.Recognizer()
        recognizer.open(path)

        return self.recognize(recognizer, writing)


    def writing_pad(self):
        from lib.writing_pad import WritingPad

        path = os.path.join(self.ROOT, "model")

        if not os.path.exists(path):
            raise ModelException, "No model found."
        
        pad = WritingPad(self.find_writing)
        pad.run()
        