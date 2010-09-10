# -*- coding: utf-8 -*-
#
#  Copyright (C) 2009  Alexandre Courbot
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import xml.sax.handler

class BasicHandler(xml.sax.handler.ContentHandler):
	def __init__(self):
		xml.sax.handler.ContentHandler.__init__(self)
		self.elementsTree = []
	
	def currentElement(self):
		return str(self.elementsTree[-1])
		
	def startElement(self, qName, atts):
		self.elementsTree.append(str(qName))
		attrName = "handle_start_" + str(qName)
		if hasattr(self, attrName):
			rfunc = getattr(self, attrName)
			rfunc(atts)
		self.characters = ""
		return True
	
	def endElement(self, qName):
		attrName = "handle_data_" + qName
		if hasattr(self, attrName):
			rfunc = getattr(self, attrName)
			rfunc(self.characters)
		attrName = "handle_end_" + str(qName)
		if hasattr(self, attrName):
			rfunc = getattr(self, attrName)
			rfunc()
		self.elementsTree.pop()
		return True
	
	def characters(self, string):
		self.characters += string
		return True

# Sample licence header
licenseString = """Copyright (C) 2009 Ulrich Apel.
This work is distributed under the conditions of the Creative Commons 
Attribution-Noncommercial-Share Alike 3.0 Licence. This means you are free:
* to Share - to copy, distribute and transmit the work
* to Remix - to adapt the work

Under the following conditions:
* Attribution. You must attribute the work by stating your use of KanjiVG in
  your own copyright header and linking to KanjiVG's website
  (http://kanjivg.tagaini.net)
* Noncommercial. You may not use this work for commercial purposes.
* Share Alike. If you alter, transform, or build upon this work, you may
  distribute the resulting work only under the same or similar license to this
  one.

See http://creativecommons.org/licenses/by-nc-sa/3.0/ for more details."""

class Kanji:
	"""Describes a kanji. The root stroke group is accessible from the root member."""
	def __init__(self, id):
		self.id = id
		self.midashi = None
		self.root = None

	def toXML(self, out, indent = 0):
		out.write("\t" * indent + '<kanji midashi="%s" id="%s">\n' % (self.midashi, self.id))
		self.root.toXML(out, 0)

	def simplify(self):
		self.root.simplify()

	def getStrokes(self):
		return self.root.getStrokes()
		

class StrokeGr:
	"""Describes a stroke group belonging to a kanji. Sub-stroke groups or strokes are available in the childs member. They can either be of class StrokeGr or Stroke so their type should be checked."""
	def __init__(self, parent):
		self.parent = parent
		if parent: parent.childs.append(self)
		# Element of strokegr, or midashi for kanji
		self.element = None
		# A more common, safer element this one derives of
		self.original = None
		self.part = None
		self.variant = False
		self.partial = False
		self.tradForm = False
		self.radicalForm = False
		self.position = None
		self.radical = None
		self.phon = None
		
		self.childs = []

	def toXML(self, out, indent = 0):
		eltString = ""
		if self.element: eltString = ' element="%s"' % (self.element)
		variantString = ""
		if self.variant: variantString = ' variant="true"'
		partialString = ""
		if self.partial: partialString = ' partial="true"'
		origString = ""
		if self.original: origString = ' original="%s"' % (self.original)
		partString = ""
		if self.part: partString = ' part="%d"' % (self.part)
		tradFormString = ""
		if self.tradForm: tradFormString = ' tradForm="true"'
		radicalFormString = ""
		if self.radicalForm: radicalFormString = ' radicalForm="true"'
		posString = ""
		if self.position: posString = ' position="%s"' % (self.position)
		radString = ""
		if self.radical: radString = ' radical="%s"' % (self.radical)
		phonString = ""
		if self.phon: phonString = ' phon="%s"' % (self.phon)
		out.write("\t" * indent + '<strokegr%s%s%s%s%s%s%s%s%s%s>\n' % (eltString, partString, variantString, origString, partialString, tradFormString, radicalFormString, posString, radString, phonString))

		for child in self.childs: child.toXML(out, indent + 1)

		out.write("\t" * indent + '</strokegr>\n')

		if not self.parent: out.write("\t" * indent + '</kanji>\n')

	def simplify(self):
		for child in self.childs: 
			if isinstance(child, StrokeGr): child.simplify()
		if len(self.childs) == 1 and isinstance(self.childs[0], StrokeGr):
			# Check if there is no conflict
			if child.element and self.element and child.element != self.element: return
			if child.original and self.original and child.original != self.original: return
			# Parts cannot be merged
			if child.part and self.part: return
			if child.variant and self.variant and child.variant != self.variant: return
			if child.partial and self.partial and child.partial != self.partial: return
			if child.tradForm and self.tradForm and child.tradForm != self.tradForm: return
			if child.radicalForm and self.radicalForm and child.radicalForm != self.radicalForm: return
			# We want to preserve inner identical positions - we may have something at the top
			# of another top element, for instance.
			if child.position and self.position: return
			if child.radical and self.radical and child.radical != self.radical: return
			if child.phon and self.phon and child.phon != self.phon: return

			# Ok, let's merge!
			child = self.childs[0]
			self.childs = child.childs
			if child.element: self.element = child.element
			if child.original: self.original = child.original
			if child.part: self.part = child.part
			if child.variant: self.variant = child.variant
			if child.partial: self.partial = child.partial
			if child.tradForm: self.tradForm = child.tradForm
			if child.radicalForm: self.radicalForm = child.radicalForm
			if child.position: self.position = child.position
			if child.radical: self.radical = child.radical
			if child.phon: self.phon = child.phon

	def getStrokes(self):
		ret = []
		for child in self.childs: 
			if isinstance(child, StrokeGr): ret += child.getStrokes()
			else: ret.append(child)
		return ret
		

