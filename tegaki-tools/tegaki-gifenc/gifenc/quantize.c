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

#include <gtk/gtk.h>
#include <string.h>
#include "gifenc.h"

/*** GENERAL ***/

void
gifenc_palette_free (GifencPalette *palette)
{
  g_return_if_fail (palette != NULL);

  if (palette->free)
    palette->free (palette->data);
  g_free (palette);
}

guint
gifenc_palette_get_alpha_index (const GifencPalette *palette)
{
  g_return_val_if_fail (palette != NULL, 0);
  g_return_val_if_fail (palette->alpha, 0);

  return palette->num_colors;
}

guint
gifenc_palette_get_num_colors (const GifencPalette *palette)
{
  g_return_val_if_fail (palette != NULL, 0);

  return palette->num_colors + (palette->alpha ? 1 : 0);
}

guint
gifenc_palette_get_color (const GifencPalette *palette, guint id)
{
  g_return_val_if_fail (palette != NULL, 0);
  g_return_val_if_fail (id < palette->num_colors, 0);

  return palette->colors[id];
}

/*** SIMPLE ***/

static guint
gifenc_palette_simple_lookup (gpointer data, guint32 color, guint32 *resulting_color)
{
  color &= 0xC0C0C0;
  *resulting_color = color + 0x202020;
  return ((color >> 18) & 0x30) |
	 ((color >> 12) & 0xC) |
	 ((color >> 6) & 0x3);
}

GifencPalette *
gifenc_palette_get_simple (gboolean alpha)
{
  GifencPalette *palette;
  guint r, g, b, i = 0;

  palette = g_new (GifencPalette, 1);

  palette->alpha = alpha;
  palette->num_colors = 64;
  palette->colors = g_new (guint, palette->num_colors);
  for (r = 0; r < 4; r++) {
    for (g = 0; g < 4; g++) {
      for (b = 0; b < 4; b++) {
	palette->colors[i++] = (r << 22) + (g << 14) + (b << 6) + 0x202020;
      }
    }
  }
  palette->data = GINT_TO_POINTER (alpha ? 1 : 0);
  palette->lookup = gifenc_palette_simple_lookup;
  palette->free = NULL;

  return palette;
}

/*** OCTREE QUANTIZATION ***/

/* maximum number of leaves before starting color reduction */
#define MAX_LEAVES (12000)
/* maximum number of leaves before stopping a running color reduction */
#define STOP_LEAVES (MAX_LEAVES >> 2)

typedef struct _GifencOctree GifencOctree;
struct _GifencOctree {
  GifencOctree *	children[8];	/* children nodes or NULL */
  guint			level;		/* how deep in tree are we? */
  guint			red;		/* sum of all red pixels */
  guint			green;		/* sum of green pixels */
  guint			blue;		/* sum of blue pixels */
  guint			count;		/* amount of pixels at this node */
  guint32     		color;		/* representations (depending on value):
					   -1: random non-leaf node 
					   -2: root node
					   0x1000000: leaf node with undefined color
					   0-0xFFFFFF: leaf node with defined color */
  guint			id;		/* color index */
};					  
typedef struct {
  GifencOctree *	tree;
  GSList *		non_leaves;
  guint			num_leaves;
} OctreeInfo;
#define OCTREE_IS_LEAF(tree) ((tree)->color <= 0x1000000)

static GifencOctree *
gifenc_octree_new (void)
{
  GifencOctree *ret = g_new0 (GifencOctree, 1);

  ret->color = (guint) -1;
  return ret;
}

static void
gifenc_octree_free (gpointer data)
{
  GifencOctree *tree = data;
  guint i;
  
  for (i = 0; i < 8; i++) {
    if (tree->children[i])
      gifenc_octree_free (tree->children[i]);
  }
  g_free (tree);
}

