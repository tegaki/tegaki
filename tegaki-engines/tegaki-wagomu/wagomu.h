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

#ifndef WAGOMU_H
#define WAGOMU_H

#include <glib.h>
#include <glib/gstdio.h>

namespace wagomu {

class Results {

public:
    Results(unsigned int size);
    ~Results();

#ifndef SWIG
    void add(unsigned i, unsigned int unicode, float dist);
#endif
    unsigned int get_unicode(unsigned int i);
    float get_distance(unsigned int i);
    unsigned int get_size();

private:
    unsigned int *unicode;
    float *dist;
    int size;
};

#ifndef SWIG
typedef struct {
    unsigned int unicode;
    float dist;
} CharDist;

typedef struct {
    unsigned int unicode;
    unsigned int n_vectors;
} Character;

typedef struct {
    unsigned int n_strokes;
    unsigned int n_chars;
    unsigned int offset;
    char pad[4];
} CharacterGroup;
#endif

class Recognizer {

public:
    ~Recognizer();

    bool open(char *path);
    Results *recognize(float *points, 
                       unsigned int n_vectors,
                       unsigned int n_strokes,
                       unsigned int n_results);
    unsigned int get_n_characters();
    unsigned int get_dimension();
    char *get_error_message();

private:
    GMappedFile *file;
    char *data;

    unsigned int n_characters;
    unsigned int n_groups;
    /* dimension contains the actual vector dimension, e.g 2,
       while VECTOR_DIMENSION_MAX contains the vector dimension plus some
       padding, e.g. 4 */
    unsigned int dimension;
    unsigned int downsample_threshold;

    Character *characters;
    CharacterGroup *groups;
    float *strokedata;

    char *error_msg;
    float dtwm[4000000];
   
    CharDist *distm;

    inline float dtw(float *s, unsigned int n, float *t, unsigned int m);
    inline float euclidean_distance(float *v1, float *v2);
};

}

#endif


