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

import os
from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError

import gtk
from gtk import gdk
import gobject

from canvas import Canvas
from chartable import CharTable

from tegaki.recognizer import Recognizer

class RecognizerWidgetBase(gtk.HBox):

    DEFAULT_CANVAS_WIDTH = 250

    __gsignals__ = {

        "commit-string" :         (gobject.SIGNAL_RUN_LAST, 
                                   gobject.TYPE_NONE,
                                   [gobject.TYPE_STRING])
    }

    def __init__(self):
        gtk.HBox.__init__(self)

        self._recognizer = None
        self._search_on_stroke = True

        self._create_ui()
        self.clear_canvas()
        self.clear_characters()

        self._load_preferences()

    def _load_preferences(self):
        pm = PreferenceManager()
        pm.load()
        self.set_drawing_stopped_time(pm["GENERAL"]["DRAWING_STOPPED_TIME"])
        self.set_search_on_stroke(pm["GENERAL"]["SEARCH_ON_STROKE"])
        self.set_selected_model(pm["GENERAL"]["SELECTED_MODEL"])
        self.set_draw_annotations(pm["GENERAL"]["DRAW_ANNOTATIONS"])

    def _save_preferences(self):
        pm = PreferenceManager()
        pm["GENERAL"]["DRAWING_STOPPED_TIME"] = self.get_drawing_stopped_time()
        pm["GENERAL"]["SEARCH_ON_STROKE"] = self.get_search_on_stroke()
        pm["GENERAL"]["SELECTED_MODEL"] = self.get_selected_model()
        pm["GENERAL"]["DRAW_ANNOTATIONS"] = self.get_draw_annotations()
        pm.save()

    def _create_toolbar_separator(self):
        self._toolbar.pack_start(gtk.HSeparator(), expand=False)

    def _create_clear_button(self):
        self._clear_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
        self._clear_button.set_image(image)
        self._clear_button.connect("clicked", self._on_clear)
        self._toolbar.pack_start(self._clear_button, expand=False)

    def _create_find_button(self):
        self._find_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON)
        self._find_button.set_image(image)
        self._find_button.connect("clicked", self._on_find)
        self._toolbar.pack_start(self._find_button, expand=False)

    def _create_undo_button(self):
        self._undo_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_UNDO, gtk.ICON_SIZE_BUTTON)
        self._undo_button.set_image(image)
        self._undo_button.connect("clicked", self._on_undo)
        self._toolbar.pack_start(self._undo_button, expand=False)

    def _create_prefs_button(self):
        self._prefs_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_PREFERENCES,
                                         gtk.ICON_SIZE_BUTTON)
        self._prefs_button.set_image(image)
        self._prefs_button.connect("clicked", self._on_prefs)
        self._toolbar.pack_start(self._prefs_button, expand=False)

    def _create_models_button(self):
        self._models_button = gtk.Button("Models")
        self._models_button.connect("button-press-event", self._on_models)
        self._toolbar.pack_start(self._models_button, expand=False)

    def _create_model_menu(self):
        menu = gtk.Menu()

        all_models = Recognizer.get_all_available_models()

        if len(all_models) == 0:
            return None

        i = 0
        for r_name, model_name, meta in all_models:
            item = gtk.MenuItem("%d. %s (%s)" % (i+1, model_name, r_name))
            item.connect("activate", self._on_activate_model, i)
            menu.append(item)
            i += 1

        return menu

    def _create_canvas(self, canvas_name):
        canvas = Canvas()
        canvas.set_size_request(self.DEFAULT_CANVAS_WIDTH,
                                self.DEFAULT_CANVAS_WIDTH)

        canvas.connect("button-press-event",
                       self._on_canvas_button_press,
                       canvas_name)

        canvas.connect("drawing-stopped",
                       self._on_canvas_drawing_stopped,
                       canvas_name)

        canvas.connect("stroke-added",
                       self._on_canvas_stroke_added,
                       canvas_name)

        setattr(self, canvas_name, canvas)

        frame = gtk.Frame()
        frame.add(canvas)

        setattr(self, canvas_name + "_frame", frame)

    def _create_chartable(self):    
        self._chartable_frame = gtk.Frame()
        self._chartable = CharTable()
        self._chartable_frame.add(self._chartable)

        self._chartable.connect("character-selected", 
                                self._on_character_selected)

    def _on_models(self, button, event):
        menu = self._create_model_menu()
        if menu:
            menu.show_all()
            menu.popup(None, None, None, event.button, event.time)
        else:
            parent = self.get_toplevel()
            msg = "No recognizers and/or no models installed!"
            dialog = ErrorDialog(parent, msg).run()

    def _on_activate_model(self, item, i):
        self.set_selected_model(i)
        self._save_preferences()

    def _on_find(self, button):
        self.find()

    def _on_undo(self, button):
        self.revert_stroke()

    def _on_prefs(self, button):
        parent = self.get_toplevel()
        if not parent.flags() & gtk.TOPLEVEL:
            parent = None
        pref_dialog = PreferenceDialog(parent)

        pref_dialog.connect("response", self._on_pref_validate)

        pref_dialog.set_search_on_stroke(self.get_search_on_stroke())
        pref_dialog.set_drawing_stopped_time(self.get_drawing_stopped_time())
        pref_dialog.set_draw_annotations(self.get_draw_annotations())

        pref_dialog.run()

    def _on_pref_validate(self, dialog, response):
        if response == gtk.RESPONSE_OK:
            if dialog.get_search_on_stroke():
                self.set_search_on_stroke(True)
            else:
                self.set_drawing_stopped_time(dialog.get_drawing_stopped_time())
            self.set_draw_annotations(dialog.get_draw_annotations())
            self._save_preferences()

        dialog.destroy()

    def _on_clear(self, button):
        self.clear_canvas()

    def clear_all(self):
        self.clear_characters()
        self.clear_canvas()

    def get_search_on_stroke(self):
        return self._search_on_stroke

    def set_search_on_stroke(self, enabled):
        self._search_on_stroke = enabled

    def get_characters(self):
        return self._chartable.get_characters()

    def get_selected_model(self):
       return self._models_button.selected_model

    def set_selected_model(self, i):
        try:
            r_name, model_name, meta = Recognizer.get_all_available_models()[i]

            klass = Recognizer.get_available_recognizers()[r_name]
            self._recognizer = klass()
            self._recognizer.set_model(meta["name"])
            self._models_button.set_label(meta["shortname"])
            # a hack to retain the model id the button
            self._models_button.selected_model = i

            self._ready = True
        except IndexError:
            self._ready = False

    def get_toolbar_vbox(self):
        return self._toolbar

