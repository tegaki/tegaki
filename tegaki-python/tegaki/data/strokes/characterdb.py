#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Exports a stroke table from characterdb.cjklib.org and prints a CSV list to
stdout.

Copyright (c) 2008, 2010, Christoph Burgmer

Released unter the MIT License.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import urllib
import codecs
import sys
import re

QUERY_URL = ("http://characterdb.cjklib.org/wiki/Special:Ask/"
             "%(query)s/%(properties)s/format=csv/sep=,/headers=hide/"
             "limit=%(limit)d/offset=%(offset)d")
"""Basic query URL."""

MAX_ENTRIES = 500
"""Maximum entries per GET request."""

#class AppURLopener(urllib.FancyURLopener):
    #version="Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"

#urllib._urlopener = AppURLopener()

def strokeorder_entry_preparator(entryList):
    columns = ['glyph', 'strokeorder']
    entry_dict = dict(zip(columns, entryList))

    character, glyph_index = entry_dict['glyph'].split('/', 1)
    if 'strokeorder' in entry_dict:
        return [(character, ' '.join(entry_dict['strokeorder'].strip('"')))]
    else:
        return []

DATA_SETS = {
             'ja': ({'query': '[[Category:Glyph]] [[Locale::J]] [[StrokeOrderForms::!]] [[StrokeOrderForms::!~*span*]]',
                     'properties': ['StrokeOrderForms']},
                    strokeorder_entry_preparator),
             'zh_CN': ({'query': '[[Category:Glyph]] [[Locale::C]] [[StrokeOrderForms::!]] [[StrokeOrderForms::!~*span*]]',
                        'properties': ['StrokeOrderForms']},
                       strokeorder_entry_preparator),
             'zh_TW': ({'query': '[[Category:Glyph]] [[Locale::T]] [[StrokeOrderForms::!]] [[StrokeOrderForms::!~*span*]]',
                        'properties': ['StrokeOrderForms']},
                       strokeorder_entry_preparator),
            }
"""Defined download sets."""

def get_data_set_iterator(name):
    try:
        parameter, preparator_func = DATA_SETS[name]
    except KeyError:
        raise ValueError("Unknown data set %r" % name)

    parameter = parameter.copy()
    if 'properties' in parameter:
        parameter['properties'] = '/'.join(('?' + prop) for prop
                                           in parameter['properties'])

    codec_reader = codecs.getreader('UTF-8')
    run = 0
    while True:
        query_dict = {'offset': run * MAX_ENTRIES, 'limit': MAX_ENTRIES}
        query_dict.update(parameter)

        query = QUERY_URL % query_dict
        query = urllib.quote(query, safe='/:=').replace('%', '-')
        f = codec_reader(urllib.urlopen(query))

        line_count = 0
        line = f.readline()
        while line:
            line = line.rstrip('\n')
            entry = re.findall(r'"[^"]+"|[^,]+', line)
            if preparator_func:
                for e in preparator_func(entry):
                    yield e
            else:
                yield entry

            line_count += 1
            line = f.readline()

        f.close()
        if line_count < MAX_ENTRIES:
            break
        run += 1


def main():
    if len(sys.argv) != 2:
        print """usage: python characterdb.py LANG
Exports a list of stroke orders from characterdb.cjklib.org and prints a
CSV list to stdout.

Available languages:"""
        print "\n".join(('  ' + name) for name in DATA_SETS.keys())
        sys.exit(1)

    for a in get_data_set_iterator(sys.argv[1]):
        print '\t'.join(cell for cell in a).encode('utf8')


if __name__ == "__main__":
    main()
