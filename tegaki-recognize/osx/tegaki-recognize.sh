#! /bin/sh

d=`dirname "$0"`
parent=`dirname "$d"`
# Ensure that we get an absolute path
parent=`(cd "$parent" ; pwd)`
res=$parent/Resources

echo "tegaki-recognize.app started at "  `date` " on " `uname -a`
X11APP=/Applications/Utilities/X11.app
if [ ! -x $X11APP ]
then
   osascript -e 'tell application "Finder" to display dialog "No X11 server found. Please install it from the MacOS X install disc, package System/Installation/Packages/X11User.pkg"'
   exit 0
fi

FONTCONFIG_FILE=$res/etc/fonts/fonts.conf TEGAKI_ENGINE_PATH=$res/engines/  PANGO_RC_FILE=$res/etc/pango/pangorc  GDK_PIXBUF_MODULE_FILE=$res/etc/gtk-2.0/gdk-pixbuf.loaders GTK_PATH=$res GTK_EXE_PREFIX=$res $res/../MacOS/tegaki-recognize.bin
