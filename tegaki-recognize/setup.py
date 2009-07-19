# -*- coding: utf-8 -*-

from distutils.core import setup
import os

def getversion():
    currdir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(currdir, "bin", "tegaki-recognize")
    import re
    regexp = re.compile(r"VERSION = '([^']*)'")
    f = open(path)
    buf = f.read()
    f.close()
    return regexp.search(buf).group(1)

# Please run
# python setup.py install   

setup(
    name = 'tegaki-recognize',
    description = 'Tegaki integration in the desktop',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://www.tegaki.org',
    version = getversion(),
    license='GPL',
    scripts = ['bin/tegaki-recognize'],
)