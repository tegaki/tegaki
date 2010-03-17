# -*- coding: utf-8 -*-

# Copyright (C) 2010 The Tegaki project contributors
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

import gobject
import gtk

import ibus

from tegakigtk.recognizer import SmartRecognizerWidget

class Engine(ibus.EngineBase):

    def __init__(self, bus, object_path):
        super(Engine, self).__init__(bus, object_path)

    def process_key_event(self, keyval, keycode, state):
        # ignore key release events
        # (key events should be handled directly in SmartRecognizerWidget)
        return False

    def enable(self):
        self._window = gtk.Window()
        self._window.set_title("Tegaki")
        self._window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self._window.set_accept_focus(False)
        rw = SmartRecognizerWidget()
        self._window.add(rw)

        self._window.show_all()

        self._window.connect("delete-event", self._on_close)
        rw.connect("commit-string", self._on_commit)

    def disable(self):
        if self._window:
            self._window.destroy()
            self._window = None

    def reset(self):
        pass

    def property_activate(self, prop_name):
        pass

    def _on_close(self, *args):
        self.disable()

    def _on_commit(self, widget, string):
        self.commit_text(ibus.Text(string))

