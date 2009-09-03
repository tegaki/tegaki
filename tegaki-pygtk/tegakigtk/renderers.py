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

import math
import cairo
from math import pi

from tegaki.character import *
from tegaki.mathutils import euclidean_distance

class _CairoRendererBase(object):

    def __init__(self, cairo_context, writing):
        self.cr = cairo_context
        self._init_colors()
        self.writing = writing
        self.draw_annotations = False
        self.draw_circles = False
        self.stroke_width = 8
        self.area_changed_cb = None
        self.stroke_added_cb = None

    def set_area_changed_callback(self, cb):
        self.area_changed_cb = cb

    def set_stroke_added_callback(self, cb):
        self.stroke_added_cb = cb

    def _area_changed(self, x, y, w, h, delay_ms):
        if self.area_changed_cb:
            sx = float(self.width) / self.writing.get_width() # scale x
            sy = float(self.height) / self.writing.get_height() # scale y
            self.area_changed_cb(int(sx*x), int(sy*y), 
                                 int(sx*w), int(sy*h), delay_ms)

    def _init_colors(self):
        self.handwriting_line_color = (0x0000, 0x0000, 0x0000, 1.0)
        self.axis_line_color = (0, 0, 0, 0.2)
        self.annotations_color = (255, 0, 0, 0.8)
        self.stroke_line_color = (255, 0, 0, 0.5)
        self.border_line_color = (0, 0, 0, 1.0)
        self.circle_color = (0, 0, 255, 0.5)

    def _with_handwriting_line(self):
        self.cr.set_line_width(self.stroke_width)
        self.cr.set_line_cap(cairo.LINE_CAP_ROUND)
        self.cr.set_line_join(cairo.LINE_JOIN_ROUND)

    def _with_circle_line(self):
        self.cr.set_line_width(self.stroke_width)
        self.cr.set_line_cap(cairo.LINE_CAP_ROUND)
        self.cr.set_line_join(cairo.LINE_JOIN_ROUND)
        self.cr.set_source_rgba (*self.circle_color)

    def _with_axis_line(self):
        self.cr.set_source_rgba (*self.axis_line_color)
        self.cr.set_line_width (4)
        self.cr.set_dash ([8, 8], 2)
        self.cr.set_line_cap(cairo.LINE_CAP_BUTT)
        self.cr.set_line_join(cairo.LINE_JOIN_ROUND)

    def _with_border_line(self):
        self.cr.set_source_rgba (*self.border_line_color)
        self.cr.set_line_width (8)
        self.cr.set_line_cap(cairo.LINE_CAP_BUTT)
        self.cr.set_line_join(cairo.LINE_JOIN_ROUND)

    def _with_annotations(self):
        self.cr.set_source_rgba (*self.annotations_color)
        self.annotation_font_size = 30 # user space units
        self.cr.set_font_size(self.annotation_font_size)

    def _draw_small_circle(self, x, y):
        self.cr.save()
        self._with_circle_line()
        self.cr.arc(x, y, 10, 0, 2*pi)
        self.cr.fill_preserve()
        self.cr.stroke()
        self.cr.restore()

    def set_draw_circles(self, draw_circles):
        self.draw_circles = draw_circles

    def set_draw_annotations(self, draw_annotations):
        self.draw_annotations = draw_annotations

    def set_stroke_width(self, stroke_width):
        self.stroke_width = stroke_width

    def draw_stroke(self, stroke, index, color, 
                    draw_annotation=False, draw_circle=False):

        l = len(stroke)

        self.cr.save()
        
        self._with_handwriting_line()
        self.cr.set_source_rgba(*color)

        point0 = stroke[0]

        if draw_circle: self._draw_small_circle(point0.x, point0.y)

        self.cr.move_to(point0.x, point0.y)
        last_point = point0
        n_points = len(stroke)

        i = 1

        for point in stroke[1:]:
            self.cr.line_to(point.x, point.y)
            self.cr.stroke()
            self.cr.move_to(point.x, point.y)

            dist = euclidean_distance(point.get_coordinates(),
                                      last_point.get_coordinates())

            if  dist > 50 or i == n_points - 1:
                win = 100 # window size
                x1 = last_point.x - win; y1 = last_point.y - win
                x2 = point.x + win; y2 = point.y + win
                if x1 > x2: x1, x2 = x2, x1
                if y1 > y2: y1, y2 = y2, y1
                w = x2 - x1; h = y2 - y1
                if point.timestamp and last_point.timestamp:
                    delay = point.timestamp - last_point.timestamp
                else:
                    delay = None
                if w > 0 and h > 0:
                    self._area_changed(x1, y1, w, h, delay) 

                last_point = point

            i += 1

        self.cr.stroke()
        self.cr.restore()

        if self.stroke_added_cb:
            self.stroke_added_cb()

        if draw_annotation:
            self._draw_annotation(stroke, index)

    def _draw_annotation(self, stroke, index):
        self.cr.save()

        self._with_annotations()
        
        x, y = stroke[0].x, stroke[0].y

        if len(stroke) == 1:
            dx, dy = x, y
        else:
            last_x, last_y = stroke[-1].x, stroke[-1].y
            dx, dy = last_x - x, last_y - y

        dl = math.sqrt(dx*dx + dy*dy)

        if dy <= dx:
            sign = 1
        else:
            sign = -1

        num = str(index + 1)
        # FIXME: how to know the actual size of the text?
        width, height = [int(self.annotation_font_size * 11.0/10.0)] * 2

        r = math.sqrt (width*width + height*height)

        x += (0.5 + (0.5 * r * dx / dl) + (sign * 0.5 * r * dy / dl) - \
              (width / 2))
              
        y += (0.5 + (0.5 * r * dy / dl) - (sign * 0.5 * r * dx / dl) - \
              (height / 2))

        x, y = int(x), int(y)

        self.cr.move_to(x, y)
        self.cr.show_text(num)
        self.cr.stroke()
        
        self._area_changed(x-50, y-50, 100, 100, 0) 

        self.cr.restore()

    def draw_background(self, color=(1, 1, 1)):
        self.cr.save()
        self.cr.set_source_rgb(*color)
        self.cr.paint()
        self.cr.restore()

    def draw_border(self):
        self.cr.save()

        self._with_axis_line()

        self.cr.move_to(0, 0)
        self.cr.line_to(0, 1000)
        self.cr.line_to(1000, 1000)
        self.cr.line_to(1000, 0)
        self.cr.line_to(0, 0)
        
        self.cr.stroke()
        self.cr.restore()        

    def draw_axis(self):
        self.cr.save()

        self._with_axis_line()

        self.cr.move_to(500, 0)
        self.cr.line_to(500, 1000)
        self.cr.move_to(0, 500)
        self.cr.line_to(1000, 500)
        
        self.cr.stroke()
        self.cr.restore()

