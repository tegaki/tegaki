/* simple gif encoder
 * Copyright (C) 2005 Benjamin Otte <otte@gnome.org
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 3 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <glib/gstdio.h>
#include "gifenc.h"


/*** UTILITIES ***/

static guint
log2n (guint number)
{
  guint ret = 0;
  while (number > 0) {
    number >>= 1;
    ret++;
  }
  return ret;
}

#define RED(x) ((guint8) ((x) >> 16))
#define GREEN(x) ((guint8) ((x) >> 8))
#define BLUE(x) ((guint8) (x))

#define COLOR(r, g, b) (((r) << 16) | ((g) << 8) | (b))

/*** WRITE ROUTINES ***/

static gboolean
gifenc_flush (Gifenc *enc, GError **error)
{
  gboolean result;

  if (enc->buffer->len == 0)
    return TRUE;

  result = enc->write_func (enc->write_data, enc->buffer->data, 
      enc->buffer->len, error);

  g_byte_array_set_size (enc->buffer, 0);
  return result;
}

static void
gifenc_write_uint16 (Gifenc *enc, guint16 value)
{
  g_return_if_fail (enc->n_bits == 0);
  
  value = GUINT16_TO_LE (value);
  g_byte_array_append (enc->buffer, (guint8 *) &value, 2);
}

static void
gifenc_write_byte (Gifenc *enc, guint8 value)
{
  g_return_if_fail (enc->n_bits == 0);
  
  g_byte_array_append (enc->buffer, &value, 1);
}

static void
gifenc_write_bits (Gifenc *enc, guint bits, guint nbits)
{
  g_return_if_fail (bits <= 24);
  g_return_if_fail ((bits & ((1 << nbits) - 1)) == bits);

  enc->bits <<= nbits;
  enc->bits |= bits;
  nbits = enc->n_bits + nbits;
  enc->n_bits = 0;
  while (nbits >= 8) {
    nbits -= 8;
    gifenc_write_byte (enc, enc->bits >> nbits);
  }
  enc->n_bits = nbits;
  enc->bits &= (1 << nbits) - 1;
}

/*** FUNCTIONS TO WRITE BLOCKS ***/

static void
gifenc_write_header (Gifenc *enc)
{
  g_byte_array_append (enc->buffer, (const guchar *) "GIF89a", 6);
}

static void
gifenc_write_lsd (Gifenc *enc, GifencPalette *palette)
{
  g_assert (palette == NULL || gifenc_palette_get_num_colors (palette) >= 2);

  gifenc_write_uint16 (enc, enc->width);
  gifenc_write_uint16 (enc, enc->height);
  gifenc_write_bits (enc, palette ? 1 : 0, 1); /* global color table flag */
  gifenc_write_bits (enc, 0x7, 3); /* color resolution */
  gifenc_write_bits (enc, 0, 1); /* sort flag */
  gifenc_write_bits (enc, palette ? 
      log2n (gifenc_palette_get_num_colors (palette) - 1) - 1 : 0, 3); /* number of colors */
  gifenc_write_byte (enc, 0); /* background color */
  gifenc_write_byte (enc, 0); /* pixel aspect ratio */
}

static void
gifenc_write_color_table (Gifenc *enc, GifencPalette *palette)
{
  guint i, table_size;

  if (!palette)
    return;
  i = gifenc_palette_get_num_colors (palette);
  table_size = 1 << log2n (i - 1);
  for (i = 0; i < palette->num_colors; i++) {
    gifenc_write_byte (enc, RED (palette->colors[i]));
    gifenc_write_byte (enc, GREEN (palette->colors[i]));
    gifenc_write_byte (enc, BLUE (palette->colors[i]));
  }
  if (palette->alpha) {
    g_byte_array_append (enc->buffer, (guint8 *) "\272\219\001", 3);
    i++;
  }
  for (; i < table_size; i++) {
    g_byte_array_append (enc->buffer, (guint8 *) "\0\0\0", 3);
  }
}

typedef struct {
  guint x;
  guint y;
  guint width;
  guint height;
  GifencPalette *palette;
  guint8 *data;
  guint rowstride;
} GifencImage;