#if 0
#define PRINT_NON_LEAVES 1
static void
gifenc_octree_print (GifencOctree *tree, guint flags)
{
#define FLAG_SET(flag) (flags & (flag))
  if (OCTREE_IS_LEAF (tree)) {
    g_print ("%*s %6d %2X-%2X-%2X\n", tree->level * 2, "", tree->count, 
	tree->red / tree->count, tree->green / tree->count, tree->blue / tree->count);
  } else {
    guint i;
    if (FLAG_SET(PRINT_NON_LEAVES))
      g_print ("%*s %6d\n", tree->level * 2, "", tree->count);
    g_assert (tree->red == 0);
    g_assert (tree->green == 0);
    g_assert (tree->blue == 0);
    for (i = 0; i < 8; i++) {
      if (tree->children[i])
	gifenc_octree_print (tree->children[i], flags);
    }
  }
#undef FLAG_SET
}
#endif

static guint
color_to_index (guint color, guint level)
{
  guint ret;

  g_assert (level < 8);

  color >>= (7 - level);
  ret = (color & 0x10000) ? 4 : 0;
  if (color & 0x100)
    ret += 2;
  if (color & 0x1)
    ret ++;
  return ret;
}

static void
gifenc_octree_add_one (GifencOctree *tree, guint32 color, guint count)
{
  tree->red += ((color >> 16) & 0xFF) * count;
  tree->green += ((color >> 8) & 0xFF) * count;
  tree->blue += (color & 0xFF) * count;
}

static void
gifenc_octree_add_color (OctreeInfo *info, guint32 color, guint count)
{
  guint i;
  GifencOctree *tree = info->tree;

  color &= 0xFFFFFF;

  for (;;) {
    tree->count += count;
    if (tree->level == 8 || OCTREE_IS_LEAF (tree)) {
      if (tree->color < 0x1000000 && tree->color != color) {
	GifencOctree *new = gifenc_octree_new ();
	new->level = tree->level + 1;
	new->count = tree->count - count;
	new->red = tree->red; tree->red = 0;
	new->green = tree->green; tree->green = 0;
	new->blue = tree->blue; tree->blue = 0;
	new->color = tree->color; tree->color = (guint) -1;
	i = color_to_index (new->color, tree->level);
	tree->children[i] = new;
	info->non_leaves = g_slist_prepend (info->non_leaves, tree);
      } else {
	gifenc_octree_add_one (tree, color, count);
	return;
      }
    } 
    i = color_to_index (color, tree->level);
    if (tree->children[i]) {
      tree = tree->children[i];
    } else {
      GifencOctree *new = gifenc_octree_new ();
      new->level = tree->level + 1;
      gifenc_octree_add_one (new, color, count);
      new->count = count;
      new->color = color;
      tree->children[i] = new;
      info->num_leaves++;
      return;
    }
  }
}

static int
octree_compare_count (gconstpointer a, gconstpointer b)
{
  return ((const GifencOctree *) a)->count - ((const GifencOctree *) b)->count;
}

static void
gifenc_octree_reduce_one (OctreeInfo *info, GifencOctree *tree)
{
  guint i;

  g_assert (!OCTREE_IS_LEAF (tree));
  for (i = 0; i < 8; i++) {
    if (!tree->children[i])
      continue;
    g_assert (OCTREE_IS_LEAF (tree->children[i]));
    tree->red += tree->children[i]->red;
    tree->green += tree->children[i]->green;
    tree->blue += tree->children[i]->blue;
    gifenc_octree_free (tree->children[i]);
    tree->children[i] = NULL;
    info->num_leaves--;
  }
  tree->color = 0x1000000;
  info->num_leaves++;
  info->non_leaves = g_slist_remove (info->non_leaves, tree);
}

static void
gifenc_octree_reduce_colors (OctreeInfo *info, guint stop)
{
  info->non_leaves = g_slist_sort (info->non_leaves, octree_compare_count);
  //g_print ("reducing %u leaves (%u non-leaves)\n", info->num_leaves, 
  //    g_slist_length (info->non_leaves));
  while (info->num_leaves > stop) {
    gifenc_octree_reduce_one (info, info->non_leaves->data);
  }
  //g_print (" ==> to %u leaves\n", info->num_leaves);
}

