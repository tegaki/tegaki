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

import gtk
from canvas import Canvas
from chartable import CharTable

class CandidateList(list):
    def __init__(self, initial_candidates=[]):
        self.extend(initial_candidates)
        self.selected = 0

    def get_selected(self):
        try:
            return self[self.selected]
        except IndexError:
            return None

    def set_selected(self, name):
        try:
            i = self.index(name)
            self.selected = i
        except ValueError:
            pass

class RecognizerWidget(gtk.HBox):

    def __init__(self):
        gtk.HBox.__init__(self)
        self._candidate_popup = None
        self._create_ui()
        self.clear()

    def clear(self):
        self._canvas1.clear()
        self._canvas2.clear()
        self._characters = []
        self._chartable.clear()

    def add_character(self, candidate_list):
        if len(candidate_list) > 0:
            self._characters.append(candidate_list)
            self._chartable.set_characters(self._get_selected_characters())

    def _get_selected_characters(self):
        return [char[char.selected] for char in self._characters]

    def _create_candidate_popup(self, characters):
        if self._candidate_popup:
            self._candidate_popup.destroy()

        self._candidate_popup = gtk.Window(gtk.WINDOW_POPUP)

        frame = gtk.Frame()
        candidate_table = CharTable()
        candidate_table.set_layout(CharTable.LAYOUT_HORIZONTAL)
        candidate_table.set_characters(characters)
        candidate_table.set_size_request(100, 100)
        frame.add(candidate_table)
        self._candidate_popup.add(frame)

        candidate_table.connect("character-selected",
                                self._on_candidate_selected)


        self._candidate_popup

    def _on_candidate_selected(self, candidate_table, event):
        char_selected = self._chartable.get_selected()
        cand_selected = candidate_table.get_selected()
        self._characters[char_selected].selected = cand_selected
        self._chartable.set_characters(self._get_selected_characters())
        self._candidate_popup.destroy()
        self._candidate_popup = None

    def _create_ui(self):
        hbox = gtk.HBox(spacing=2)

        self._canvas1 = Canvas()
        self._canvas1.set_size_request(250, 250)
        self._canvas2 = Canvas()
        self._canvas2.set_size_request(250, 250)

        self._canvas1.connect("stroke-added", self._on_canvas1_stroke_added)
        self._canvas2.connect("stroke-added", self._on_canvas2_stroke_added)

        frame = gtk.Frame()
        frame.add(self._canvas1)
        hbox.pack_start(frame)

        frame = gtk.Frame()
        frame.add(self._canvas2)
        hbox.pack_start(frame)

        frame = gtk.Frame()
        self._chartable = CharTable()
        frame.add(self._chartable)

        self._chartable.connect("character-selected", 
                                self._on_character_selected)

        vbox = gtk.VBox(spacing=2)
        vbox.pack_start(frame, expand=False)
        vbox.pack_start(hbox, expand=True)

        self._add_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        self._add_button.set_image(image)
        self._add_button.connect("clicked", self._on_add)

        self._clear_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
        self._clear_button.set_image(image)
        self._clear_button.connect("clicked", self._on_clear)

        vbox2 = gtk.VBox()
        vbox2.pack_start(self._add_button, expand=False)
        vbox2.pack_start(self._clear_button, expand=False)

        self.pack_start(vbox, expand=True)
        self.pack_start(vbox2, expand=False)

        self.connect("destroy", self._on_destroy)

    def _on_canvas1_stroke_added(self, canvas):
        self._canvas2.clear()
    
    def _on_canvas2_stroke_added(self, canvas):
        self._canvas1.clear()

    def _on_add(self, button):
        candidate_list = CandidateList(["あ", "い","う", "え", "お", 
                                        "か", "き", "く", "け", "こ",
                                        "さ", "し", "す", "せ", "そ"])
        self.add_character(candidate_list)

    def _on_clear(self, button):
        self.clear()

    def _on_character_selected(self, chartable, event):
        selected = self._chartable.get_selected()
        candidates = self._characters[selected][0:9]
        self._create_candidate_popup(candidates)
        self._candidate_popup.move(int(event.x_root), int(event.y_root))
        self._candidate_popup.show_all()        

    def _on_destroy(self, event):
        if self._candidate_popup:
            self._candidate_popup.destroy()


if __name__ == "__main__":
    window = gtk.Window()
    recognizer_widget = RecognizerWidget()
    window.add(recognizer_widget)
    window.show_all()

    gtk.main()