static void
gifenc_write_image_description (Gifenc *enc, const GifencImage *image)
{
  gifenc_write_byte (enc, 0x2C);
  gifenc_write_uint16 (enc, image->x);
  gifenc_write_uint16 (enc, image->y);
  gifenc_write_uint16 (enc, image->width);
  gifenc_write_uint16 (enc, image->height);
  gifenc_write_bits (enc, image->palette ? 1 : 0, 1); /* local color table flag */
  gifenc_write_bits (enc, 0, 1); /* interlace flag */
  gifenc_write_bits (enc, 0, 1); /* sort flag */
  gifenc_write_bits (enc, 0, 2); /* reserved */
  gifenc_write_bits (enc, image->palette ? 
      log2n (gifenc_palette_get_num_colors (image->palette) - 1) - 1 : 0, 3); /* number of palette */
  gifenc_write_color_table (enc, image->palette);
}

typedef struct {
  guint8 data[255];
  guint bytes;
  guint current_data;
  guint bits;
} EncodeBuffer;

static void
gifenc_buffer_write (Gifenc *enc, EncodeBuffer *buffer)
{
  if (buffer->bytes == 0)
    return;
  gifenc_write_byte (enc, buffer->bytes);
  g_byte_array_append (enc->buffer, buffer->data, buffer->bytes);
  buffer->bytes = 0;
}

static void G_GNUC_UNUSED
print_bits (const char *text, guint data, int bits)
{
  int i;
  g_print ("%s %u (", text, data);
  for (i = bits - 1; i >= 0; i--) {
    g_print ("%c", data & (1 << i) ? '1' : '0');
  }
  g_print (")\n");
}
#define print_bits(text, data, bits)

static void
gifenc_buffer_append (Gifenc *enc, EncodeBuffer *buffer, guint data, guint bits)
{
  g_assert (buffer->bits + bits < 24);

  //g_print ("got code %u (%u)\n", data, bits);
  print_bits ("appending", data, bits);
  buffer->current_data |= (data << buffer->bits);
  buffer->bits += bits;
  while (buffer->bits >= 8) {
    if (buffer->bytes == 255)
      gifenc_buffer_write (enc, buffer);
    buffer->data[buffer->bytes] = buffer->current_data;
    print_bits ("got", buffer->data[buffer->bytes], 8);
    buffer->bits -= 8;
    buffer->current_data >>= 8;
    buffer->bytes++;
  }
}

static void
gifenc_buffer_flush (Gifenc *enc, EncodeBuffer *buffer)
{
  if (buffer->bits)
    gifenc_buffer_append (enc, buffer, 0, 8 - buffer->bits);
  gifenc_buffer_write (enc, buffer);
  gifenc_write_byte (enc, 0);
}

static void
gifenc_write_image_data (Gifenc *enc, const GifencImage *image)
{
  guint codesize, wordsize, x, y;
  guint next = 0, count = 0, clear, eof, hashcode, hashvalue, cur, codeword;
  guint8 *data;
#define HASH_SIZE (5003)
  struct {
    guint value;
    guint code;
  } hash[HASH_SIZE];
  EncodeBuffer buffer = { { 0, }, 0, 0, 0 };
  
  codesize = log2n (gifenc_palette_get_num_colors (image->palette ? 
	image->palette : enc->palette) - 1);
  codesize = MAX (codesize, 2);
  gifenc_write_byte (enc, codesize);
  //g_print ("codesize with %u palette is %u\n", enc->n_palette, codesize);
  clear = 1 << codesize;
  eof = clear + 1;
  codeword = cur = *image->data;
  //g_print ("read byte %u\n", cur);
  wordsize = codesize + 1;
  gifenc_buffer_append (enc, &buffer, clear, wordsize);
  if (1 == image->width) {
    y = 1;
    x = 0;
    data = image->data + image->rowstride;
  } else {
    y = 0;
    x = 1;
    data = image->data;
  }

  while (y < image->height) {
    count = eof + 1;
    next = (1 << wordsize);
    /* clear hash */
    memset (hash, 0xFF, sizeof (hash));
    while (y < image->height) {
      cur = data[x];
      //g_print ("read byte %u\n", cur);
      x++;
      if (x >= image->width) {
	y++;
	x = 0;
	data += image->rowstride;
      }
      hashcode = codeword ^ (cur << 4);
      hashvalue = (codeword << 8) | cur;
loop:
      if (hash[hashcode].value == hashvalue) {
	codeword = hash[hashcode].code;
	continue;
      }
      if (hash[hashcode].value != (guint) -1) { /* not empty */
	hashcode = (hashcode + 0xF) % HASH_SIZE;
	goto loop;
      }
      /* found empty slot, put code there */
      hash[hashcode].value = hashvalue;
      hash[hashcode].code = count;
      //g_print ("saving as %u (%X):", count, count);
      gifenc_buffer_append (enc, &buffer, codeword, wordsize);
      count++;
      codeword = cur;
      if (count > next) {
	if (wordsize == 12) {
	  gifenc_buffer_append (enc, &buffer, clear, wordsize);
	  wordsize = codesize + 1;
	  break;
	}
	next = MIN (next << 1, 0xFFF);
	wordsize++;
      }
    }
  }
  gifenc_buffer_append (enc, &buffer, codeword, wordsize);
  if (count == next) {
    wordsize++;
    if (wordsize > 12) {
      wordsize = codesize + 1;
      gifenc_buffer_append (enc, &buffer, clear, wordsize);
    }
  }
  gifenc_buffer_append (enc, &buffer, eof, wordsize);
  gifenc_buffer_flush (enc, &buffer);
}