class SimpleRecognizerWidget(RecognizerWidgetBase):

    def __init__(self):
        RecognizerWidgetBase.__init__(self)

    def _create_toolbar(self):
        self._toolbar = gtk.VBox(spacing=2)
        self._create_find_button()
        self._create_toolbar_separator()
        self._create_undo_button()
        self._create_clear_button()
        self._create_toolbar_separator()
        self._create_models_button()
        self._create_prefs_button()

    def _create_ui(self):
        self._create_canvasbox()
        self._create_chartable()

        vbox = gtk.VBox(spacing=2)
        vbox.pack_start(self._canvasbox, expand=True)
        vbox.pack_start(self._chartable_frame, expand=False)

        self._create_toolbar()
        self.set_spacing(2)
        self.pack_start(vbox, expand=True)
        self.pack_start(self._toolbar, expand=False)

    def _create_canvasbox(self):
        self._create_canvas("_canvas")
        self._canvasbox = self._canvas_frame  

    def _on_canvas_button_press(self, widget, event, curr_canv):
        pass
  
    def _on_canvas_drawing_stopped(self, widget, curr_canv):
        if not self._search_on_stroke:
            self.find()

    def _on_canvas_stroke_added(self, widget, curr_canv):
        if self._search_on_stroke:
            self.find()

    def _on_character_selected(self, chartable, event):
        chars = self._chartable.get_characters()
        selected = self._chartable.get_selected()
        self.emit("commit-string", chars[selected])

    def clear_canvas(self):
        self._canvas.clear()
        self.clear_characters()

    def clear_characters(self):
        self._chartable.clear() 

    def get_drawing_stopped_time(self):
        return self._canvas.get_drawing_stopped_time()

    def set_drawing_stopped_time(self, time_msec):
        self._search_on_stroke = False
        self._canvas.set_drawing_stopped_time(time_msec)

    def get_draw_annotations(self):
        return self._canvas.get_draw_annotations()

    def set_draw_annotations(self, active):
        self._canvas.set_draw_annotations(active)

    def revert_stroke(self):
        self._canvas.revert_stroke()
        if self._search_on_stroke:
            self.find()

    def find(self):
        if not self._ready:
            return

        writing = self._canvas.get_writing().copy()

        if writing.get_n_strokes() > 0:
            candidates = self._recognizer.recognize(writing, n=9)
            candidates = [char for char, prob in candidates]
            self._chartable.set_characters(candidates)

    def get_writing(self):
        self._canvas.get_writing()

    def set_writing(self, writing):
        self._canvas.set_writing(writing)