class _SurfaceRendererBase(object):

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_size(self):
        return (self.width, self.height)

class _ImageRendererBase(_SurfaceRendererBase):
    
    def write_to_png(self, filename):
        self.surface.write_to_png(filename)

    def get_data(self):
        return self.surface.get_data()

    def get_area_data(self, x, y, width, height):
        data = self.get_data()
        stride = self.surface.get_stride() # number of bytes per line
        bpp = stride / self.surface.get_width() # bytes per pixel
        start = 0
        if y > 0:
            start += y * stride
        if x > 0:
            start += x * bpp
        buf = ""
        for i in range(height):
            buf += data[start:start+width*bpp]
            start += stride
        return buf

    def get_stride(self):
        return self.surface.get_stride()
    
class WritingCairoRenderer(_CairoRendererBase):

    def __init__(self, *a, **kw):
        _CairoRendererBase.__init__(self, *a, **kw)
        self.draw_annotations = True

    def draw_writing(self):
        strokes = self.writing.get_strokes(full=True)
        n_strokes = len(strokes)

        for i in range(n_strokes):
            self.draw_stroke(strokes[i],
                             i,
                             self.handwriting_line_color,
                             draw_annotation=self.draw_annotations,
                             draw_circle=self.draw_circles)

class WritingStepsCairoRenderer(_CairoRendererBase):

    def __init__(self, cairo_context, writing,
                       stroke_groups=None,
                       start=0,
                       length=None,
                       n_chars_per_row=None):
        
        _CairoRendererBase.__init__(self, cairo_context, writing)

    def _init(self):
        n_strokes = self.writing.get_n_strokes()
        
        if not self.stroke_groups:
            self.stroke_groups = [1] * n_strokes
        else:
            n = sum(self.stroke_groups)
            diff = n_strokes - n
            if diff > 0:
                # fix the number of groups if not enough
                self.stroke_groups += [1] * diff
            elif diff < 0:
                # fix the number of groups if too big
                tmp = []
                i = 0
                while sum(tmp) <= n_strokes:
                    tmp.append(self.stroke_groups[i])
                    i += 1
                self.stroke_groups = tmp

        n_stroke_groups = len(self.stroke_groups)

        if not self.length or self.start + self.length > n_stroke_groups:
            self.length = n_stroke_groups - self.start

        # interval groups are used to know which strokes are grouped together
        interval_groups = []
        
        interval_groups.append((0, self.stroke_groups[0] - 1))
        
        for i in range(1, n_stroke_groups):
            prev = interval_groups[i-1][1]
            interval_groups.append((prev + 1, prev + self.stroke_groups[i]))

        self.interval_groups = interval_groups

        # rows and cols
        if not self.n_chars_per_row:
            self.n_rows = 1
            self.n_cols = self.length
        else:
            self.n_cols = self.n_chars_per_row
            self.n_rows = int(math.ceil(float(self.length) / self.n_cols))

        # this factor is a multiplication factor used to determine
        # the amount of space to leave between two character steps
        self.FACTOR = 1.05
        
        # find proportional image size
        # we use width / n_cols == height / n_rows
        if self.width and not self.height:
            self.height = int(self.width / self.n_cols * self.n_rows)
        elif self.height and not self.width:
            self.width = int(self.n_cols * self.height / self.n_rows)
        elif not self.height and not self.width:
            raise ValueError, \
                  "At least one of height or width should be defined."
    
    def draw_writing_steps(self):       
        strokes = self.writing.get_strokes(full=True)
        n_strokes = len(strokes)
        n_stroke_groups = len(self.interval_groups)

        self.cr.save()

        x_scale = 1.0 / (self.n_cols * self.FACTOR)

        if self.n_rows == 1:
            y_scale = 1.0
        else:
            y_scale = 1.0 / (self.n_rows * self.FACTOR)
            
        self.cr.scale(x_scale, y_scale)

        for i in range(self.start, self.start + self.length):
            if i != self.start:
                if self.n_rows > 1 and i % self.n_cols == 0:
                    self.cr.translate((-self.n_cols+1) *
                                       self.writing.get_width() * self.FACTOR,
                                       self.writing.get_height() * self.FACTOR)
                else:
                    self.cr.translate(self.writing.get_width() * self.FACTOR,0) 
                
            # draw the character step
            for j in range(n_strokes):
                interval_min, interval_max = self.interval_groups[i]
                
                if interval_min <= j and j <= interval_max:
                    color = self.handwriting_line_color
                    draw_annotation = self.draw_annotations
                    draw_circle = self.draw_circles
                else:
                    color = self.stroke_line_color
                    draw_annotation = False
                    draw_circle = False
                   
                self.draw_stroke(strokes[j],
                                 j,
                                 color,
                                 draw_annotation=draw_annotation,
                                 draw_circle=draw_circle)

        self.cr.restore()