static void
gifenc_write_graphic_control (Gifenc *enc, GifencPalette *palette, 
    guint milliseconds)
{
  gifenc_write_byte (enc, 0x21); /* extension */
  gifenc_write_byte (enc, 0xF9); /* extension type */
  gifenc_write_byte (enc, 0x04); /* size */
  gifenc_write_bits (enc, 0, 3); /* reserved */
  gifenc_write_bits (enc, 1, 3); /* disposal: do not dispose */
  gifenc_write_bits (enc, 0, 1); /* no user input required */
  gifenc_write_bits (enc, palette->alpha ? 1 : 0, 1); /* transparent color? */
  gifenc_write_uint16 (enc, milliseconds / 10); /* display this long */
  gifenc_write_byte (enc, palette->alpha ? palette->num_colors : 0); /* transparent color index */
  gifenc_write_byte (enc, 0); /* terminator */
}

static void
gifenc_write_loop (Gifenc *enc)
{
  gifenc_write_byte (enc, 0x21); /* extension */
  gifenc_write_byte (enc, 0xFF); /* application extension */
  gifenc_write_byte (enc, 11); /* block size */
  g_byte_array_append (enc->buffer, (guint8 *) "NETSCAPE2.0", 11);
  gifenc_write_byte (enc, 3); /* block size */
  gifenc_write_byte (enc, 1); /* ??? */
  gifenc_write_byte (enc, 0); /* ??? */
  gifenc_write_byte (enc, 0); /* ??? */
  gifenc_write_byte (enc, 0); /* block terminator */
}

/*** PUBLIC API ***/

Gifenc *
gifenc_new (guint width, guint height, GifencWriteFunc write_func, 
    gpointer write_data, GDestroyNotify write_destroy)
{
  Gifenc *enc;

  g_return_val_if_fail (width <= G_MAXUINT16, NULL);
  g_return_val_if_fail (height <= G_MAXUINT16, NULL);
  g_return_val_if_fail (write_func, NULL);
  
  enc = g_slice_new0 (Gifenc);
  enc->width = width;
  enc->height = height;
  enc->buffer = g_byte_array_new ();
  enc->write_func = write_func;
  enc->write_data = write_data;
  enc->write_destroy = write_destroy;

  return enc;
}

gboolean
gifenc_initialize (Gifenc *enc, GifencPalette *palette, gboolean loop, GError **error)
{
  g_return_val_if_fail (enc != NULL, FALSE);
  g_return_val_if_fail (enc->state == GIFENC_STATE_NEW, FALSE);
  g_return_val_if_fail (palette != NULL, FALSE);

  gifenc_write_header (enc);
  gifenc_write_lsd (enc, palette);
  gifenc_write_color_table (enc, palette);
  if (loop)
    gifenc_write_loop (enc);
  if (!gifenc_flush (enc, error))
    return FALSE;

  enc->palette = palette;
  enc->state = GIFENC_STATE_INITIALIZED;
  return TRUE;
}