class SmartRecognizerWidget(RecognizerWidgetBase):

    OTHER_CANVAS_COLOR = (0xFFFF, 0xFFFF, 0xFFFF) 
    CURR_CANVAS_COLOR =  map(lambda x: x * 256, (255, 235, 235))

    def __init__(self):
        RecognizerWidgetBase.__init__(self)

    def _create_toolbar(self):
        self._toolbar = gtk.VBox(spacing=2)
        self._create_commit_button()
        self._create_del_button()
        self._create_toolbar_separator()
        self._create_find_button()
        self._create_toolbar_separator()
        self._create_undo_button()
        self._create_clear_button()
        self._create_toolbar_separator()
        self._create_models_button()
        self._create_prefs_button()

    def _create_commit_button(self):
        self._commit_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON)
        self._commit_button.set_image(image)
        self._commit_button.connect("clicked", self._on_commit)
        self._toolbar.pack_start(self._commit_button, expand=False)

    def _create_del_button(self):
        self._del_button = gtk.Button("Del")
        self._del_button.connect("clicked", self._on_delete)
        self._toolbar.pack_start(self._del_button, expand=False)

    def _create_ui(self):
        self._create_canvasbox()
        self._create_chartable()

        vbox = gtk.VBox(spacing=2)
        vbox.pack_start(self._chartable_frame, expand=False)
        vbox.pack_start(self._canvasbox, expand=True)

        self._create_toolbar()
        self.set_spacing(2)
        self.pack_start(vbox, expand=True)
        self.pack_start(self._toolbar, expand=False)

    def _create_canvasbox(self):
        self._canvasbox = gtk.HBox(spacing=2)
        self._create_canvas("_canvas1")
        self._create_canvas("_canvas2")
        self._canvasbox.pack_start(self._canvas1_frame)
        self._canvasbox.pack_start(self._canvas2_frame)

    def _find(self, canvas):
        if not self._ready:
            return

        writing = getattr(self, canvas).get_writing()

        if writing.get_n_strokes() == 0:
            return

        writing = writing.copy()
        candidates = self._recognizer.recognize(writing)
        candidates = [char for char, prob in candidates]     
        
        if candidates:
            candidate_list = CandidateList(candidates)

            if canvas == self._last_completed_canvas:
                # update the current character if the same canvas was used
                last = len(self.get_characters()) - 1
                self.replace_character(last, candidate_list)
                self._writings[last] = writing
            else:
                # append character otherwise
                self.add_character(candidate_list)
                self._writings.append(writing)

        self._last_completed_canvas = canvas

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
        for canvas, color in ((curr_canv, self.CURR_CANVAS_COLOR),
                            (othr_canv, self.OTHER_CANVAS_COLOR)):

            getattr(self, canvas).set_background_color(*color)

    def _on_canvas_button_press(self, widget, event, curr_canv):
        othr_canv = self._other_canvas(curr_canv)

        if self._focused_canvas == othr_canv:
            getattr(self, curr_canv).clear()

            if getattr(self, othr_canv).get_writing().get_n_strokes() > 0 and \
               self._last_completed_canvas != othr_canv and \
               not self._search_on_stroke:

                self._find(othr_canv)

        self._set_canvas_focus(curr_canv)
  
    def _on_canvas_drawing_stopped(self, widget, curr_canv):
        if self._focused_canvas == curr_canv and not self._search_on_stroke:
            self._find(curr_canv)

    def _on_canvas_stroke_added(self, widget, curr_canv):
        if self._search_on_stroke:
            self._find(curr_canv)

    def _on_commit(self, button):
        chars = self.get_selected_characters()
        if len(chars) > 0:
            self.clear_all()
            self.emit("commit-string", "".join(chars))

    def _on_delete(self, button):
        self.delete_character()

    def _on_character_selected(self, chartable, event):
        selected = self._chartable.get_selected()

        candidates = self._characters[selected]
        popup = CandidatePopup(candidates)
        popup.move(int(event.x_root), int(event.y_root) + \
                    int(self._chartable.allocation.height/3))


        popup.connect("character-selected", self._on_candidate_selected)
        popup.connect("hide", self._on_popup_close)
        popup.connect("edit-character", self._on_edit_character)
        popup.connect("delete-character", self._on_delete_character)

        popup.popup()

    def _on_candidate_selected(self, popup, event):
        char_selected = self._chartable.get_selected()
        cand_selected = popup.get_selected()
        self._characters[char_selected].selected = cand_selected
        self._chartable.set_characters(self.get_selected_characters())
        self._chartable.unselect()
       
    def _on_edit_character(self, popup):
        char_selected = self._chartable.get_selected()
        edit_window = gtk.Window()
        edit_window.set_title("Edit character")
        rw = SimpleRecognizerWidget()
        rw.set_writing(self._writings[char_selected])
        edit_window.add(rw)

        parent = self.get_toplevel()
        if parent.flags() & gtk.TOPLEVEL:
            edit_window.set_transient_for(parent)
            edit_window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            edit_window.set_type_hint(gdk.WINDOW_TYPE_HINT_DIALOG)
        edit_window.set_modal(True)
       
        rw.connect("commit-string", self._on_commit_edited_char, char_selected)
        
        edit_window.show_all()

    def _on_commit_edited_char(self, rw, char, char_selected):
        candidate_list = CandidateList(rw.get_characters())
        candidate_list.set_selected(char)
        self.replace_character(char_selected, candidate_list)
        rw.get_parent().destroy()

    def _on_delete_character(self, popup):
        char_selected = self._chartable.get_selected()
        self.remove_character(char_selected)

    def _on_popup_close(self, popup):
        self._chartable.unselect()

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

    def add_character(self, candidate_list):
        if len(candidate_list) > 0:
            self._characters.append(candidate_list)
            self._chartable.set_characters(self.get_selected_characters())

    def replace_character(self, index, candidate_list):
        if len(candidate_list) > 0:
            try:
                self._characters[index] = candidate_list
                self._chartable.set_characters(self.get_selected_characters())
            except IndexError:
                pass

    def remove_character(self, index):
        length = len(self._chartable.get_characters())
        if length > 0 and index <= length - 1:
            del self._characters[index]
            del self._writings[index]
            self._chartable.set_characters(self.get_selected_characters())    
       
    def get_selected_characters(self):
        return [char[char.selected] for char in self._characters]

    def get_drawing_stopped_time(self):
        return self._canvas1.get_drawing_stopped_time()

    def set_drawing_stopped_time(self, time_msec):
        self._search_on_stroke = False
        for canvas in (self._canvas1, self._canvas2):
            canvas.set_drawing_stopped_time(time_msec)

    def get_draw_annotations(self):
        return self._canvas1.get_draw_annotations()

    def set_draw_annotations(self, active):
        for canvas in (self._canvas1, self._canvas2):
            canvas.set_draw_annotations(active)

    def revert_stroke(self):
        if self._focused_canvas:
            getattr(self, self._focused_canvas).revert_stroke()

    def find(self):
        if self._focused_canvas:
            self._find(self._focused_canvas)

