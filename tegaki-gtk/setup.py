# -*- coding: utf-8 -*-

from distutils.core import setup
import os

# Please run
# python setup.py install   

setup(
    name = 'tegaki-gtk',
    description = 'Tegaki GTK library',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://tegaki.sourceforge.net',
    version = '0.1',
    license='GPL',
    packages = ['tegakigtk'],
    package_dir = {'tegakigtk':'tegakigtk/'},
    data_files=[('share/tegaki/icons/', ['data/tegaki/icons/handwriting.png'])]
)