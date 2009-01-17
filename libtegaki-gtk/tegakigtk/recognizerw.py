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
from gtk import gdk
import gobject

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

    __gsignals__ = {
        "writing-completed" :     (gobject.SIGNAL_RUN_LAST, 
                                   gobject.TYPE_NONE,
                                   [gobject.TYPE_PYOBJECT]),

        "commit-string" :         (gobject.SIGNAL_RUN_LAST, 
                                   gobject.TYPE_NONE,
                                   [gobject.TYPE_STRING])
    }

    MODE_ONE_CANVAS = 0
    MODE_TWO_CANVAS = 1

    def __init__(self, mode=MODE_TWO_CANVAS):
        gtk.HBox.__init__(self)

        self._candidate_popup = None

        self._mode = mode

        self._create_ui()
        self.clear_canvas()
        self.clear_characters()

    def clear_canvas(self):
        self._canvas1.clear()
            
        if self._canvas2:
            self._canvas2.clear()
        
        self._focused_canvas = None
        self._last_completed_canvas = None

    def delete_character(self):
        try:
            self._characters.pop()
            self._chartable.set_characters(self.get_selected_characters())

            if self._last_completed_canvas:
                getattr(self, self._last_completed_canvas).clear()
        except IndexError:
            pass

    def clear_characters(self):
        self._characters = []
        self._chartable.clear() 

    def clear_all(self):
        self.clear_characters()
        self.clear_canvas()

    def add_character(self, candidate_list):
        if len(candidate_list) > 0:
            self._characters.append(CandidateList(candidate_list))
            self._chartable.set_characters(self.get_selected_characters())
        

    def get_selected_characters(self):
        return [char[char.selected] for char in self._characters]

    def set_drawing_stopped_time(self, time_msec):
        for canvas in (self._canvas1, self._canvas2):
            if canvas:
                canvas.set_drawing_stopped_time(time_msec)

    def revert_stroke(self):
        if self._focused_canvas:
            getattr(self, self._focused_canvas).revert_stroke()

    def _create_candidate_popup(self, characters):
        # FIXME: real popup windows are faster and don't appear
        # in the window manager but they don't respond to the focus-out event.
        # See gdk.pointer_grab
        # self._candidate_popup = gtk.Window(gtk.WINDOW_POPUP)
        self._candidate_popup = gtk.Window()
        self._candidate_popup.set_decorated(False)
        self._candidate_popup.set_title("Candidates")

        frame = gtk.Frame()
        candidate_table = CharTable()
        candidate_table.set_layout(CharTable.LAYOUT_HORIZONTAL)
        candidate_table.set_characters(characters)
        candidate_table.set_size_request(100, 100)
        frame.add(candidate_table)
        self._candidate_popup.add(frame)

        candidate_table.connect("character-selected",
                                self._on_candidate_selected)

        self._candidate_popup.connect("focus-out-event",
                                      self._on_popup_focus_out)

    def _hide_popup(self):
        if self._candidate_popup:
            self._candidate_popup.destroy()
            self._candidate_popup = None

    def _on_popup_focus_out(self, popup, event):
        self._hide_popup()

    def _on_candidate_selected(self, candidate_table, event):
        char_selected = self._chartable.get_selected()
        cand_selected = candidate_table.get_selected()
        self._characters[char_selected].selected = cand_selected
        self._chartable.set_characters(self.get_selected_characters())
        self._candidate_popup.destroy()
        self._candidate_popup = None

    def _create_ui(self):
        self._create_canvasbox()

        frame = gtk.Frame()
        self._chartable = CharTable()
        frame.add(self._chartable)

        self._chartable.connect("character-selected", 
                                self._on_character_selected)

        vbox = gtk.VBox(spacing=2)
        vbox.pack_start(frame, expand=False)
        vbox.pack_start(self._canvasbox, expand=True)

        self._create_toolbar() 
       
        self.set_spacing(2)
        self.pack_start(vbox, expand=True)
        self.pack_start(self._toolbar, expand=False)

        self.connect("destroy", self._on_destroy)

    def _create_canvasbox(self):
        

        self._canvas1 = Canvas()
        self._canvas1.set_size_request(250, 250)


        self._canvas1.connect("button-press-event",
                              self._on_canvas_button_press,
                              "_canvas1")

        self._canvas1.connect("drawing-stopped",
                              self._on_canvas_drawing_stopped,
                              "_canvas1")

        frame = gtk.Frame()
        frame.add(self._canvas1)

        if self._mode == RecognizerWidget.MODE_ONE_CANVAS:
            self._canvasbox = frame
            self._canvas2 = None
        elif self._mode == RecognizerWidget.MODE_TWO_CANVAS:

            self._canvasbox = gtk.HBox(spacing=2)


            self._canvasbox.pack_start(frame)

            self._canvas2 = Canvas()
            self._canvas2.set_size_request(250, 250)

            self._canvas2.connect("button-press-event",
                                self._on_canvas_button_press,
                                "_canvas2")

            self._canvas2.connect("drawing-stopped",
                                self._on_canvas_drawing_stopped,
                                "_canvas2")


            frame = gtk.Frame()
            frame.add(self._canvas2)
            self._canvasbox.pack_start(frame)

    def _create_toolbar(self):
        self._del_button = gtk.Button("Del")
        self._del_button.connect("clicked", self._on_delete)

        self._commit_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON)
        self._commit_button.set_image(image)
        self._commit_button.connect("clicked", self._on_commit)

        self._clear_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
        self._clear_button.set_image(image)
        self._clear_button.connect("clicked", self._on_clear)

        self._find_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON)
        self._find_button.set_image(image)
        self._find_button.connect("clicked", self._on_find)

        self._undo_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_UNDO, gtk.ICON_SIZE_BUTTON)
        self._undo_button.set_image(image)
        self._undo_button.connect("clicked", self._on_undo)

        self._prefs_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_PREFERENCES,
                                         gtk.ICON_SIZE_BUTTON)
        self._prefs_button.set_image(image)
        self._prefs_button.connect("clicked", self._on_prefs)

        self._toolbar = gtk.VBox(spacing=2)
        self._toolbar.pack_start(self._commit_button, expand=False)
        self._toolbar.pack_start(self._del_button, expand=False)
        self._toolbar.pack_start(gtk.HSeparator(), expand=False)
        self._toolbar.pack_start(self._find_button, expand=False)
        self._toolbar.pack_start(gtk.HSeparator(), expand=False)
        self._toolbar.pack_start(self._undo_button, expand=False)
        self._toolbar.pack_start(self._clear_button, expand=False)
        self._toolbar.pack_start(gtk.HSeparator(), expand=False)
        self._toolbar.pack_start(self._prefs_button, expand=False)

    def _on_canvas_button_press(self, widget, event, curr_canv):
        if curr_canv == "_canvas1":
            othr_canv = "_canvas2"
        elif curr_canv == "_canvas2":
            othr_canv = "_canvas1"
        else:
            return

        if self._focused_canvas == othr_canv:
            getattr(self, curr_canv).clear()

            if getattr(self, othr_canv).get_writing().get_n_strokes() > 0 and \
               self._last_completed_canvas != othr_canv:

                self.emit("writing-completed", 
                          getattr(self, othr_canv).get_writing())

                self._last_completed_canvas = othr_canv

        self._focused_canvas = curr_canv
   

    def _on_canvas_drawing_stopped(self, widget, curr_canv):
        if self._focused_canvas == curr_canv:
            self.emit("writing-completed", 
                      getattr(self, curr_canv).get_writing())
            self._last_completed_canvas = curr_canv


    def _on_find(self, button):
        if self._focused_canvas:
            self.emit("writing-completed", 
                      getattr(self, self._focused_canvas).get_writing())
            self._last_completed_canvas = self._focused_canvas            

    def _on_undo(self, button):
        self.revert_stroke()

    def _on_prefs(self, button):
        pass

    def _on_commit(self, button):
        chars = self.get_selected_characters()
        self.clear_all()
        if len(chars) > 0:
            self.emit("commit-string", "".join(chars))

    def _on_clear(self, button):
        self.clear_canvas()

    def _on_delete(self, button):
        self.delete_character()

    def _on_character_selected(self, chartable, event):
        selected = self._chartable.get_selected()
        candidates = self._characters[selected][0:9]
        self._create_candidate_popup(candidates)
        self._candidate_popup.move(int(event.x_root), int(event.y_root) + \
                                   int(self._chartable.allocation.height/2))
        self._candidate_popup.show_all()   

    def _on_destroy(self, event):
        self._hide_popup()

if __name__ == "__main__":
    import sys

    try:
        msec = int(sys.argv[1])
    except IndexError:
        msec = 0

    try:
        hide = int(sys.argv[2])
    except IndexError:
        hide = False

    window = gtk.Window()

    if hide:
        recognizer_widget = RecognizerWidget(RecognizerWidget.MODE_ONE_CANVAS)
    else:
        recognizer_widget = RecognizerWidget(RecognizerWidget.MODE_TWO_CANVAS)

    recognizer_widget.set_drawing_stopped_time(msec)

    from tegaki.recognizer import ZinniaRecognizer

    recognizer = ZinniaRecognizer()

    def on_writing_completed(rw, writing):
        res = recognizer.recognize("handwriting-ja", writing, 9)
        rw.add_character([char for char, prob in res])

    def on_commit_string(rw, string):
        print string

    recognizer_widget.connect("writing-completed", on_writing_completed)
    recognizer_widget.connect("commit-string", on_commit_string)

    window.add(recognizer_widget)
    window.show_all()

    gtk.main()