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

import gtk
from gtk import gdk
from tegakigtk.renderers import WritingImageRenderer 

class _WritingPixbufRenderer(WritingImageRenderer):

    def get_pixbuf(self):
        w, h = self.surface.get_width(), self.surface.get_height()
        pixmap = gdk.Pixmap(None, w, h, 24)
        cr = pixmap.cairo_create()
        cr.set_source_surface(self.surface, 0, 0)
        cr.paint ()
        pixbuf = gtk.gdk.Pixbuf (gdk.COLORSPACE_RGB, True, 8, w, h)
        pixbuf = pixbuf.get_from_drawable(pixmap,
                                          gdk.colormap_get_system(), 
                                          0, 0, 0, 0, w, h)
        return pixbuf

class WritingIconView(gtk.IconView):

    def __init__(self):
        self._model = gtk.ListStore(gdk.Pixbuf, str)
        gtk.IconView.__init__(self, self._model)
        self.set_selection_mode(gtk.SELECTION_SINGLE)
        self.set_reorderable(False)
        self.set_pixbuf_column(0)
        self.set_text_column(1)
        self.set_item_width(100)

    def set_writings(self, writings):
        """
        writings: a list of tegaki.Writing objects.
        """
        self._model.clear()
        characters = []
        for writing in writings:
            char = Character()
            char.set_writing(writing)
            char.set_utf8("?")
            characters.append(char)
        self.set_characters(characters)

    def set_characters(self, characters):
        """
        characters: a list of tegaki.Character objects.
        """
        self._model.clear()
        for char in characters:
            writing = char.get_writing()
            renderer = _WritingPixbufRenderer(writing, 
                                              self.get_item_width(),
                                              self.get_item_width())
            renderer.set_draw_annotations(False)
            renderer.draw_background()
            renderer.draw_border()
            #renderer.draw_axis()
            renderer.draw_writing()
            self._model.append((renderer.get_pixbuf(), char.get_utf8()))

    def show_icon_text(self):
        self.set_text_column(1)

    def hide_icon_text(self):
        self.set_text_column(-1)

if __name__ == "__main__":
    import sys
    from glob import glob
    import os.path

    from tegaki.character import Character

    folder = sys.argv[1] # a folder contains XML character files

    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_default_size(500, 500)
    iconview = WritingIconView()
    scrolledwindow = gtk.ScrolledWindow()
    scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  
    characters = []
    for path in glob(os.path.join(folder, "*.xml")):
        char = Character()
        char.read(path)
        characters.append(char)

    iconview.set_item_width(80)
    iconview.set_characters(characters)
    iconview.hide_icon_text()

    scrolledwindow.add(iconview)
    window.add(scrolledwindow)
    window.show_all()

    gtk.main()