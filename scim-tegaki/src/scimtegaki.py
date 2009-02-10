# -*- coding: utf-8 -*-

# Copyright (C) 2009 Mathieu Blondel
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

import scim
import gobject
import gtk

from gettext import dgettext
_ = lambda a : dgettext ("scim-tegaki", a)
N_ = lambda x : x

from tegakigtk.recognizer import SmartRecognizerWidget

class TegakiHelper(scim.HelperAgent):

    def __init__(self, helper_info):
        self._helper_info = helper_info
        scim.HelperAgent.__init__(self)

    def run(self, uuid, config, display):
        self.config = config
        self._uuid = uuid
        self._display = display
        self._init_agent()
        self._create_ui()
        #self.load_config(config)
        gtk.main()
        self.config.flush()
        self.reload_config()
        self.close_connection()

    def _create_ui (self):
        self._window = gtk.Window()
        self._window.set_title("Tegaki")
        self._window.set_position(gtk.WIN_POS_CENTER)
        self._window.set_accept_focus(False)
        rw = SmartRecognizerWidget()
        self._window.add(rw)
        self._window.show_all()

        self._window.connect("destroy", self._on_destroy)
        rw.connect("commit-string", self._on_commit)

    def _on_destroy(self, window):
        gtk.main_quit()

    def _on_commit(self, widget, string):
        self.commit_string(-1, "", string)

    def _init_properties (self):
        prop = scim.Property("/Tegaki", _("Tegaki"),
                             self._helper_info[2],
                             _("Show/Hide Tegaki."))

        self.register_properties((prop, ))

    def _init_agent(self):
        fd = self.open_connection(self._helper_info,
                                  self._display)
        if fd >= 0:
            self._init_properties()

            condition = gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP
            gobject.io_add_watch(fd, condition, self.on_agent_event)

    def on_agent_event(self, fd, condition):
        if condition == gobject.IO_IN:
            while self.has_pending_event():
                self.filter_event()
            return True
        elif condition == gobject.IO_ERR or condition == gobject.IO_HUP:
            gtk.main_quit()
            return False
        
        return False

    def trigger_property(self, ic, uuid, prop):
        if prop == "/Tegaki":
            if self._window.get_property("visible"):
                self._xpos, self._ypos = self._window.get_position()
                self._window.hide()
            else:
                self._window.move(self._xpos, self._ypos)
                self._window.show()

if __name__ == "__main__":
    class CC:
        def __init__ (self):
            pass

        def read (self, name, v):
            return v
        def write (self, name, v):
            pass
        def flush(self):
            pass

    __UUID__ = "6937480c-e1a4-11dd-b959-080027da9e6f"
    helper_info = (__UUID__, "", "", "", 1)
    
    TegakiHelper(helper_info).run (__UUID__, CC(), ":0.0")