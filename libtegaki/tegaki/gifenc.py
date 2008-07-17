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

def from_le16(c):
    return ord(c[0]) + (ord(c[1]) << 8)

def to_le16(i):
    return chr(i & 255) + chr(i >> 8 & 255)

def from_byte(c):
    return ord(c[0])

def to_byte(i):
    return chr(i & 255)

def log2n(n):
    ret = 0
    while n > 0:
        n >>= 1
        ret += 1
  
    return ret

class ColorTable(object):

    def __init__(self):
        self.colors = [0x00000000, 0x00FFFFFF] # black and white
        self.alpha = None

    def get_color(self, index):
        """
        Returns the color as an integer
        """
        return self.colors[index]

    def get_rgb(self, index):
        """
        Returns the color as a RGB triplet
        """
        color = self.get_color(index)
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return (r,g,b)

    def get_n_colors(self):
        return len(self.colors)

class GIFEncoder(object):

    class Image(object):

        def __init__(self):
            self.x = None
            self.y = None
            self.width = None
            self.height = None
            self.data = None
            self.color_table = None
            self.rowstride = None

    def __init__(self, width, height, file):
        self.width = width
        self.height = height
        self.file = file
        self.color_table = None

        self.fp = open(file, "w")
        self.bits = 0
        self.n_bits = 0

        self._write_header()

    def set_color_table(self, color_table):
        self.color_table = color_table

        self._write_lsd()
        self._write_color_table(color_table)

    def add_image(self, x, y, width, height,
                  display_millis, data, rowstride,
                  color_table=None):

        if x + width > self.width or width <= 0 or \
           y + height > self.height or height <= 0:
            raise TypeError

        image = Image()
        image.x = x
        image.y = y
        image.width = width
        image.height = height
        image.data = data
        image.color_table = color_table
        image.rowstride = rowstride

        if not color_table:
            color_table = self.color_table

        self._write_graphic_control(color_table, display_millis)
        self._write_image_description(image)
        self._write_image_data(image)
        
    def close(self):
        self.fp.close()

    # write routines

    def _write_le16(self, n):
        self.fp.write(to_le16(n))

    def _write_byte(self, n):
        self.fp.write(to_byte(n))

    def _write_bits(self, bits, nbits):
        if bits > 24:
            return

        if (bits & ((1 << nbits) - 1)) != bits:
            return

        self.bits <<= nbits
        self.bits |= bits
        nbits = self.n_bits + nbits

        self.n_bits = 0

        while nbits >= 8:
            nbits -= 8
            self._write_byte(self.bits >> nbits)

        self.n_bits = nbits
        self.bits &= (1 << nbits) - 1

    # blocks    

    def _write_header(self):
        self.fp.write("GIF89a")
        
    def _write_lsd(self): # logical screen description
        assert(self.color_table.get_n_colors() >= 2)

        self._write_le16(self.width)
        self._write_le16(self.height)

        # global color table flag
        # indicates whether a global color_table is present
        # the color_table should follow directly after the lsd block
        if self.color_table:
            self._write_bits(1, 1)
        else:
            self._write_bits(0, 1)

        # color resolution = number of bits per color - 1
        self._write_bits(0x7, 3)

        # sort flag, whether the global color table is sorted or not
        # 0 = not sorted
        # 1 = ordered by decreasing importance, most frequent color first
        self._write_bits(0, 1)

        # size of the color table
        # size = 2 ^ (value of the field + 1)
        if self.color_table:
            size = log2n(self.color_table.get_n_colors() - 1) - 1
        else:
            size = 0

        self._write_bits(size, 3)

        # background color index in the color table
        # should be 0 if no color_table used
        self._write_byte(0)

        # pixel aspect ratio
        # if different from 0, then the following formula is used:
        # aspect ratio = (pixel aspect ratio + 15) / 64
        self._write_byte(0)

    def _write_graphic_control (self, color_table, display_millis):
        self._write_byte(0x21) # extension 
        self._write_byte(0xF9) # extension type
        self._write_byte(0x04) # size
        self._write_bits(0, 3) # reserved
        self._write_bits(1, 3) # disposal: do not dispose
        self._write_bits(0, 1) # no user input required

        # transparent color?
        if color_table.aplha:
            self._write_bits(1, 1)
        else:
            self._write_bits(0, 1)
            
        self._write_uint16(milliseconds / 10) # display this long

        # transparent color index
        if color_table.alpha:
            self._write_byte(color_table.num_colors)
        else:
            self._write_byte(0)
            
        self._write_byte (0) # terminator

    def _write_image_description(self, image):
        self._write_byte(0x2C)
        self._write_uint16(image.x)
        self._write_uint16(image.y)
        self._write_uint16(image.width)
        self._write_uint16(image.height)

        # local color table flag
        if image.color_table:
            self._write_bits(1, 1)
        else:
            self._write_bits(0, 1)
        
        self._write_bits(0, 1) # interlace flag
        self._write_bits(0, 1) # sort flag
        self._write_bits(0, 2) # reserved

        # number of color_table
        if image.color_table:
            n = log2n(image.color_table.get_n_colors() - 1) - 1
        else:
            n = 0

        self._write_bits(n, 3)

        self._write_color_table(image.color_table)

    def _write_color_table(self, color_table):
        i = color_table.get_n_colors()
        
        table_size = 1 << log2n (i - 1)

        for i in range(self.color_table.get_n_colors()):
            for color in self.color_table.get_rgb(i):
                self._write_byte(color)

        if color_table.alpha:
            self.fp.write("\272\219\001")

        while i < table_size:
            self.fp.write("\0\0\0")
            i += 1

    def _write_image_data(self, image):
        pass
    #guint codesize, wordsize, x, y;
    #guint next = 0, count = 0, clear, eof, hashcode, hashvalue, cur, codeword;
    #guint8 *data;
    ##define HASH_SIZE (5003)
    #struct {
        #guint value;
        #guint code;
    #} hash[HASH_SIZE];
    #EncodeBuffer buffer = { { 0, }, 0, 0, 0 };

    #codesize = log2n (gifenc_color_table_get_num_colors (image->color_table ?
        #image->color_table : enc->color_table) - 1);
    #codesize = MAX (codesize, 2);
    #gifenc_write_byte (enc, codesize);
    #//g_print ("codesize with %u color_table is %u\n", enc->n_color_table,