class CandidatePopup(gtk.Window):

    __gsignals__ = {

        "character_selected" : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                [gobject.TYPE_PYOBJECT]),

        "edit-character"     : (gobject.SIGNAL_RUN_LAST, 
                                gobject.TYPE_NONE,
                                []),

        "delete-character"   : (gobject.SIGNAL_RUN_LAST, 
                                gobject.TYPE_NONE,
                                [])
    }

    def __init__(self, candidates):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self._candidates = candidates
        self._create_ui()

    def get_selected(self):
        return self._chartable.get_selected()

    def _create_ui(self):
        self.add_events(gdk.BUTTON_PRESS_MASK)

        self.set_title("Candidates")

        frame = gtk.Frame()
        self._chartable = CharTable()
        self._chartable.add_events(gdk.BUTTON_PRESS_MASK)
        self._chartable.set_characters(self._candidates)
        self._chartable.set_layout(CharTable.LAYOUT_HORIZONTAL)
        max_width, max_height = self._chartable.get_max_char_size()
        self._chartable.set_size_request(int(max_width*3.5),
                                         int(max_height*3.5))
        frame.add(self._chartable)

        self.connect("button-press-event", self._on_button_press)
        self._chartable.connect("character-selected",
                                self._on_character_selected)

        vbox = gtk.VBox(spacing=2)
        vbox.pack_start(frame)

        self._edit_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_EDIT,
                                         gtk.ICON_SIZE_BUTTON)
        self._edit_button.set_image(image)
        self._edit_button.set_relief(gtk.RELIEF_NONE)
        self._edit_button.connect("clicked", self._on_edit)

        self._delete_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_DELETE,
                                         gtk.ICON_SIZE_BUTTON)
        self._delete_button.set_image(image)
        self._delete_button.set_relief(gtk.RELIEF_NONE)
        self._delete_button.connect("clicked", self._on_delete)

        self._close_button = gtk.Button()
        image = gtk.image_new_from_stock(gtk.STOCK_CLOSE,
                                         gtk.ICON_SIZE_BUTTON)
        self._close_button.set_image(image)
        self._close_button.set_relief(gtk.RELIEF_NONE)
        self._close_button.connect("clicked", self._on_close)

        frame = gtk.Frame()
        buttonbox = gtk.HBox()
        buttonbox.pack_start(self._edit_button, expand=False)
        buttonbox.pack_start(self._delete_button, expand=False)
        buttonbox.pack_start(self._close_button, expand=False)
        frame.add(buttonbox)
        vbox.pack_start(frame)

        self.add(vbox)

    def _on_close(self, button):
        self.popdown()

    def _on_edit(self, button):
        self.emit("edit-character")
        self.popdown()

    def _on_delete(self, button):
        self.emit("delete-character")
        self.popdown()

    def _on_character_selected(self, chartable, event):
        self.emit("character-selected", event)

    def _on_button_press(self, window, event):
        # If we're clicking outside of the window or in the chartable
        # close the popup
        if (event.window != self.window or
            (tuple(self.allocation.intersect(
                   gdk.Rectangle(x=int(event.x), y=int(event.y),
                                 width=1, height=1)))) == (0, 0, 0, 0)):
            self.popdown()

    def popup(self):
        self.show_all()

        # grab pointer
        self.grab_add()
        gdk.pointer_grab(self.window,
                         True,
                         gdk.BUTTON_PRESS_MASK|
                         gdk.BUTTON_RELEASE_MASK|
                         gdk.POINTER_MOTION_MASK,
                         None, None, 
                         gtk.get_current_event_time())

    def popdown(self):
        gdk.pointer_ungrab(gtk.get_current_event_time())
        self.grab_remove()
        self.destroy()

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

