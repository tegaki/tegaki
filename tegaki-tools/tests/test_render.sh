#!/bin/sh

mkdir -p /tmp/tegaki-render
rm -rf /tmp/tegaki-render/*

for ext in png pdf svg; do

./src/tegaki-render tests/data/39365.xml /tmp/tegaki-render/39365-1.$ext

./src/tegaki-render tests/data/39365.xml /tmp/tegaki-render/39365-2.$ext \
    --steps

./src/tegaki-render tests/data/39365.xml /tmp/tegaki-render/39365-3.$ext \
    --steps --steps-groups 1,1,3,1,4,2,2

./src/tegaki-render tests/data/39365.xml /tmp/tegaki-render/39365-4.$ext \
    --steps --steps-n-chars-per-row 5

./src/tegaki-render tests/data/39365.xml /tmp/tegaki-render/39365-5.$ext \
    --without-circles --without-annot --stroke-width 8

done

./src/tegaki-render tests/data/39365.xml /tmp/tegaki-render/39365-1.gif \
    --without-annot --loop
./src/tegaki-render tests/data/39365.xml /tmp/tegaki-render/39365-2.gif \
    --stroke-by-stroke --without-annot
./src/tegaki-render tests/data/39365.xml /tmp/tegaki-render/39365-3.gif \
    --stroke-by-stroke --without-annot --frame-duration 1000