#codesize);
    #clear = 1 << codesize;
    #eof = clear + 1;
    #codeword = cur = *image->data;
    #//g_print ("read byte %u\n", cur);
    #wordsize = codesize + 1;
    #gifenc_buffer_append (enc, &buffer, clear, wordsize);
    #if (1 == image->width) {
        #y = 1;
        #x = 0;
        #data = image->data + image->rowstride;
    #} else {
        #y = 0;
        #x = 1;
        #data = image->data;
    #}

    #while (y < image->height) {
        #count = eof + 1;
        #next = (1 << wordsize);
        #/* clear hash */
        #memset (hash, 0xFF, sizeof (hash));
        #while (y < image->height) {
        #cur = data[x];
        #//g_print ("read byte %u\n", cur);
        #x++;
        #if (x >= image->width) {
        #y++;
        #x = 0;
        #data += image->rowstride;
        #}
        #hashcode = codeword ^ (cur << 4);
        #hashvalue = (codeword << 8) | cur;
    #loop:
        #if (hash[hashcode].value == hashvalue) {
        #codeword = hash[hashcode].code;
        #continue;
        #}
        #if (hash[hashcode].value != (guint) -1) { /* not empty */
        #hashcode = (hashcode + 0xF) % HASH_SIZE;
        #goto loop;
        #}
        #/* found empty slot, put code there */
        #hash[hashcode].value = hashvalue;
        #hash[hashcode].code = count;
        #//g_print ("saving as %u (%X):", count, count);
        #gifenc_buffer_append (enc, &buffer, codeword, wordsize);
        #count++;
        #codeword = cur;
        #if (count > next) {
        #if (wordsize == 12) {
        #gifenc_buffer_append (enc, &buffer, clear, wordsize);
        #wordsize = codesize + 1;
        #break;
        #}
        #next = MIN (next << 1, 0xFFF);
        #wordsize++;
        #}
        #}
    #}
    #gifenc_buffer_append (enc, &buffer, codeword, wordsize);
    #if (count == next) {
        #wordsize++;
        #if (wordsize > 12) {
        #wordsize = codesize + 1;
        #gifenc_buffer_append (enc, &buffer, clear, wordsize);
        #}
    #}
    #gifenc_buffer_append (enc, &buffer, eof, wordsize);
    #gifenc_buffer_flush (enc, &buffer);


if __name__ == "__main__":
    enc = GIFEncoder(1280, 800, "test.gif")
    color_table = ColorTable()
    enc.set_color_table(color_table)
    enc.close()