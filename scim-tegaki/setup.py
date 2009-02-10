# -*- coding: utf-8 -*-

from distutils.core import setup
import os

# Please run
# python setup.py install   

setup(
    name = 'scimtegaki',
    description = 'Tegaki integration in SCIM',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://tegaki.sourceforge.net',
    version = '0.1',
    license='GPL',
    data_files=[('share/scim-python/helper/tegaki/',
                 ['src/__init__.py', 'src/scimtegaki.py'])]

)