class ErrorDialog(gtk.MessageDialog):

    def __init__(self, parent, msg):
        gtk.MessageDialog.__init__(self, parent, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)

        self.connect("response", lambda w,r: self.destroy())

class PreferenceManager(dict):

    def __init__(self):
        dict.__init__(self)
        self._init_paths()
        self._init_dirs()
        self._init_defaults()

    def _init_defaults(self):
        self["GENERAL"] = {}

    def _init_paths(self):
        try:
            self._home_dir = os.environ['HOME']
            self._tegaki_dir = os.path.join(self._home_dir, ".tegaki")
        except KeyError:
            self._home_dir = os.environ['USERPROFILE']
            self._tegaki_dir = os.path.join(self._home_dir, "tegaki")

        self._conf_file = os.path.join(self._tegaki_dir, "recognizer.ini")

    def _init_dirs(self):
        if not os.path.exists(self._tegaki_dir):
            os.makedirs(self._tegaki_dir)

    def load(self):
        config = SafeConfigParser()
        config.read(self._conf_file)

        for opt, dflt, meth  in [("SEARCH_ON_STROKE", True, config.getboolean),
                                 ("DRAWING_STOPPED_TIME", 0, config.getint),
                                 ("SELECTED_MODEL", 0, config.getint),
                                 ("DRAW_ANNOTATIONS", 1, config.getboolean)]:

            try:
                self["GENERAL"][opt] = meth("GENERAL", opt)
            except (NoSectionError, NoOptionError, ValueError), e:
                self["GENERAL"][opt] = dflt

    def save(self):
        config = SafeConfigParser()
        
        for section in self.keys():
            if not config.has_section(section):
                config.add_section(section)

            for opt, value in self[section].items():
                config.set(section, opt, str(value))

        f = open(self._conf_file, "w")
        config.write(f)
        f.close()

