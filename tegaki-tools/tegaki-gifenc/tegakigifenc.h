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

#ifndef TEGAKIGIFENC_H
#define TEGAKIGIFENC_H

#include <stdio.h>

extern "C" {
#include "gifenc/gifenc.h"
}

namespace tegakigifenc {

class GifEncoder {

public:
    GifEncoder();
    ~GifEncoder();
    bool open(char *filename, 
              unsigned int width, unsigned int height,
              bool alpha, bool loop);
    void add_image(unsigned int x, unsigned int y,
                   unsigned int width, unsigned int height,
                   unsigned int display_millis, 
                   char *data,
                   unsigned int rowstride);
    void set_palette_for_image(char *data,
                               unsigned int width, unsigned int height,
                               unsigned int rowstride,
                               bool alpha,
                               unsigned int max_colors);
    void close();

private:
    Gifenc *enc;
    GifencPalette *palette; 
    FILE *output;
};


}

#endif


