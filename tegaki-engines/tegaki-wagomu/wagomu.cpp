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
#include <float.h>
#include <math.h>

#ifdef HAVE_MEMALIGN
#include <malloc.h>
#else
#define memalign(a,b) malloc((b))
#endif

#include "wagomu.h"

#define MAGIC_NUMBER 0x77778888
#define VEC_DIM_MAX 4

#undef MIN
#define MIN(a,b) ((a) < (b) ? (a) : (b))

#undef MIN3
#define MIN3(a,b,c) (MIN((a),MIN((b),(c))))

#undef MIN4
#define MIN4(a,b,c,d) (MIN((a),MIN3((b),(c),(d))))

#undef MAX
#define MAX(a,b) ((a) > (b) ? (a) : (b))

#undef MAX3
#define MAX3(a,b,c) (MAX((a),MAX((b),(c))))

#undef MAX4
#define MAX4(a,b,c,d) (MAX((a),MAX3((b),(c),(d))))

#ifdef __SSE__

#undef MIN3VEC
#define MIN3VEC(a,b,c) (_mm_min_ps((a),_mm_min_ps((b),(c))))

#endif

#undef SWAP
#define SWAP(a,b,tmp) tmp = a; a = b; b = tmp

namespace wagomu {

Character::Character(unsigned int n_vec, unsigned int n_stro) {
    n_vectors = n_vec;
    n_strokes = n_stro;
    if (n_vec > 0)
        /*
        ptr = malloc(size+align+1);
        diff= ((-(int)ptr - 1)&(align-1)) + 1;
        ptr += diff;
        ((char*)ptr)[-1]= diff;
        */
        points = (float *) memalign(16, n_vec * VEC_DIM_MAX *
                                        sizeof(float));
}

Character::~Character() {
    if (n_vectors > 0)
        if (points) free(points); /* free(ptr - ((char*)ptr)[-1]); */
}

float *Character::get_points() {
    return points;
}

unsigned int Character::get_n_vectors() {
    return n_vectors;
}

unsigned int Character::get_n_strokes() {
    return n_strokes;
}

void Character::set_value(unsigned int i, float value) {
    points[i] = value;
}

Results::Results(unsigned int s) {
    size = s;
    if (size > 0) {
        unicode = (unsigned int*) malloc(size * sizeof(unsigned int));
        dist = (float *) malloc(size * sizeof(float));
    }
}

Results::~Results() {
    if (size > 0) {
        if (unicode) free(unicode);
        if (dist) free(dist);
    }
}

void Results::add(unsigned int i, unsigned int u, float d) {
    unicode[i] = u;
    dist[i] = d;
}

unsigned int Results::get_unicode(unsigned int i) {
    return unicode[i];
}

float Results::get_distance(unsigned int i) {
    return dist[i];
}

unsigned int Results::get_size() {
    return size;
}

Recognizer::Recognizer() {
    window_size = 3;
}

Recognizer::~Recognizer() {
    if (file) g_mapped_file_free(file);
    if (distm) free(distm);
    if (dtw1) free(dtw1);
    if (dtw2) free(dtw2);
}

unsigned int Recognizer::get_window_size() {
    return window_size;
}

void Recognizer::set_window_size(unsigned int size) {
    window_size = size;
}

bool Recognizer::open(char *path) {
    unsigned int *header;
    char *cursor;
    unsigned int max_n_vectors;

    file = g_mapped_file_new(path, FALSE, NULL);

    if (!file) {
        error_msg = (char *) "Couldn't map file";
        return false;
    }

    data = g_mapped_file_get_contents(file);

    header = (unsigned int *)data;

    if (header[0] != MAGIC_NUMBER) {
        error_msg = (char *) "Not a valid file";
        return false;
    }

    n_characters =  header[1];
    n_groups = header[2];
    dimension = header[3];
    downsample_threshold = header[4];

    if (n_characters == 0 || n_groups == 0) {
        error_msg = (char *) "No characters in this model";
        return false;
    }
    
    cursor = data + 5 * sizeof(unsigned int);
    characters = (CharacterInfo *)cursor;

    cursor += n_characters * sizeof(CharacterInfo);
    groups = (CharacterGroup *)cursor;

    strokedata = (float *)(data + groups[0].offset);

    distm = (CharDist *) malloc(n_characters * sizeof(CharDist));

    max_n_vectors = get_max_n_vectors();

#ifdef __SSE__
    dtw1v = (wg_v4sf *) memalign(16, max_n_vectors * VEC_DIM_MAX *
                                     sizeof(wg_v4sf));
    dtw2v = (wg_v4sf *) memalign(16, max_n_vectors * VEC_DIM_MAX *
                                     sizeof(wg_v4sf));
    dtw1 = (float *) dtw1v;
    dtw2 = (float *) dtw2v;
#else
    dtw1 = (float *) memalign(16, max_n_vectors * VEC_DIM_MAX *
                                  sizeof(float));
    dtw2 = (float *) memalign(16, max_n_vectors * VEC_DIM_MAX *
                                  sizeof(float));
#endif

    return true;
}

unsigned int Recognizer::get_max_n_vectors() {
    unsigned int i, max_n_vectors;

    for (i=0, max_n_vectors=0; i < n_characters; i++)
        if (characters[i].n_vectors > max_n_vectors)
            max_n_vectors = characters[i].n_vectors;

    return max_n_vectors;
}

unsigned int Recognizer::get_n_characters() {
    return n_characters;
}

unsigned int Recognizer::get_dimension() {
    return dimension;
}

/* The euclidean distance is replaced by the sum of absolute
   differences for performance reasons... */

inline float Recognizer::local_distance(float *v1, float *v2) {
    float sum = 0;
#ifdef __SSE__
    wg_v4sf res, v_;
    v_.v = _mm_set_ps1(-0.0);
    
    res.v = _mm_sub_ps(((wg_v4sf *)v2)->v, ((wg_v4sf *)v1)->v);
    res.v = _mm_andnot_ps(v_.v,res.v); // absolute value

    for (unsigned int i=0; i < dimension; i++)
        sum += res.s[i];
#else
    for (unsigned int i=0; i < dimension; i++) 
        sum += fabs(v2[i] - v1[i]);
#endif
    return sum;
}

/*

m [X][ ][ ][ ][ ][r]
  [X][ ][ ][ ][ ][ ]
  [X][ ][ ][ ][ ][ ]
  [X][ ][ ][ ][ ][ ]
  [0][X][X][X][X][X]
                  n

Each cell in the n*m matrix is defined as follows:
    
    dtw(i,j) = local_distance(i,j) + MIN3(dtw(i-1,j-1), dtw(i-1,j), dtw(i,j-1))

Cells marked with an X are set to infinity.
The bottom-left cell is set to 0.
The top-right cell is the result.

At any given time, we only need two columns of the matrix, thus we use
two arrays dtw1 and dtw2 as our data structure.

[   ]   [   ]
[ j ]   [ j ]
[j-1]   [j-1]
[   ]   [   ]
[ X ]   [ X ]
dtw1    dtw2

A cell can thus be calculated as follows:

    dtw2(j) = local_distance(i,j) + MIN3(dtw2(j-1), dtw1(j), dtw1(j-1))

*/

inline float Recognizer::dtw(float *s, unsigned int n, 
                             float *t, unsigned int m) {
    /*
    Compare an input sequence with a reference sequence.

    s: input sequence
    n: number of vectors in s

    t: reference sequence
    m: number of vectors in t
    */
    unsigned int i, j;
    float cost;
    float *t_start, *tmp;

    t_start = t;

    /* Initialize the edge cells */
    for (i=1; i < m; i++)
        dtw1[i] = FLT_MAX;

    dtw1[0] = 0;
    dtw2[0] = FLT_MAX;

    s += VEC_DIM_MAX;
   
    /* Iterate over columns */
    for (i=1; i < n; i++) {
        t = t_start + VEC_DIM_MAX;

        /* Iterate over cells of that column */
        for (j=1; j < m; j++) {
            cost = local_distance(s, t);
            /* Inductive step */
            dtw2[j] = cost + MIN3(dtw2[j-1],dtw1[j],dtw1[j-1]);

            t += VEC_DIM_MAX;
        }

        SWAP(dtw1,dtw2,tmp);
        *dtw2 = FLT_MAX;

        s += VEC_DIM_MAX;
    }

    return dtw1[m-1];
}

#ifdef __SSE__
inline wg_v4sf Recognizer::local_distance4(float *s,
                                           float *t0,
                                           float *t1,
                                           float *t2,
                                           float *t3) {
    wg_v4sf v_, v0, v1, v2, v3;
    v_.v = _mm_set_ps1(-0.0);
    v0.v = _mm_sub_ps(((wg_v4sf *)t0)->v, ((wg_v4sf *)s)->v);
    v0.v = _mm_andnot_ps(v_.v,v0.v); // absolute value
    v1.v = _mm_sub_ps(((wg_v4sf *)t1)->v, ((wg_v4sf *)s)->v);
    v1.v = _mm_andnot_ps(v_.v,v1.v); // absolute value
    v2.v = _mm_sub_ps(((wg_v4sf *)t2)->v, ((wg_v4sf *)s)->v);
    v2.v = _mm_andnot_ps(v_.v,v2.v); // absolute value
    v3.v = _mm_sub_ps(((wg_v4sf *)t3)->v, ((wg_v4sf *)s)->v);
    v3.v = _mm_andnot_ps(v_.v,v3.v); // absolute value
    // convert row vectors to column vectors
    _MM_TRANSPOSE4_PS(v0.v, v1.v, v2.v, v3.v);
    v3.v = _mm_add_ps(v3.v, v2.v);
    v3.v = _mm_add_ps(v3.v, v1.v);
    v3.v = _mm_add_ps(v3.v, v0.v);
    return v3;
}

#define DTW4_PROCESS_REMAINING(n, m, t) \
do { \
    for (j=common; j < m; j++) { \
        costf = local_distance(s, t); \
        dtw2v[j].s[n] = costf + MIN3(dtw2v[j-1].s[n], \
                                     dtw1v[j].s[n], \
                                     dtw1v[j-1].s[n]); \
        t += VEC_DIM_MAX; \
    } \
} while(0)

inline wg_v4sf Recognizer::dtw4(float *s, unsigned int n, 
                                float *t0, unsigned int m0,
                                float *t1, unsigned int m1,
                                float *t2, unsigned int m2,
                                float *t3, unsigned int m3) {
    /*
    Compare an input sequence with 4 reference sequences.

    For one column of the DTW matrix, MIN4(m0,m1,m2,m3) cells are calculated
    using vector instructions. The rest of the cells are calculated
    sequentially.

    s: input sequence
    n: number of vectors in s

    t0..t3: reference sequences
    m0..m3: number of vectors in the sequence
    */
    unsigned int i, j, common;
    wg_v4sf cost;
    float costf;
    float *t_start0, *t_start1, *t_start2, *t_start3;
    wg_v4sf *tmp;
    wg_v4sf res;

    t_start0 = t0; t_start1 = t1; t_start2 = t2; t_start3 = t3;

    /* Initialize the edge cells */
    dtw1v[0].v = _mm_set_ps1(0);
    dtw2v[0].v = _mm_set_ps1(FLT_MAX);

    for (i=1; i < MAX4(m0,m1,m2,m3); i++)
        dtw1v[i].v = _mm_set_ps1(FLT_MAX);

    s += VEC_DIM_MAX;
   
    common = MIN4(m0,m1,m2,m3);

    /* Iterate over columns */
    for (i=1; i < n; i++) {
        t0 = t_start0 + VEC_DIM_MAX; t1 = t_start1 + VEC_DIM_MAX;
        t2 = t_start2 + VEC_DIM_MAX; t3 = t_start3 + VEC_DIM_MAX;

        /* Iterate over cells of that column */
        /* Process 4 cells at a time in parallel */
        for (j=1; j < common; j++) {
            cost = local_distance4(s, t0, t1, t2, t3);
            /* Inductive step */
            dtw2v[j].v = _mm_add_ps(cost.v,
                                MIN3VEC(dtw2v[j-1].v,dtw1v[j].v,dtw1v[j-1].v));

            t0 += VEC_DIM_MAX; t1 += VEC_DIM_MAX;
            t2 += VEC_DIM_MAX; t3 += VEC_DIM_MAX;
        }

        /* The remaining of cells is calculated sequentially */
        DTW4_PROCESS_REMAINING(0, m0, t0);
        DTW4_PROCESS_REMAINING(1, m1, t1);
        DTW4_PROCESS_REMAINING(2, m2, t2);
        DTW4_PROCESS_REMAINING(3, m3, t3);

        SWAP(dtw1v,dtw2v,tmp);
        dtw2v[0].v = _mm_set_ps1(FLT_MAX);

        s += VEC_DIM_MAX;
    }

    res.s[0] = dtw1v[m0-1].s[0]; res.s[1] = dtw1v[m1-1].s[1];
    res.s[2] = dtw1v[m2-1].s[2]; res.s[3] = dtw1v[m3-1].s[3];
    
    return res;
}
#endif

static int char_dist_cmp(CharDist *a, CharDist *b) {
    if (a->dist < b->dist) return -1;
    if (a->dist > b->dist) return 1;
    return  0;
}


#if 0
static void assert_aligned16(char *p) {
    if ((((uintptr_t)(p)) % 16) != 0)
        printf("assertion failed\n");
}
#endif

Results *Recognizer::recognize(Character *ch, unsigned int n_results) {

    unsigned int group_id, i, size, n_chars, char_id, n_group_chars;
    unsigned int n_vectors, n_strokes;
    float *cursor = strokedata;
    float *input;

    n_vectors = ch->get_n_vectors();
    n_strokes = ch->get_n_strokes();
    input = ch->get_points();

    #if 0
    assert_aligned16((char *) input);
    #endif

    for (group_id=0, n_chars=0, char_id=0; group_id < n_groups; group_id++) {
        /* Only compare the input with templates which have
           +- window_size the same number of strokes as the input */
        if (n_strokes > window_size) {
            if (groups[group_id].n_strokes > (n_strokes + window_size))
                break;

            if (groups[group_id].n_strokes < (n_strokes - window_size)) {
                char_id += groups[group_id].n_chars;
                continue;
            }
        }

        cursor = (float *) (data + groups[group_id].offset);

#ifdef __SSE__
        float *ref1, *ref2, *ref3, *ref4;
        unsigned int size1, size2, size3, size4;
        wg_v4sf dtwres4;

        /* Process 4 reference characters at a time */
        for (i=0; i < (groups[group_id].n_chars / 4); i++) {
            distm[n_chars].unicode = characters[char_id].unicode;
            ref1 = cursor;
            size1 = characters[char_id].n_vectors;
            ref2 = ref1 + characters[char_id].n_vectors * VEC_DIM_MAX;
            char_id++;

            distm[n_chars+1].unicode = characters[char_id].unicode;
            size2 = characters[char_id].n_vectors;
            ref3 = ref2 + characters[char_id].n_vectors * VEC_DIM_MAX;
            char_id++;

            distm[n_chars+2].unicode = characters[char_id].unicode;
            size3 = characters[char_id].n_vectors;
            ref4 = ref3 + characters[char_id].n_vectors * VEC_DIM_MAX;
            char_id++;

            distm[n_chars+3].unicode = characters[char_id].unicode;            
            size4 = characters[char_id].n_vectors;
            cursor = ref4 + characters[char_id].n_vectors *
                     VEC_DIM_MAX;
            char_id++;

            dtwres4 = dtw4(input, n_vectors, 
                           ref1, size1, 
                           ref2, size2, 
                           ref3, size3, 
                           ref4, size4);

            distm[n_chars++].dist = dtwres4.s[0];
            distm[n_chars++].dist = dtwres4.s[1];
            distm[n_chars++].dist = dtwres4.s[2];
            distm[n_chars++].dist = dtwres4.s[3];
        }

        /* Process the remaining of references */
        n_group_chars = (groups[group_id].n_chars % 4);
#else
        /* SSE not available, we need to process references sequentially */
        n_group_chars = groups[group_id].n_chars;
#endif

        for (i=0; i < n_group_chars; i++) {
            distm[n_chars].unicode = characters[char_id].unicode;
            distm[n_chars].dist = dtw(input, n_vectors, 
                                      cursor, characters[char_id].n_vectors);
            cursor += characters[char_id].n_vectors * VEC_DIM_MAX;
            char_id++;
            n_chars++;
        }

    }

    /* sort the results with glibc's quicksort */
    qsort ((void *) distm, 
           (size_t) n_chars, 
           sizeof (CharDist), 
           (int (*) (const void *, const void*)) char_dist_cmp);

    size = MIN(n_chars, n_results);

    Results *results = new Results(size);

    for(i=0; i < size; i++)
        results->add(i, distm[i].unicode, distm[i].dist);

    return results;
}

char* Recognizer::get_error_message() {
    return error_msg;
}

}
