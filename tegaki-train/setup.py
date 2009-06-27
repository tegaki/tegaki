# -*- coding: utf-8 -*-

from distutils.core import setup
import os

# Please run
# python setup.py install   

setup(
    name = 'tegaki-train',
    description = 'Train Tegaki with your own handwriting',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://tegaki.sourceforge.net',
    version = '0.1',
    license='GPL',
    scripts = ['bin/tegaki-train'],
)