class WritingImageRenderer(WritingCairoRenderer, _ImageRendererBase):

    def __init__(self, writing, width, height):
        """
        width and height are in pixels.
        """
        self.width = width
        self.height = height
        
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(self.surface)
        cr.scale(float(width) / writing.get_width(), 
                 float(height) / writing.get_height())
        WritingCairoRenderer.__init__(self, cr, writing)

class WritingSVGRenderer(WritingCairoRenderer, _SurfaceRendererBase):
    
    def __init__(self, writing, filename, width, height):
        """
        width and height are in points (1 point == 1/72.0 inch).
        """
        self.width = width
        self.height = height
        
        self.surface = cairo.SVGSurface(filename, width, height)
        cr = cairo.Context(self.surface)
        cr.scale(float(width) / writing.get_width(), 
                 float(height) / writing.get_height())
        WritingCairoRenderer.__init__(self, cr, writing)

class WritingPDFRenderer(WritingCairoRenderer, _SurfaceRendererBase):
    
    def __init__(self, writing, filename, width, height):
        """
        width and height are in points (1 point == 1/72.0 inch).
        """
        self.width = width
        self.height = height
        
        self.surface = cairo.PDFSurface(filename, width, height)
        cr = cairo.Context(self.surface)
        cr.scale(float(width) / writing.get_width(), 
                 float(height) / writing.get_height())
        WritingCairoRenderer.__init__(self, cr, writing)

