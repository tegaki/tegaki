modelfile=handwriting-ja

$(modelfile).model: $(modelfile).xml
	tegaki-build -t $(modelfile).xml zinnia $(modelfile).meta

installpath=/usr/local/share/tegaki/models/zinnia/

install: $(modelfile).model
	mkdir -p $(installpath)
	install -c $(modelfile).meta $(modelfile).model $(installpath)
