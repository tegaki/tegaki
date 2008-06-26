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
from gtk import gdk
import gobject
import pango
import math

from character import *
import tomoe

class Canvas(gtk.Widget):
    """
    A character drawing canvas.

    A port of Takuro Ashie's TomoeCanvas to pygtk.
    Also based on a tutorial by Mark Mruss.
    """

    # Default canvas size
    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 400

    __gsignals__ = dict(stroke_added=(gobject.SIGNAL_RUN_LAST,
                                      gobject.TYPE_NONE,
                                      ()))
    
    def __init__(self):
        gtk.Widget.__init__(self)
        
        self.width = self.DEFAULT_WIDTH
        self.height = self.DEFAULT_HEIGHT

        self.drawing = False
        self.pixmap = None

        self.writing = Writing()

        self.locked = False

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
        font_desc = pango.FontDescription("Sans 12")
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
       requisition.height = self.DEFAULT_HEIGHT
       requisition.width = self.DEFAULT_WIDTH

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
            
            self.pixmap = gdk.Pixmap(self.window,
                                     self.width,
                                     self.height)

            self._init_gc()

            self.refresh()

    def do_expose_event(self, event):
        """
        This is where the widget must draw itself.
        """
        retval = False
        
        self.window.draw_drawable(self.style.fg_gc[self.state],
                                  self.pixmap,
                                  event.area.x, event.area.y,
                                  event.area.x, event.area.y,
                                  event.area.width, event.area.height)

        return retval
    
    def motion_notify_event(self, widget, event):
        retval = False

        if self.locked or not self.drawing:
            return retval

        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state

        self._append_point(*self._internal_coordinates(x, y))

        # In addition to x and y, the following features may be
        # interesting to add:
        #
        # time, pressure, xtilt and ytilt


        return retval

    def do_button_press_event(self, event):
        retval = False

        if self.locked:
            return retval

        if event.button == 1:
            self.drawing = True
            self.writing.move_to(*self._internal_coordinates(event.x, event.y))

        return retval

    def do_button_release_event(self, event):
        retval = False

        if self.locked or not self.drawing:
            return retval

        self.drawing = False

        self.refresh(force_draw=True)

        self.emit("stroke_added")

        return retval

    # Private...

    def _gc_set_foreground (self, gc, color):
        default_color = gdk.Color(0, 0x0000, 0x0000, 0x0000)

        colormap = gdk.colormap_get_system ()

        if color:
            colormap.alloc_color(color, True, True)
            gc.set_foreground(color)
        else:
            colormap.alloc_color(default_color, True, True)
            gc.set_foreground(default_color)

    def _init_gc(self):
                                                  
        color = gdk.Color(0, 0x0000, 0x0000, 0x0000)
        self.handwriting_line_gc = gdk.GC(self.window)
        self._gc_set_foreground(self.handwriting_line_gc, color)
        self.handwriting_line_gc.set_line_attributes(4,
                                                     gdk.LINE_SOLID,
                                                     gdk.CAP_ROUND,
                                                     gdk.JOIN_ROUND)

        color = gdk.Color(0, 0x8000, 0x0000, 0x0000)
        self.annotation_gc = gdk.GC(self.window)
        self._gc_set_foreground(self.annotation_gc, color)

        color = gdk.Color(0, 0x8000, 0x8000, 0x8000)
        self.axis_gc = gdk.GC(self.window)
        self._gc_set_foreground(self.axis_gc, color)
        self.axis_gc.set_line_attributes(1,
                                         gdk.LINE_ON_OFF_DASH,
                                         gdk.CAP_BUTT,
                                         gdk.JOIN_ROUND)

    def _internal_coordinates(self, x, y):
        """
        Converts window coordinates to internal coordinates.
        """
        sx = float(Writing.WIDTH) / self.width
        sy = float(Writing.HEIGHT) / self.height
        
        return (int(x * sx), int(y * sy))
    
    def _window_coordinates(self, x, y):
        """
        Converts internal coordinates to window coordinates.
        """
        sx = float(self.width) / Writing.WIDTH
        sy = float(self.height) / Writing.WIDTH
        
        return (int(x * sx), int(y * sy))

    def _append_point(self, x, y):
        # x and y are internal coordinates
        
        p2 = (x, y)
        
        strokes = self.writing.get_strokes()

        last_stroke = strokes[-1]

        p1 = last_stroke[-1]

        self._draw_line(p1, p2, self.handwriting_line_gc, force_draw=True)

        self.writing.line_to(x, y)
        
    def _draw_stroke(self, stroke, index):
        l = len(stroke)
        
        for i in range(l):
            if i == l - 1:
                break

            p1 = stroke[i]
            p2 = stroke[i+1]

            self._draw_line(p1, p2, self.handwriting_line_gc)

        self._draw_annotation(stroke, index)

    def _draw_line(self, p1, p2, line_gc, force_draw=False):
        # p1 and p2 are two points in internal coordinates
        
        p1 = self._window_coordinates(*p1)
        p2 = self._window_coordinates(*p2)
        
        self.pixmap.draw_line(line_gc, p1[0], p1[1], p2[0], p2[1])

        if force_draw:
            x = min(p1[0], p2[0]) - 2
            y = min(p1[1], p2[1]) - 2
            width = abs(p1[0] - p2[0]) + 2 * 2
            height = abs(p1[1] - p2[1]) + 2 * 2

            self.queue_draw_area(x, y, width, height)

    def _draw_annotation(self, stroke, index):
        x, y = self._window_coordinates(stroke[0][0], stroke[0][1])

        if len(stroke) == 1:
            dx, dy = x, y
        else:
            last_x, last_y = self._window_coordinates(stroke[-1][0],
                                                      stroke[-1][1])
            dx, dy = last_x - x, last_y - y

        dl = math.sqrt(dx*dx + dy*dy)

        if dy <= dx:
            sign = 1
        else:
            sign = -1

        num = str(index + 1)
        layout = self.create_pango_layout(num)
        width, height = layout.get_pixel_size()

        r = math.sqrt (width*width + height*height);

        x += (0.5 + (0.5 * r * dx / dl) + (sign * 0.5 * r * dy / dl) - \
              (width / 2));
              
        y += (0.5 + (0.5 * r * dy / dl) - (sign * 0.5 * r * dx / dl) - \
              (height / 2));

        self.pixmap.draw_layout(self.annotation_gc, int(x), int(y), layout);

    def _draw_axis(self):
        self.pixmap.draw_line(self.axis_gc,
                              self.width / 2, 0,
                              self.width / 2, self.height)

        self.pixmap.draw_line(self.axis_gc,
                              0, self.height / 2,
                              self.width, self.height / 2)

    def _draw_background(self):
        self.pixmap.draw_rectangle(self.style.white_gc,
                                   True,
                                   0, 0,
                                   self.allocation.width,
                                   self.allocation.height)

        self._draw_axis()

    # Public...

    def refresh(self, force_draw=False):
        self._draw_background()

        if self.writing:
            strokes = self.writing.get_strokes()

            for i in range(len(strokes)):
                self._draw_stroke(strokes[i], i)

        if force_draw:
            self.window.draw_drawable(self.style.fg_gc[self.state],
                                      self.pixmap,
                                      0, 0,
                                      0, 0,
                                      self.allocation.width,
                                      self.allocation.height);

    def get_writing(self, writing_width=None, writing_height=None):

        if writing_width and writing_height:
            # Convert to requested size
            xratio = float(writing_width) / Writing.WIDTH
            yratio = float(writing_height) / Writing.HEIGHT

            return self.writing.resize(xratio, yratio)
        else:
            return self.writing

    def set_writing(self, writing, writing_width=None, writing_height=None):

        if writing_width and writing_height:
            # Convert to internal size
            xratio = float(Writing.WIDTH) / writing_width
            yratio = float(Writing.HEIGHT) / writing_height
           
            self.writing = self.writing.resize(xratio, yratio)
        else:
            self.writing = writing

        if self.flags() & gtk.REALIZED:
            self.refresh(force_draw=True)

    def clear(self):
        self.writing.clear()

        self.refresh(force_draw=True)

    def revert_stroke(self):
        n = self.writing.get_n_strokes()

        if n > 0:
            self.writing.remove_last_stroke()
            self.refresh(force_draw=True)
        
gobject.type_register(Canvas)
        
if __name__ == "__main__":
    def on_stroke_added(widget):
        print "stroke added!"
        
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    
    canvas = Canvas()
    canvas.connect("stroke_added", on_stroke_added)
    window.add(canvas)
    
    window.show_all()
    window.connect('delete-event', gtk.main_quit)
    
    gtk.main()