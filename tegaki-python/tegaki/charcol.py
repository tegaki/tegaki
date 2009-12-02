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

import sqlite3
import base64
import tempfile
import re
import os

from tegaki.dictutils import SortedDict
from tegaki.character import _XmlBase, Point, Stroke, Writing, Character

def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = d[idx] = row[idx]
    return d

class ObjectProxy(object):
    """
    An object that forwards all attribute and method calls to another object.

    Object proxies are used to automatically reflect back in the db
    changes that are made to objects. For example:
    
    >>> char = charcol.get_all_characters()[0]
    >>> char.set_utf8(newvalue) # will be automatically changed in the db
    """

    WRITE_METHODS = []
    READ_METHODS = []
    WRITE_ATTRIBUTES = []

    def __init__(self, charpool, obj, charobj=None):
        self._charpool = charpool
        # the object to redirect attributes and method calls to
        self._obj = obj
        # the original character object
        self._charobj = obj if charobj is None else charobj

    def __getattr__(self, attr_):
        attr = getattr(self._obj, attr_)

        write = False
        if attr_ in self.WRITE_METHODS: 
            write = True
        elif not attr_ in self.READ_METHODS:
            return attr
        def wrapper(*args, **kw):
            if write: self._charpool.add_char(self._charobj)
            return _apply_proxy(self._charpool, attr(*args, **kw),
self._charobj)
        return wrapper


    def __setattr__(self, attr, value):
        if attr in self.WRITE_ATTRIBUTES:
            self._charpool.add_char(self._charobj)
            setattr(self._obj, attr, value)
        self.__dict__[attr] = value

    def __eq__(self, othr):        
        if othr.__class__.__name__.endswith("Proxy"):
            othr = othr._obj
        return self._obj == othr

    def __ne__(self, othr):
        return not(self == othr)

class PointProxy(ObjectProxy):
    """
    Proxy to Point.
    """
    WRITE_METHODS = ["resize", "move_rel", "copy_from"]
    WRITE_ATTRIBUTES = Point.KEYS

    def __getitem__(self, x):
        return self._obj[x]

class StrokeProxy(ObjectProxy):
    """
    Proxy to Stroke.
    """

    WRITE_METHODS = ["append_point", "insert", "smooth", "clear", 
                     "downsample", "downsample_threshold",
                     "upsample", "upsample_threshod"]
    READ_METHODS = []

    def __getitem__(self, i):
        return _apply_proxy(self._charpool, self._obj[i], self._charobj)

    def __len__(self):
        return len(self._obj)

class WritingProxy(ObjectProxy):
    """
    Proxy to Writing.
    """

    # Note: Some method calls need not be mentioned below
    # because they automatically update the db thanks to 
    # Point and Stroke methods that are being used in their implementation.

    WRITE_METHODS = ["clear", "move_to_point", "line_to_point",
                     "set_width", "set_height", "remove_stroke"]
    READ_METHODS = ["get_strokes"]    

class CharacterProxy(ObjectProxy):
    """
    Proxy to Writing.
    """

    WRITE_METHODS = ["set_utf8", "set_unicode", "set_writing", 
                     "read", "read_string"]
    READ_METHODS = ["get_writing"]

OBJ_PROXY = {Character: CharacterProxy,
             Writing : WritingProxy,
             Stroke : StrokeProxy,
             Point : PointProxy}

def _apply_proxy(charpool, obj, charobj):
    return _apply_proxy_rec(charpool, obj, charobj)

def _apply_proxy_rec(charpool, obj, charobj, reclevel=0):
    try:
        return OBJ_PROXY[obj.__class__](charpool, obj, charobj)
    except KeyError:
        if (isinstance(obj, tuple) or isinstance(obj, list)) and reclevel <= 1:
            return [_apply_proxy_rec(charpool, ele, charobj, reclevel+1) \
                        for ele in obj]
        else:
            return obj

class _CharPool(dict):
    """
    Holds characters that need be updated.

    We don't want changes to be immediately reflected back to the db
    for performance reasons. The _CharPool keeps track of what objects need
    be updated.
    """
    
    def __init__(self, cursor):
        self._c = cursor

    def add_char(self, char):        
        self[char.charid] = char

    def _update_character(self, char):
        self._c.execute("""UPDATE characters 
SET utf8=?, n_strokes=?, data=?, sha1=?
WHERE charid=?""", (char.get_utf8(), char.get_writing().get_n_strokes(),
                    _adapt_character(char), char.hash(), char.charid))

    def clear_pool_threshold(self, threshold=100):
        if len(self) > threshold:
            self.clear_pool()
    
    def clear_pool(self):        
        for charid, char in self.items():
            self._update_character(char)
            self.clear()

