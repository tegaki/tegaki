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

class WritingCairoRenderer(object):

    def __init__(self, cairo_context):
        self.cr = cairo_context
        self._init_colors()

    def _init_colors(self):
        self.handwriting_line_color = (0x0000, 0x0000, 0x0000, 1.0)
        self.axis_line_color = (0, 0, 0, 0.2)
        self.annotations_color = (0x8000, 0x0000, 0x0000, 0.2)
        self.annotations_color = (0, 0, 0, 0.2)

    def _with_handwriting_line(self):
        self.cr.set_line_width(8)
        self.cr.set_line_cap(cairo.LINE_CAP_ROUND)
        self.cr.set_line_join(cairo.LINE_JOIN_ROUND)

    def _with_axis_line(self):
        self.cr.set_source_rgba (*self.axis_line_color)
        self.cr.set_line_width (4)
        self.cr.set_dash ([8, 8], 2)

    def _with_annotations(self):
        self.cr.set_source_rgba (*self.annotations_color)
        self.annotation_font_size = 30 # user space units
        self.cr.set_font_size(self.annotation_font_size)
        
    def draw_stroke(self, stroke, index, color, draw_annotation=True):
        l = len(stroke)

        self.cr.save()
        
        self._with_handwriting_line()
        self.cr.set_source_rgba(*self.handwriting_line_color)

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

    def draw_writing(self, writing, draw_annotation=True):
        strokes = writing.get_strokes(full=True)
        n_strokes = len(strokes)

        for i in range(n_strokes):
            self.draw_stroke(strokes[i],
                             i,
                             self.handwriting_line_color,
                             draw_annotation)
       
    def draw_background(self):
        self.cr.save()
        self.cr.set_source_rgb(1, 1, 1)
        self.cr.paint()
        self.cr.restore()

    def draw_axis(self):
        self.cr.save ()

        self._with_axis_line()

        self.cr.move_to (500, 0)
        self.cr.line_to (500, 1000)
        self.cr.move_to (0, 500)
        self.cr.line_to (1000, 500)
        
        self.cr.stroke ()
        self.cr.restore ()

class WritingImageRenderer(WritingCairoRenderer):

    def __init__(self, width, height):
        """
        width and height are in pixels.
        """
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(self.surface)
        cr.scale(float(width) / Writing.WIDTH, float(height) / Writing.HEIGHT)
        WritingCairoRenderer.__init__(self, cr)
        
    def write_to_png(self, filename):
        self.surface.write_to_png(filename)

class WritingSVGRenderer(WritingCairoRenderer):
    
    def __init__(self, filename, width, height):
        """
        width and height are in points (1 point == 1/72.0 inch).
        """
        self.surface = cairo.SVGSurface(filename, width, height)
        cr = cairo.Context(self.surface)
        cr.scale(float(width) / Writing.WIDTH, float(height) / Writing.HEIGHT)
        WritingCairoRenderer.__init__(self, cr)

class WritingPDFRenderer(WritingCairoRenderer):
    
    def __init__(self, filename, width, height):
        """
        width and height are in points (1 point == 1/72.0 inch).
        """
        self.surface = cairo.PDFSurface(filename, width, height)
        cr = cairo.Context(self.surface)
        cr.scale(float(width) / Writing.WIDTH, float(height) / Writing.HEIGHT)
        WritingCairoRenderer.__init__(self, cr)

def inch_to_pt(*arr):
    return [inch * 72 for inch in arr]

def cm_to_pt(*arr):
    return [round(cm * 28.3464567) for cm in arr]

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print "Need a writing file at least."
        sys.exit()

    char = Character()
    char.read(sys.argv[1])

    png_renderer = WritingImageRenderer(400, 400)
    svg_renderer = WritingSVGRenderer("test.svg", *cm_to_pt(10, 10))
    pdf_renderer = WritingPDFRenderer("test.pdf", *cm_to_pt(20, 20))

    for renderer in (png_renderer, svg_renderer, pdf_renderer):
        renderer.draw_background()
        renderer.draw_axis()
        renderer.draw_writing(char.get_writing())
        
    png_renderer.write_to_png("test.png")