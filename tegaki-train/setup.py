# -*- coding: utf-8 -*-

from distutils.core import setup
import os

def getversion():
    currdir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(currdir, "bin", "tegaki-train")
    import re
    regexp = re.compile(r"VERSION = '([^']*)'")
    f = open(path)
    buf = f.read()
    f.close()
    return regexp.search(buf).group(1)

# Please run
# python setup.py install   

setup(
    name = 'tegaki-train',
    description = 'Train Tegaki with your own handwriting',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://tegaki.sourceforge.net',
    version = getversion(),
    license='GPL',
    scripts = ['bin/tegaki-train'],
)