# -*- coding: utf-8 -*-

import os
import re
import subprocess
from distutils.core import setup, Extension

VERSION = "0.3"

def pkg_config(package, option):
    sub = subprocess.Popen(["pkg-config",option,package],
                           stdout=subprocess.PIPE)
    spaces = re.compile('\s+',re.DOTALL)
    args = spaces.split(sub.stdout.read().strip())
    sub.stdout.close()
    sub.wait()
    return [a[2:] for a in args]

setup(
    name="tegaki-gifenc",
    description = 'GIF encoder for Tegaki',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://www.tegaki.org',
    version = VERSION,
    license='GPL',
    py_modules=['tegakigifenc'],
    ext_modules=[Extension("_tegakigifenc",
                           ["tegakigifenc.i","tegakigifenc.cpp",
                            "gifenc/gifenc.c", "gifenc/quantize.c"],
                           include_dirs = pkg_config('gtk+-2.0','--cflags'),
                           libraries = pkg_config('gtk+-2.0','--libs'),
                           #library_dirs = pkg_config('glib-2.0','--libs'),
                           swig_opts=['-c++'])],

)