# -*- coding: utf-8 -*-

from distutils.core import setup
import os

def getversion():
    currdir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(currdir, "tegakigtk", "__init__.py")
    import re
    regexp = re.compile(r"VERSION = '([^']*)'")
    f = open(path)
    buf = f.read()
    f.close()
    return regexp.search(buf).group(1)

# Please run
# python setup.py install   

setup(
    name = 'tegaki-gtk',
    description = 'Tegaki GTK library',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://tegaki.sourceforge.net',
    version = getversion(),
    license='GPL',
    packages = ['tegakigtk'],
    package_dir = {'tegakigtk':'tegakigtk/'},
    data_files=[('share/tegaki/icons/', ['data/tegaki/icons/handwriting.png'])]
)