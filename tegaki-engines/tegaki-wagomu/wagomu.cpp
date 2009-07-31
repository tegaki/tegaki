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

#include "wagomu.h"

#define MAGIC_NUMBER 0x77778888
#define VECTOR_DIMENSION_MAX 4

#undef MIN
#define MIN(a,b) ((a) < (b) ? (a) : (b))

#undef MIN3
#define MIN3(a,b,c) (MIN((a),MIN((b),(c))))

#define WINDOW_SIZE 4

namespace wagomu {

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

Recognizer::~Recognizer() {
    if (file)
        g_mapped_file_free(file);
    if (distm)
        free(distm);
}

bool Recognizer::open(char *path) {
    unsigned int *header;
    char *cursor;

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
    characters = (Character *)cursor;

    cursor += n_characters * sizeof(Character);
    groups = (CharacterGroup *)cursor;

    strokedata = (float *)(data + groups[0].offset);

    distm = (CharDist *) malloc(n_characters * sizeof(CharDist));

    return true;
}

unsigned int Recognizer::get_n_characters() {
    return n_characters;
}

unsigned int Recognizer::get_dimension() {
    return dimension;
}

inline float Recognizer::euclidean_distance(float *v1, float *v2) {
    /*float diff, sum = 0;

    for (int i=0; i < dimension; i++) {
        diff = v2[i] - v1[i];
        sum += diff * diff;
    }

    return sqrtf(sum);*/

    float sum;
    for (unsigned int i=0; i < dimension; i++)
        sum += fabsf(v2[i] - v1[i]);

    return sum;
}

inline float Recognizer::dtw(float *s, unsigned int n, 
                             float *t, unsigned int m) {
    /*
    s: first sequence
    n: number of vectors in s
    t: second sequence
    n: number of vectors in t
    */
    unsigned int k, i, j;
    float cost;
    float *t_start;

    t_start = t;

    for (k=n; k < n*m; k=k+n)
        dtwm[k] = FLT_MAX;

    for (k=1; k < n; k++)
        dtwm[k] = FLT_MAX;

    dtwm[0] = 0;

    s += VECTOR_DIMENSION_MAX;
   
    for (i=1; i < n; i++) {
        t = t_start + VECTOR_DIMENSION_MAX;

        for (j=1; j < m; j++) {
            k = j * n + i;
            cost = euclidean_distance(s, t);
            dtwm[k] = cost + MIN3(dtwm[k-1],dtwm[k-n-1],dtwm[k-n]);

            t += VECTOR_DIMENSION_MAX;
        }

        s += VECTOR_DIMENSION_MAX;
    }
    
    return dtwm[k];
}

static int char_dist_cmp(CharDist *a, CharDist *b) {
    if (a->dist < b->dist) return -1;
    if (a->dist > b->dist) return 1;
    return  0;
}

Results *Recognizer::recognize(float *points, 
                              unsigned int n_vectors, 
                              unsigned int n_strokes,
                              unsigned int n_results) {

    unsigned int group_id, i, size, n_chars, char_id;
    float *cursor = strokedata;

    for (group_id=0, n_chars=0, char_id=0; group_id < n_groups; group_id++) {
        /* Only compare the input with templates which have
           +- WINDOW_SIZE the same number of strokes as the input */
        if (groups[group_id].n_strokes > (n_strokes + WINDOW_SIZE))
            break;
        if (groups[group_id].n_strokes > WINDOW_SIZE &&
            groups[group_id].n_strokes < (n_strokes - WINDOW_SIZE)) {
            char_id += groups[group_id].n_chars;
            continue;
        }

        cursor = (float *) (data + groups[group_id].offset);

        for (i=0; i < groups[group_id].n_chars; i++) {
            distm[n_chars].unicode = characters[char_id].unicode;
            distm[n_chars].dist = dtw(points, n_vectors, 
                                      cursor, characters[char_id].n_vectors);
            cursor += characters[char_id].n_vectors * VECTOR_DIMENSION_MAX;
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