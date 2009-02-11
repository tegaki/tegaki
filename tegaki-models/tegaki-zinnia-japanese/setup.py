# -*- coding: utf-8 -*-

from distutils.core import setup

# Please run
# python setup.py install  

setup(
    name = 'tegaki-zinnia-japanese',
    description = 'Japanese handwriting model for Zinnia',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://tegaki.sourceforge.net',
    version = '0.1',
    license='LGPL',
    data_files=[('share/tegaki/models/zinnia/',
                 ['handwriting-ja.model', 'handwriting-ja.meta'])]
)