class Stroke:
	"""A single stroke, containing its type and (optionally) its SVG data."""
	def __init__(self):
		self.stype = None
		self.svg = None

	def toXML(self, out, indent = 0):
		if not self.svg: out.write("\t" * indent + '<stroke type="%s"/>\n' % (self.stype))
		else: out.write("\t" * indent + '<stroke type="%s" path="%s"/>\n' % (self.stype, self.svg))

class KanjisHandler(BasicHandler):
	"""XML handler for parsing kanji files. It can handle single-kanji files or aggregation files. After parsing, the kanjis are accessible through the kanjis member, indexed by their svg file name."""
	def __init__(self):
		BasicHandler.__init__(self)
		self.kanjis = {}
		self.currentKanji = None
		self.groups = []

	def handle_start_kanji(self, attrs):
		id = str(attrs["id"])
		self.currentKanji = Kanji(id)
		self.currentKanji.midashi = unicode(attrs["midashi"])
		self.kanjis[id] = self.currentKanji

	def handle_end_kanji(self):
		if len(self.groups) != 0:
			print "WARNING: stroke groups remaining after reading kanji!"
		self.currentKanji = None
		self.groups = []

	def handle_start_strokegr(self, attrs):
		if len(self.groups) == 0: parent = None
		else: parent = self.groups[-1]
		group = StrokeGr(parent)

		# Now parse group attributes
		if attrs.has_key("element"): group.element = unicode(attrs["element"])
		if attrs.has_key("variant"): group.variant = str(attrs["variant"])
		if attrs.has_key("partial"): group.partial = str(attrs["partial"])
		if attrs.has_key("original"): group.original = unicode(attrs["original"])
		if attrs.has_key("part"): group.part = int(attrs["part"])
		if attrs.has_key("tradForm") and str(attrs["tradForm"]) == "true": group.tradForm = True
		if attrs.has_key("radicalForm") and str(attrs["radicalForm"]) == "true": group.radicalForm = True
		if attrs.has_key("position"): group.position = unicode(attrs["position"])
		if attrs.has_key("radical"): group.radical = unicode(attrs["radical"])
		if attrs.has_key("phon"): group.phon = unicode(attrs["phon"])

		self.groups.append(group)

	def handle_end_strokegr(self):
		group = self.groups.pop()
		if len(self.groups) == 0:
			if self.currentKanji.root:
				print "WARNING: overwriting root of kanji!"
			self.currentKanji.root = group

	def handle_start_stroke(self, attrs):
		stroke = Stroke()
		stroke.stype = unicode(attrs["type"])
		if attrs.has_key("path"): stroke.svg = unicode(attrs["path"])
		self.groups[-1].childs.append(stroke)
