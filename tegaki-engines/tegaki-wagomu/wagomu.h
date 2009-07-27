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
    Results(int size);
    ~Results();

    void add(int i, char *utf8, float dist);
    char *get_utf8(int i);
    float get_distance(int i);
    int get_size();

private:
    char **utf8;
    float *dist;
    int size;
};

typedef struct {
    char *utf8;
    float dist;
} CharDist;

class Recognizer {

public:
    ~Recognizer();

    bool open(char *path);
    Results *recognize(float *points, 
                       unsigned short n_vectors, 
                       unsigned short n_results);
    unsigned long get_n_characters();
    unsigned short get_dimension();
    char *get_error_message();

private:
    GMappedFile *file;
    char *data;

    unsigned long n_characters;
    unsigned short dimension;
    char *error_msg;
    float dtwm[4000000];
   
    CharDist *distm;

    inline float dtw(float *s, unsigned short n, float *t, unsigned short m);
    inline float euclidean_distance(float *v1, float *v2);
};

}

#endif


