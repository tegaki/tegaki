/*
* Copyright (C) 2009 The Tegaki project contributors
*
* This program is free software; you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation; either version 2 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License along
* with this program; if not, write to the Free Software Foundation, Inc.,
* 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/

/* 
* Contributors to this file:
*  - Mathieu Blondel
*/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "tegakigifenc.h"


namespace tegakigifenc {

static gboolean
encoder_write_data (gpointer       closure,
                    const guchar * data,
                    gsize          len,
                    GError **      error)
{
  FILE *f = (FILE *)closure;
  fwrite(data, 1, len, f);
  return 1;
}

GifEncoder::GifEncoder()
{
    palette = NULL;
}

void GifEncoder::set_palette_for_image(char *data,
                                       unsigned int width, unsigned int height,
                                       unsigned int rowstride,
                                       bool alpha,
                                       unsigned int max_colors)
{
    palette = gifenc_quantize_image ((const guint8 *) data,
                                     width, height, rowstride, 
                                     alpha ? TRUE : FALSE, max_colors);
}

bool GifEncoder::open(char *filename, 
                      unsigned int width, unsigned int height,
                      bool alpha, bool loop)
{
    output = fopen(filename, "w");
    if (!output) return false;
    enc = gifenc_new(width, height, encoder_write_data, output, NULL);
    if (!palette) palette = gifenc_palette_get_simple(alpha ? TRUE : FALSE);
    gifenc_initialize (enc, palette, loop ? TRUE : FALSE, NULL);
    return true;
}

void GifEncoder::add_image(unsigned int x, unsigned int y,
                           unsigned int width, unsigned int height,
                           unsigned int display_millis, 
                           char *data,
                           unsigned int rowstride) 
{
    guint8 *target = (guint8 *) malloc(width * height * sizeof(guint8) * 4);
    gifenc_dither_rgb(target, rowstride, palette, (guint8 *)data, 
                      width, height, rowstride);
    gifenc_add_image(enc, x, y, width, height, display_millis, 
                     (guint8 *)target, rowstride, NULL);
    free(target);
}

void GifEncoder::close() {
    gifenc_close(enc, NULL);
}

GifEncoder::~GifEncoder() {
    if(enc) gifenc_free(enc);
}

}
