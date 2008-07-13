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

import math
import cairo

from tegaki.character import *

class _CairoRendererBase(object):

    def __init__(self, cairo_context, writing):
        self.cr = cairo_context
        self._init_colors()
        self.writing = writing
        self.draw_annotations = False

    def _init_colors(self):
        self.handwriting_line_color = (0x0000, 0x0000, 0x0000, 1.0)
        self.axis_line_color = (0, 0, 0, 0.2)
        self.annotations_color = (0x00, 0x00, 0x00ff, 0.5)
        self.stroke_line_color = (255, 0, 0, 0.5)

    def _with_handwriting_line(self):
        self.cr.set_line_width(8)
        self.cr.set_line_cap(cairo.LINE_CAP_ROUND)
        self.cr.set_line_join(cairo.LINE_JOIN_ROUND)

    def _with_axis_line(self):
        self.cr.set_source_rgba (*self.axis_line_color)
        self.cr.set_line_width (4)
        self.cr.set_dash ([8, 8], 2)
        self.cr.set_line_cap(cairo.LINE_CAP_BUTT)
        self.cr.set_line_join(cairo.LINE_JOIN_ROUND)

    def _with_annotations(self):
        self.cr.set_source_rgba (*self.annotations_color)
        self.annotation_font_size = 30 # user space units
        self.cr.set_font_size(self.annotation_font_size)

    def set_draw_annotations(self, draw_annotations):
        self.draw_annotations = draw_annotations

    def draw_stroke(self, stroke, index, color, draw_annotation=False):
        l = len(stroke)

        self.cr.save()
        
        self._with_handwriting_line()
        self.cr.set_source_rgba(*color)

        point0 = stroke[0]
        self.cr.move_to(point0.x, point0.y)

        for point in stroke[1:]:
            self.cr.line_to(point.x, point.y)

        self.cr.stroke()
        self.cr.restore()

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

        self.cr.restore()

    def draw_background(self, color=(1, 1, 1)):
        self.cr.save()
        self.cr.set_source_rgb(*color)
        self.cr.paint()
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
                             draw_annotation=self.draw_annotations)

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

        if not self.length or start + self.length > n_stroke_groups:
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
            self.n_cols = n_chars_per_row
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
                    self.cr.translate((-self.n_cols+1) * Writing.WIDTH *
                                      self.FACTOR, Writing.HEIGHT * self.FACTOR)
                else:
                    self.cr.translate(Writing.WIDTH * self.FACTOR, 0) 
                
            # draw the character step
            for j in range(n_strokes):
                interval_min, interval_max = self.interval_groups[i]
                
                if interval_min <= j and j <= interval_max:
                    color = self.handwriting_line_color
                    draw_annotation = self.draw_annotations
                else:
                    color = self.stroke_line_color
                    draw_annotation = False
                   
                self.draw_stroke(strokes[j],
                                 j,
                                 color,
                                 draw_annotation=draw_annotation)

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
        cr.scale(float(width) / Writing.WIDTH, float(height) / Writing.HEIGHT)
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
        cr.scale(float(width) / Writing.WIDTH, float(height) / Writing.HEIGHT)
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
        cr.scale(float(width) / Writing.WIDTH, float(height) / Writing.HEIGHT)
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
        cr.scale(float(self.width) / Writing.WIDTH,
                 float(self.height) / Writing.HEIGHT)
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
        cr.scale(float(self.width) / Writing.WIDTH,
                 float(self.height) / Writing.HEIGHT)
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
        cr.scale(float(self.width) / Writing.WIDTH,
                 float(self.height) / Writing.HEIGHT)
        WritingStepsCairoRenderer.__init__(self, cr, writing)

def inch_to_pt(*arr):
    arr = [inch * 72 for inch in arr]
    if len(arr) == 1:
        return arr[0]
    else:
        return arr

def cm_to_pt(*arr):
    arr = [round(cm * 28.3464567) for cm in arr]
    if len(arr) == 1:
        return arr[0]
    else:
        return arr

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print "Need a writing file at least."
        sys.exit()

    if len(sys.argv) >= 3:
        stroke_groups = [int(n) for n in sys.argv[2].split(",")]
    else:
        stroke_groups = None

    if len(sys.argv) >= 4:
        start, length = [int(n) for n in sys.argv[3].split(",")]
    else:
        start, length = 0, None

    if len(sys.argv) >= 5:
        n_chars_per_row = int(sys.argv[4])
    else:
        n_chars_per_row = None

    char = Character()
    char.read(sys.argv[1])
    writing = char.get_writing()
    
    png_renderer = WritingImageRenderer(writing, 400, 400)
    svg_renderer = WritingSVGRenderer(writing, "test.svg",
                                      *cm_to_pt(20, 20))
    pdf_renderer = WritingPDFRenderer(writing, "test.pdf",
                                      *cm_to_pt(20, 20))

    for renderer in (png_renderer, svg_renderer, pdf_renderer):
        renderer.draw_background()
        renderer.draw_axis()
        renderer.draw_writing()
        
    png_renderer.write_to_png("test.png")

    png_renderer = WritingStepsImageRenderer(writing, height=400,
                                             stroke_groups=stroke_groups,
                                             start=start,
                                             length=length,
                                             n_chars_per_row=n_chars_per_row)

    height_pt = cm_to_pt(4)
                                             
    svg_renderer = WritingStepsSVGRenderer(writing,
                                           "test_steps.svg",
                                           height=height_pt,
                                           stroke_groups=stroke_groups,
                                           start=start,
                                           length=length,
                                           n_chars_per_row=n_chars_per_row)
    pdf_renderer = WritingStepsPDFRenderer(writing,
                                           "test_steps.pdf",
                                           height=height_pt,
                                           stroke_groups=stroke_groups,
                                           start=start,
                                           length=length,
                                           n_chars_per_row=n_chars_per_row)

    for renderer in (png_renderer, svg_renderer, pdf_renderer):
        renderer.draw_background()
        renderer.draw_writing_steps()
        
    png_renderer.write_to_png("test_steps.png")