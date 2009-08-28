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

#ifdef __SSE__
#include <xmmintrin.h>
#endif

namespace wagomu {

class Character {

public:
    Character(unsigned int n_vectors, unsigned int n_strokes);
    ~Character();

    float *get_points();
    unsigned int get_n_vectors();
    unsigned int get_n_strokes();
    void set_value(unsigned int i, float value);

private:
    float *points;
    unsigned int n_vectors;
    unsigned int n_strokes;
};

class Results {

public:
    Results(unsigned int size);
    ~Results();

#ifndef SWIG
    /* This method is public but is not meant to be called from Python */ 
    void add(unsigned i, unsigned int unicode, float dist);
#endif
    unsigned int get_unicode(unsigned int i);
    float get_distance(unsigned int i);
    unsigned int get_size();

private:
    unsigned int *unicode;
    float *dist;
    unsigned int size;
};

#ifndef SWIG
typedef struct {
    unsigned int unicode;
    float dist;
} CharDist;

typedef struct {
    unsigned int unicode;
    unsigned int n_vectors;
} CharacterInfo;

typedef struct {
    unsigned int n_strokes;
    unsigned int n_chars;
    unsigned int offset;
    char pad[4];
} CharacterGroup;

#ifdef __SSE__
typedef union {
    __m128 v;
    float s[4];
} wg_v4sf;
#endif

#endif /* SWIG */

class Recognizer {

public:
    Recognizer();
    ~Recognizer();

    bool open(char *path);
    Results *recognize(Character *ch, unsigned int n_results);
    unsigned int get_n_characters();
    unsigned int get_dimension();
    unsigned int get_window_size();
    void set_window_size(unsigned int size);
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

    CharacterInfo *characters;
    CharacterGroup *groups;
    float *strokedata;

#ifdef __SSE__
    wg_v4sf *dtw1v;
    wg_v4sf *dtw2v;
#endif

    float *dtw1;
    float *dtw2;

    char *error_msg;

    CharDist *distm;

    unsigned int window_size;

    unsigned int get_max_n_vectors();

    inline float local_distance(float *v1, float *v2);

    inline float dtw(float *s, unsigned int n, float *t, unsigned int m);

#ifdef __SSE__
    inline wg_v4sf local_distance4(float *s,
                                   float *t0,
                                   float *t1,
                                   float *t2,
                                   float *t3);

    inline wg_v4sf dtw4(float *s, unsigned int n, 
                        float *t0, unsigned int m0,
                        float *t1, unsigned int m1,
                        float *t2, unsigned int m2,
                        float *t3, unsigned int m3);
#endif

};

}

#endif


