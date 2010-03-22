# -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.command.install import install as installbase
import os
import sys
from glob import glob

def getversion():
    currdir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(currdir, "bin", "tegaki-recognize")
    import re
    regexp = re.compile(r"VERSION = '([^']*)'")
    f = open(path)
    buf = f.read()
    f.close()
    return regexp.search(buf).group(1)

def load_file(filename):
    f = open(filename)
    ret = f.read()
    f.close()
    return ret

def save_file(filename, txt):
    f = open(filename, "w")
    f.write(txt)
    f.close()

class install(installbase):
    def run(self):
        installbase.run(self)
        self._write_file("tegaki-recognize.in", 
                         os.path.join("share", "menu"),
                         0644)
        self._write_file("tegaki-recognize.desktop.in", 
                         os.path.join("share", "applications"),
                         0644)

    def _write_file(self, filename, folder, mode):
        txt = load_file(filename)
        txt = self._replace_prefix(txt)
        outdir = os.path.join(self._getprefix(), folder)
        out = os.path.join(outdir, filename.replace(".in", ""))
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        print "Writing", out
        save_file(out, txt)
        os.chmod(out, mode)

    def _replace_prefix(self, txt):
        return txt.replace("@PREFIX", self._getprefix())       

    def _getprefix(self):
        try:
            # >= 2.6
            if self.prefix_option is None:
                return "/usr/local"
            else:
                return self.prefix_option
        except AttributeError:
            # < 2.6
            return self.prefix

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
                             includes="gtk,atk,pangocairo,cairo,gio,tegaki,tegaki.trainer,tegaki.recognizer,tegakigtk,zinnia,wagomu,tegaki.arrayutils")),
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
    data_files=[('share/pixmaps/', glob("data/icons/*.svg"))],
    cmdclass={'install':install}
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
