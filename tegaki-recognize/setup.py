# -*- coding: utf-8 -*-

from distutils.core import setup
import os
import sys

def getversion():
    currdir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(currdir, "bin", "tegaki-recognize")
    import re
    regexp = re.compile(r"VERSION = '([^']*)'")
    f = open(path)
    buf = f.read()
    f.close()
    return regexp.search(buf).group(1)

# Please run
# python setup.py install   

mainscript = 'bin/tegaki-recognize'

if sys.platform == 'darwin' and "py2app" in sys.argv[1:]:
    import py2app

    extra_options = dict(
    setup_requires=['py2app'],
    app=[mainscript + ".py"],
    # Cross-platform applications generally expect sys.argv to
    # be used for opening files.
    options=dict(py2app=dict(argv_emulation=True,
                             site_packages=True,
                             iconfile="data/icons/tegaki-recognize.icns",
                             includes="gtk,atk,pangocairo,cairo,gio,tegaki,tegaki.trainer,tegaki.recognizer,tegakigtk,zinnia")),
    )
elif sys.platform == 'win32' and "py2exe" in sys.argv[1:]:
    import py2exe
    
    extra_options = dict(
    setup_requires=['py2exe'],
    windows=[{'script' : mainscript,
                  'icon_resources': [(0x0004, 'data/icons/tegaki-recognize.ico')]},],
    options=dict(py2exe=dict(
                                   compressed=1,
                                   optimize=2, 
                                   bundle_files=3,
                                   includes="gtk,atk,pangocairo,cairo,tegaki,tegaki.trainer,tegaki.recognizer,tegakigtk,zinnia,tegaki.arrayutils,tegaki.engines,wagomu")),
    )
else:
    extra_options = dict(
    # Normally unix-like platforms will use "setup.py install"
    # and install the main script as such
    scripts=[mainscript],
     )


setup(
    name = 'tegaki-recognize',
    description = 'Tegaki integration in the desktop',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://www.tegaki.org',
    version = getversion(),
    license='GPL',
    **extra_options
)
