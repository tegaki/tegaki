# -*- coding: utf-8 -*-

import os
import re
import subprocess
from distutils.core import setup, Extension

def pkg_config(package, option):
    sub = subprocess.Popen(["pkg-config",option,package],
                           stdout=subprocess.PIPE)
    spaces = re.compile('\s+',re.DOTALL)
    args = spaces.split(sub.stdout.read().strip())
    sub.stdout.close()
    sub.wait()
    return [a[2:] for a in args]

setup(name="tegaki-wagomu",
      py_modules=['wagomu'],
      ext_modules=[Extension("_wagomu",
                             ["wagomu.i","wagomu.cpp"],
                             include_dirs = pkg_config('glib-2.0','--cflags'),
                             libraries = pkg_config('glib-2.0','--libs'),
                             #library_dirs = pkg_config('glib-2.0','--libs'),
                             swig_opts=['-c++'])],

      data_files=[('share/tegaki/engines/', ['tegakiwagomu.py'])]
)