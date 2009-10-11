modelfile=handwriting-zh_TW

$(modelfile).model: $(modelfile).xml
	tegaki-build -c $(modelfile).xml zinnia $(modelfile).meta

installpath=/usr/local/share/tegaki/models/zinnia/

install: $(modelfile).model
	mkdir -p $(installpath)
	install -c $(modelfile).meta $(modelfile).model $(installpath)
