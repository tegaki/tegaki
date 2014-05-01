# -*- coding: utf-8 -*-

import os
import re
import subprocess
import platform
from distutils.core import setup, Extension

def getversion():
    currdir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(currdir, "tegakiwagomu.py")
    import re
    regexp = re.compile(r"VERSION = '([^']*)'")
    f = open(path)
    buf = f.read()
    f.close()
    return regexp.search(buf).group(1)

def pkg_config(package, option):
    sub = subprocess.Popen(["pkg-config",option,package],
                           stdout=subprocess.PIPE)
    spaces = re.compile('\s+',re.DOTALL)
    args = spaces.split(sub.stdout.read().strip())
    sub.stdout.close()
    sub.wait()
    return [a[2:] for a in args]

if platform.system() in ["Darwin", "OpenBSD", "Windows"]:
    macros = []
elif platform.system() in ["NetBSD", "FreeBSD", "DragonFly"]:
    macros = [("HAVE_POSIX_MEMALIGN", None)]
else:
    macros = [("HAVE_MEMALIGN", None)]
    

setup(
    name="tegaki-wagomu",
    description = 'Simple handwriting recognition engine based on DTW',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://www.tegaki.org',
    version = getversion(),
    license='GPL',
    py_modules=['wagomu'],
    ext_modules=[Extension("_wagomu",
                           ["wagomu.i","wagomu.cpp"],
                           include_dirs = pkg_config('glib-2.0','--cflags'),
                           libraries = pkg_config('glib-2.0','--libs'),
                           define_macros=macros,
                           #library_dirs = pkg_config('glib-2.0','--libs'),
                           swig_opts=['-c++'])],

    data_files=[('share/tegaki/engines', ['tegakiwagomu.py'])]
)
