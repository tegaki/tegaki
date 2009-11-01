#!/bin/sh

RM="`which rm` -vrf"
MKDIR="`which mkdir` -p"

DIST_DIR="`pwd`/dist/"
PACKAGES="tegaki-python tegaki-pygtk scim-tegaki tegaki-recognize"
PACKAGES="$PACKAGES tegaki-train tegaki-tools"
PACKAGES="$PACKAGES tegaki-train tegaki-tools"
PACKAGES="$PACKAGES tegaki-engines/tegaki-wagomu"

echo "Creating dist directory $DIST_DIR..."
$RM $DIST_DIR
$MKDIR $DIST_DIR

echo "Cleaning directories..."
for package in $PACKAGES; do
    $RM $package/build
    $RM $package/dist
done

echo "Building archives..."
for package in $PACKAGES; do
    (
    echo "$package..."
    cd $package
    git log -- ./ > ChangeLog
    python setup.py sdist
    cp dist/*.tar.gz $DIST_DIR/
    )
done