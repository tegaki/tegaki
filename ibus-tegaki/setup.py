# -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.command.install import install as installbase
import os
import sys
from glob import glob

import engine

def load_file(filename):
    f = open(filename)
    ret = f.read()
    f.close()
    return ret

def save_file(filename, txt):
    f = open(filename, "w")
    f.write(txt)
    f.close()

def replace_constants(txt):
    for cst in dir(engine):
        if cst.upper() == cst: # only constants
            cstvalue = getattr(engine, cst)
            txt = txt.replace("@"+cst, cstvalue)
    return txt

class install(installbase):
    def run(self):
        installbase.run(self)
        self._write_file("tegaki.xml.in", 
                         os.path.join("share", "ibus", "component"),
                         0644)
        self._write_file("ibus-engine-tegaki.in", 
                         os.path.join("lib", "ibus-tegaki"),
                         0755)

    def _write_file(self, filename, folder, mode):
        txt = load_file(filename)
        txt = replace_constants(self._replace_prefix(txt))
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
        if self.prefix_option is None:
            return "/usr/local"
        else:
            return self.prefix_option
            

# Please run
# python setup.py install  

setup(
    name = 'ibus-tegaki',
    description = 'Tegaki integration in ibus',
    author = 'Mathieu Blondel',
    author_email = 'mathieu ÂT mblondel DÔT org',
    url = 'http://www.tegaki.org',
    version = engine.VERSION,
    license='GPL',
    data_files=[('share/ibus-tegaki/engine', glob("engine/*.py")),
                ('share/ibus-tegaki/icons', glob("*.svg"))],
    cmdclass={'install':install}
)