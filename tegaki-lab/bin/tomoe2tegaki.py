# Converts Tomoe format (all characters in one XML file)
# to Tegaki Lab format (one file per character)

import sys
import os
import tomoe

from tegaki.character import *

def tomoechar2tegakichar(tomoechar):
    tegakichar = Character()
    tegakichar.set_utf8(tomoechar.get_utf8())

    writing = Writing()

    for stroke in tomoechar.get_writing().get_strokes():
        s = Stroke()
        for x, y in stroke:
            s.append_point(Point(x=x, y=y))
        writing.append_stroke(s)

    tegakichar.set_writing(writing)

    return tegakichar 

def is_kanji(char):
    if not (
            (char >= 0x4E00 and char <= 0x9FBF) or \
            (char >= 0x3400 and char <= 0x4DBF) or \
            (char >= 0x20000 and char <= 0x2A6DF) or \
            (char >= 0x3190 and char <= 0x319F) or \
            (char >= 0xF900 and char <= 0xFAFF) or \
            (char >= 0x2F800 and char <= 0x2FA1F)
            ):

        return False
    else:
        return True

dictfile = sys.argv[1]
output_dir = sys.argv[2]

dictobject = tomoe.Dict("XML", filename = dictfile, editable = False)
query = tomoe.Query()

candidates = dictobject.search(query)

for c in candidates:
    char = tomoechar2tegakichar(c.get_char())
    charunicode = unicode(char.get_utf8(), "utf8")
    if len(charunicode) == 1:
        charcode = int(ord(unicode(charunicode)))
        if not is_kanji(charcode):
            continue
        char.write(os.path.join(output_dir, "%d.xml.gz" % charcode), 
                   gzip=True)