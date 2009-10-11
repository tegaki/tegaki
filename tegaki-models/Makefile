all=tegaki-zinnia-japanese tegaki-zinnia-japanese-light \
tegaki-zinnia-japanese-joyo tegaki-zinnia-japanese-kyoiku \
tegaki-zinnia-simplified-chinese tegaki-zinnia-simplified-chinese-light \
tegaki-zinnia-traditional-chinese

alldist=tegaki-zinnia-japanese-dist tegaki-zinnia-japanese-light-dist \
tegaki-zinnia-japanese-joyo-dist tegaki-zinnia-japanese-kyoiku-dist \
tegaki-zinnia-simplified-chinese-dist \
tegaki-zinnia-simplified-chinese-light-dist \
tegaki-zinnia-traditional-chinese-dist

all: $(all)

# shortcuts
tzj: tegaki-zinnia-japanese
tzjl: tegaki-zinnia-japanese-light
tzjk: tegaki-zinnia-japanese-kyoiku
tzjj: tegaki-zinnia-japanese-joyo
tzsc: tegaki-zinnia-simplified-chinese
tzscl: tegaki-zinnia-simplified-chinese-light
tztc: tegaki-zinnia-traditional-chinese

# build japanese
tegaki-zinnia-japanese: tegaki-zinnia-japanese-build data/train/japanese/handwriting-ja.xml
	cp -u -p data/train/japanese/handwriting-ja.xml build/$@/
	make -C build/$@

tegaki-zinnia-japanese-kyoiku: tegaki-zinnia-japanese-kyoiku-build data/train/japanese/handwriting-ja.xml
	tegaki-convert -t data/train/japanese/handwriting-ja.xml --include data/script/kyoiku-kanji.txt build/$@/kyoiku-kanji.xml
	touch -r data/train/japanese/handwriting-ja.xml build/$@/kyoiku-kanji.xml
	make -C build/$@

tegaki-zinnia-japanese-joyo: tegaki-zinnia-japanese-joyo-build data/train/japanese/handwriting-ja.xml
	tegaki-convert -t data/train/japanese/handwriting-ja.xml --include data/script/joyo-kanji.txt build/$@/joyo-kanji.xml
	touch -r data/train/japanese/handwriting-ja.xml build/$@/joyo-kanji.xml
	make -C build/$@

# build simplified-chinese
tegaki-zinnia-simplified-chinese: tegaki-zinnia-simplified-chinese-build data/train/simplified-chinese/handwriting-zh_CN.xml
	cp -u -p data/train/simplified-chinese/handwriting-zh_CN.xml build/$@
	make -C build/$@

# build traditional chinese
tegaki-zinnia-traditional-chinese: tegaki-zinnia-traditional-chinese-build data/train/traditional-chinese/handwriting-zh_TW.xml data/train/traditional-chinese/out-domain data/train/simplified-chinese/handwriting-zh_CN.xml data/train/japanese/handwriting-ja.xml
	tegaki-bootstrap -q --domain=BIG5 --locale=T --max-samples=1 \
build/$@/handwriting-zh_TW.xml \
-c data/train/traditional-chinese/handwriting-zh_TW.xml \
-d data/train/traditional-chinese/out-domain \
-t data/train/simplified-chinese/handwriting-zh_CN.xml \
-t data/train/japanese/handwriting-ja.xml
	make -C build/$@

# prepare build-directory
tegaki-zinnia-japanese-build tegaki-zinnia-japanese-joyo-build tegaki-zinnia-japanese-kyoiku-build tegaki-zinnia-simplified-chinese-build tegaki-zinnia-traditional-chinese-build:
	model=$(subst -build,,$@); \
	mkdir -p build/$$model; \
	cp $$model/* build/$$model/; \
	sed "s?\[recognizer-name\]?zinnia?" < README.in > build/$$model/README.txt; \
	cp LGPL build/$$model/COPYING

# light models
tegaki-zinnia-japanese-light: tegaki-zinnia-japanese
	rm -rf build/$@
	cp -R -p build/tegaki-zinnia-japanese build/$@
	zinnia_convert -c 0.005 build/tegaki-zinnia-japanese-light/handwriting-ja.model.txt \
build/tegaki-zinnia-japanese-light/handwriting-ja.model

tegaki-zinnia-simplified-chinese-light: tegaki-zinnia-simplified-chinese
	rm -rf build/$@
	cp -R -p build/tegaki-zinnia-simplified-chinese build/$@
	zinnia_convert -c 0.005 build/tegaki-zinnia-simplified-chinese-light/handwriting-zh_CN.model.txt \
build/tegaki-zinnia-simplified-chinese-light/handwriting-zh_CN.model

tegaki-zinnia-traditional-chinese-light: tegaki-zinnia-traditional-chinese
	rm -rf build/$@
	cp -R -p build/tegaki-zinnia-traditional-chinese build/$@
	zinnia_convert -c 0.005 build/tegaki-zinnia-traditional-chinese-light/handwriting-zh_TW.model.txt \
build/tegaki-zinnia-traditional-chinese-light/handwriting-zh_TW.model

# prepare all zip files
dist: $(alldist)

$(alldist): $(all)
	model=$(subst -dist,,$@); \
	version=`cat build/$$model/VERSION`; \
	mkdir -p dist; \
	rm -rf dist/$$model; \
	cp -R build/$$model dist/$$model-$$version; \
	rm dist/*/*.model.txt ; \
	(cd dist/; rm $$model-$$version.zip; zip -r $$model-$$version.zip $$model-$$version) ; \
	rm -rf dist/$$model-$$version

# force to rebuild next time!
clean:
	rm -rf build/*
