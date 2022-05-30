# vim:set et sts=4 sw=4:
#
# ibus-tmpl - The Input Bus template project
#
# Copyright (c) 2007-2008 Huang Peng <shawn.p.huang@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import ibus
from . import engine


class EngineFactory(ibus.EngineFactoryBase):
    def __init__(self, bus):
        self.__bus = bus
        super(EngineFactory, self).__init__(self.__bus)

        self.__id = 0

    def create_engine(self, engine_name):
        print(engine_name)
        if engine_name == "tegaki":
            self.__id += 1
            return engine.Engine(self.__bus, "%s/%d" % \
                ("/org/freedesktop/IBus/Tegaki/Engine", self.__id))

        return super(EngineFactory, self).create_engine(engine_name)

