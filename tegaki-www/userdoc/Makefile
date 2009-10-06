all: index.html userdoc.pdf

index.html: userdoc.txt
	# the markdown and pandoc packages from Debian/Ubuntu are needed to run this
	echo "<html>\n<body>\n<title>Tegaki User Documentation</title>\n</head>\n" > index.html
	markdown userdoc.txt >> index.html
	echo "</html>" >> index.html

userdoc.pdf: userdoc.txt
	markdown2pdf userdoc.txt -o userdoc.pdf
