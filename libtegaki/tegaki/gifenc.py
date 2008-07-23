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

def rgb(color):
    """
    Returns the RGB triplet for color.
    """
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    return (r,g,b)

def color(r, g, b):
    """
    Returns the 24bits color from the RGB triplet. 
    """
    return (((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF))  

class ColorTable(object):

    def __init__(self):
        self.alpha = None

    def get_color(self, index):
        raise NotImplementedError

    def get_n_colors(self):
        raise NotImplementedError
    
    def get_index(self, color):
        raise NotImplementedError
    
    def quantize(self, data):
        """
        Returns the data quantized with the color table.
        """
        return [self.get_index(color) for color in data]
    
class SimpleColorTable(ColorTable):
    
    def __init__(self):
        ColorTable.__init__(self)
    
        self._table = self._get_table()
        
    def _get_table(self):
        table = []
        for r in (0x00, 0x33, 0x66, 0x99, 0xcc, 0xff):
            for g in (0x00, 0x33, 0x66, 0x99, 0xcc, 0xff):
                for b in (0x00, 0x33, 0x66, 0x99, 0xcc, 0xff):
                    table.append(color(r, g, b))
        return table
    
    def get_color(self, index):
        return self._table[index]

    def get_n_colors(self):
        return len(self._table)
    
    def get_index(self, color):
        r, g, b = rgb(color)
        return (((r / 47) % 6) * 6 * 6 + ((g / 47) % 6) * 6 + ((b / 47) % 6)) # use 25 instead of 47?

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

        # Extensions intended to modify a Table-based image must appear
        # before the corresponding Image Descriptor.
        self._write_graphic_control(color_table, display_millis)
        
        self._write_image_descriptor(image)
        self._write_image_data(image)

    def set_looping(self):
        self._write_loop()
        
    def set_comments(self, comments):
        if type(comments) != list:
            raise TypeError
        
        self._write_comments(comments)        
        
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
        
    def _write(self, buf):
        self.fp.write(buf)

    # blocks    

    def _write_header(self):
        self._write("GIF89a")
        
    def _write_lsd(self): # logical screen description
        assert(self.color_table.get_n_colors() >= 2)

        self._write_le16(self.width)
        self._write_le16(self.height)

        # Global Color Table Flag - Flag indicating the presence of a
        # Global Color Table; if the flag is set, the Global Color Table will
        # immediately follow the Logical Screen Descriptor. This flag also
        # selects the interpretation of the Background Color Index; if the
        # flag is set, the value of the Background Color Index field should
        # be used as the table index of the background color. (This field is
        # the most significant bit of the byte.)
        #
        #    Values :    0 -   No Global Color Table follows, the Background
        #                      Color Index field is meaningless.
        #                1 -   A Global Color Table will immediately follow, the
        #                      Background Color Index field is meaningful.
        if self.color_table:
            self._write_bits(1, 1)
        else:
            self._write_bits(0, 1)

        # Color resolution = number of bits per color - 1
        # Color Resolution - Number of bits per primary color available
        # to the original image, minus 1. This value represents the size of
        # the entire palette from which the colors in the graphic were
        # selected, not the number of colors actually used in the graphic.
        # For example, if the value in this field is 3, then the palette of
        # the original image had 4 bits per primary color available to create
        # the image.  This value should be set to indicate the richness of
        # the original palette, even if not every color from the whole
        # palette is available on the source machine.
        self._write_bits(0x7, 3)

        # Sort Flag - Indicates whether the Global Color Table is sorted.
        # If the flag is set, the Global Color Table is sorted, in order of
        # decreasing importance. Typically, the order would be decreasing
        # frequency, with most frequent color first. This assists a decoder,
        # with fewer available colors, in choosing the best subset of colors;
        # the decoder may use an initial segment of the table to render the
        # graphic.
        #
        #    Values :    0 -   Not ordered.
        #                1 -   Ordered by decreasing importance, most
        #                      important color first.
        self._write_bits(0, 1)

        # Size of the color table
        # size = 2 ^ (value of the field + 1)
        if self.color_table:
            size = log2n(self.color_table.get_n_colors() - 1) - 1
        else:
            size = 0

        self._write_bits(size, 3)

        # Background Color Index - Index into the Global Color Table for
        # the Background Color. The Background Color is the color used for
        # those pixels on the screen that are not covered by an image. If the
        # Global Color Table Flag is set to (zero), this field should be zero
        # and should be ignored.
        self._write_byte(0)

        # Pixel Aspect Ratio - Factor used to compute an approximation
        # of the aspect ratio of the pixel in the original image.  If the
        # value of the field is not 0, this approximation of the aspect ratio
        # is computed based on the formula:
        #
        # Aspect Ratio = (Pixel Aspect Ratio + 15) / 64
        #
        # The Pixel Aspect Ratio is defined to be the quotient of the pixel's
        # width over its height.  The value range in this field allows
        # specification of the widest pixel of 4:1 to the tallest pixel of
        # 1:4 in increments of 1/64th.
        #    
        #    Values :        0 -   No aspect ratio information is given.
        #               1..255 -   Value used in the computation.
        self._write_byte(0)

    def _write_graphic_control (self, color_table, display_millis):
        # Identifies the block as an extension
        self._write_byte(0x21)
        # Identifies the block as a graphic control block
        self._write_byte(0xF9)
        
        self._write_byte(0x04) # Block size
        self._write_bits(0, 3) # Reserved
        
        # Disposal Method - Indicates the way in which the graphic is to
        # be treated after being displayed.
        #
        #    Values :    0 -   No disposal specified. The decoder is
        #                      not required to take any action.
        #                1 -   Do not dispose. The graphic is to be left
        #                      in place.
        #                2 -   Restore to background color. The area used by the
        #                      graphic must be restored to the background color.
        #                3 -   Restore to previous. The decoder is required to
        #                      restore the area overwritten by the graphic with
        #                      what was there prior to rendering the graphic.
        self._write_bits(1, 3)
        
        # User Input Flag - Indicates whether or not user input is
        # expected before continuing. If the flag is set, processing will
        # continue when user input is entered. The nature of the User input
        # is determined by the application (Carriage Return, Mouse Button
        # Click, etc.).
        #
        #    Values :    0 -   User input is not expected.
        #                1 -   User input is expected.
        self._write_bits(0, 1) # no user input required

        # Transparency Flag - Indicates whether a transparency index is
        # given in the Transparent Index field. (This field is the least
        # significant bit of the byte.)
        #
        #    Values :    0 -   Transparent Index is not given.
        #                1 -   Transparent Index is given.
        if color_table.aplha:
            self._write_bits(1, 1)
        else:
            self._write_bits(0, 1)
        
        # Delay Time - If not 0, this field specifies the number of
        # hundredths (1/100) of a second to wait before continuing with the
        # processing of the Data Stream. The clock starts ticking immediately
        # after the graphic is rendered. This field may be used in
        # conjunction with the User Input Flag field.            
        self._write_le16(milliseconds / 10)

        # Transparency Index - The Transparency Index is such that when
        # encountered, the corresponding pixel of the display device is not
        # modified and processing goes on to the next pixel. The index is
        # present if and only if the Transparency Flag is set to 1.
        if color_table.alpha:
            self._write_byte(color_table.num_colors)
        else:
            self._write_byte(0)
        
        # Block Terminator - This zero-length data block marks the end of    
        self._write_byte(0)

    def _write_image_descriptor(self, image):
        # Identifies the beginning of an image descriptor
        self._write_byte(0x2C)
        
        self._write_le16(image.x)
        self._write_le16(image.y)
        self._write_le16(image.width)
        self._write_le16(image.height)

        # Local Color Table Flag - Indicates the presence of a Local Color
        # Table immediately following this Image Descriptor. (This field is
        # the most significant bit of the byte.)
        #
        #   Values :    0 -   Local Color Table is not present. Use
        #                     Global Color Table if available.
        #               1 -   Local Color Table present, and to follow
        #                     immediately after this Image Descriptor.
        if image.color_table:
            self._write_bits(1, 1)
        else:
            self._write_bits(0, 1)
        
        # Interlace Flag - Indicates if the image is interlaced. An image
        # is interlaced in a four-pass interlace pattern; see Appendix E for
        # details.
        #
        #    Values :    0 - Image is not interlaced.
        #                1 - Image is interlaced.
        self._write_bits(0, 1)
        
        # Sort flag - See same flag in LSD block.
        self._write_bits(0, 1)
        
        self._write_bits(0, 2) # Reserved

        # Local color table size - See LSD block.
        if image.color_table:
            n = log2n(image.color_table.get_n_colors() - 1) - 1
        else:
            n = 0

        self._write_bits(n, 3)

        if image.color_table:
            self._write_color_table(image.color_table)

    def _write_color_table(self, color_table):
        i = color_table.get_n_colors()
        
        table_size = 1 << log2n (i - 1)

        for i in range(self.color_table.get_n_colors()):
            for color in self.color_table.get_rgb(i):
                self._write_byte(color)

        if color_table.alpha:
            self._write("\272\219\001")

        while i < table_size:
            self._write("\0\0\0")
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

    def _write_loop(self):
        # Identifies the block as an extension
        self._write_byte(0x21)
        # Identifies the extension as the Application extension
        self._write_byte(0xFF)
        
        # Block size
        self._write_byte(11)
        
        # Application
        self._write("NETSCAPE2.0")
        
        # Application authentication
        self._write_byte(3)
        
        # ???
        self._write_byte(1)
        self._write_byte(0)
        self._write_byte(0)
        
        # Block terminator
        self._write_byte(0)
        
    def _write_comments(self, comments):
        # Identifies the block as an extension
        self._write_byte(0x21)
        # Identifies the extension as the Comment extension
        self._write_byte(0xFE)
        
        for comment in comments:
            comment = comment[0:253] # Maximum length is 255
            self._write_byte(len(comment))
            self._write(comment)
        
        # Block terminator
        self._write_byte(0)
                        

if __name__ == "__main__":
    #enc = GIFEncoder(1280, 800, "test.gif")
    #color_table = ColorTable()
    #enc.set_color_table(color_table)
    #enc.close()
    color_table = SimpleColorTable()
    i = color_table.get_index(color(29, 100, 120))
    print rgb(color_table.get_color(i))
    