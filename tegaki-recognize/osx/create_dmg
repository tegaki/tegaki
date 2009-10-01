#! /bin/sh

# This script is copied and adapted from the Advene project.
# See http://liris.cnrs.fr/advene/

version=$1
if [ -z "$version" ]
then
  echo "Syntaxe: $0 version"
  exit 1
fi

echo "Creating image tegaki-recognize-${version}.dmg"

/usr/bin/hdiutil create -fs HFS+ -format UDZO -imagekey zlib-level=9 -srcfolder dist/tegaki-recognize.app  -volname tegaki-recognize-${version} dist/tegaki-recognize-${version}.dmg
