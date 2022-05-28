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

# Contributors to this file:
# - Mathieu Blondel

import sys
import os
import scim

from gettext import dgettext
_ = lambda a : dgettext ("scim-tegaki", a)

__UUID__ = "6937480c-e1a4-11dd-b959-080027da9e6f"
__NAME__ = _("Tegaki")

# Fixme: dont't hardcode icon path
__ICON__ = ""
for path in ("/usr/local/share/tegaki/icons", "/usr/share/tegaki/icons"):
    path = os.path.join(path, "handwriting.png")
    if os.path.exists(path):
        __ICON__ = path
        break

__DESC__ = _("Tegaki helper")
__OPT__ = scim.SCIM_HELPER_STAND_ALONE | scim.SCIM_HELPER_NEED_SCREEN_INFO

helper_info = (__UUID__, __NAME__, __ICON__, __DESC__, __OPT__)

def get_info ():
    return helper_info

def run_helper (uuid, config, display):
    if uuid != __UUID__:
        return
    display_arg = "--display=%s" % display
    sys.argv.append (display_arg)
    from . import scimtegaki
    scimtegaki.TegakiHelper(helper_info).run(uuid, config, display)