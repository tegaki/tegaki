#! /bin/sh

# This script is copied and adapted from the Advene project.
# See http://liris.cnrs.fr/advene/

#sudo chmod 755 /opt

Basedir=./dist/tegaki-recognize.app
Frameworks=${Basedir}/Contents/Frameworks
Resources=${Basedir}/Contents/Resources
MacOS=${Basedir}/Contents/MacOS

rm -rf build dist
cp bin/tegaki-recognize bin/tegaki-recognize.py
/opt/local/bin/python setup.py py2app
rm bin/tegaki-recognize.py

# Copy pango and pixbuf loader modules
mkdir -p ${Resources}/lib/pango/1.6.0/modules

echo "Copying all Pango modules ..."
cp -R /opt/local/lib/pango/1.6.0/modules/*.so ${Resources}/lib/pango/1.6.0/modules/

echo "Copying GTK modules"
cp -r /opt/local/lib/gtk-2.0 $Resources/lib

# generate new pango.modules file
mkdir -p ${Resources}/etc/pango/

/opt/local/bin/pango-querymodules | sed "s?/opt/local/lib/pango/1.6.0/modules/?../Resources/lib/pango/1.6.0/modules/?" > $Resources/etc/pango/pango.modules

# Generate pangorc 
cat > $Resources/etc/pango/pangorc <<EOF 
[Pango]
ModuleFiles=./etc/pango/pango.modules
EOF

# Copy the fonts.conf file
mkdir -p ${Resources}/etc/fonts/conf.d
cp osx/fonts.conf $Resources/etc/fonts/fonts.conf
cp /opt/local/etc/fonts/conf.avail/* ${Resources}/etc/fonts/conf.d/

# Remove any reference to Verdana, since it makes Pango unusable
#perl -pi -e 's/.*verdana.*//i' $Resources/fonts.conf

# generate a new GDK pixbufs loaders file
mkdir -p $Resources/etc/gtk-2.0/
#GDK_PIXBUF_MODULEDIR=/Users/mathieublondel/Desktop/projects/hwr/tegaki-recognize/dist/tegaki-recognize.app/Contents/Resources/lib/gtk-2.0/2.10.0/loaders/ /opt/local/bin/gdk-pixbuf-query-loaders > $Resources/etc/gtk-2.0/gdk-pixbuf.loaders
sed "s?/opt/local/lib/gtk-2.0/2.10.0/loaders/?../Resources/lib/gtk-2.0/2.10.0/loaders/?" < /opt/local/etc/gtk-2.0/gdk-pixbuf.loaders > $Resources/etc/gtk-2.0/gdk-pixbuf.loaders

# Some libraries (pixbufloader-gif, pixbufloader-xpm, svg_loader) have too large dependencies. 
ln -s ../Frameworks ${MacOS}/f

# Copy gtk python modules. This will override the py2app way (creating a _gtk.pyc wrapper in the site-packages.zip, which tries to load _gtk.so from lib-dynload, but it crashes)
cp -r /opt/local/lib/python2.5/site-packages/gtk-2.0/* $Resources/lib/python2.5

echo "Fixing library names ..."
# fix the libraries we include
for dylib in $Frameworks/*.dylib ${Resources}/lib/pango/1.6.0/modules/*.so $Resources/lib/gtk-2.0/2.10.0/*/*.so $Resources/lib/python2.5/*.so $Resources/lib/python2.5/*/*.so 
do
    # skip symlinks
    if test ! -L $dylib ; then
	
	# change all the dependencies

	changes=""
	for lib in `otool -L $dylib | egrep "(/opt/local|/local/|libs/)" | awk '{print $1}'` ; do
	    base=`basename $lib`
	    #changes="$changes -change $lib @executable_path/../Frameworks/$base"
	    changes="$changes -change $lib @executable_path/f/$base"
	done

	if test "x$changes" != x ; then
	    if  install_name_tool $changes $dylib ; then
		:
	    else
                echo "Error for $dylib"
		#exit 1
	    fi
	fi

	# now the change what the library thinks its own name is

	base=`basename $dylib`
	#install_name_tool -id @executable_path/../Frameworks/$base $dylib
	install_name_tool -id @executable_path/f/$base $dylib
    fi
done

# Copy french gtk2.0 locale
#cp -r /opt/local/share/locale/fr/LC_MESSAGES/*.mo ${Resources}/locale/fr/LC_MESSAGES

# Copy Tegaki engines
mkdir -p  $Resources/engines
cp ../tegaki-python/tegaki/engines/*.*  $Resources/engines/

mv ${MacOS}/tegaki-recognize ${MacOS}/tegaki-recognize.bin
cp osx/tegaki-recognize.sh $MacOS/tegaki-recognize
chmod 755 $MacOS/tegaki-recognize

# Make sure that macports don't interfere with the bundle
#sudo chmod 0 /opt
