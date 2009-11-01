modelfile=handwriting-zh_CN

$(modelfile).model: $(modelfile).xml
	tegaki-build -t $(modelfile).xml wagomu $(modelfile).meta

installpath=/usr/local/share/tegaki/models/wagomu/

install: $(modelfile).model
	mkdir -p $(installpath)
	install -c $(modelfile).meta $(modelfile).model $(installpath)
