#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import codecs
import xml.sax
from kanjivg import *
import sys

# Read all kanjis
handler = KanjisHandler()
xml.sax.parse(sys.argv[1], handler)
kanjis = handler.kanjis.values()

kanjis.sort(lambda x,y: cmp(x.id, y.id))

sdict_v = {}
sdict = {}
kdict_v = {}
kdict = {}

for kanji in kanjis:
    strokes_v = [s.stype for s in kanji.getStrokes()]

    if "None" in strokes_v: continue

    # strokes without stroke variants
    strokes = [s[0] for s in strokes_v]

    # convert to byte-strings
    strokes_v = [s.encode("utf8") for s in strokes_v]
    strokes = [s.encode("utf8") for s in strokes]

    utf8 = kanji.midashi.encode("utf8")

    kdict_v[utf8] = strokes_v
    kdict[utf8] = strokes
    
    for _strokes,d in ((strokes,sdict),(strokes_v,sdict_v)):
       for s in _strokes:
           d[s] = d.get(s, 0) + 1
 


print >> sys.stderr, "n strokes", len(sdict_v)
print >> sys.stderr, "n strokes (without variants)", len(sdict)
print >> sys.stderr, "n characters", len(kdict)

for utf8 in sorted(kdict.keys()):
    print "%s\t%s" % (utf8, " ".join(kdict[utf8]))

