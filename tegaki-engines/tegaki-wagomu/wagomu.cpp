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

#define MAGIC_NUMBER 0x7777

#ifndef MIN
#  define MIN(a,b) ((a) < (b) ? (a) : (b))
#endif

#ifndef MIN3
#  define MIN3(a,b,c) (MIN((a),MIN((b),(c))))
#endif


namespace wagomu {

Results::Results(int s) {
    size = s;
    if (size > 0) {
        utf8 = (char **) malloc(size * sizeof(char *));
        dist = (float *) malloc(size * sizeof(float));
    }
}

Results::~Results() {
    if (size > 0) {
        if (utf8) free(utf8);
        if (dist) free(dist);
    }
}

void Results::add(int i, char *u, float d) {
    utf8[i] = u;
    dist[i] = d;
}

char *Results::get_utf8(int i) {
    return utf8[i];
}

float Results::get_distance(int i) {
    return dist[i];
}

int Results::get_size() {
    return size;
}

Recognizer::~Recognizer() {
    if (file)
        g_mapped_file_free(file);
    if (distm)
        free(distm);
}

bool Recognizer::open(char *path) {
    file = g_mapped_file_new(path, FALSE, NULL);

    if (!file) {
        error_msg = (char *) "Couldn't map file";
        return false;
    }

    data = g_mapped_file_get_contents(file);

    if (*(unsigned short *)data != MAGIC_NUMBER) {
        error_msg = (char *) "Not a valid file";
        return false;
    }

    n_characters =  *(unsigned long *)(data+2);
    dimension = *(unsigned short *)(data+6);

    distm = (CharDist *) malloc(n_characters * sizeof(CharDist));

    return true;
}

unsigned long Recognizer::get_n_characters() {
    return n_characters;
}

unsigned short Recognizer::get_dimension() {
    return dimension;
}

float Recognizer::euclidean_distance(float *v1, float *v2) {
    float diff, sum = 0;

    for (int i=0; i < dimension; i++) {
        diff = v2[i] - v1[i];
        sum += diff * diff;
    }

    return sqrtf(sum);
}

float Recognizer::dtw(float *s, unsigned short n, 
                      float *t, unsigned short m) {
    /*
    s: first sequence
    n: number of vectors in s
    t: second sequence
    n: number of vectors in t
    */
    int k, i, j;
    float cost;
    float *t_start;

    t_start = t;

    for (k=n; k < n*m; k=k+n)
        dtwm[k] = FLT_MAX;

    for (k=1; k < n; k++)
        dtwm[k] = FLT_MAX;

    dtwm[0] = 0;

    s += dimension;
   
    for (i=1; i < n; i++) {
        t = t_start + dimension;

        for (j=1; j < m; j++) {
            k = j * n + i;
            cost = euclidean_distance(s, t);
            dtwm[k] = cost + MIN3(dtwm[k-1],dtwm[k-n-1],dtwm[k-n]);
            t += dimension;
        }

        s += dimension;
    }
    
    return dtwm[k];
}

static int char_dist_cmp(CharDist *a, CharDist *b) {
    if (a->dist < b->dist) return -1;
    if (a->dist > b->dist) return 1;
    return  0;
}

Results *Recognizer::recognize(float *points, 
                              unsigned short n_vectors, 
                              unsigned short n_results) {

    unsigned short utf8len, n_vectors_template;
    char *cursor = data + 8; // skip magic_number, n_characters, dimension
    unsigned int i, size;
    
    for (i=0; i < n_characters; i++) {
        utf8len = *(unsigned short *)cursor;
        cursor += 2;
        distm[i].utf8 = cursor;
        cursor += utf8len;
        n_vectors_template =  *(unsigned short *)cursor;
        cursor += 2;
        distm[i].dist = dtw(points, n_vectors, 
                            (float *)cursor, n_vectors_template);
        cursor += n_vectors_template * dimension * 4;
    }

    /* sort the results with glibc's quicksort */
    qsort ((void *) distm, 
           (size_t) n_characters, 
           sizeof (CharDist), 
           (int (*) (const void *, const void*)) char_dist_cmp);

    size = MIN(n_characters, n_results);

    Results *results = new Results(size);

    for(i=0; i < size; i++)
        results->add(i, strdup(distm[i].utf8), distm[i].dist);

    return results;
}

char* Recognizer::get_error_message() {
    return error_msg;
}

}