static guint
gifenc_octree_finalize (GifencOctree *tree, guint start_id, guint *colors)
{
  if (OCTREE_IS_LEAF (tree)) {
    if (tree->color > 0xFFFFFF)
      tree->color = 
	((tree->red / tree->count) << 16) |
	((tree->green / tree->count) << 8) |
	(tree->blue / tree->count);
    tree->id = start_id;
    colors[start_id] = tree->color;
    return tree->id + 1;
  } else {
    guint i;
    for (i = 0; i < 8; i++) {
      if (tree->children[i])
	start_id = gifenc_octree_finalize (tree->children[i], start_id, colors);
    }
    return start_id;
  }
  g_assert_not_reached ();
  return 0;
}

static guint
gifenc_octree_lookup (gpointer data, guint32 color, guint32 *looked_up_color)
{
  GifencOctree *tree = data;
  guint idx;

  if (OCTREE_IS_LEAF (tree)) {
    *looked_up_color = tree->color;
    return tree->id;
  } 
  idx = color_to_index (color, tree->level);
  if (tree->children[idx] == NULL) {
    static const guint order[8][7] = {
      { 2, 1, 4, 3, 6, 5, 7 },
      { 3, 0, 5, 2, 7, 4, 6 },
      { 0, 3, 6, 1, 4, 7, 5 },
      { 1, 2, 7, 6, 5, 0, 4 },
      { 6, 5, 0, 7, 2, 1, 3 },
      { 7, 4, 1, 6, 3, 0, 2 },
      { 4, 7, 2, 5, 0, 3, 1 },
      { 5, 6, 3, 4, 1, 2, 0 }
    };
    guint i, tmp;
    for (i = 0; i < 7; i++) {
      tmp = order[idx][i];
      if (!tree->children[tmp])
	continue;
      /* make selection smarter, like using closest match */
      return gifenc_octree_lookup (
	  tree->children[tmp],
	  color, looked_up_color);
    }
    g_assert_not_reached ();
  }
  return gifenc_octree_lookup (
      tree->children[idx],
      color, looked_up_color);
}

GifencPalette *
gifenc_quantize_image (const guint8 *data, guint width, guint height,
    guint rowstride, gboolean alpha, guint max_colors)
{
  guint x, y;
  const guint32 *row;
  OctreeInfo info = { NULL, NULL, 0 };
  GifencPalette *palette;
  
  g_return_val_if_fail (width * height <= (G_MAXUINT >> 8), NULL);

  info.tree = gifenc_octree_new ();
  info.tree->color = (guint) -2; /* special node */

  if (TRUE) {
    guint r, g, b, count;
    static const guint8 colors[] = { 0, 85, 170, 255 };
    count = (width * height) / (4 * 4 * 4);
    for (r = 0; r < 4; r++) {
      for (g = 0; g < 4; g++) {
	for (b = 0; b < 4; b++) {
	  gifenc_octree_add_color (&info, 
	      (colors[r] << 16) + (colors[g] << 8) + colors[b], 1);
	}
      }
    }
  }
  
  for (y = 0; y < height; y++) {
    row = (const guint32 *) data;
    for (x = 0; x < width; x++) {
      gifenc_octree_add_color (&info, row[x] & 0xFFFFFF, 1);
    }
    //if (info.num_leaves > MAX_LEAVES)
    //  gifenc_octree_reduce_colors (&info, STOP_LEAVES);
    data += rowstride;
  }
  //gifenc_octree_print (info.tree, 1);
  gifenc_octree_reduce_colors (&info, max_colors - (alpha ? 1 : 0));
  
  //gifenc_octree_print (info.tree, 1);
  //g_print ("total: %u colors (%u non-leaves)\n", info.num_leaves, 
  //    g_slist_length (info.non_leaves));

  palette = g_new (GifencPalette, 1);
  palette->alpha = alpha;
  palette->colors = g_new (guint, info.num_leaves);
  palette->num_colors = info.num_leaves;
  palette->data = info.tree;
  palette->lookup = gifenc_octree_lookup;
  palette->free = gifenc_octree_free;

  gifenc_octree_finalize (info.tree, 0, palette->colors);
  g_slist_free (info.non_leaves);

  return (GifencPalette *) palette;
}

