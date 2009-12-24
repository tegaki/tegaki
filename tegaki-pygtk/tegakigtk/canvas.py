# -*- coding: utf-8 -*-

# Copyright (C) 2008 The Tegaki project contributors
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

class Canvas(gtk.Widget):
    """
    A character drawing canvas.

    This widget receives the input from the user and can return the
    corresponding L{tegaki.Writing} objects.

    It also has a "replay" method which can display a stroke-by-stroke
    animation of the current writing.

    The code was originally ported from Tomoe (C language).
    Since then many additional features were added.
    """

    #: Default canvas size
    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 400

    #: Default canvas size
    DEFAULT_REPLAY_SPEED = 50 # msec

    #: - the stroke-added signal is emitted when the user has added a stroke
    #: - the drawing-stopped signal is emitted when the user has stopped drawing
    __gsignals__ = {
        "stroke_added" :     (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        "drawing_stopped" :  (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
    }
    
    def __init__(self):
        gtk.Widget.__init__(self)
        
        self._width = self.DEFAULT_WIDTH
        self._height = self.DEFAULT_HEIGHT

        self._drawing = False
        self._pixmap = None

        self._writing = Writing()

        self._locked = False

        self._drawing_stopped_time = 0
        self._drawing_stopped_id = 0
        self._draw_annotations = True
        self._need_draw_axis = True

        self._handwriting_line_gc = None
        self._annotation_gc = None
        self._axis_gc = None
        self._stroke_gc = None
        self._background_writing_gc = None
        self._background_gc = None

        self._background_color = (0xFFFF, 0xFFFF, 0xFFFF)

        self._background_character = None
        self._background_writing = None

        self._first_point_time = None

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

        self._init_gc()

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
        self._width = self.allocation.width
        self._height = self.allocation.height        
 
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)
            
            self._pixmap = gdk.Pixmap(self.window,
                                      self._width,
                                      self._height)

            self.refresh()

    def do_expose_event(self, event):
        """
        This is where the widget must draw itself.
        """
        retval = False
        
        self.window.draw_drawable(self.style.fg_gc[self.state],
                                  self._pixmap,
                                  event.area.x, event.area.y,
                                  event.area.x, event.area.y,
                                  event.area.width, event.area.height)

        return retval
    
    def motion_notify_event(self, widget, event):
        retval = False

        if self._locked or not self._drawing:
            return retval

        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state

        x, y = self._internal_coordinates(x, y)

        point = Point()
        point.x = x
        point.y = y
        point.timestamp = event.time - self._first_point_time
        #point.pressure = pressure
        #point.xtilt = xtilt
        #point.ytilt = ytilt

        self._append_point(point)

        return retval

    def do_button_press_event(self, event):
        retval = False

        if self._locked:
            return retval

        if self._drawing_stopped_id > 0:
            gobject.source_remove(self._drawing_stopped_id)
            self._drawing_stopped_id = 0

        if event.button == 1:
            self._drawing = True

            x, y = self._internal_coordinates(event.x, event.y)

            point = Point()
            point.x = x
            point.y = y

            if self._writing.get_n_strokes() == 0:
                self._first_point_time = event.time
                point.timestamp = 0
            else:
                if self._first_point_time is None:
                    # in the case we add strokes to an imported character
                    self._first_point_time = event.time - \
                                             self._writing.get_duration() - 50
                                         
                point.timestamp = event.time - self._first_point_time
                
            #point.pressure = pressure
            #point.xtilt = xtilt
            #point.ytilt = ytilt
            
            self._writing.move_to_point(point)

        return retval

    def do_button_release_event(self, event):
        retval = False

        if self._locked or not self._drawing:
            return retval

        self._drawing = False

        self.refresh(force_draw=True)

        self.emit("stroke_added")

        if self._drawing_stopped_time > 0:

            def _on_drawing_stopped():
                self.emit("drawing_stopped")
                return False
             
            self._drawing_stopped_id = \
                            gobject.timeout_add(self._drawing_stopped_time,
                            _on_drawing_stopped)

        self._draw_background_writing_stroke()

        return retval

    # Private...

    def _gc_set_foreground (self, gc, color):
        colormap = gdk.colormap_get_system ()

        if color:
            color = colormap.alloc_color(color, True, True)
            gc.set_foreground(color)
        else:
            default_color = gdk.Color(0x0000, 0x0000, 0x0000, 0)
            default_color = colormap.alloc_color(default_color, True, True)
            gc.set_foreground(default_color)

    def _init_gc(self):
                                                  
        if not self._handwriting_line_gc:
            color = gdk.Color(red=0x0000, blue=0x0000, green=0x0000)
            self._handwriting_line_gc = gdk.GC(self.window)
            self._gc_set_foreground(self._handwriting_line_gc, color)
            self._handwriting_line_gc.set_line_attributes(4,
                                                         gdk.LINE_SOLID,
                                                         gdk.CAP_ROUND,
                                                         gdk.JOIN_ROUND)

        if not self._stroke_gc:
            color = gdk.Color(red=0xff00, blue=0x0000, green=0x0000)
            self._stroke_gc = gdk.GC(self.window)
            self._gc_set_foreground(self._stroke_gc, color)
            self._stroke_gc.set_line_attributes(4,
                                                gdk.LINE_SOLID,
                                                gdk.CAP_ROUND,
                                                gdk.JOIN_ROUND)

        if not self._background_writing_gc:
            color = gdk.Color(red=0xcccc, blue=0xcccc, green=0xcccc)
            self._background_writing_gc = gdk.GC(self.window)
            self._gc_set_foreground(self._background_writing_gc, color)
            self._background_writing_gc.set_line_attributes(4,
                                                            gdk.LINE_SOLID,
                                                            gdk.CAP_ROUND,
                                                            gdk.JOIN_ROUND)
        if not self._annotation_gc:
            color = gdk.Color(red=0x8000, blue=0x0000, green=0x0000)
            self._annotation_gc = gdk.GC(self.window)
            self._gc_set_foreground(self._annotation_gc, color)

        if not self._axis_gc:
            color = gdk.Color(red=0x8000, blue=0x8000, green=0x8000)
            self._axis_gc = gdk.GC(self.window)
            self._gc_set_foreground(self._axis_gc, color)
            self._axis_gc.set_line_attributes(1,
                                             gdk.LINE_ON_OFF_DASH,
                                             gdk.CAP_BUTT,
                                             gdk.JOIN_ROUND)

        if not self._background_gc:
            color = gdk.Color(*self._background_color)
            self._background_gc = gdk.GC(self.window)
            self._gc_set_foreground(self._background_gc, color)

    def _internal_coordinates(self, x, y):
        """
        Converts window coordinates to internal coordinates.
        """
        sx = float(self._writing.get_width()) / self._width
        sy = float(self._writing.get_height()) / self._height
        
        return (int(x * sx), int(y * sy))
    
    def _window_coordinates(self, x, y):
        """
        Converts internal coordinates to window coordinates.
        """
        sx = float(self._width) / self._writing.get_width()
        sy = float(self._height) / self._writing.get_height()
        
        return (int(x * sx), int(y * sy))

    def _append_point(self, point):
        # x and y are internal coordinates
        
        p2 = (point.x, point.y)
        
        strokes = self._writing.get_strokes(full=True) 

        p1 = strokes[-1][-1].get_coordinates()

        self._draw_line(p1, p2, self._handwriting_line_gc, force_draw=True)

        self._writing.line_to_point(point)
        
    def _draw_stroke(self, stroke, index, gc, draw_annotation=True):
        l = len(stroke)
        
        for i in range(l):
            if i == l - 1:
                break

            p1 = stroke[i]
            p1 = (p1.x, p1.y)
            p2 = stroke[i+1]
            p2 = (p2.x, p2.y)

            self._draw_line(p1, p2, gc)

        if draw_annotation:
            self._draw_annotation(stroke, index)

    def _draw_line(self, p1, p2, line_gc, force_draw=False):
        # p1 and p2 are two points in internal coordinates
        
        p1 = self._window_coordinates(*p1)
        p2 = self._window_coordinates(*p2)
        
        self._pixmap.draw_line(line_gc, p1[0], p1[1], p2[0], p2[1])

        if force_draw:
            x = min(p1[0], p2[0]) - 2
            y = min(p1[1], p2[1]) - 2
            width = abs(p1[0] - p2[0]) + 2 * 2
            height = abs(p1[1] - p2[1]) + 2 * 2

            self.queue_draw_area(x, y, width, height)

    def _draw_annotation(self, stroke, index, force_draw=False):
        x, y = self._window_coordinates(stroke[0].x, stroke[0].y)

        if len(stroke) == 1:
            dx, dy = x, y
        else:
            last_x, last_y = self._window_coordinates(stroke[-1].x,
                                                      stroke[-1].y)
            dx, dy = last_x - x, last_y - y
            if dx == dy == 0:
                dx, dy = x, y

        dl = math.sqrt(dx*dx + dy*dy)

        if dy <= dx:
            sign = 1
        else:
            sign = -1

        num = str(index + 1)
        layout = self.create_pango_layout(num)
        width, height = layout.get_pixel_size()

        r = math.sqrt (width*width + height*height)

        x += (0.5 + (0.5 * r * dx / dl) + (sign * 0.5 * r * dy / dl) - \
              (width / 2))
              
        y += (0.5 + (0.5 * r * dy / dl) - (sign * 0.5 * r * dx / dl) - \
              (height / 2))

        x, y = int(x), int(y)

        self._pixmap.draw_layout(self._annotation_gc, x, y, layout)

        if force_draw:
            self.queue_draw_area(x-2, y-2, width+4, height+4)

    def _draw_axis(self):        
        self._pixmap.draw_line(self._axis_gc,
                               self._width / 2, 0,
                               self._width / 2, self._height)

        self._pixmap.draw_line(self._axis_gc,
                               0, self._height / 2,
                               self._width, self._height / 2)

    def _draw_background(self):
        self._pixmap.draw_rectangle(self._background_gc,
                                    True,
                                    0, 0,
                                    self.allocation.width,
                                    self.allocation.height)

        if self._need_draw_axis:
            self._draw_axis()


    def _draw_background_character(self):
        if self._background_character:
            raise NotImplementedError

    def _draw_background_writing(self):
        if self._background_writing:
            strokes = self._background_writing.get_strokes(full=True)

            start = self._writing.get_n_strokes() + 1
            
            for i in range(start, len(strokes)):
                self._draw_stroke(strokes[i],
                                  i,
                                  self._background_writing_gc,
                                  draw_annotation=False)

    def _draw_background_writing_stroke(self):
        if self._background_writing and self._writing.get_n_strokes() < \
           self._background_writing.get_n_strokes():

            time.sleep(0.5)

            l = self._writing.get_n_strokes()

            self._strokes = self._background_writing.get_strokes(full=True)
            self._strokes = self._strokes[l:l+1]
        
            self._curr_stroke = 0
            self._curr_point = 1
            self._refresh_writing = False

            speed = self._get_speed(self._curr_stroke)

            gobject.timeout_add(speed, self._on_animate)

                

    def _redraw(self):
        self.window.draw_drawable(self.style.fg_gc[self.state],
                                  self._pixmap,
                                  0, 0,
                                  0, 0,
                                  self.allocation.width,
                                  self.allocation.height)

    def _get_speed(self, index):
        if self._speed:
            speed = self._speed
        else:
            duration = self._strokes[index].get_duration()
            if duration:
                speed = duration / len(self._strokes[index])
            else:
                speed = self.DEFAULT_REPLAY_SPEED
        return speed       

    def _on_animate(self):
        self._locked = True
        
        if self._curr_stroke > 0 and self._curr_point == 1 and \
           not self._speed:            
            # inter stroke duration
            # t2 = self._strokes[self._curr_stroke][0].timestamp
            # t1 = self._strokes[self._curr_stroke - 1][-1].timestamp
            # time.sleep(float(t2 - t1) / 1000)
            time.sleep(float(self._get_speed(self._curr_stroke))/1000)
        
        p1 = self._strokes[self._curr_stroke][self._curr_point - 1]
        p1 = (p1.x, p1.y)
        p2 = self._strokes[self._curr_stroke][self._curr_point]
        p2 = (p2.x, p2.y)

        self._draw_line(p1, p2, self._stroke_gc, force_draw=True)

        if len(self._strokes[self._curr_stroke]) == self._curr_point + 1:
            # if we reach the stroke last point
                         
            if self._draw_annotations:
                self._draw_annotation(self._strokes[self._curr_stroke],
                                                    self._curr_stroke)
                                                
            self._curr_point = 1
            self._curr_stroke += 1
                
            if len(self._strokes) != self._curr_stroke:
                # if there are remaining strokes to process

                speed = self._get_speed(self._curr_stroke)

                gobject.timeout_add(speed, self._on_animate)
            else:
                # last stroke and last point was reached
                self._locked = False
                
            if self._refresh_writing:
                self.refresh(n_strokes=self._curr_stroke, force_draw=True)
                
            return False
        else:
            self._curr_point += 1

        return True

    def _refresh(self, writing, n_strokes=None, force_draw=False):
        if self.flags() & gtk.REALIZED and self._pixmap:
            self._draw_background()

            self._draw_background_character()
            self._draw_background_writing()

            strokes = writing.get_strokes(full=True)

            if not n_strokes:
                n_strokes = len(strokes)

            for i in range(n_strokes):
                self._draw_stroke(strokes[i], i, self._handwriting_line_gc,
                                  draw_annotation=self._draw_annotations)

            if force_draw:
                self._redraw()

    # Public...

    def get_drawing_stopped_time(self):
        """
        Get the inactivity time after which a character is considered drawn.

        @rtype: int
        @return: time in milliseconds
        """
        return self._drawing_stopped_time

    def set_drawing_stopped_time(self, time_msec):
        """
        Set the inactivity time after which a character is considered drawn.

        @type time_msec: int
        @param time_msec: time in milliseconds
        """
        self._drawing_stopped_time = time_msec

    def set_draw_annotations(self, draw_annotations):
        """
        Set whether to display stroke-number annotations or not.

        @type draw_annotations: boolean
        """
        self._draw_annotations = draw_annotations

    def get_draw_annotations(self):
        """
        Return whether stroke-number annotations are displayed or not.
        """
        return self._draw_annotations

    def set_draw_axis(self, draw_axis):
        self._need_draw_axis = draw_axis

    def get_draw_axis(self):
        return self._need_draw_axis

    def refresh(self, n_strokes=None, force_draw=False):
        """
        Update the screen.
        """
        if self._writing:
            self._refresh(self._writing,
                         n_strokes=n_strokes,
                         force_draw=force_draw)

    def replay(self, speed=None):
        """
        Display an animation of the current writing.
        One point is drawn every "speed" msec.

        If speed is None, uses the writing original speed when available or
        DEFAULT_REPLAY_SPEED when not available.

        @type speed: int
        @type speed: time between each point in milliseconds
        """
        self._draw_background()
        self._redraw()

        self._strokes = self._writing.get_strokes(full=True)

        if len(self._strokes) == 0:
            return
        
        self._curr_stroke = 0
        self._curr_point = 1
        self._speed = speed
        self._refresh_writing = True

        speed = self._get_speed(self._curr_stroke)

        gobject.timeout_add(speed, self._on_animate)

    def get_writing(self, writing_width=None, writing_height=None):
        """
        Return a L{tegaki.Writing} object for the current handwriting.

        @type writing_width: int
        @param writing_width: the width that the writing should have or \
                              None if default
        @type writing_height: int
        @param writing_height: the height that the writing should have or \
                              None if default
        @rtype: Writing

        """

        if writing_width and writing_height:
            # Convert to requested size
            xratio = float(writing_width) / self._writing.get_width()
            yratio = float(writing_height) / self._writing.get_height()

            return self._writing.resize(xratio, yratio)
        else:
            return self._writing

    def set_writing(self, writing, writing_width=None, writing_height=None):

        if writing_width and writing_height:
            # Convert to internal size
            xratio = float(self._writing.get_width()) / writing_width
            yratio = float(self._writing.get_height()) / writing_height
           
            self._writing = self._writing.resize(xratio, yratio)
        else:
            self._writing = writing

        
        self.refresh(force_draw=True)

    def clear(self):
        """
        Erase the current writing.
        """
        self._writing.clear()

        self.refresh(force_draw=True)

    def revert_stroke(self):
        """
        Undo the latest stroke
        """
        n = self._writing.get_n_strokes()

        if n > 0:
            self._writing.remove_last_stroke()
            self.refresh(force_draw=True)

    def normalize(self):
        """
        Normalize the current writing. (See L{tegaki.normalize})
        """
        self._writing.normalize()
        self.refresh(force_draw=True)

    def smooth(self):
        """
        Smooth the current writing. (See L{tegaki.smooth})
        """
        self._writing.smooth()
        self.refresh(force_draw=True)

    def set_background_character(self, character):
        """
        Set a character as background.

        @type character: str
        """
        self._background_character = character

    def get_background_writing(self):
        return self._background_writing
    
    def set_background_writing(self, writing, speed=25):
        """
        Set a writing as background. 

        Strokes of the background writing are displayed one at a time. 
        This is intended to let users "follow" the background writing like a
        template.

        @type writing: L{tegaki.Writing}
        """
        self.clear()
        self._background_writing = writing
        self._speed = speed
        time.sleep(0.5)
        self._draw_background_writing_stroke()
        self.refresh(force_draw=True)

    def set_background_color(self, r, g, b):
        """
        Set background color.

        @type r: int
        @param r: red
        @type g: int
        @param g: green
        @type b: int
        @param b: blue
        """
        self._background_color = (r, g, b)
        
        if self._background_gc:
            # This part can only be called after the widget is visible
            color = gdk.Color(red=r, green=g, blue=b)
            self._background_gc = gdk.GC(self.window)
            self._gc_set_foreground(self._background_gc, color)
            self.refresh(force_draw=True)
        
gobject.type_register(Canvas)
        
if __name__ == "__main__":
    import sys
    import copy
    
    def on_stroke_added(widget):
        print "stroke added!"
        
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    
    canvas = Canvas()
    
    canvas.connect("stroke_added", on_stroke_added)
    
    if len(sys.argv) >= 2:

        if sys.argv[1] == "upsample":
            try:
                n = int(sys.argv[2])
            except IndexError:
                n = 5

            def on_drawing_stopped(widget):
                print "before: %d pts" % widget.get_writing().get_n_points()
                widget.get_writing().upsample(n)
                widget.refresh(force_draw=True)
                print "after: %d pts" % widget.get_writing().get_n_points()

        elif sys.argv[1] == "upsamplet":
            try:
                n = int(sys.argv[2])
            except IndexError:
                n = 10

            def on_drawing_stopped(widget):
                print "before: %d pts" % widget.get_writing().get_n_points()
                widget.get_writing().upsample_threshold(n)
                widget.refresh(force_draw=True)
                print "after: %d pts" % widget.get_writing().get_n_points()

        elif sys.argv[1] == "downsample":
            try:
                n = int(sys.argv[2])
            except IndexError:
                n = 5

            def on_drawing_stopped(widget):
                print "before: %d pts" % widget.get_writing().get_n_points()
                widget.get_writing().downsample(n)
                widget.refresh(force_draw=True)
                print "after: %d pts" % widget.get_writing().get_n_points()

        elif sys.argv[1] == "downsamplet":
            try:
                n = int(sys.argv[2])
            except IndexError:
                n = 10

            def on_drawing_stopped(widget):
                print "before: %d pts" % widget.get_writing().get_n_points()
                widget.get_writing().downsample_threshold(n)
                widget.refresh(force_draw=True)
                print "after: %d pts" % widget.get_writing().get_n_points()
                
        elif sys.argv[1] == "smooth":
            def on_drawing_stopped(widget):
                widget.smooth()

        elif sys.argv[1] == "normalize":
            def on_drawing_stopped(widget):
                widget.normalize()
                
        elif sys.argv[1] == "replay":
            def on_drawing_stopped(widget):
                widget.replay()

        elif sys.argv[1] == "replay-speed":
            def on_drawing_stopped(widget):
                widget.replay(speed=25)

        elif sys.argv[1] == "background-writing":
            def on_drawing_stopped(widget):
                background_writing = widget.get_background_writing()
                if not background_writing:
                    writing = copy.copy(widget.get_writing())
                    widget.set_background_writing(writing)
 
        else:
            def on_drawing_stopped(widget):
                print "drawing stopped!"

        if sys.argv[1] == "background-char":
            canvas.set_background_character("愛")

    else:
        def on_drawing_stopped(widget):
            print "drawing stopped!"
            print widget.get_writing().to_xml()
                             
    canvas.set_draw_annotations(False)
    canvas.set_drawing_stopped_time(1000)
    canvas.connect("drawing_stopped", on_drawing_stopped)
    
    window.add(canvas)
    
    window.show_all()
    window.connect('delete-event', gtk.main_quit)
    
    gtk.main()