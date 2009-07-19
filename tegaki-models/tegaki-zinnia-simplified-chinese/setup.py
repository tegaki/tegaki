# -*- coding: utf-8 -*-

from distutils.core import setup

# Please run
# python setup.py install  

setup(
    name = 'tegaki-zinnia-simplified-chinese',
    description = 'Simplified Chinese handwriting model for Zinnia',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://www.tegaki.org',
    version = '0.2',
    license='LGPL',
    data_files=[('share/tegaki/models/zinnia/',
                 ['handwriting-zh_CN.model', 'handwriting-zh_CN.meta'])]
)