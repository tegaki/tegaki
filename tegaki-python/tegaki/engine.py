# -*- coding: utf-8 -*-

# Copyright (C) 2009 The Tegaki project contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import platform

from tegaki.dictutils import SortedDict

class Engine(object):
    """
    Base class for Recognizer and Trainer.
    """

    @classmethod
    def _get_search_path(cls, what):
        """
        Return a list of search path.  

        @typ what: str
        @param what: "models" or "engines"
        """
        libdir = os.path.dirname(os.path.abspath(__file__))

        try:
            # UNIX
            homedir = os.environ['HOME']
            homeengines = os.path.join(homedir, ".tegaki", what)
        except KeyError:
            # Windows
            homedir = os.environ['USERPROFILE']
            homeengines = os.path.join(homedir, "tegaki", what)

        search_path = [# For Unix
                       "/usr/local/share/tegaki/%s/" % what,
                       "/usr/share/tegaki/%s/" % what,
                       # for Maemo
                       "/media/mmc1/tegaki/%s/" % what,
                       "/media/mmc2/tegaki/%s/" % what,
                       # personal directory
                       homeengines,
                       # lib dir
                       os.path.join(libdir, what)]

        # For Windows
        try:
            search_path += [os.path.join(os.environ["APPDATA"], "tegaki",
                                         what),
                            r"C:\Python25\share\tegaki\%s" % what,
                            r"C:\Python26\share\tegaki\%s" % what]
        except KeyError:
            pass

        # For OSX
        if platform.system() == "Darwin":
            search_path += [os.path.join(homedir, "Library", 
                                         "Application Support", "tegaki", what),
                            os.path.join("/Library", "Application Support",
                                         "tegaki", what)]

        try:
            env = {"engines": "TEGAKI_ENGINE_PATH", 
                   "models" : "TEGAKI_MODEL_PATH"}[what]

            if env in os.environ and \
               os.environ[env].strip() != "":
                search_path += os.environ[env].strip().split(os.path.pathsep)

        except KeyError:
            pass

        return search_path

    @classmethod
    def read_meta_file(cls, meta_file):
        """
        Read a .meta file.

        @type meta_file: str
        @param meta_file: meta file file to read

        @rtype: dict
        """
        f = open(meta_file)
        ret = SortedDict()
        for line in f.readlines():
            try:
                key, value = [s.strip() for s in line.strip().split("=")]
                ret[key] = value
            except ValueError:
                continue
        f.close()
        return ret
