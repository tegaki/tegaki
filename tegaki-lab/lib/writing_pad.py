# -*- coding: utf-8 -*-

# Copyright (C) 2008 Mathieu Blondel
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

import gtk
import os
from tegakigtk.canvas import Canvas

class WritingPad(object):

    def canvas_clear(self, clear_button, data=None):
        self.canvas.clear()
        self.clear_label()

    def canvas_undo(self, save_button, data=None):
        writing = self.canvas.get_writing()
        if writing.get_n_strokes() > 0:
            self.canvas.revert_stroke()

    def canvas_find(self, save_button, data=None):
        writing = self.canvas.get_writing()

        self.clear_label()

        if self.find_method:
            res = self.find_method(writing)

            if res:
                text = " ".join(res)
                self.label.set_text(text)

    def canvas_set_writing(self, writing):
        self.canvas.set_writing(writing)

    def clear_label(self):
        self.label.set_text("")

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def __init__(self, find_method=None):
        self.find_method = find_method
        
        # window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(10)
        self.window.set_resizable(False)

        # find button
        self.find_button = gtk.Button(stock=gtk.STOCK_FIND)
        self.find_button.connect("clicked", self.canvas_find)

        # undo button
        self.undo_button = gtk.Button(stock=gtk.STOCK_UNDO)
        self.undo_button.connect("clicked", self.canvas_undo)

        # clear button
        self.clear_button = gtk.Button(stock=gtk.STOCK_CLEAR)
        self.clear_button.connect("clicked", self.canvas_clear)

        # vbox
        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.find_button)
        self.vbox.pack_start(self.undo_button)
        self.vbox.pack_start(self.clear_button)

        # canvas
        self.canvas = Canvas()
        self.canvas.set_size_request(300, 300)

        # hbox
        self.hbox = gtk.HBox(spacing=5)
        self.hbox.pack_start(self.canvas, expand=False)
        self.hbox.pack_start(self.vbox, expand=False)

        # result label
        self.label = gtk.Label()

        # final vbox
        self.fvbox = gtk.VBox(spacing=3)
        self.fvbox.pack_start(self.hbox)
        self.fvbox.pack_start(gtk.HSeparator())
        self.fvbox.pack_start(self.label)

        self.window.add(self.fvbox)
        self.window.show_all()

    def run(self):
        gtk.main()