gboolean
gifenc_add_image (Gifenc *enc, guint x, guint y, guint width, guint height, 
    guint display_millis, guint8 *data, guint rowstride, GError **error)
{
  GifencImage image = { x, y, width, height, NULL, data, rowstride };

  g_return_val_if_fail (enc != NULL, FALSE);
  g_return_val_if_fail (enc->state == GIFENC_STATE_INITIALIZED, FALSE);
  g_return_val_if_fail (width > 0, FALSE);
  g_return_val_if_fail (x + width <= enc->width, FALSE);
  g_return_val_if_fail (height > 0, FALSE);
  g_return_val_if_fail (y + height <= enc->height, FALSE);

  //g_print ("adding image (display time %u)\n", display_millis);
  gifenc_write_graphic_control (enc, image.palette ? image.palette : enc->palette, 
      display_millis);
  gifenc_write_image_description (enc, &image);
  gifenc_write_image_data (enc, &image);
  return gifenc_flush (enc, error);
}

gboolean
gifenc_close (Gifenc *enc, GError **error)
{
  g_return_val_if_fail (enc != NULL, FALSE);
  g_return_val_if_fail (enc->state == GIFENC_STATE_INITIALIZED, FALSE);

  gifenc_write_byte (enc, 0x3B);
  if (!gifenc_flush (enc, error))
    return FALSE;

  enc->state = GIFENC_STATE_CLOSED;
  return TRUE;
}

gboolean
gifenc_free (Gifenc *enc)
{
  gboolean success;

  g_return_val_if_fail (enc != NULL, FALSE);

  success = enc->state == GIFENC_STATE_CLOSED;

  if (enc->write_destroy)
    enc->write_destroy (enc->write_data);
  if (enc->palette)
    gifenc_palette_free (enc->palette);
  //g_byte_array_unref (enc->buffer);
  g_byte_array_free (enc->buffer, TRUE);
  g_slice_free (Gifenc, enc);

  return success;
}

guint
gifenc_get_width (Gifenc *gifenc)
{
  g_return_val_if_fail (gifenc != NULL, 0);

  return gifenc->width;
}

guint
gifenc_get_height (Gifenc *gifenc)
{
  g_return_val_if_fail (gifenc != NULL, 0);

  return gifenc->height;
}

/* Floyd-Steinman factors */
#define FACTOR0 (23)
#define FACTOR1 (79)
#define FACTOR2 (41)
#define FACTOR_FRONT (113)

void
gifenc_dither_rgb (guint8* target, guint target_rowstride, 
    const GifencPalette *palette, const guint8 *data, guint width, guint height, 
    guint rowstride)
{
  guint x, y, i, c;
  gint *this_error, *next_error;
  guint8 this[3];
  gint err[3] = { 0, 0, 0 };
  guint32 pixel;
  
  g_return_if_fail (palette != NULL);

  this_error = g_new0 (gint, (width + 2) * 3);
  next_error = g_new (gint, (width + 2) * 3);
  i = 0;
  for (y = 0; y < height; y++) {
    const guint32 *row = (const guint32 *) data;
    gint *cur_error = this_error + 3;
    gint *cur_next_error = next_error;
    err[0] = err[1] = err[2] = 0;
    memset (cur_next_error, 0, sizeof (gint) * 6);
    for (x = 0; x < width; x++) {
      //g_print ("%dx%d  %2X%2X%2X  %2d %2d %2d", x, y, row[0], row[1], row[2],
      //    (err[0] + cur_error[0]) >> 8, (err[1] + cur_error[1]) >> 8,
      //    (err[2] + cur_error[2]) >> 8);
      for (c = 0; c < 3; c++) {
	err[c] = ((err[c] + cur_error[c]) >> 8) + (guint8) (*row >> 8 * c);
	this[c] = err[c] = CLAMP (err[c], 0, 0xFF);
      }
      pixel = COLOR (err[2], err[1], err[0]);
      //g_print ("  %2X%2X%2X =>", this[0], this[1], this[2]);
      target[x] = palette->lookup (palette->data, pixel, &pixel);
      //g_print (" %2X%2X%2X (%u) %p\n", this[0], this[1], this[2], (guint) target[x], target + x);
      for (c = 0; c < 3; c++) {
	this[c] = *row >> 8 * c;
	err[c] -= this[c];
	cur_next_error[c] += FACTOR0 * err[c];
	cur_next_error[c + 3] += FACTOR1 * err[c];
	cur_next_error[c + 6] = FACTOR2 * err[c];
	err[c] *= FACTOR_FRONT;
      }
      row++;
      cur_error += 3;
      cur_next_error += 3;
    }
    data += rowstride;
    cur_error = this_error;
    this_error = next_error;
    next_error = cur_error;
    target += target_rowstride;
  }
  g_free (this_error);
  g_free (next_error);
}