def _convert_character(data):
    # converts a BLOB into an object
    char = Character()
    char.read_string(base64.b64decode(data), gzip=True)
    return char

def _adapt_character(char):
    # converts an object into a BLOB
    return base64.b64encode(char.write_string(gzip=True))

class CharacterCollection(_XmlBase):
    """
    A collection of L{Characters<Character>}.

    A CharacterCollection is composed of sets.
    Each set can be composed of zero, one, or more characters.

    /!\ Sets do not necessarily contain only characters of the same class
    / utf8 value. Sets may also be used to group characters in other fashions
    (e.g. by number of strokes, by handwriting quality, etc...).
    Therefore the set name is not guaranteed to contain the utf8 value of
    the characters of that set. The utf8 value must be retrieved from each
    character individually.
    """

    #: With PROXY set to True, proxy objects are returned in place of
    #: character, writing, stroke and point objects in order to automatically
    #: reflect changes to these objects back to the sqlite db.
    #: However, there is probably overhead usigng them.
    PROXY = True

    DTD = \
"""
<!ELEMENT character-collection (set*)>
<!ELEMENT set (character*)>

<!-- The name attribute identifies a set uniquely -->
<!ATTLIST set name CDATA #REQUIRED>

<!ELEMENT character (utf8?,width?,height?,strokes)>
<!ELEMENT utf8 (#PCDATA)>
<!ELEMENT width (#PCDATA)>
<!ELEMENT height (#PCDATA)>
<!ELEMENT strokes (stroke+)>
<!ELEMENT stroke (point+)>
<!ELEMENT point EMPTY>

<!ATTLIST point x CDATA #REQUIRED>
<!ATTLIST point y CDATA #REQUIRED>
<!ATTLIST point timestamp CDATA #IMPLIED>
<!ATTLIST point pressure CDATA #IMPLIED>
<!ATTLIST point xtilt CDATA #IMPLIED>
<!ATTLIST point ytilt CDATA #IMPLIED>
"""

    def __init__(self, path=":memory:"):
        self.bind(path)

    # DB utils

    def _e(self, req, *a, **kw):
        self._charpool.clear_pool()
        #print req, a, kw
        return self._c.execute(req, *a, **kw)

    def _fo(self):
        return self._c.fetchone()

    def _fa(self):
        return self._c.fetchall()

    def _efo(self, req, *a, **kw):
        self._e(req, *a, **kw)
        return self._fo()

    def _efa(self, req, *a, **kw):
        self._e(req, *a, **kw)
        return self._fa()

    def _has_tables(self):
        self._e("SELECT count(type) FROM sqlite_master WHERE type = 'table'")
        return self._fo()[0] > 0

    def _create_tables(self):
        self._c.executescript("""
CREATE TABLE character_sets(
  setid    INTEGER PRIMARY KEY, 
  name     TEXT
);

CREATE TABLE characters(
  charid     INTEGER PRIMARY KEY,
  setid      INTEGER REFERENCES character_sets,
  utf8       TEXT,
  n_strokes  INTEGER,
  data       BLOB, -- gz xml
  sha1       TEXT
);

CREATE INDEX character_setid_index ON characters(setid);
""")

    def get_character_from_row(self, row):
        # charid, setid, utf8, n_strokes, data, sha1
        char = _convert_character(row['data'])
        char.charid = row['charid']
        if self.PROXY:
            return CharacterProxy(self._charpool, char)
        else:
            return char

    def _update_set_ids(self):
        self._SETIDS = SortedDict()
        for row in self._efa("SELECT * FROM character_sets ORDER BY setid"):
            self._SETIDS[row['name'].encode("utf8")] = row['setid']    

    # Public API

    def bind(self, path):
        """ 
        Bind database to a db file.

        All changes to the previous binded database will be lost 
        if you haven't committed changes with commit().

        @type path: str

        Possible values for path:
            ":memory:"                  for fully in memory database

            ""                          for a in memory database that uses 
                                        temp files under pressure

            "/path/to/file.chardb"      for file-based database
        """
        self._con = sqlite3.connect(path)
        self._con.text_factory = sqlite3.OptimizedUnicode
        self._con.row_factory = _dict_factory #sqlite3.Row 
        self._c = self._con.cursor()
        self._charpool = _CharPool(self._c)

        if not self._has_tables():
            self._create_tables()

        self._update_set_ids()
        self._path = path

    def get_filename(self):
        return None if self._path in (":memory:", "") else self._path

    def commit(self):
        """
        Commit changes since last commit.
        """
        self._charpool.clear_pool()
        self._con.commit()

    @staticmethod
    def from_character_directory(directory,
                                 extensions=["xml", "bz2", "gz"], 
                                 recursive=True,
                                 check_duplicate=False):
        """
        Creates a character collection from a directory containing
        individual character files.
        """
        regexp = re.compile("\.(%s)$" % "|".join(extensions))
        charcol = CharacterCollection()
        
        for name in os.listdir(directory):
            full_path = os.path.join(directory, name)
            if os.path.isdir(full_path) and recursive:
                charcol += CharacterCollection.from_character_directory(
                               full_path, extensions)
            elif regexp.search(full_path):
                char = Character()
                gzip = False; bz2 = False
                if full_path.endswith(".gz"): gzip = True
                if full_path.endswith(".bz2"): bz2 = True
                
                try:
                    char.read(full_path, gzip=gzip, bz2=bz2)
                except ValueError:
                    continue # ignore malformed XML files

                utf8 = char.get_utf8()
                if utf8 is None: utf8 = "Unknown"

                charcol.add_set(utf8)
                if not check_duplicate or \
                   not char in charcol.get_characters(utf8):
                    charcol.append_character(utf8, char)
                
        return charcol

    def concatenate(self, other, check_duplicate=False):
        """ 
        Merge two charcols together and return a new charcol 

        @type other: CharacterCollection
        """
        new = CharacterCollection()
        new.merge([self, other], check_duplicate=check_duplicate)
        return new

    def merge(self, charcols, check_duplicate=False):
        """ 
        Merge several charcacter collections into the current collection.

        @type charcols: list
        @param charcols: a list of CharacterCollection to merge
        """
        for charcol in charcols:
            for set_name in charcol.get_set_list():
                self.add_set(set_name)
                characters = self.get_characters(set_name)
                for char in charcol.get_characters(set_name):
                    if not check_duplicate or not char in characters:
                        self.append_character(set_name, char)

    def __add__(self, other):
        return self.concatenate(other)
                   
    def add_set(self, set_name):
        """
        Add a new set_name to collection.

        @type set_name: str
        """
        if set_name in self._SETIDS: return
        self._e("INSERT INTO character_sets(name) VALUES (?)", (set_name,))
        self._update_set_ids()

    def remove_set(self, set_name):
        """
        Remove set_name from collection.

        @type set_name: str
        """
        self._e("DELETE FROM character_sets WHERE name=?", (set_name,))
        self._update_set_ids()

    def get_set_list(self):
        """
        Return the sets available in collection.

        @rtype: list of str
        """
        return self._SETIDS.keys()

    def get_n_sets(self):
        """
        Return the number of sets available in collection.

        @rtype: int
        """
        return len(self._SETIDS)

    def get_characters(self, set_name, limit=-1, offset=0):
        """
        Return character belonging to a set.

        @type set_name: str
        @param set_name: the set characters belong to

        @type limit: int
        @param limit: the number of characters needed or -1 if all

        @type offset: int
        @param offset: the offset to start from (0 if from beginning)

        @rtype: list of L{Character}
        """
        i = self._SETIDS[set_name]
        self._e("""SELECT * FROM characters 
WHERE setid=? ORDER BY charid LIMIT ? OFFSET ?""", (i, int(limit), int(offset)))
        return map(self.get_character_from_row, self._fa())

    def get_n_characters(self, set_name):
        """
        Return the number of character belonging to a set.

        @type set_name: str
        @param set_name: the set characters belong to

        @rtype int
        """
        i = self._SETIDS[set_name]
        return self._efo("""SELECT count(charid) FROM characters
WHERE setid=?""", (i,))[0]

    def get_all_characters(self, limit=-1, offset=0):
        """
        Return all characters in collection.
    
        @type limit: int
        @param limit: the number of characters needed or -1 if all

        @type offset: int
        @param offset: the offset to start from (0 if from beginning)

        @rtype: list of L{Character}
        """
        self._e("""SELECT * FROM characters 
ORDER BY charid LIMIT ? OFFSET ?""", (int(limit), int(offset)))
        return map(self.get_character_from_row, self._fa())

    def get_total_n_characters(self):
        """
        Return the total number of characters in collection.

        @rtype: int
        """
        return self._efo("SELECT count(charid) FROM characters")[0]

    def set_characters(self, set_name, characters):
        """
        Set/Replace the characters of a set.

        @type set_name: str
        @param set_name: the set that needs be updated

        @type characters: list of L{Character}
        """
        i = self._SETIDS[set_name]
        self._e("DELETE FROM characters WHERE setid=?", (i,))
        for char in characters:
            self.append_character(set_name, char)

    def append_character(self, set_name, character):
        """
        Append a new character to a set.

        @type set_name: str
        @param set_name: the set to which the character needs be added

        @type character: L{Character}
        """
        i = self._SETIDS[set_name]
        self._e("""INSERT INTO 
characters (setid, utf8, n_strokes, data, sha1) 
VALUES (?,?,?,?,?)""", (i, character.get_utf8(),
                        character.get_writing().get_n_strokes(),
                        _adapt_character(character), character.hash()))

    def insert_character(self, set_name, i, character):
        """
        Insert a new character to a set at a given position.

        @type set_name: str
        @param set_name: the set to which the character needs be inserted

        @type i: int
        @param i: position

        @type character: L{Character}
        """
        chars = self.get_characters(set_name)
        chars.insert(i, character)
        self.set_characters(set_name, chars)

    def remove_character(self, set_name, i):
        """
        Remove a character from a set at a given position.

        @type set_name: str
        @param set_name: the set from which the character needs be removed

        @type i: int
        @param i: position
        """
        setid = self._SETIDS[set_name]
        charid = self._efo("""SELECT charid FROM characters
WHERE setid=? ORDER BY charid LIMIT 1 OFFSET ?""", (setid, i))[0]
        if charid:
            self._e("DELETE FROM characters WHERE charid=?", (charid,))

    def remove_last_character(self, set_name):
        """
        Remove the last character from a set.

        @type set_name: str
        @param set_name: the set from which the character needs be removed
        """
        setid = self._SETIDS[set_name]
        charid = self._efo("""SELECT charid FROM characters
WHERE setid=? ORDER BY charid DESC LIMIT 1""", (setid,))[0]
        if charid:
            self._e("DELETE FROM characters WHERE charid=?", (charid,))

    def update_character_object(self, character):
        """
        Update a character.

        @type character: L{Character}

        character must have been previously retrieved from the collection.
        """
        if not hasattr(character, "charid"):
            raise ValueError, "The character object needs a charid attribute"
        self._e("""UPDATE characters 
SET utf8=?, n_strokes=?, data=?, sha1=?
WHERE charid=?""", (character.get_utf8(),
                    character.get_writing().get_n_strokes(),
                    _adapt_character(character), 
                    character.hash(),
                    character.charid))

    def replace_character(self, set_name, i, character):
        """
        Replace the character at a given position with a new character.

        @type set_name: str
        @param set_name: the set where the character needs be replaced

        @type i: int
        @param i: position

        @type character: L{Character}
        """
        setid = self._SETIDS[set_name]
        charid = self._efo("""SELECT charid FROM characters
WHERE setid=? ORDER BY charid LIMIT 1 OFFSET ?""", (setid, i))[0]
        if charid:
            character.charid = charid
            self.update_character_object(character)
           
    def _get_dict_from_text(self, text):
        text = text.replace(" ", "").replace("\n", "").replace("\t", "")
        dic = {}
        for c in text:
            dic[c] = 1
        return dic

    def include_characters_from_text(self, text):
        """
        Only keep characters found in a text.

        Or put differently, remove all characters but those found in a text.

        @type text: str
        """
        dic = self._get_dict_from_text(unicode(text, "utf8"))
        for set_name in self.get_set_list():
            i = 0
            for char in self.get_characters(set_name)[:]:
                if not char.get_unicode() in dic:
                    self.remove_character(set_name, i)
                else:
                    i += 1
        self.remove_empty_sets()

    def include_characters_from_files(self, text_files):
        """
        Only keep characters found in text_files.

        @type text_files: list
        @param text_files: a list of file paths
        """
        buf = ""
        for inc_path in text_files:
            f = open(inc_path)
            buf += f.read()
            f.close()

        if len(buf) > 0:
            self.include_characters_from_text(buf)

    def exclude_characters_from_text(self, text):
        """
        Exclude characters found in a text.

        @type text: str
        """
        dic = self._get_dict_from_text(unicode(text, "utf8"))
        for set_name in self.get_set_list():
            i = 0
            for char in self.get_characters(set_name)[:]:
                if char.get_unicode() in dic:
                    self.remove_character(set_name, i)
                else:
                    i += 1
        self.remove_empty_sets()

    def exclude_characters_from_files(self, text_files):
        """
        Exclude characters found in text_files.

        @type text_files: list
        @param text_files: a list of file paths
        """
        buf = ""
        for exc_path in text_files:
            f = open(exc_path)
            buf += f.read()
            f.close()

        if len(buf) > 0:
            self.exclude_characters_from_text(buf)

    def remove_samples(self, keep_at_most):
        """
        Remove samples.

        @type keep_at_most: the maximum number of samples to keep.
        """
        for set_name in self.get_set_list():
            if self.get_n_characters(set_name) > keep_at_most:
                setid = self._SETIDS[set_name]
                charids = self._efa("""SELECT charid FROM characters
WHERE setid=? ORDER BY charid LIMIT -1 OFFSET ?""", (setid, keep_at_most))
                charids = ",".join([str(row['charid']) for row in charids])
                self._e("""DELETE FROM characters WHERE charid IN(?)""", 
                        (charids,))

    def remove_empty_sets(self):
        """
        Remove sets that don't include any character.
        """
        for set_name in self.get_set_list():
            if self.get_n_characters(set_name) == 0:
                self.remove_set(set_name)

    def to_xml(self):
        """
        Converts collection to XML.

        @rtype: str
        """
        s = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        s += "<character-collection>\n"

        for set_name in self.get_set_list():
            s += "<set name=\"%s\">\n" % set_name

            for character in self.get_characters(set_name):
                s += "  <character>\n"

                utf8 = character.get_utf8()
                if utf8:
                    s += "    <utf8>%s</utf8>\n" % utf8

                for line in character.get_writing().to_xml().split("\n"):
                    s += "    %s\n" % line
                
                s += "  </character>\n"

            s += "</set>\n"

        s += "</character-collection>\n"

        return s

    # XML processing...    

    def _start_element(self, name, attrs):
        self._tag = name

        if self._first_tag:
            self._first_tag = False
            if self._tag != "character-collection":
                raise ValueError, \
                      "The very first tag should be <character-collection>"

        if self._tag == "set":
            if not attrs.has_key("name"):
                raise ValueError, "<set> should have a name attribute"

            self._curr_set_name = attrs["name"].encode("UTF-8")
            self.add_set(self._curr_set_name)

        if self._tag == "character":
            self._curr_char = Character()
            self._curr_writing = self._curr_char.get_writing()
            self._curr_width = None
            self._curr_height = None
            self._curr_utf8 = None

        if self._tag == "stroke":
            self._curr_stroke = Stroke()
            
        elif self._tag == "point":
            point = Point()

            for key in ("x", "y", "pressure", "xtilt", "ytilt", "timestamp"):
                if attrs.has_key(key):
                    value = attrs[key].encode("UTF-8")
                    if key in ("pressure", "xtilt", "ytilt"):
                        value = float(value)
                    else:
                        value = int(float(value))
                else:
                    value = None

                setattr(point, key, value)

            self._curr_stroke.append_point(point)

    def _end_element(self, name):
        if name == "character-collection":
            for s in ["_tag", "_curr_char", "_curr_writing", "_curr_width",
                      "_curr_height", "_curr_utf8", "_curr_stroke",
                      "_curr_chars", "_curr_set_name"]:
                if s in self.__dict__:
                    del self.__dict__[s]
               
        if name == "character":
            if self._curr_utf8:
                self._curr_char.set_utf8(self._curr_utf8)
            if self._curr_width:
                self._curr_writing.set_width(self._curr_width)
            if self._curr_height:
                self._curr_writing.set_height(self._curr_height)
            self.append_character(self._curr_set_name, self._curr_char)

        if name == "stroke":
            if len(self._curr_stroke) > 0:
                self._curr_writing.append_stroke(self._curr_stroke)
            self._stroke = None

        self._tag = None

    def _char_data(self, data):
        if self._tag == "utf8":
            self._curr_utf8 = data.encode("UTF-8")
        if self._tag == "width":
            self._curr_width = int(data)
        elif self._tag == "height":
            self._curr_height = int(data)
