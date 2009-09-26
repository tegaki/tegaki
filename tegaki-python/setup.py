# -*- coding: utf-8 -*-

from distutils.core import setup
import os

def getversion():
    currdir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(currdir, "tegaki", "__init__.py")
    import re
    regexp = re.compile(r"VERSION = '([^']*)'")
    f = open(path)
    buf = f.read()
    f.close()
    return regexp.search(buf).group(1)

# Please run
# python setup.py install  

setup(
    name = 'tegaki-python',
    description = 'Tegaki Python library',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://www.tegaki.org',
    version = getversion(),
    license='GPL',
    packages = ['tegaki', 'tegaki.engines'],
    package_dir = {'tegaki':'tegaki', 'tegaki.engines':'tegaki/engines'}
)