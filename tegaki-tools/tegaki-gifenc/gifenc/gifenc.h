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

#include <glib.h>
#include <gtk/gtk.h>

#ifndef __HAVE_GIFENC_H__
#define __HAVE_GIFENC_H__

typedef struct _GifencPalette GifencPalette;
typedef struct _GifencColor GifencColor;
typedef struct _Gifenc Gifenc;

typedef gboolean (* GifencWriteFunc) (gpointer closure, const guchar *data, gsize len, GError **error);

typedef enum {
  GIFENC_STATE_NEW = 0,
  GIFENC_STATE_INITIALIZED,
  GIFENC_STATE_CLOSED,
} GifencState;

struct _GifencPalette {
  gboolean	alpha;
  guint32 *	colors;
  guint		num_colors;
  guint		byte_order;
  gpointer	data;
  guint		(* lookup)	(gpointer		data,
				 guint32	      	color,
				 guint32 *		resulting_color);
  void		(* free)	(gpointer		data);
};

struct _Gifenc {
  /* error checking */
  GifencState           state;

  /* output */
  GifencWriteFunc       write_func;
  gpointer              write_data;
  GDestroyNotify        write_destroy;
  GByteArray *          buffer;
  guint			bits;
  guint			n_bits;
  
  /* image */
  guint		  	width;
  guint			height;
  guint			byte_order;
  GifencPalette *	palette;
};

Gifenc *        gifenc_new              (guint                  width,
                                         guint                  height,
                                         GifencWriteFunc        write_func,
                                         gpointer               write_data,
                                         GDestroyNotify         write_destroy);
gboolean        gifenc_free             (Gifenc *		enc);
					 
gboolean        gifenc_initialize	(Gifenc *		enc,
					 GifencPalette *	palette,
                                         gboolean       	loop,
                                         GError **      	error);
gboolean        gifenc_add_image	(Gifenc *		enc,
					 guint			x,
					 guint			y,
					 guint			width,
					 guint			height,
					 guint			display_millis,
					 guint8 *		data,
					 guint			rowstride,
                                         GError **		error);
gboolean        gifenc_close            (Gifenc *       	gifenc,
                                         GError **      	error);
guint           gifenc_get_width        (Gifenc *               gifenc);
guint           gifenc_get_height       (Gifenc *               gifenc);

void		gifenc_dither_rgb	(guint8 *		target,
					 guint			target_rowstride,
					 const GifencPalette *	palette,
					 const guint8 *		data,
					 guint			width,
					 guint			height,
					 guint			rowstride);
gboolean	gifenc_dither_rgb_with_full_image
					(guint8 *		target,
					 guint			target_rowstride,
					 guint8 *		full,
					 guint			full_rowstride,
					 const GifencPalette *	palette,
					 const guint8 *		data,
					 guint			width,
					 guint			height,
					 guint			rowstride,
					 GdkRectangle *		rect_out);

/* from quantize.c */
void		gifenc_palette_free	(GifencPalette *	palette);
GifencPalette *	gifenc_palette_get_simple (gboolean		alpha);
GifencPalette *	gifenc_quantize_image	(const guint8 *		data,
					 guint			width, 
					 guint			height,
					 guint			rowstride, 
					 gboolean		alpha,
					 guint			max_colors);
guint		gifenc_palette_get_alpha_index
					(const GifencPalette *	palette);
guint		gifenc_palette_get_num_colors
					(const GifencPalette *	palette);
guint32		gifenc_palette_get_color(const GifencPalette *	palette,
					 guint			id);
					

#endif /* __HAVE_GIFENC_H__ */