gboolean
gifenc_dither_rgb_with_full_image (guint8 *target, guint target_rowstride, 
    guint8 *full, guint full_rowstride,
    const GifencPalette *palette, const guint8 *data, guint width, guint height, 
    guint rowstride, GdkRectangle *rect_out)
{
  int x, y, i, c;
  gint *this_error, *next_error;
  guint8 this[3], alpha;
  gint err[3] = { 0, 0, 0 };
  guint32 pixel;
  GdkRectangle area = { width, height, 0, 0 };
  
  g_return_val_if_fail (palette != NULL, FALSE);
  g_return_val_if_fail (palette->alpha, FALSE);
  alpha = gifenc_palette_get_alpha_index (palette);

  this_error = g_new0 (gint, (width + 2) * 3);
  next_error = g_new (gint, (width + 2) * 3);
  i = 0;
  for (y = 0; y < (int) height; y++) {
    const guint32 *row = (const guint32 *) data;
    gint *cur_error = this_error + 3;
    gint *cur_next_error = next_error;
    err[0] = err[1] = err[2] = 0;
    memset (cur_next_error, 0, sizeof (gint) * 6);
    for (x = 0; x < (int) width; x++) {
      //g_print ("%dx%d  %2X%2X%2X  %2d %2d %2d", x, y, row[0], row[1], row[2],
      //    (err[0] + cur_error[0]) >> 8, (err[1] + cur_error[1]) >> 8,
      //    (err[2] + cur_error[2]) >> 8);
      for (c = 0; c < 3; c++) {
	err[c] = ((err[c] + cur_error[c]) >> 8) + (guint8) (*row >> 8 * c);
	this[c] = err[c] = CLAMP (err[c], 0, 0xFF);
      }
      //g_print ("  %2X%2X%2X =>", this[0], this[1], this[2]);
      pixel = COLOR (this[2], this[1], this[0]);
      target[x] = palette->lookup (palette->data, pixel, &pixel);
      if (target[x] == full[x]) {
	target[x] = alpha;
      } else {
	area.x = MIN (x, area.x);
	area.y = MIN (y, area.y);
	area.width = MAX (x, area.width);
	area.height = MAX (y, area.height);
	full[x] = target[x];
      }
      //g_print (" %2X%2X%2X (%u) %p\n", this[0], this[1], this[2], (guint) target[x], target + x);
      for (c = 0; c < 3; c++) {
	this[0] = *row >> 8 * c;
	err[c] -= this[c];
	cur_next_error[c] += FACTOR0 * err[c];
	cur_next_error[c + 3] += FACTOR1 * err[c];
	cur_next_error[c + 6] = FACTOR2 * err[c];
	err[c] *= FACTOR_FRONT;
      }
      row++;
      cur_error += 3;
      cur_next_error += 3;
    }
    data += rowstride;
    cur_error = this_error;
    this_error = next_error;
    next_error = cur_error;
    target += target_rowstride;
    full += full_rowstride;
  }
  g_free (this_error);
  g_free (next_error);

  if (area.width < area.x || area.height < area.y) {
    return FALSE;
  } else {
    if (rect_out) {
      area.width = area.width - area.x + 1;
      area.height = area.height - area.y + 1;
      //g_print ("image was %d %d, relevant is %d %d %d %d\n", width, height,
      //    area.x, area.y, area.width, area.height);
      *rect_out = area;
    }
    return TRUE;
  }
}

