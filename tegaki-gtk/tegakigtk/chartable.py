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
import gobject
import pango
import math
import time

from tegaki.character import *

class CharTable(gtk.Widget):
    """
    A nifty character table.

    A port of Takuro Ashie's TomoeCharTable to pygtk.
    """

    LAYOUT_SINGLE_HORIZONTAL = 0
    LAYOUT_SINGLE_VERTICAL = 1
    LAYOUT_HORIZONTAL = 2
    LAYOUT_VERTICAL = 3

    DEFAULT_FONT_SCALE = 2.0 #pango.SCALE_XX_LARGE

    __gsignals__ = {
        "character_selected" : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                [gobject.TYPE_PYOBJECT])
    }
    
    def __init__(self):
        gtk.Widget.__init__(self)

        self._pixmap = None

        self._padding = 2
        self._selected = None
        self._prelighted = None
        self._layout = self.LAYOUT_SINGLE_HORIZONTAL

        self._h_adj = None
        self._v_adj = None

        self.clear()

        self.connect("motion_notify_event", self.motion_notify_event)
        
    # Events...

    def do_realize(self):
        """
        Called when the widget should create all of its
        windowing resources.  We will create our gtk.gdk.Window.
        """
        # Set an internal flag telling that we're realized
        self.set_flags(self.flags() | gtk.REALIZED)

        # Create a new gdk.Window which we can draw on.
        # Also say that we want to receive exposure events
        # and button click and button press events
        self.window = gdk.Window(self.get_parent_window(),

                                 x=self.allocation.x,
                                 y=self.allocation.y,
                                 width=self.allocation.width,
                                 height=self.allocation.height,

                                 window_type=gdk.WINDOW_CHILD,
                                 wclass=gdk.INPUT_OUTPUT,
                                 visual=self.get_visual(),
                                 colormap=self.get_colormap(),

                                 event_mask=gdk.EXPOSURE_MASK |
                                            gdk.BUTTON_PRESS_MASK |
                                            gdk.BUTTON_RELEASE_MASK |
                                            gdk.POINTER_MOTION_MASK |
                                            gdk.POINTER_MOTION_HINT_MASK |
                                            gdk.ENTER_NOTIFY_MASK |
                                            gdk.LEAVE_NOTIFY_MASK)


        # Associate the gdk.Window with ourselves, Gtk+ needs a reference
        # between the widget and the gdk window
        self.window.set_user_data(self)

        # Attach the style to the gdk.Window, a style contains colors and
        # GC contextes used for drawing
        self.style.attach(self.window)

        # The default color of the background should be what
        # the style (theme engine) tells us.
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)

        # Font
        font_desc = self.style.font_desc.copy()
        size = font_desc.get_size()
        font_desc.set_size(int(size * self.DEFAULT_FONT_SCALE))
        self.modify_font(font_desc)

    def do_unrealize(self):
        """
        The do_unrealized method is responsible for freeing the GDK resources
        De-associate the window we created in do_realize with ourselves
        """
        self.window.destroy()
    
    def do_size_request(self, requisition):
        """
        The do_size_request method Gtk+ is called on a widget to ask it the
        widget how large it wishes to be.
        It's not guaranteed that gtk+ will actually give this size to the
        widget.
        """
        self.ensure_style()
        context = self.get_pango_context()
        metrics = context.get_metrics(self.style.font_desc,
                                      context.get_language())

        # width
        char_width = metrics.get_approximate_char_width()
        digit_width = metrics.get_approximate_digit_width()
        char_pixels = pango.PIXELS(int(max(char_width, digit_width) *
                                        self.DEFAULT_FONT_SCALE))
        requisition.width = char_pixels + self._padding * 2

        # height
        ascent = metrics.get_ascent()
        descent = metrics.get_descent()
        requisition.height = pango.PIXELS(ascent + descent) + self._padding * 2

    def do_size_allocate(self, allocation):
        """
        The do_size_allocate is called when the actual
        size is known and the widget is told how much space
        could actually be allocated."""

        self.allocation = allocation
        self.width = self.allocation.width
        self.height = self.allocation.height        
 
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)
            
            self._pixmap = gdk.Pixmap(self.window,
                                      self.width,
                                      self.height)

            self.draw()

    def do_expose_event(self, event):
        """
        This is where the widget must draw itself.
        """
        retval = False
       
        if self.flags() & gtk.REALIZED and not self._pixmap:
            self._pixmap = gdk.Pixmap(self.window,
                                      self.allocation.width,
                                      self.allocation.height)

            self._adjust_adjustments()
            self.draw()

        if self._pixmap:
            self.window.draw_drawable(self.style.fg_gc[self.state],
                                     self._pixmap,
                                     event.area.x, event.area.y,
                                     event.area.x, event.area.y,
                                     event.area.width, event.area.height)

        return retval
    
    def motion_notify_event(self, widget, event):
        retval = False

        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state

        prev_prelighted = self._prelighted
        self._prelighted = self._get_char_id_from_coordinates(x, y)

        if prev_prelighted != self._prelighted:
            self.draw()

        return retval

    def do_button_press_event(self, event):
        retval = False

        prev_selected = self._selected
        self._selected = self._get_char_id_from_coordinates(event.x, event.y)

        if prev_selected != self._selected:
            self.draw()

        if self._selected >= 0:
            self.emit("character_selected", event)

        return retval

    def do_button_release_event(self, event):
        return False

    def get_max_char_size(self):
        context = self.get_pango_context()
        metrics = context.get_metrics(self.style.font_desc,
                                      context.get_language())

        # width
        char_width = metrics.get_approximate_char_width()
        digit_width = metrics.get_approximate_digit_width()
        max_char_width = pango.PIXELS(int(max(char_width, digit_width) *
                                           self.DEFAULT_FONT_SCALE))

        # height
        ascent = metrics.get_ascent()
        descent = metrics.get_descent()
        max_char_height = pango.PIXELS(int((ascent + descent) *
                                            self.DEFAULT_FONT_SCALE))

        return (max_char_width, max_char_height)

    def _get_char_frame_size(self):
        sizes = [layout.get_pixel_size() for layout in self._layouts]

        if len(sizes) > 0:
            inner_width = max([size[0] for size in sizes])
            inner_height = max([size[1] for size in sizes])
        else:
            inner_width, inner_height = self.get_max_char_size()

        outer_width = inner_width + 2 * self._padding
        outer_height = inner_height + 2 * self._padding

        return [inner_width, inner_height, outer_width, outer_height]



    def _get_char_id_from_coordinates(self, x, y):
        inner_width, inner_height, outer_width, outer_height = \
            self._get_char_frame_size()

        h_offset = 0; v_offset = 0

        if self._h_adj: h_offset = h_adj.get_value()
        if self._v_adj: v_offset = v_adj.get_value()

        # Calculate columns for horizontal layout
        cols = self.allocation.width / outer_width
        if cols <= 0: cols = 1

        # Calculate rows for vertical layout
        rows = self.allocation.height / outer_height
        if rows <= 0: rows = 1

        for i in range(len(self._layouts)):

            if self._layout == self.LAYOUT_SINGLE_HORIZONTAL:
                area_x = outer_width * i - h_offset

                if x >= area_x and x < area_x + outer_width:
                    return i

            elif self._layout == self.LAYOUT_SINGLE_VERTICAL:
                area_y = outer_height * i - v_offset

                if y >= area_y and y < area_y + outer_height:
                    return i

            elif self._layout == self.LAYOUT_HORIZONTAL:
                area_x = outer_width  * (i % cols) - h_offset
                area_y = outer_height * (i / cols) - v_offset

                if x >= area_x and x < area_x + outer_width and \
                   y >= area_y and y < area_y + outer_height:
                
                    return i

            elif self._layout == self.LAYOUT_VERTICAL:
                area_x = outer_width  * (i / rows) - h_offset
                area_y = outer_height * (i % rows) - v_offset

                if x >= area_x and x < area_x + outer_width and \
                    y >= area_y and y < area_y + outer_height:

                    return i

        return None

    def _adjust_adjustments(self):
        pass

    def draw(self):
        if not self._pixmap:
            return

        inner_width, inner_height, outer_width, outer_height = \
            self._get_char_frame_size()

        y_pos = (self.allocation.height - inner_height) / 2
        x_pos = (self.allocation.width - inner_width) / 2

        cols = self.allocation.width / outer_width
        if cols <= 0: cols = 1

        rows = self.allocation.height / outer_height
        if rows <= 0: rows = 1

        h_offset = 0; v_offset = 0

        if self._h_adj: h_offset = h_adj.get_value()
        if self._v_adj: v_offset = v_adj.get_value()

        # Fill background
        self._pixmap.draw_rectangle(self.style.white_gc,
                                    True,
                                    0, 0,
                                    self.allocation.width,
                                    self.allocation.height)

        # Draw characters
        for i in range(len(self._layouts)):
            layout = self._layouts[i]
            selected = i == self._selected
            char_width, char_height = layout.get_pixel_size()

           
            if self._layout == self.LAYOUT_SINGLE_HORIZONTAL:
                outer_x = outer_width * i - h_offset
                outer_y = 0
                outer_height = self.allocation.height
                inner_x = outer_x + (outer_width  - char_width)  / 2
                inner_y = y_pos

                if outer_x + outer_width < 0:
                    continue

                if outer_x + outer_width > self.allocation.width:
                    break

            elif self._layout == self.LAYOUT_SINGLE_VERTICAL:
                outer_x = 0
                outer_y = outer_height * i - v_offset
                outer_width = self.allocation.width
                inner_x = x_pos
                inner_y = outer_y + (outer_height - char_height) / 2

                if outer_y + outer_height < 0:
                    continue

                if outer_y + outer_height > self.allocation.height:
                    break

            elif self._layout == self.LAYOUT_HORIZONTAL:
                outer_x      = outer_width  * (i % cols) - h_offset
                outer_y      = outer_height * (i / cols) - v_offset
                inner_x      = outer_x + (outer_width  - char_width)  / 2
                inner_y      = outer_y + (outer_height - char_height) / 2

                if outer_y + outer_height < 0:
                    continue

                if outer_y + outer_height > self.allocation.height:
                    break

            elif self._layout == self.LAYOUT_VERTICAL:
                outer_x      = outer_width  * (i / rows) - h_offset
                outer_y      = outer_height * (i % rows) - v_offset
                inner_x      = outer_x + (outer_width  - char_width)  / 2
                inner_y      = outer_y + (outer_height - char_height) / 2

                if outer_x + outer_width < 0:
                    continue

                if outer_x + outer_width > self.allocation.width:
                    break

            if selected:
                outer_gc = self.style.bg_gc[gtk.STATE_SELECTED]
                inner_gc = self.style.white_gc
            else:
                outer_gc = self.style.white_gc
                inner_gc = self.style.black_gc

            self._pixmap.draw_rectangle(outer_gc,
                                        True,
                                        outer_x, outer_y,
                                        outer_width, outer_height)

            self._pixmap.draw_layout(inner_gc, 
                                     inner_x, inner_y,
                                     layout)

            if i == self._prelighted:
                # FIXME: doesn't seem to work
                self.style.paint_shadow(self.window,
                                        gtk.STATE_PRELIGHT, gtk.SHADOW_OUT,
                                        None, None, None,
                                        outer_x, outer_y,
                                        outer_width, outer_height)


        self.window.draw_drawable(self.style.fg_gc[self.state],
                                  self._pixmap,
                                  0, 0,
                                  0, 0,
                                  self.allocation.width, self.allocation.height)

    def set_characters(self, characters):
        self._layouts = []
        for character in characters:
            self._layouts.append(self.create_pango_layout(character))
        self.draw()
        self._characters = characters

    def get_characters(self):
        return self._characters

    def get_selected(self):
        return self._selected

    def unselect(self):
        self._selected = None
        self.draw()

    def clear(self):
        self._selected = None
        self._prelighted = None
        self.set_characters([])

    def set_layout(self, layout):
        self._layout = layout
        
gobject.type_register(CharTable)
        
if __name__ == "__main__":
    import sys

    window = gtk.Window()
    chartable = CharTable()
    chartable.set_characters(["あ", "い","う", "え", "お", 
                              "か", "き", "く", "け", "こ",
                              "さ", "し", "す", "せ", "そ"])

    try:
        layout = int(sys.argv[1])
        if layout > 3: layout = 0
    except IndexError:
        layout = 0

    chartable.set_layout(layout)


    def on_selected(widget, event):
        print "char_selected", chartable.get_selected()
        print "ev button", event.button
        print "ev time", event.time
       
    chartable.connect("character-selected", on_selected)

    window.add(chartable)
    window.show_all()
    gtk.main()
    