class PreferenceDialog(gtk.Dialog):

    def __init__(self, parent):
        gtk.Dialog.__init__(self)
        self._init_dialog(parent)
        self._create_ui()

    def _init_dialog(self, parent):
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.set_default_response(gtk.RESPONSE_OK)
        self.set_has_separator(True)
        self.set_transient_for(parent)
        self.set_border_width(6)
        self.set_modal(True)
        self.set_title("Preferences")

    def _create_ui(self):
        self._search_on_stroke = gtk.RadioButton(group=None, 
                                                 label="Search on stroke")
        self._search_on_stroke.connect("toggled", self._on_search_on_stroke)

        
        self._search_after = gtk.RadioButton(group=self._search_on_stroke,
                                             label="Search after:")
        self._search_after.connect("toggled", self._on_search_after)
        adjustment = gtk.Adjustment(value=0, lower=0, upper=3000, step_incr=100,
                                    page_incr=0, page_size=0)
        self._spinbutton = gtk.SpinButton(adjustment)
        self._spinbutton.set_sensitive(False)
        self._search_after_hbox = gtk.HBox(spacing=2)
        self._search_after_hbox.pack_start(self._search_after, expand=False)
        self._search_after_hbox.pack_start(self._spinbutton, expand=False)
        self._search_after_hbox.pack_start(gtk.Label("[msecs]"), expand=False)

        self._draw_annotations = gtk.CheckButton(label="Draw annotations")

        main_vbox = self.get_child()
        main_vbox.set_spacing(10)
        main_vbox.pack_start(self._search_on_stroke)
        main_vbox.pack_start(self._search_after_hbox)
        main_vbox.pack_start(self._draw_annotations)
        self.show_all()

    def _on_search_on_stroke(self, radiobutton):
        self._spinbutton.set_sensitive(False)

    def _on_search_after(self, radiobutton):
        self._spinbutton.set_sensitive(True)

    def get_search_on_stroke(self):
        return self._search_on_stroke.get_active()

    def set_search_on_stroke(self, active):
        self._search_on_stroke.set_active(active)
        self._search_after.set_active(not(active))

    def get_draw_annotations(self):
        return self._draw_annotations.get_active()

    def set_draw_annotations(self, active):
        self._draw_annotations.set_active(active)

    def get_search_after(self):
        return self._search_after.get_active()

    def set_search_after(self, active):
        self._search_after.set_active(active)
        self._search_on_stroke.set_active(not(active))

    def get_drawing_stopped_time(self):
        return int(self._spinbutton.get_value())

    def set_drawing_stopped_time(self, time):
        self._spinbutton.set_value(int(time))

if __name__ == "__main__":
    import sys

    try:
        simple = int(sys.argv[1])
    except IndexError:
        simple = False

    window = gtk.Window()

    if simple:
        recognizer_widget = SimpleRecognizerWidget()
    else:
        recognizer_widget = SmartRecognizerWidget()

    def on_commit_string(rw, string):
        print string

    recognizer_widget.connect("commit-string", on_commit_string)

    window.add(recognizer_widget)
    window.show_all()

    gtk.main()