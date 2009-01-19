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

from tegaki.recognizer import Recognizer

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

        "commit-string" :         (gobject.SIGNAL_RUN_LAST, 
                                   gobject.TYPE_NONE,
                                   [gobject.TYPE_STRING])
    }

    MODE_ONE_CANVAS = 0
    MODE_TWO_CANVAS = 1

    OTHER_CANVAS_COLOR = (0xFFFF, 0xFFFF, 0xFFFF) 
    CURR_CANVAS_COLOR =  map(lambda x: x * 256, (255, 235, 235))

    def __init__(self, mode=MODE_TWO_CANVAS):
        gtk.HBox.__init__(self)

        self._candidate_popup = None

        self._mode = mode

        self._recognizer = None

        self._create_ui()
        self.clear_canvas()
        self.clear_characters()

        self._activate_first_model()

    def clear_canvas(self):
        self._canvas1.clear()
            
        if self._canvas2:
            self._canvas2.clear()
        
        self._set_canvas_focus("_canvas1")
        self._last_completed_canvas = None

    def delete_character(self):
        try:
            self._characters.pop()
            self._writings.pop()
            self._chartable.set_characters(self.get_selected_characters())
            self._chartable.unselect()
        except IndexError:
            pass

    def clear_characters(self):
        self._characters = []
        self._writings = []
        self._chartable.clear() 

    def clear_all(self):
        self.clear_characters()
        self.clear_canvas()

    def add_character(self, candidate_list):
        if len(candidate_list) > 0:
            self._characters.append(CandidateList(candidate_list))
            self._chartable.set_characters(self.get_selected_characters())

    def replace_character(self, index, candidate_list):
        if len(candidate_list) > 0:
            try:
                self._characters[index] = CandidateList(candidate_list)
                self._chartable.set_characters(self.get_selected_characters())
            except IndexError:
                pass
        

    def get_selected_characters(self):
        return [char[char.selected] for char in self._characters]

    def set_drawing_stopped_time(self, time_msec):
        for canvas in (self._canvas1, self._canvas2):
            if canvas:
                canvas.set_drawing_stopped_time(time_msec)

    def revert_stroke(self):
        if self._focused_canvas:
            getattr(self, self._focused_canvas).revert_stroke()

            if self._chartable.get_selected():
                self._writing_completed(self._focused_canvas, unselect=False)

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
        candidate_table.set_size_request(100, 110)
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
        self._chartable.unselect()

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

        self._models_button = gtk.Button("Models")
        self._models_button.connect("button-press-event", self.on_models)

        self._toolbar = gtk.VBox(spacing=2)
        self._toolbar.pack_start(self._commit_button, expand=False)
        self._toolbar.pack_start(self._del_button, expand=False)
        self._toolbar.pack_start(gtk.HSeparator(), expand=False)
        self._toolbar.pack_start(self._find_button, expand=False)
        self._toolbar.pack_start(gtk.HSeparator(), expand=False)
        self._toolbar.pack_start(self._undo_button, expand=False)
        self._toolbar.pack_start(self._clear_button, expand=False)
        self._toolbar.pack_start(gtk.HSeparator(), expand=False)
        self._toolbar.pack_start(self._models_button, expand=False)
        self._toolbar.pack_start(self._prefs_button, expand=False)

    def _create_model_menu(self):
        menu = gtk.Menu()

        for r_name, klass in Recognizer.get_available_recognizers().items():
            recognizer = klass()

            i = 1
            for model_name, meta in klass.get_available_models().items():
                item = gtk.MenuItem("%d. %s (%s)" % (i, model_name, r_name))
                item.connect("activate", 
                             self._on_activate_model, 
                             r_name,
                             meta)
                menu.append(item)
                i += 1

        return menu

    def _activate_first_model(self):
        r_name, klass = Recognizer.get_available_recognizers().items()[0]
        model_name, meta = klass.get_available_models().items()[0]
        self._set_recognizer(r_name, meta)

    def _on_activate_model(self, item, recognizer_name, meta):
        self._set_recognizer(recognizer_name, meta) 

    def _set_recognizer(self, recognizer_name, meta):
        klass = Recognizer.get_available_recognizers()[recognizer_name]
        self._recognizer = klass()
        self._recognizer.set_model(meta["name"])
        self._models_button.set_label(meta["shortname"])

    def _writing_completed(self, canvas, unselect=True):
            writing = getattr(self, canvas).get_writing()

            if writing.get_n_strokes() == 0:
                return

            writing = writing.copy()
            candidates = self._recognizer.recognize(writing)
            candidates = [char for char, prob in candidates]
    
            self._last_completed_canvas = canvas     

            if candidates:
                sel_char = self._chartable.get_selected()

                if sel_char is not None:
                    self.replace_character(sel_char, candidates)
                    self._writings[sel_char] = writing

                    if unselect:
                        self._chartable.unselect()
                else:
                    self.add_character(candidates)
                    self._writings.append(writing)

    def _other_canvas(self, canvas):
        if canvas == "_canvas1":
            othr_canv = "_canvas2"
        else:
            othr_canv = "_canvas1"
        return othr_canv
    
    def _set_canvas_focus(self, curr_canv):
        othr_canv = self._other_canvas(curr_canv)
        self._focused_canvas = curr_canv

        # set background color
        if self._canvas2:
            for canvas, color in ((curr_canv, self.CURR_CANVAS_COLOR),
                                  (othr_canv, self.OTHER_CANVAS_COLOR)):

                getattr(self, canvas).set_background_color(*color)

    def _on_canvas_button_press(self, widget, event, curr_canv):
        othr_canv = self._other_canvas(curr_canv)

        if self._focused_canvas == othr_canv:
            getattr(self, curr_canv).clear()

            if getattr(self, othr_canv).get_writing().get_n_strokes() > 0 and \
               self._last_completed_canvas != othr_canv:

                self._writing_completed(othr_canv)

        self._set_canvas_focus(curr_canv)
  
    def _on_canvas_drawing_stopped(self, widget, curr_canv):
        if self._focused_canvas == curr_canv:
            self._writing_completed(curr_canv)

    def on_models(self, button, event):
        menu = self._create_model_menu()
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    def _on_find(self, button):
        if self._focused_canvas:
            self._writing_completed(self._focused_canvas)         

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

        if event.button == 3: # right click
            candidates = self._characters[selected]
            self._create_candidate_popup(candidates)
            self._candidate_popup.move(int(event.x_root), int(event.y_root) + \
                                       int(self._chartable.allocation.height/3))
            self._candidate_popup.show_all() 
        
        elif event.button == 1: # left click
            sel_writing = self._writings[selected]
            
            if self._canvas2:
                self._canvas2.clear()

            self._canvas1.set_writing(sel_writing)
            self._set_canvas_focus("_canvas1")

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

    def on_commit_string(rw, string):
        print string

    recognizer_widget.connect("commit-string", on_commit_string)

    window.add(recognizer_widget)
    window.show_all()

    gtk.main()