class WritingStepsImageRenderer(WritingStepsCairoRenderer, _ImageRendererBase):

    def __init__(self, writing,
                       width=None, height=None,
                       stroke_groups=None,
                       start=0,
                       length=None,
                       n_chars_per_row=None):
        """
        width and height are in pixels.
        """
        self.writing = writing
        self.width = width
        self.height = height
        self.stroke_groups = stroke_groups
        self.start = start
        self.length = length
        self.n_chars_per_row = n_chars_per_row

        self._init()
        
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                          self.width, self.height)
        cr = cairo.Context(self.surface)
        cr.scale(float(self.width) / writing.get_width(),
                 float(self.height) / writing.get_height())
        WritingStepsCairoRenderer.__init__(self, cr, writing)
        
    def write_to_png(self, filename):
        self.surface.write_to_png(filename)
    
class WritingStepsSVGRenderer(WritingStepsCairoRenderer, _SurfaceRendererBase):
    
    def __init__(self, writing,
                       filename,
                       width=None, height=None,
                       stroke_groups=None,
                       start=0,
                       length=None,
                       n_chars_per_row=None):
        """
        width and height are in points (1 point == 1/72.0 inch).
        """
        self.writing = writing
        self.width = width
        self.height = height
        self.stroke_groups = stroke_groups
        self.start = start
        self.length = length
        self.n_chars_per_row = n_chars_per_row

        self._init()
        
        self.surface = cairo.SVGSurface(filename, self.width, self.height)
        cr = cairo.Context(self.surface)
        cr.scale(float(self.width) / writing.get_width(),
                 float(self.height) / writing.get_height())
        WritingStepsCairoRenderer.__init__(self, cr, writing)

class WritingStepsPDFRenderer(WritingStepsCairoRenderer, _SurfaceRendererBase):
    
    def __init__(self, writing,
                       filename,
                       width=None, height=None,
                       stroke_groups=None,
                       start=0,
                       length=None,
                       n_chars_per_row=None):
        """
        width and height are in points (1 point == 1/72.0 inch).
        """
        self.writing = writing
        self.width = width
        self.height = height
        self.stroke_groups = stroke_groups
        self.start = start
        self.length = length
        self.n_chars_per_row = n_chars_per_row

        self._init()
        
        self.surface = cairo.PDFSurface(filename, self.width, self.height)
        cr = cairo.Context(self.surface)
        cr.scale(float(self.width) / writing.get_width(),
                 float(self.height) / writing.get_height())
        WritingStepsCairoRenderer.__init__(self, cr, writing)

def inch_to_pt(*arr):
    arr = [inch * 72 for inch in arr]
    if len(arr) == 1:
        return arr[0]
    else:
        return arr

def cm_to_pt(*arr):
    arr = [int(round(cm * 28.3464567)) for cm in arr]
    if len(arr) == 1:
        return arr[0]
    else:
        return arr
