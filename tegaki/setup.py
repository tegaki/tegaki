# -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.sysconfig import get_config_var
import os

# Please run
# python setup.py install   

print get_config_var("prefix")

setup(
    name = 'tegaki',
    description = 'Tegaki library',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://tegaki.sourceforge.net',
    version = '0.1',
    license='GPL',
    packages = ['tegaki'],
    package_dir = {'tegaki':'tegaki/'}
)