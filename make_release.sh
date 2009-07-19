#!/bin/sh

RM="`which rm` -vrf"
MKDIR="`which mkdir` -p"

TMP_DIR="/tmp/tegaki"
PACKAGES="tegaki-python tegaki-pygtk scim-tegaki tegaki-recognize"
PACKAGES="$PACKAGES tegaki-train tegaki-tools"
PACKAGES="$PACKAGES tegaki-models/tegaki-zinnia-japanese"
PACKAGES="$PACKAGES tegaki-models/tegaki-zinnia-simplified-chinese"

echo "Creating temporary directory..."
$RM $TMP_DIR
$MKDIR $TMP_DIR

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
    python setup.py sdist
    cp dist/*.tar.gz $TMP_DIR/
    )
done